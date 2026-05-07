"""Performance por Fase do Funil.

Usa regex match definido em `user_data/config/fases.json` para classificar cada
campanha em uma fase (ex: TOPO/MEIO/FUNDO ou custom). Agrega métricas por fase
e mostra onde está o gargalo do investimento.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import config as cfg
from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class FaseMetricas:
    id: str
    label: str
    cor: str
    spend: float
    impressions: float
    clicks: float
    inline_link_clicks: float
    results: float
    revenue: float
    cpm: float
    cpc: float
    ctr: float
    cpa: float
    roas: float
    share_spend: float = 0.0  # preenchido após agregação


# --- Classificação por nome de campanha -----------------------------------

def classificar_campanha(campaign_name: str, regex_match: dict[str, list[str]]) -> str:
    """Retorna o id da fase cuja regex casa primeiro; `outros` se nenhuma."""
    if not campaign_name:
        return "outros"
    nome = campaign_name.lower()
    for fase_id, patterns in regex_match.items():
        for p in patterns:
            try:
                if re.search(p, nome, re.IGNORECASE):
                    return fase_id
            except re.error:
                continue
    return "outros"


def _aggregate(rows: list[dict[str, Any]]) -> tuple[float, float, float, float, float, float]:
    spend = impressions = clicks = inline = results = revenue = 0.0
    for r in rows:
        spend += float(r.get("spend") or 0)
        impressions += float(r.get("impressions") or 0)
        clicks += float(r.get("clicks") or 0)
        inline += float(r.get("inline_link_clicks") or 0)
        purchases = mc.extract_action_count(r.get("actions"), "purchase")
        leads = mc.extract_action_count(r.get("actions"), "lead")
        results += purchases or leads
        revenue += mc.extract_action_value(r.get("action_values"), "purchase")
    return spend, impressions, clicks, inline, results, revenue


def agrupar_por_fase(
    rows: list[dict[str, Any]],
    fases_config: dict[str, Any],
) -> list[FaseMetricas]:
    fases = fases_config.get("fases", [])
    regex_match = fases_config.get("regex_match", {})

    # Bucketeia
    buckets: dict[str, list[dict]] = {f["id"]: [] for f in fases}
    buckets["outros"] = []

    for r in rows:
        fid = classificar_campanha(r.get("campaign_name") or "", regex_match)
        if fid not in buckets:
            fid = "outros"
        buckets[fid].append(r)

    # Calcula métricas por bucket
    out: list[FaseMetricas] = []
    for f in fases:
        rows_f = buckets.get(f["id"], [])
        spend, impr, clicks, inline, results, revenue = _aggregate(rows_f)
        out.append(
            FaseMetricas(
                id=f["id"],
                label=f["label"],
                cor=f.get("cor", "#999"),
                spend=spend,
                impressions=impr,
                clicks=clicks,
                inline_link_clicks=inline,
                results=results,
                revenue=revenue,
                cpm=m.cpm(spend, impr),
                cpc=m.cpc(spend, inline or clicks),
                ctr=m.ctr(inline, impr),
                cpa=m.cpa(spend, results),
                roas=m.roas(revenue, spend),
            )
        )

    # "outros" fase (sem label configurada)
    rows_outros = buckets.get("outros", [])
    if rows_outros:
        spend, impr, clicks, inline, results, revenue = _aggregate(rows_outros)
        out.append(
            FaseMetricas(
                id="outros",
                label="Outros (sem match)",
                cor="#6b7280",
                spend=spend,
                impressions=impr,
                clicks=clicks,
                inline_link_clicks=inline,
                results=results,
                revenue=revenue,
                cpm=m.cpm(spend, impr),
                cpc=m.cpc(spend, inline or clicks),
                ctr=m.ctr(inline, impr),
                cpa=m.cpa(spend, results),
                roas=m.roas(revenue, spend),
            )
        )

    # Share de gasto
    total_spend = sum(f.spend for f in out)
    if total_spend > 0:
        for f in out:
            f.share_spend = f.spend / total_spend * 100

    return out


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows = meta.get_ad_insights(
        ad_account_id,
        since=periodo.since,
        until=periodo.until,
        filtering=filtering,
    )

    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    fases_config = cfg.get_fases()
    if not fases_config.get("fases"):
        return (
            "Nenhuma fase cadastrada. Rode `trafego setup` e escolha um template de fases.",
            None,
        )

    metricas_por_fase = agrupar_por_fase(rows, fases_config)

    # Identifica fase com melhor e pior CPA
    com_cpa = [f for f in metricas_por_fase if f.cpa > 0 and f.results > 0]
    melhor_cpa = min(com_cpa, key=lambda f: f.cpa) if com_cpa else None
    pior_cpa = max(com_cpa, key=lambda f: f.cpa) if com_cpa else None

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "fases": metricas_por_fase,
        "melhor_cpa": melhor_cpa,
        "pior_cpa": pior_cpa,
        "total_spend": sum(f.spend for f in metricas_por_fase),
        "total_results": sum(f.results for f in metricas_por_fase),
    }
    filename = report.build_output_filename("fases", produto_nome)
    return report.render_markdown("fases.md.j2", context, output_filename=filename)
