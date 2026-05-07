"""Análise 4.1 — Health Score da Conta (0-100).

Pontuação geral composta por 5 dimensões VTSD:
  - Diversidade criativa (cobertura da Mandala) — 20%
  - Saúde de públicos (frequência, temperatura) — 20%
  - Eficiência de funil (etapas acima do threshold) — 25%
  - Performance financeira (ROAS, CPL vs benchmark) — 25%
  - Consistência temporal (variação de CPL) — 10%

Ver `skill/SKILL.md` para referência original da persona Sofia.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class DimensaoHealth:
    nome: str
    peso_pct: float
    score: float      # 0-100
    comentario: str


@dataclass
class HealthResult:
    score_total: float
    classificacao: str
    emoji: str
    dimensoes: list[DimensaoHealth]
    resumo_sofia: str


def _score_diversidade_criativa(tipos_presentes: int, total: int = 18) -> tuple[float, str]:
    """Diversidade = cobertura Mandala. 18/18 = 100."""
    pct = (tipos_presentes / total) * 100
    if pct >= 60:
        com = f"Mandala bem coberta ({tipos_presentes}/{total})."
    elif pct >= 33:
        com = f"Diversidade média ({tipos_presentes}/{total}) — explorar mais tipos."
    else:
        com = f"Pouca diversidade ({tipos_presentes}/{total}) — risco alto de fadiga simultânea."
    return min(pct, 100), com


def _score_saude_publicos(freq_media: float, mix_ok: bool) -> tuple[float, str]:
    """Frequência + mix HOT/COLD equilibrado."""
    score = 100.0
    problemas = []

    if freq_media > 5.0:
        score -= 50
        problemas.append(f"Frequência {freq_media:.1f} crítica")
    elif freq_media > 3.5:
        score -= 25
        problemas.append(f"Frequência {freq_media:.1f} em alerta")
    elif freq_media < 1.5:
        score -= 10
        problemas.append(f"Frequência {freq_media:.1f} muito baixa (pouco alcance)")

    if not mix_ok:
        score -= 20
        problemas.append("Mix HOT/COLD/SUPERCOLD desbalanceado")

    com = "Públicos saudáveis." if not problemas else "; ".join(problemas)
    return max(0, score), com


def _score_funil(etapas_saudaveis: int, etapas_totais: int) -> tuple[float, str]:
    if etapas_totais == 0:
        return 50.0, "Dados insuficientes (sem pixel/CAPI)."
    pct = etapas_saudaveis / etapas_totais * 100
    com = f"{etapas_saudaveis}/{etapas_totais} etapas do funil dentro do ideal."
    return pct, com


def _score_financeiro(roas: float, cpa_pct_ticket: float) -> tuple[float, str]:
    score = 50.0
    if roas >= 3.0:
        score = 85
    elif roas >= 2.0:
        score = 65
    elif roas > 0:
        score = 40

    if cpa_pct_ticket > 40:
        score = min(score, 35)
    elif cpa_pct_ticket > 25:
        score = min(score, 60)

    if roas == 0:
        return 30.0, "Sem ROAS detectável — verificar pixel/CAPI"

    return score, f"ROAS {roas:.2f}x · CPA {cpa_pct_ticket:.0f}% do ticket"


def _score_consistencia(variacao_cpl_pct: float) -> tuple[float, str]:
    if variacao_cpl_pct < 15:
        return 95.0, f"CPL consistente (variação {variacao_cpl_pct:.0f}%)."
    if variacao_cpl_pct < 30:
        return 70.0, f"CPL moderadamente variável ({variacao_cpl_pct:.0f}%)."
    return 40.0, f"CPL instável (variação {variacao_cpl_pct:.0f}%) — investigar sazonalidade ou fadiga."


def calcular_health(inputs: dict[str, Any]) -> HealthResult:
    """inputs esperados:
    - tipos_presentes_mandala (int)
    - freq_media (float)
    - mix_ok (bool)
    - etapas_saudaveis (int)
    - etapas_totais (int)
    - roas (float)
    - cpa_pct_ticket (float)
    - variacao_cpl_pct (float)
    """
    s_diver, c_diver = _score_diversidade_criativa(inputs.get("tipos_presentes_mandala", 0))
    s_publ, c_publ = _score_saude_publicos(inputs.get("freq_media", 0), inputs.get("mix_ok", False))
    s_funil, c_funil = _score_funil(
        inputs.get("etapas_saudaveis", 0), inputs.get("etapas_totais", 0),
    )
    s_fin, c_fin = _score_financeiro(inputs.get("roas", 0), inputs.get("cpa_pct_ticket", 0))
    s_cons, c_cons = _score_consistencia(inputs.get("variacao_cpl_pct", 0))

    dimensoes = [
        DimensaoHealth("Diversidade Criativa (Mandala)", 20, s_diver, c_diver),
        DimensaoHealth("Saúde de Públicos", 20, s_publ, c_publ),
        DimensaoHealth("Eficiência de Funil", 25, s_funil, c_funil),
        DimensaoHealth("Performance Financeira", 25, s_fin, c_fin),
        DimensaoHealth("Consistência Temporal", 10, s_cons, c_cons),
    ]

    total = sum(d.score * d.peso_pct / 100 for d in dimensoes)

    if total >= 85:
        cat, emoji, resumo = "Excelente", "🟢", (
            "Conta saudável, foco em escala. As três identidades do VTSD (Consumidor, "
            "Produto, Comunicador) estão alinhadas. Escalar respeitando curva é a jogada."
        )
    elif total >= 70:
        cat, emoji, resumo = "Boa", "🟡", (
            "Conta funcionando bem, otimizações pontuais. Identificar 1-2 dimensões "
            "mais baixas e agir nelas eleva o score pro verde."
        )
    elif total >= 50:
        cat, emoji, resumo = "Regular", "🟠", (
            "Problemas específicos a resolver antes de escalar. "
            "Nas dimensões mais baixas: seu budget está sendo mal alocado."
        )
    else:
        cat, emoji, resumo = "Crítica", "🔴", (
            "PARAR escalada. Diagnóstico profundo urgente. "
            "Geralmente combinação de público saturado + criativo fadigado + oferta não clara."
        )

    return HealthResult(
        score_total=total,
        classificacao=cat,
        emoji=emoji,
        dimensoes=dimensoes,
        resumo_sofia=resumo,
    )


def _collect_inputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Coleta inputs das análises individuais pra compor o health."""
    from trafego_analysis.analyses.funil_waterfall import construir_waterfall
    from trafego_analysis.analyses.mandala_vtsd import analisar_rows as mandala_rows
    from trafego_analysis.analyses.prospeccao_retargeting import calcular_mix

    # Mandala
    mandala = mandala_rows(rows, creative_fetcher=None)
    tipos_presentes = mandala["cobertura_atual"]

    # Públicos
    mix = calcular_mix(rows)
    total_impr = sum(float(r.get("impressions") or 0) for r in rows)
    freq_w = sum(
        float(r.get("frequency") or 0) * float(r.get("impressions") or 0) for r in rows
    )
    freq_media = (freq_w / total_impr) if total_impr else 0
    mix_ok = mix.hot_pct < 50 and mix.cold_pct > 20

    # Funil
    wf = construir_waterfall(rows)
    etapas_com_taxa = [e for e in wf.etapas if e.taxa_passagem is not None and e.saudavel_min is not None]
    etapas_saudaveis = sum(1 for e in etapas_com_taxa if e.taxa_passagem >= e.saudavel_min)
    etapas_totais = len(etapas_com_taxa)

    # Financeiro
    total_spend = sum(float(r.get("spend") or 0) for r in rows)
    total_purchases = sum(mc.extract_action_count(r.get("actions"), "purchase") for r in rows)
    total_revenue = sum(mc.extract_action_value(r.get("action_values"), "purchase") for r in rows)
    roas = m.roas(total_revenue, total_spend)
    cpa = m.cpa(total_spend, total_purchases) if total_purchases > 0 else 0
    cpa_pct = (cpa / 297 * 100) if cpa else 0  # ticket default 297 — ideal passar ticket real

    return {
        "tipos_presentes_mandala": tipos_presentes,
        "freq_media": freq_media,
        "mix_ok": mix_ok,
        "etapas_saudaveis": etapas_saudaveis,
        "etapas_totais": etapas_totais,
        "roas": roas,
        "cpa_pct_ticket": cpa_pct,
        "variacao_cpl_pct": 20,  # placeholder — calculo real exige série temporal
    }


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    ticket: float = 297,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows = meta.get_ad_insights(
        ad_account_id, since=periodo.since, until=periodo.until, filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    inputs = _collect_inputs(rows)
    if ticket > 0:
        # Recalcula cpa_pct com ticket real
        total_spend = sum(float(r.get("spend") or 0) for r in rows)
        total_p = sum(mc.extract_action_count(r.get("actions"), "purchase") for r in rows)
        cpa = m.cpa(total_spend, total_p) if total_p > 0 else 0
        inputs["cpa_pct_ticket"] = (cpa / ticket * 100) if cpa else 0

    health = calcular_health(inputs)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "ticket": ticket,
        "health": health,
    }
    filename = report.build_output_filename("health-score", produto_nome)
    return report.render_markdown("health_score.md.j2", context, output_filename=filename)
