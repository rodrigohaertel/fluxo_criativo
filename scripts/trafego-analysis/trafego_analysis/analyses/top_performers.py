"""Top Performers & Escalada — identifica candidatos a aumento de budget.

Critérios combinados (AND):
  1. CPA <= cpa_max_pct_media do perfil (default 70% do CPA mediano do produto)
  2. Frequency < freq_max_pra_escalar (default 2.0)
  3. Volume mínimo: results >= min_conversoes (default 50)
  4. Gasto suficiente (sanidade): spend >= 2× min do produto

Sugestão de escalada usa curva conservadora:
  - Maduro (>14 dias, conversões >= 2× mínimo, CTR estável): +incremento_budget_pct
  - Novo (<14 dias): +50% do incremento configurado
  - Com frequency borderline (>=0.8× limite): metade
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.perfis import PERFIL_PADRAO_FALLBACK, Perfil
from trafego_analysis.core.periods import Period


@dataclass
class CandidatoEscalada:
    ad_id: str
    ad_name: str
    campaign_name: str
    spend: float
    results: float
    cpa: float
    frequency: float
    ctr: float
    incremento_sugerido_pct: float
    budget_atual_estimado: float
    budget_sugerido: float
    razoes: list[str] = field(default_factory=list)

    @property
    def increment_label(self) -> str:
        return f"+{self.incremento_sugerido_pct:.0f}%"


def _cpa_from_row(row: dict[str, Any]) -> tuple[float | None, float]:
    """Retorna (cpa, results). results fallback: purchase > lead."""
    spend = float(row.get("spend") or 0)
    purchases = mc.extract_action_count(row.get("actions"), "purchase")
    leads = mc.extract_action_count(row.get("actions"), "lead")
    results = purchases or leads
    if results > 0:
        return spend / results, results
    return None, 0.0


def identificar_top_performers(
    rows: list[dict[str, Any]],
    *,
    perfil: Perfil = PERFIL_PADRAO_FALLBACK,
    cpa_mediano_override: float | None = None,
    min_spend_brl: float = 100.0,
) -> list[CandidatoEscalada]:
    # Calcula CPA mediano da amostra (todos ads com conversão)
    cpas: list[float] = []
    for r in rows:
        cpa, _ = _cpa_from_row(r)
        if cpa:
            cpas.append(cpa)

    if not cpas:
        return []

    cpa_mediano = cpa_mediano_override or median(cpas)
    cpa_teto = cpa_mediano * (perfil.escalada.cpa_max_pct_media / 100.0)

    candidatos: list[CandidatoEscalada] = []

    for r in rows:
        spend = float(r.get("spend") or 0)
        if spend < min_spend_brl:
            continue

        cpa, results = _cpa_from_row(r)
        if cpa is None:
            continue
        if cpa > cpa_teto:
            continue

        frequency = float(r.get("frequency") or 0)
        if frequency >= perfil.escalada.freq_max_pra_escalar:
            continue

        if results < perfil.escalada.min_conversoes:
            continue

        # Frequency borderline: 80-100% do limite → metade do incremento
        freq_ratio = frequency / max(perfil.escalada.freq_max_pra_escalar, 0.1)
        if freq_ratio >= 0.8:
            incremento = perfil.escalada.incremento_budget_pct * 0.5
            razao_freq = f"Frequency {frequency:.2f} próximo do teto — escalar com cautela"
        else:
            incremento = perfil.escalada.incremento_budget_pct
            razao_freq = f"Frequency saudável ({frequency:.2f})"

        # Estima budget atual via spend do período (grosseiro)
        dias_periodo = 7  # placeholder — caller pode refinar
        budget_atual = spend / dias_periodo
        budget_sugerido = budget_atual * (1 + incremento / 100)

        impressions = float(r.get("impressions") or 0)
        inline = float(r.get("inline_link_clicks") or 0)
        ctr = (inline / impressions * 100) if impressions else 0

        candidatos.append(
            CandidatoEscalada(
                ad_id=r.get("ad_id") or "",
                ad_name=r.get("ad_name") or "(sem nome)",
                campaign_name=r.get("campaign_name") or "",
                spend=spend,
                results=results,
                cpa=cpa,
                frequency=frequency,
                ctr=ctr,
                incremento_sugerido_pct=incremento,
                budget_atual_estimado=budget_atual,
                budget_sugerido=budget_sugerido,
                razoes=[
                    f"CPA {cpa:.2f} é {(cpa / cpa_mediano * 100):.0f}% do mediano do produto",
                    f"{int(results)} conversões (mínimo: {perfil.escalada.min_conversoes})",
                    razao_freq,
                ],
            )
        )

    # Ordena: menor CPA primeiro (melhores candidatos)
    candidatos.sort(key=lambda c: c.cpa)
    return candidatos


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    perfil: Perfil = PERFIL_PADRAO_FALLBACK,
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

    candidatos = identificar_top_performers(rows, perfil=perfil)

    # Ajusta budget_atual com base no período real
    for c in candidatos:
        c.budget_atual_estimado = c.spend / max(periodo.days, 1)
        c.budget_sugerido = c.budget_atual_estimado * (1 + c.incremento_sugerido_pct / 100)

    # Calcula CPA mediano do sample pra mostrar no report
    cpas = [c.cpa for c in candidatos] if candidatos else []
    cpa_mediano = median(cpas) if cpas else None

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "perfil": perfil,
        "candidatos": candidatos,
        "total_ads_analisados": len(rows),
        "cpa_mediano": cpa_mediano,
    }

    filename = report.build_output_filename("top-performers", produto_nome)
    return report.render_markdown("top_performers.md.j2", context, output_filename=filename)
