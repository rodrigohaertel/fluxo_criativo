"""Baseline rolling por produto e fase.

A cada métrica (CPA, CTR, CPM, frequency) calcula percentis P25/P50/P75
sobre janela rolling (default 30 dias). Persistido em SQLite para evitar
recomputação, com invalidação por TTL de 6 horas.

Interface principal:
  compute_baseline(meta, ad_account_id, produto_nome, fase_id, janela_dias=30)

Retorna BaselineStats com percentis e amostragem usada.
"""

from __future__ import annotations

import sqlite3
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core.config import get_paths

BASELINE_SCHEMA = """
CREATE TABLE IF NOT EXISTS baseline (
    key             TEXT PRIMARY KEY,
    payload         TEXT NOT NULL,
    created_at      INTEGER NOT NULL,
    ttl_s           INTEGER NOT NULL
);
"""


@dataclass
class BaselineStats:
    """Percentis rolling para uma métrica específica."""

    metrica: str
    p25: float | None
    p50: float | None  # mediana
    p75: float | None
    n_amostras: int
    janela_dias: int

    @property
    def tem_dados_suficientes(self) -> bool:
        """≥10 amostras é o mínimo para percentis fazerem sentido."""
        return self.n_amostras >= 10


@dataclass
class Baseline:
    """Conjunto completo de baselines por métrica para produto+fase."""

    produto: str | None
    fase: str | None
    ad_account_id: str
    janela_dias: int
    stats: dict[str, BaselineStats] = field(default_factory=dict)

    def cpa_p50(self) -> float | None:
        s = self.stats.get("cpa")
        return s.p50 if s else None

    def ctr_p50(self) -> float | None:
        s = self.stats.get("ctr")
        return s.p50 if s else None


# --- Cálculo --------------------------------------------------------------

def _percentis(valores: list[float]) -> tuple[float | None, float | None, float | None]:
    """Retorna (P25, P50, P75) ou (None, None, None) se amostra insuficiente."""
    limpos = [v for v in valores if v is not None and v > 0]
    if len(limpos) < 4:
        return None, None, None
    q = statistics.quantiles(limpos, n=4)
    return q[0], q[1], q[2]


def _compute_stats(rows: list[dict[str, Any]]) -> dict[str, BaselineStats]:
    """Gera BaselineStats para cada métrica a partir dos rows de ad insights."""
    cpas: list[float] = []
    ctrs: list[float] = []
    cpms: list[float] = []
    freqs: list[float] = []

    for row in rows:
        impressions = float(row.get("impressions") or 0)
        spend = float(row.get("spend") or 0)
        if impressions < 500 or spend < 10:
            continue  # amostra fraca — polui a mediana

        # CPA — prefere purchase, fallback lead
        purchases = mc.extract_action_count(row.get("actions"), "purchase")
        leads = mc.extract_action_count(row.get("actions"), "lead")
        results = purchases or leads
        if results > 0:
            cpas.append(spend / results)

        # CTR link
        inline = float(row.get("inline_link_clicks") or 0)
        if inline > 0:
            ctrs.append(m.ctr(inline, impressions))
        else:
            ctr_geral = float(row.get("ctr") or 0)
            if ctr_geral > 0:
                ctrs.append(ctr_geral)

        # CPM
        cpms.append(m.cpm(spend, impressions))

        # Frequency
        f = float(row.get("frequency") or 0)
        if f > 0:
            freqs.append(f)

    out: dict[str, BaselineStats] = {}
    for nome, valores in [("cpa", cpas), ("ctr", ctrs), ("cpm", cpms), ("frequency", freqs)]:
        p25, p50, p75 = _percentis(valores)
        out[nome] = BaselineStats(
            metrica=nome,
            p25=p25,
            p50=p50,
            p75=p75,
            n_amostras=len(valores),
            janela_dias=0,  # preenchido pelo caller
        )
    return out


def _filter_fase(rows: list[dict[str, Any]], regex_list: list[str]) -> list[dict[str, Any]]:
    """Filtra rows cuja `campaign_name` bate com algum regex da lista."""
    if not regex_list:
        return rows
    import re

    patterns = [re.compile(p, re.IGNORECASE) for p in regex_list]
    return [r for r in rows if any(p.search(r.get("campaign_name") or "") for p in patterns)]


def _filter_produto(rows: list[dict[str, Any]], produto_nome: str) -> list[dict[str, Any]]:
    """Filtra rows cuja campanha contém o nome do produto (case-insensitive)."""
    nome = produto_nome.lower()
    return [r for r in rows if nome in (r.get("campaign_name") or "").lower()]


# --- Cache persistente ----------------------------------------------------

@contextmanager
def _baseline_conn():
    path = get_paths().insights_db
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(BASELINE_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _cache_key(ad_account_id: str, produto: str | None, fase: str | None, janela_dias: int) -> str:
    return f"{ad_account_id}::{produto or 'all'}::{fase or 'all'}::{janela_dias}"


def _load_cached(key: str, ttl_s: int = 6 * 3600) -> Baseline | None:
    import json

    now = int(time.time())
    with _baseline_conn() as c:
        row = c.execute(
            "SELECT payload, created_at FROM baseline WHERE key = ?", (key,)
        ).fetchone()
    if not row:
        return None
    payload, created_at = row
    if now - created_at > ttl_s:
        return None
    data = json.loads(payload)
    stats = {
        nome: BaselineStats(**s)
        for nome, s in data.get("stats", {}).items()
    }
    return Baseline(
        produto=data.get("produto"),
        fase=data.get("fase"),
        ad_account_id=data.get("ad_account_id"),
        janela_dias=data.get("janela_dias", 30),
        stats=stats,
    )


def _save_cache(key: str, baseline: Baseline) -> None:
    import json
    from dataclasses import asdict

    with _baseline_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO baseline (key, payload, created_at, ttl_s) VALUES (?, ?, ?, ?)",
            (
                key,
                json.dumps(asdict(baseline)),
                int(time.time()),
                6 * 3600,
            ),
        )


# --- API principal ---------------------------------------------------------

def compute_baseline(
    meta: mc.MetaClient,
    ad_account_id: str,
    *,
    produto_nome: str | None = None,
    fase_regex: list[str] | None = None,
    fase_id: str | None = None,
    janela_dias: int = 30,
    today: date | None = None,
    force_refresh: bool = False,
) -> Baseline:
    """Calcula baselines rolling para o subset (produto, fase) na janela.

    Se `produto_nome` ou `fase_regex` forem None, não aplica o filtro correspondente.
    Usa cache SQLite (TTL 6h) exceto se `force_refresh=True`.
    """
    today = today or date.today()
    key = _cache_key(ad_account_id, produto_nome, fase_id, janela_dias)

    if not force_refresh:
        cached = _load_cached(key)
        if cached:
            return cached

    rows = meta.get_ad_insights(
        ad_account_id,
        since=today - timedelta(days=janela_dias),
        until=today - timedelta(days=1),
    )

    if produto_nome:
        rows = _filter_produto(rows, produto_nome)
    if fase_regex:
        rows = _filter_fase(rows, fase_regex)

    stats = _compute_stats(rows)
    for s in stats.values():
        s.janela_dias = janela_dias

    baseline = Baseline(
        produto=produto_nome,
        fase=fase_id,
        ad_account_id=ad_account_id,
        janela_dias=janela_dias,
        stats=stats,
    )
    _save_cache(key, baseline)
    return baseline


def invalidate_baseline_cache() -> int:
    with _baseline_conn() as c:
        cursor = c.execute("DELETE FROM baseline")
        return cursor.rowcount
