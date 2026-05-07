"""Análise 4.6 — Plano de Otimização Executivo.

Consolida as outras análises em um **único relatório executivo** com:
  - Status geral (Health Score)
  - Top 3 alertas
  - Top 3 oportunidades de escala
  - Pausas recomendadas
  - Plano de ação ordenado (próximos 7 dias)

É o "relatório pra mostrar ao chefe / decision-maker".
"""

from __future__ import annotations

from typing import Any

from trafego_analysis.analyses.alertas_prioritarios import gerar_alertas
from trafego_analysis.analyses.conta_health import _collect_inputs, calcular_health
from trafego_analysis.analyses.pausa_hierarquica import decidir_pausas
from trafego_analysis.analyses.top_performers import identificar_top_performers
from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.perfis import PERFIL_PADRAO_FALLBACK
from trafego_analysis.core.periods import Period


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

    # 1. Health Score
    inputs = _collect_inputs(rows)
    health = calcular_health(inputs)

    # 2. Alertas
    alertas = gerar_alertas(rows)
    top_alertas = alertas[:3]

    # 3. Oportunidades de escala
    top_perf = identificar_top_performers(rows, perfil=PERFIL_PADRAO_FALLBACK)
    top_escala = top_perf[:3]

    # 4. Pausas recomendadas
    pausas = decidir_pausas(rows)
    top_pausas = pausas[:5]

    economia_pausas = sum(p.economia_estimada for p in top_pausas)
    economia_escala_potencial = sum(c.budget_sugerido - c.budget_atual_estimado for c in top_escala)

    # 5. Plano ordenado
    plano: list[dict[str, str]] = []

    if health.score_total < 50:
        plano.append({
            "ordem": "1",
            "prazo": "hoje",
            "acao": "CONGELAR escalada. Executar todas as pausas críticas antes de qualquer coisa.",
            "urgencia": "CRÍTICA",
        })

    if top_pausas:
        plano.append({
            "ordem": str(len(plano) + 1),
            "prazo": "24h",
            "acao": f"Executar {len(top_pausas)} pausas (economia ~{economia_pausas:.0f} R$/dia).",
            "urgencia": "ALTA",
        })

    if top_alertas:
        plano.append({
            "ordem": str(len(plano) + 1),
            "prazo": "24-48h",
            "acao": f"Resolver top {len(top_alertas)} alertas prioritários.",
            "urgencia": "ALTA",
        })

    if top_escala and health.score_total >= 70:
        plano.append({
            "ordem": str(len(plano) + 1),
            "prazo": "3-7 dias",
            "acao": (
                f"Escalar top {len(top_escala)} performers (+{economia_escala_potencial:.0f} R$/dia budget). "
                "Respeitar curva: incremento → esperar 3-4 dias → avaliar."
            ),
            "urgencia": "MÉDIA",
        })

    if health.score_total < 70:
        plano.append({
            "ordem": str(len(plano) + 1),
            "prazo": "7 dias",
            "acao": "Rodar Mandala VTSD (`trafego mandala`) e produzir 3-5 criativos novos dos tipos ausentes.",
            "urgencia": "MÉDIA",
        })

    plano.append({
        "ordem": str(len(plano) + 1),
        "prazo": "semana 2",
        "acao": "Rodar `trafego plano-executivo` novamente e comparar health score — era 70, virou 80? Continuar rotina.",
        "urgencia": "BAIXA",
    })

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "health": health,
        "top_alertas": top_alertas,
        "top_escala": top_escala,
        "top_pausas": top_pausas,
        "economia_pausas": economia_pausas,
        "economia_escala_potencial": economia_escala_potencial,
        "plano": plano,
    }
    filename = report.build_output_filename("plano-executivo", produto_nome)
    return report.render_markdown("plano_executivo.md.j2", context, output_filename=filename)
