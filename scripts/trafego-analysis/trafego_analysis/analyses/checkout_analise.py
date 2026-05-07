"""Análise 3.6 — Análise de Checkout.

Foco nas 3 últimas etapas do funil: LPV → Checkout Iniciado → Compra. Detecta
abandono no formulário vs. antes de clicar comprar.

Sem CAPI configurado (ex: Hotmart sem integração), os dados de checkout podem
não vir pelo pixel — a skill sinaliza.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class EtapaCheckout:
    nome: str
    volume: float
    taxa_passagem: float | None
    status: str   # "OK" | "ATENÇÃO" | "CRÍTICO" | "SEM_DADOS"


@dataclass
class AnaliseCheckout:
    etapas: list[EtapaCheckout]
    abandono_pre_checkout: float        # % que chegou na LP mas não clicou em comprar
    abandono_durante_checkout: float    # % iniciou checkout mas não concluiu
    maior_vazamento: str
    diagnostico_vtsd: str
    acoes: list[str]


def analisar_rows(rows: list[dict[str, Any]]) -> AnaliseCheckout:
    total_lpv = sum(
        mc.extract_action_count(r.get("actions"), "landing_page_view") for r in rows
    )
    total_ic = sum(
        mc.extract_action_count(r.get("actions"), "initiate_checkout") for r in rows
    )
    total_p = sum(
        mc.extract_action_count(r.get("actions"), "purchase") for r in rows
    )

    # Taxa LPV → IC (% que chegou na LP e clicou em comprar)
    taxa_lpv_ic = (total_ic / total_lpv * 100) if total_lpv > 0 else None
    # Taxa IC → P (% do checkout que virou compra)
    taxa_ic_p = (total_p / total_ic * 100) if total_ic > 0 else None

    etapas = [
        EtapaCheckout(
            nome="Landing Page Views",
            volume=total_lpv,
            taxa_passagem=None,
            status="SEM_DADOS" if total_lpv == 0 else "OK",
        ),
        EtapaCheckout(
            nome="Checkout Iniciado",
            volume=total_ic,
            taxa_passagem=taxa_lpv_ic,
            status=(
                "SEM_DADOS" if taxa_lpv_ic is None else
                "OK" if taxa_lpv_ic >= 20 else
                "ATENÇÃO" if taxa_lpv_ic >= 10 else
                "CRÍTICO"
            ),
        ),
        EtapaCheckout(
            nome="Compras",
            volume=total_p,
            taxa_passagem=taxa_ic_p,
            status=(
                "SEM_DADOS" if taxa_ic_p is None else
                "OK" if taxa_ic_p >= 30 else
                "ATENÇÃO" if taxa_ic_p >= 15 else
                "CRÍTICO"
            ),
        ),
    ]

    abandono_pre = 100 - (taxa_lpv_ic or 0) if taxa_lpv_ic is not None else 0
    abandono_dur = 100 - (taxa_ic_p or 0) if taxa_ic_p is not None else 0

    # Identifica maior vazamento
    if taxa_lpv_ic is not None and taxa_ic_p is not None:
        if abandono_pre > abandono_dur * 2:
            maior = "pre_checkout"
            diag = (
                "**Maior vazamento ANTES do checkout.** Pessoas chegam na LP mas não clicam "
                "em comprar. No VTSD isso aponta para **Oferta não percebida** ou "
                "**Quadro na Parede** não convincente. Problema de PÁGINA, não de pagamento."
            )
            acoes = [
                "Revisar **Oferta** — preço visível? Garantia clara? Escassez?",
                "Revisar **Quadro na Parede** — o resultado final está tangível?",
                "Prova social perto do CTA",
                "Testar CTA em 2+ locais da página (topo, meio, fim)",
            ]
        elif abandono_dur > 50:
            maior = "durante_checkout"
            diag = (
                "**Maior vazamento DURANTE o checkout.** Pessoas clicam em comprar mas abandonam "
                "no pagamento. Problema de UX/fricção — não é VTSD, é técnico."
            )
            acoes = [
                "Reduzir campos do formulário de checkout",
                "Formas de pagamento e parcelamento bem no topo",
                "Badge de segurança visível",
                "Testar checkout em mobile (1/3 dos abandonos vem daí)",
                "Se ticket alto: adicionar opção de PIX",
            ]
        else:
            maior = "equilibrado"
            diag = "Abandonos balanceados — sem gargalo único."
            acoes = [
                "Testar pequenas otimizações em cada etapa",
                "Acompanhar tendência semanal — piora em uma etapa sinaliza foco",
            ]
    else:
        maior = "sem_dados"
        diag = (
            "⚠️ **Dados de checkout ausentes.** Se o produto é Hotmart (ou similar), "
            "normalmente precisa configurar CAPI (Conversions API) para eventos "
            "`initiate_checkout` e `purchase` chegarem no pixel Meta."
        )
        acoes = [
            "Configurar CAPI Hotmart → Meta (docs.hotmart.com)",
            "Ou colar dados manualmente para análise mais precisa",
        ]

    return AnaliseCheckout(
        etapas=etapas,
        abandono_pre_checkout=abandono_pre,
        abandono_durante_checkout=abandono_dur,
        maior_vazamento=maior,
        diagnostico_vtsd=diag,
        acoes=acoes,
    )


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

    resultado = analisar_rows(rows)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "resultado": resultado,
    }
    filename = report.build_output_filename("checkout", produto_nome)
    return report.render_markdown("checkout.md.j2", context, output_filename=filename)
