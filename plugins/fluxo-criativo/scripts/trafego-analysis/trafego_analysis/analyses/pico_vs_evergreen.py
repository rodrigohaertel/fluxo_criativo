"""Análise 3.5 — Pico vs. Evergreen (comparativo de urgência).

Compara performance em período de Pico (com urgência embutida) vs. Evergreen
(sem urgência). Diagnóstico: o produto depende de urgência ou funciona no
always-on?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class PicoEvergreen:
    pico_spend: float
    pico_cpa: float
    pico_roas: float
    evergreen_spend: float
    evergreen_cpa: float
    evergreen_roas: float
    delta_cpa_pct: float        # positivo = evergreen mais caro que pico
    delta_roas_pct: float
    conclusao: str


def comparar(
    rows_pico: list[dict[str, Any]],
    rows_evergreen: list[dict[str, Any]],
) -> PicoEvergreen:
    def _agg(rows):
        spend = sum(float(r.get("spend") or 0) for r in rows)
        results = sum(
            mc.extract_action_count(r.get("actions"), "purchase")
            or mc.extract_action_count(r.get("actions"), "lead") for r in rows
        )
        revenue = sum(
            mc.extract_action_value(r.get("action_values"), "purchase") for r in rows
        )
        cpa = m.cpa(spend, results)
        roas = m.roas(revenue, spend)
        return spend, cpa, roas

    p_spend, p_cpa, p_roas = _agg(rows_pico)
    e_spend, e_cpa, e_roas = _agg(rows_evergreen)

    delta_cpa = ((e_cpa - p_cpa) / p_cpa * 100) if p_cpa > 0 else 0
    delta_roas = ((e_roas - p_roas) / p_roas * 100) if p_roas > 0 else 0

    # Conclusão VTSD
    if p_cpa > 0 and e_cpa > 0 and delta_cpa > 50:
        conclusao = (
            f"🔴 **Produto depende MUITO de urgência** — Evergreen {delta_cpa:.0f}% mais caro que Pico. "
            "No VTSD isso aponta que o perpétuo precisa embutir elemento de urgência "
            "(prazo, bônus limitado, janela fechada mensal) ou o CPL fica inviável."
        )
    elif delta_cpa > 20:
        conclusao = (
            "🟡 **Produto moderadamente dependente de urgência.** "
            f"Evergreen paga {delta_cpa:.0f}% a mais. Otimização: adicionar elementos "
            "de urgência no VVV ou Isca Digital do perpétuo."
        )
    elif p_cpa > 0 and e_cpa > 0:
        conclusao = (
            "🟢 **Produto performa bem no Evergreen.** "
            "CPA similar entre Pico e Perpétuo — não depende de urgência forçada. "
            "A Furadeira + Decorados estão funcionando sozinhos."
        )
    else:
        conclusao = (
            "Dados insuficientes para conclusão. Colete pelo menos 2 períodos "
            "com padrões diferentes (com e sem Pico) antes de comparar."
        )

    return PicoEvergreen(
        pico_spend=p_spend,
        pico_cpa=p_cpa,
        pico_roas=p_roas,
        evergreen_spend=e_spend,
        evergreen_cpa=e_cpa,
        evergreen_roas=e_roas,
        delta_cpa_pct=delta_cpa,
        delta_roas_pct=delta_roas,
        conclusao=conclusao,
    )


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo_pico: Period,
    periodo_evergreen: Period,
    produto_nome: str | None = None,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows_pico = meta.get_ad_insights(
        ad_account_id, since=periodo_pico.since, until=periodo_pico.until, filtering=filtering,
    )
    rows_evergreen = meta.get_ad_insights(
        ad_account_id, since=periodo_evergreen.since, until=periodo_evergreen.until, filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows_pico = [r for r in rows_pico if nome_low in (r.get("campaign_name") or "").lower()]
        rows_evergreen = [r for r in rows_evergreen if nome_low in (r.get("campaign_name") or "").lower()]

    resultado = comparar(rows_pico, rows_evergreen)

    context = {
        "produto": produto_nome or "todos",
        "periodo_pico": periodo_pico,
        "periodo_evergreen": periodo_evergreen,
        "resultado": resultado,
    }
    filename = report.build_output_filename("pico-vs-evergreen", produto_nome)
    return report.render_markdown(
        "pico_evergreen.md.j2", context, output_filename=filename,
    )
