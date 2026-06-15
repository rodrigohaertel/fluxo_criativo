"""Análise 3.3 — Projeção de Escala.

Com base no CPA atual, frequência e saturação, estima como o CPA evolui se o
budget for dobrado/triplicado. Resposta direta ao operador: **posso subir
agora ou não?**
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class Cenario:
    multiplicador_budget: float       # 1.5x, 2x, 3x
    cpa_estimado: float
    delta_cpa_pct: float
    nivel_risco: str                  # baixo | medio | alto
    recomendacao: str


def projetar(cpa_atual: float, frequencia: float, budget_atual: float) -> list[Cenario]:
    """Projeta CPA futuro em 3 cenários (1.5x, 2x, 3x o budget)."""
    cenarios: list[Cenario] = []

    for mult in (1.5, 2.0, 3.0):
        # Heurística: quanto maior a freq, maior o CPA drift ao escalar
        if frequencia < 2.0:
            base_drift = 5 + (mult - 1) * 10      # 1.5x: +10%, 2x: +15%, 3x: +25%
        elif frequencia < 3.5:
            base_drift = 10 + (mult - 1) * 15     # 1.5x: +17%, 2x: +25%, 3x: +40%
        elif frequencia < 5.0:
            base_drift = 20 + (mult - 1) * 25     # 1.5x: +32%, 2x: +45%, 3x: +70%
        else:
            base_drift = 40 + (mult - 1) * 40     # saturação: drift alto

        cpa_est = cpa_atual * (1 + base_drift / 100)

        if base_drift < 15:
            risco = "baixo"
            rec = "Escalar livremente respeitando curva de 3-4 dias."
        elif base_drift < 30:
            risco = "medio"
            rec = "Escalar com cautela. Monitorar 48h. Se CPA subir >15%, recuar."
        elif base_drift < 50:
            risco = "alto"
            rec = "NÃO escalar nesse multiplicador. Ampliar audiência antes."
        else:
            risco = "alto"
            rec = "INVIÁVEL. Público saturado, multiplicador quebra o ROAS."

        cenarios.append(Cenario(
            multiplicador_budget=mult,
            cpa_estimado=cpa_est,
            delta_cpa_pct=base_drift,
            nivel_risco=risco,
            recomendacao=rec,
        ))

    return cenarios


def analisar_rows(rows: list[dict[str, Any]], periodo_dias: int) -> dict[str, Any]:
    total_spend = sum(float(r.get("spend") or 0) for r in rows)
    total_impr = sum(float(r.get("impressions") or 0) for r in rows)
    total_results = sum(
        mc.extract_action_count(r.get("actions"), "purchase")
        or mc.extract_action_count(r.get("actions"), "lead")
        for r in rows
    )

    freq_weighted = sum(
        float(r.get("frequency") or 0) * float(r.get("impressions") or 0) for r in rows
    )
    freq_media = (freq_weighted / total_impr) if total_impr else 0
    cpa_atual = m.cpa(total_spend, total_results) if total_results > 0 else 0
    budget_diario = total_spend / max(periodo_dias, 1)

    cenarios = projetar(cpa_atual, freq_media, budget_diario) if cpa_atual > 0 else []

    return {
        "cpa_atual": cpa_atual,
        "frequencia_atual": freq_media,
        "budget_diario": budget_diario,
        "total_results": total_results,
        "cenarios": cenarios,
    }


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows = meta.get_ad_insights(
        ad_account_id, since=periodo.since, until=periodo.until, filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    resultado = analisar_rows(rows, periodo_dias=periodo.days)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        **resultado,
    }
    filename = report.build_output_filename("projecao", produto_nome)
    return report.render_markdown("projecao.md.j2", context, output_filename=filename)
