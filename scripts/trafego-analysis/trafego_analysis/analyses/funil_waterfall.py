"""Funil Waterfall — diagnóstico ponta a ponta do funil de conversão.

Calcula o "caminho" percorrido pelo público desde a impressão do ad até a compra:

  Impression → 3s View → Link Click → LP View → VSL Start → VSL 55% → Checkout Init → Purchase

Para cada etapa, mostra:
  - Volume absoluto
  - Taxa de passagem (etapa_n / etapa_anterior)
  - Drop % (quanto foi perdido na transição)

Identifica a etapa de MAIOR perda relativa — o "gargalo" real do funil. Como
cada etapa tem um playbook diferente de correção, saber QUAL está furando muda
a ação inteira.

Este módulo é agnóstico: a Meta nem sempre expõe todos os eventos (ex: VSL 55%
só vem se houver custom event ou player Wistia/Panda integrado). Quando um
evento não vem, a linha fica marcada como "sem dados" em vez de inferir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class EtapaFunil:
    id: str
    label: str
    volume: float
    taxa_passagem: float | None     # % do passo anterior que chegou aqui
    drop_pct: float | None          # % perdido na transição
    saudavel_min: float | None      # benchmark mínimo para a taxa
    tem_dados: bool = True


@dataclass
class WaterfallResult:
    etapas: list[EtapaFunil] = field(default_factory=list)
    gargalo: EtapaFunil | None = None
    etapas_sem_dados: list[str] = field(default_factory=list)


# Benchmarks BR 2026 para taxa de passagem em cada etapa (% do anterior)
BENCHMARKS_ETAPAS = {
    "view_3s": 25.0,                 # Hook rate
    "link_click": 1.5,               # CTR link
    "lp_view": 70.0,                 # Connect rate
    "vsl_start": 40.0,               # Offer rate
    "vsl_55pct": 55.0,               # True play
    "initiate_checkout": 20.0,       # % LPV → checkout (varia muito por produto)
    "purchase": 30.0,                # CR checkout
}


# Mapa etapa → action_type da Meta (quando aplicável)
ACTION_TYPE_MAP = {
    "link_click": "link_click",
    "lp_view": "landing_page_view",
    "initiate_checkout": "initiate_checkout",
    "purchase": "purchase",
}


def _sum_metric(rows: list[dict[str, Any]], metric: str) -> float:
    return sum(float(r.get(metric) or 0) for r in rows)


def _sum_action(rows: list[dict[str, Any]], action_type: str) -> float:
    total = 0.0
    for r in rows:
        total += mc.extract_action_count(r.get("actions"), action_type)
    return total


def _sum_video_action(rows: list[dict[str, Any]], field_name: str) -> float:
    """Soma o valor `video_view` do array de `video_*_watched_actions`."""
    total = 0.0
    for r in rows:
        arr = r.get(field_name)
        if not arr:
            continue
        for a in arr:
            if a.get("action_type") in ("video_view", "video_play_actions"):
                total += float(a.get("value") or 0)
    return total


def construir_waterfall(rows: list[dict[str, Any]]) -> WaterfallResult:
    # Coleta volumes brutos por etapa
    impressions = _sum_metric(rows, "impressions")
    v3s = _sum_video_action(rows, "video_30_sec_watched_actions")
    if v3s == 0:
        v3s = _sum_video_action(rows, "video_p25_watched_actions")
    # 55% video watched — proxy via p50 (hold rate calculado separadamente em outras análises)
    vsl_55 = _sum_video_action(rows, "video_p50_watched_actions")

    link_clicks = _sum_metric(rows, "inline_link_clicks")
    if link_clicks == 0:
        link_clicks = _sum_action(rows, "link_click")
    lp_views = _sum_action(rows, "landing_page_view")
    checkout = _sum_action(rows, "initiate_checkout")
    purchases = _sum_action(rows, "purchase")

    etapas_def = [
        ("impression",        "Impressões",              impressions,   None),
        ("view_3s",           "3s views (hook)",         v3s,           "view_3s"),
        ("link_click",        "Cliques no link",         link_clicks,   "link_click"),
        ("lp_view",           "Landing page views",      lp_views,      "lp_view"),
        ("vsl_55pct",         "VSL 55%+",                vsl_55,        "vsl_55pct"),
        ("initiate_checkout", "Início de checkout",      checkout,      "initiate_checkout"),
        ("purchase",          "Compras",                 purchases,     "purchase"),
    ]

    result = WaterfallResult()
    vol_anterior: float | None = None

    for etapa_id, label, volume, bench_key in etapas_def:
        tem_dados = volume > 0 or etapa_id == "impression"
        taxa = None
        drop = None
        if tem_dados and vol_anterior is not None and vol_anterior > 0:
            taxa = volume / vol_anterior * 100
            drop = 100 - taxa

        bench = BENCHMARKS_ETAPAS.get(bench_key) if bench_key else None
        etapa = EtapaFunil(
            id=etapa_id,
            label=label,
            volume=volume,
            taxa_passagem=taxa,
            drop_pct=drop,
            saudavel_min=bench,
            tem_dados=tem_dados,
        )
        result.etapas.append(etapa)

        if not tem_dados:
            result.etapas_sem_dados.append(label)
        if tem_dados:
            vol_anterior = volume

    # Identifica gargalo: maior drop relativo entre as etapas que têm benchmark
    candidatos_gargalo = [
        e for e in result.etapas
        if e.drop_pct is not None and e.saudavel_min is not None
        and e.taxa_passagem is not None
        and e.taxa_passagem < e.saudavel_min
    ]
    if candidatos_gargalo:
        # Pior é a que está mais distante do mínimo saudável (em pontos %)
        candidatos_gargalo.sort(
            key=lambda e: (e.saudavel_min or 0) - (e.taxa_passagem or 0),
            reverse=True,
        )
        result.gargalo = candidatos_gargalo[0]

    return result


def diagnostico_playbook(gargalo: EtapaFunil | None) -> str:
    """Retorna playbook de correção para o gargalo identificado."""
    if not gargalo:
        return (
            "Nenhum gargalo crítico detectado — todas as etapas rastreáveis estão "
            "dentro ou acima do benchmark. Foque em escalar winners (`trafego top-performers`)."
        )
    playbooks = {
        "view_3s": (
            "Gargalo no **hook do criativo**. Os primeiros 3 segundos não estão "
            "parando o scroll. Ações: (1) reformule a abertura do vídeo com hook "
            "mais forte — pergunta, polêmica, prova ou promessa; (2) varie "
            "thumbnail/primeiro frame; (3) rode variações A/B só do hook."
        ),
        "link_click": (
            "Gargalo no **CTR**. O criativo segura atenção mas não converte em "
            "clique. Ações: (1) CTA mais claro no copy e/ou botão; (2) prova "
            "social visível antes do CTA; (3) teste um gancho diferente na chamada."
        ),
        "lp_view": (
            "Gargalo na **landing page**. As pessoas clicam mas não chegam (ou "
            "saltam imediatamente). Ações: (1) verifique velocidade de carregamento "
            "(<3s mobile); (2) coerência entre promessa do ad e LP — quebra de "
            "expectativa derruba tudo; (3) mobile-first — 80%+ do tráfego vem de "
            "celular."
        ),
        "vsl_55pct": (
            "Gargalo no **VSL / oferta**. Pessoas começam mas abandonam antes da "
            "metade. Ações: (1) primeiros 60s do VSL — hook da mensagem; (2) "
            "subtítulos e thumbnails dentro do vídeo para re-engajar; (3) "
            "revisite promessa do VSL — está genérica?"
        ),
        "initiate_checkout": (
            "Gargalo na **decisão de compra**. Pessoas assistem mas não clicam "
            "pra comprar. Ações: (1) urgência / escassez genuína; (2) garantia "
            "visível; (3) prova social específica do tipo de cliente; (4) "
            "revisite o preço percebido vs valor entregue."
        ),
        "purchase": (
            "Gargalo no **checkout**. Iniciam o pagamento mas abandonam. Ações: "
            "(1) reduza campos do formulário; (2) mostre formas de pagamento "
            "e parcelamento no topo; (3) badge de segurança; (4) teste checkout "
            "em mobile — 1/3 dos abandonos vem daí."
        ),
    }
    return playbooks.get(
        gargalo.id,
        f"Gargalo em **{gargalo.label}** — taxa {gargalo.taxa_passagem:.1f}% "
        f"vs mínimo saudável de {gargalo.saudavel_min:.1f}%.",
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
        ad_account_id,
        since=periodo.since,
        until=periodo.until,
        filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    waterfall = construir_waterfall(rows)
    playbook = diagnostico_playbook(waterfall.gargalo)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "etapas": waterfall.etapas,
        "gargalo": waterfall.gargalo,
        "etapas_sem_dados": waterfall.etapas_sem_dados,
        "playbook": playbook,
    }
    filename = report.build_output_filename("funil", produto_nome)
    return report.render_markdown("funil.md.j2", context, output_filename=filename)
