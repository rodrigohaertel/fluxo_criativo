"""Comparativo Período a Período — WoW / MoM / YoY / customizável.

Compara duas janelas do mesmo tamanho (atual vs anterior) em:
  - Spend, Impressões, Clicks, Results, Revenue
  - CPM, CPC, CTR, CPA, ROAS, Frequency

Interpretação automática: classifica cada delta como saudável / atenção / alerta
com base em direcionalidade (ex: CPA caindo é bom, CTR subindo é bom).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import PeriodComparison


class TipoDelta(StrEnum):
    POSITIVO = "POSITIVO"
    NEGATIVO = "NEGATIVO"
    NEUTRO = "NEUTRO"


@dataclass
class DeltaMetrica:
    nome: str
    valor_atual: float
    valor_anterior: float
    delta_abs: float
    delta_pct: float | None
    unidade: str
    tipo: TipoDelta
    # True se aumentar é bom (revenue), False se aumentar é ruim (CPA)
    direction_up_is_good: bool


# Direção desejada de cada métrica (True = subir é bom)
DIRECTION = {
    "spend": None,                  # neutro — depende do contexto
    "impressions": True,
    "reach": True,
    "clicks": True,
    "inline_link_clicks": True,
    "results": True,
    "revenue": True,
    "cpm": False,                   # queda é bom
    "cpc": False,
    "ctr": True,
    "cpa": False,
    "roas": True,
    "frequency": None,              # neutro — tem zona ideal
}

LABELS = {
    "spend": ("Gasto", "R$"),
    "impressions": ("Impressões", ""),
    "reach": ("Alcance", ""),
    "clicks": ("Cliques", ""),
    "inline_link_clicks": ("Cliques no link", ""),
    "results": ("Conversões", ""),
    "revenue": ("Receita", "R$"),
    "cpm": ("CPM", "R$"),
    "cpc": ("CPC", "R$"),
    "ctr": ("CTR", "%"),
    "cpa": ("CPA", "R$"),
    "roas": ("ROAS", "x"),
    "frequency": ("Frequency", ""),
}


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, float]:
    agg = {
        "spend": 0.0,
        "impressions": 0.0,
        "reach": 0.0,
        "clicks": 0.0,
        "inline_link_clicks": 0.0,
        "results": 0.0,
        "revenue": 0.0,
    }
    freq_weighted = 0.0

    for r in rows:
        spend = float(r.get("spend") or 0)
        impr = float(r.get("impressions") or 0)

        agg["spend"] += spend
        agg["impressions"] += impr
        agg["reach"] += float(r.get("reach") or 0)
        agg["clicks"] += float(r.get("clicks") or 0)
        agg["inline_link_clicks"] += float(r.get("inline_link_clicks") or 0)

        purchases = mc.extract_action_count(r.get("actions"), "purchase")
        leads = mc.extract_action_count(r.get("actions"), "lead")
        agg["results"] += purchases or leads

        pv = mc.extract_action_value(r.get("action_values"), "purchase")
        agg["revenue"] += pv

        freq_weighted += float(r.get("frequency") or 0) * impr

    # Métricas derivadas
    agg["cpm"] = m.cpm(agg["spend"], agg["impressions"])
    agg["cpc"] = m.cpc(agg["spend"], agg["inline_link_clicks"] or agg["clicks"])
    agg["ctr"] = m.ctr(agg["inline_link_clicks"], agg["impressions"])
    agg["cpa"] = m.cpa(agg["spend"], agg["results"])
    agg["roas"] = m.roas(agg["revenue"], agg["spend"])
    agg["frequency"] = (freq_weighted / agg["impressions"]) if agg["impressions"] else 0

    return agg


def _delta(atual: float, anterior: float) -> tuple[float, float | None]:
    abs_delta = atual - anterior
    if anterior == 0:
        return abs_delta, None
    return abs_delta, (atual - anterior) / anterior * 100


def _classify(metrica: str, pct: float | None) -> TipoDelta:
    if pct is None or abs(pct) < 3:
        return TipoDelta.NEUTRO
    direction = DIRECTION.get(metrica)
    if direction is None:
        return TipoDelta.NEUTRO
    if direction and pct > 0:
        return TipoDelta.POSITIVO
    if not direction and pct < 0:
        return TipoDelta.POSITIVO
    return TipoDelta.NEGATIVO


def comparar(
    rows_atual: list[dict[str, Any]],
    rows_anterior: list[dict[str, Any]],
) -> list[DeltaMetrica]:
    a = _aggregate(rows_atual)
    b = _aggregate(rows_anterior)

    deltas: list[DeltaMetrica] = []
    for k, (label, unit) in LABELS.items():
        abs_d, pct_d = _delta(a.get(k, 0), b.get(k, 0))
        deltas.append(
            DeltaMetrica(
                nome=label,
                valor_atual=a.get(k, 0),
                valor_anterior=b.get(k, 0),
                delta_abs=abs_d,
                delta_pct=pct_d,
                unidade=unit,
                tipo=_classify(k, pct_d),
                direction_up_is_good=DIRECTION.get(k) is True,
            )
        )
    return deltas


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    comparison: PeriodComparison,
    produto_nome: str | None = None,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows_atual = meta.get_ad_insights(
        ad_account_id,
        since=comparison.current.since,
        until=comparison.current.until,
        filtering=filtering,
    )
    rows_anterior = meta.get_ad_insights(
        ad_account_id,
        since=comparison.previous.since,
        until=comparison.previous.until,
        filtering=filtering,
    )

    if produto_nome:
        nome_low = produto_nome.lower()
        rows_atual = [r for r in rows_atual if nome_low in (r.get("campaign_name") or "").lower()]
        rows_anterior = [r for r in rows_anterior if nome_low in (r.get("campaign_name") or "").lower()]

    deltas = comparar(rows_atual, rows_anterior)

    positivos = [d for d in deltas if d.tipo == TipoDelta.POSITIVO]
    negativos = [d for d in deltas if d.tipo == TipoDelta.NEGATIVO]

    context = {
        "produto": produto_nome or "todos",
        "comparison": comparison,
        "deltas": deltas,
        "positivos_count": len(positivos),
        "negativos_count": len(negativos),
    }
    filename = report.build_output_filename("comparativo", produto_nome)
    return report.render_markdown("comparativo.md.j2", context, output_filename=filename)
