"""Análise 4.2 — Alertas Prioritários.

Consolida sinais críticos de toda a conta em lista ranqueada por urgência. É
o "o que preciso fazer AGORA" em um único relatório.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class Alerta:
    severidade: str            # "critica" | "alta" | "media"
    categoria: str
    titulo: str
    descricao: str
    acao: str
    recursos: list[str]        # nomes de ads/adsets/campanhas afetados


def gerar_alertas(rows: list[dict[str, Any]]) -> list[Alerta]:
    alertas: list[Alerta] = []

    # Alerta 1: Ads com gasto alto e zero conversão
    ads_queimando = []
    for r in rows:
        spend = float(r.get("spend") or 0)
        p = mc.extract_action_count(r.get("actions"), "purchase")
        l = mc.extract_action_count(r.get("actions"), "lead")
        if spend > 100 and (p + l) == 0:
            ads_queimando.append((r.get("ad_name") or "?", spend))

    if ads_queimando:
        ads_queimando.sort(key=lambda x: x[1], reverse=True)
        alertas.append(Alerta(
            severidade="critica",
            categoria="Queima de budget",
            titulo=f"{len(ads_queimando)} ads com gasto alto e zero conversão",
            descricao=(
                f"Total queimado: {sum(s for _, s in ads_queimando):.0f} R$. "
                "Pixel quebrado, Oferta não comunicada, ou segmentação absurdamente errada."
            ),
            acao="Pausar hoje e investigar pixel. Se pixel OK, revisar Oferta.",
            recursos=[n for n, _ in ads_queimando[:5]],
        ))

    # Alerta 2: Frequência crítica
    ads_saturados = []
    for r in rows:
        freq = float(r.get("frequency") or 0)
        spend = float(r.get("spend") or 0)
        if freq >= 5.0 and spend > 50:
            ads_saturados.append((r.get("ad_name") or "?", freq))

    if ads_saturados:
        alertas.append(Alerta(
            severidade="alta",
            categoria="Saturação",
            titulo=f"{len(ads_saturados)} ads com frequência ≥ 5.0",
            descricao=(
                "Identidade do Consumidor saturada nesses ads. CPA vai subir 20-40% "
                "nos próximos dias se nada mudar."
            ),
            acao="Ampliar audiência ou criar SUPERCOLD. Não subir budget.",
            recursos=[n for n, _ in ads_saturados[:5]],
        ))

    # Alerta 3: Rankings múltiplos below_average
    ads_ruins = []
    for r in rows:
        rankings = [
            r.get("quality_ranking"),
            r.get("engagement_rate_ranking"),
            r.get("conversion_rate_ranking"),
        ]
        below = sum(
            1 for rr in rankings
            if rr and str(rr).lower().startswith("below_average")
        )
        if below >= 2 and float(r.get("spend") or 0) > 30:
            ads_ruins.append((r.get("ad_name") or "?", below))

    if ads_ruins:
        alertas.append(Alerta(
            severidade="alta",
            categoria="Relevância",
            titulo=f"{len(ads_ruins)} ads com 2+ rankings below_average",
            descricao=(
                "Meta está penalizando esses ads. CPA 30-60% mais alto que o saudável. "
                "Múltiplas identidades VTSD falhando simultaneamente."
            ),
            acao="Pausar ou refazer (não tentar salvar com pequenos ajustes).",
            recursos=[n for n, _ in ads_ruins[:5]],
        ))

    # Alerta 4: CTR crítico com gasto relevante
    ads_ctr_baixo = []
    for r in rows:
        impr = float(r.get("impressions") or 0)
        clicks = float(r.get("inline_link_clicks") or 0)
        spend = float(r.get("spend") or 0)
        if impr > 5000 and spend > 30 and clicks > 0:
            ctr = m.ctr(clicks, impr)
            if ctr < 0.5:
                ads_ctr_baixo.append((r.get("ad_name") or "?", ctr))

    if ads_ctr_baixo:
        alertas.append(Alerta(
            severidade="media",
            categoria="CTR crítico",
            titulo=f"{len(ads_ctr_baixo)} ads com CTR < 0.5%",
            descricao=(
                "Criativo não está chamando clique. Identidade do Produto confusa "
                "ou hook não ativando Urgência Oculta."
            ),
            acao="Testar variação de hook no MESMO criativo, ou substituir.",
            recursos=[n for n, _ in ads_ctr_baixo[:5]],
        ))

    # Ordena por severidade
    ordem = {"critica": 0, "alta": 1, "media": 2}
    alertas.sort(key=lambda a: ordem[a.severidade])
    return alertas


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

    alertas = gerar_alertas(rows)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "alertas": alertas,
        "total": len(alertas),
    }
    filename = report.build_output_filename("alertas", produto_nome)
    return report.render_markdown("alertas.md.j2", context, output_filename=filename)
