"""Análise 3.4 — Caixa Rápido Health Check.

Foco em produtos de ticket baixo (≤ R$ 197) com conversão rápida. ROAS mínimo
3x para viabilidade. Diagnóstico binário: escalar, manter ou pausar.

No VTSD: Caixa Rápido é a linha de frente de monetização — tem que girar
rápido. Se não tá rodando no mínimo 3x, a conta tá queimando caixa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class CaixaResultado:
    roas: float
    cpa: float
    cpa_pct_ticket: float
    ctr: float
    connect_rate: float
    status: str            # "escalar" | "manter" | "otimizar" | "pausar"
    diagnostico: str
    proximos_passos: list[str]


def analisar_rows(
    rows: list[dict[str, Any]],
    ticket: float,
) -> CaixaResultado:
    total_spend = sum(float(r.get("spend") or 0) for r in rows)
    total_clicks = sum(float(r.get("inline_link_clicks") or r.get("clicks") or 0) for r in rows)
    total_impr = sum(float(r.get("impressions") or 0) for r in rows)
    total_purchases = sum(
        mc.extract_action_count(r.get("actions"), "purchase") for r in rows
    )
    total_revenue = sum(
        mc.extract_action_value(r.get("action_values"), "purchase") for r in rows
    )

    # Se Hotmart não conectou, estima receita pelo ticket
    if total_revenue == 0 and total_purchases > 0:
        total_revenue = total_purchases * ticket

    roas = m.roas(total_revenue, total_spend)
    cpa = m.cpa(total_spend, total_purchases) if total_purchases > 0 else 0
    cpa_pct = (cpa / ticket * 100) if ticket > 0 else 0
    ctr = m.ctr(total_clicks, total_impr)
    leads = sum(mc.extract_action_count(r.get("actions"), "lead") for r in rows)
    connect = (total_purchases / leads * 100) if leads > 0 else 0

    # Status binário do Caixa Rápido
    if roas >= 3.0 and cpa_pct <= 25:
        status = "escalar"
        diag = "Caixa Rápido saudável. ROAS acima de 3x e CPA eficiente."
        passos = [
            "Aumentar budget em 25-30% (se freq < 3.5)",
            "Monitorar CPA por 48h após incremento",
            "Preparar criativos reserva para girar se fadiga aparecer",
        ]
    elif roas >= 2.0:
        status = "manter"
        diag = (
            f"Caixa Rápido em zona morna (ROAS {roas:.2f}x). "
            "Manter orçamento atual e otimizar antes de subir."
        )
        passos = [
            "NÃO escalar agora — ROAS precisa chegar a 3x primeiro",
            "Revisar Oferta: preço correto? Escassez clara?",
            "Renovar criativo — provavelmente Urgência Oculta precisa trocar",
        ]
    elif roas > 0:
        status = "otimizar"
        diag = (
            f"Caixa Rápido abaixo da viabilidade (ROAS {roas:.2f}x vs. 3x mínimo). "
            "Revisar antes de pausar."
        )
        passos = [
            "Pausar conjuntos com CPA > 40% do ticket",
            "Revisar **Oferta** (promessa + preço + escassez) — VTSD diz que é aqui",
            "Se após 7 dias não virar, PAUSAR e rever o produto",
        ]
    else:
        status = "pausar"
        diag = "Sem conversões ou ROAS zerado. Não dá pra diagnosticar — pausar e investigar pixel."
        passos = [
            "Verificar pixel de purchase — está disparando?",
            "Checkout acessível? URL quebrada?",
            "Reativar apenas depois de confirmar rastreamento",
        ]

    return CaixaResultado(
        roas=roas,
        cpa=cpa,
        cpa_pct_ticket=cpa_pct,
        ctr=ctr,
        connect_rate=connect,
        status=status,
        diagnostico=diag,
        proximos_passos=passos,
    )


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    ticket: float = 97,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows = meta.get_ad_insights(
        ad_account_id, since=periodo.since, until=periodo.until, filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    resultado = analisar_rows(rows, ticket=ticket)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "ticket": ticket,
        "resultado": resultado,
    }
    filename = report.build_output_filename("caixa-rapido", produto_nome)
    return report.render_markdown("caixa_rapido.md.j2", context, output_filename=filename)
