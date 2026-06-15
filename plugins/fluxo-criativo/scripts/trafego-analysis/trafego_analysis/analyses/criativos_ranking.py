"""Ranking de Criativos — score composto + DNA dos winners.

Score composto por ad (0-100):
  40% hook_rate_normalizado
  30% hold_rate_normalizado
  20% ctr_normalizado
  10% cpa_normalizado_invertido (CPA baixo vira score alto)

Normalização: z-score dentro do sample, convertido pra 0-100 via percentil.

Retorna top N ads ordenados pelo score. Para os top (default 3), extrai DNA via
`criativos_taxonomia.dna_do_ganhador`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report, vtsd
from trafego_analysis.core.periods import Period


@dataclass
class CreativeScore:
    ad_id: str
    ad_name: str
    campaign_name: str
    spend: float
    impressions: float
    # Métricas
    hook_rate: float
    hold_rate: float
    ctr: float
    cpa: float | None
    results: float
    # Score
    score: float = 0.0
    rank: int = 0
    ranking_quality: str = ""
    creative_features: Any = None  # CreativeFeatures opcional


def _extract_video_metrics(row: dict[str, Any]) -> tuple[float, float]:
    """Retorna (video_3s_views, thruplay) extraídos do row."""
    v3s = mc.extract_action_count(row.get("video_30_sec_watched_actions"), "video_view")
    if v3s == 0:
        # Usa p25 como proxy inicial — nem todos os ads têm 30s
        v3s = mc.extract_action_count(row.get("video_p25_watched_actions"), "video_view")
    thruplay = mc.extract_action_count(row.get("video_thruplay_watched_actions"), "video_view")
    # Fallback: p100
    if thruplay == 0:
        thruplay = mc.extract_action_count(row.get("video_p100_watched_actions"), "video_view")
    return v3s, thruplay


def _cpa_from_row(row: dict[str, Any]) -> tuple[float | None, float]:
    spend = float(row.get("spend") or 0)
    purchases = mc.extract_action_count(row.get("actions"), "purchase")
    leads = mc.extract_action_count(row.get("actions"), "lead")
    results = purchases or leads
    if results > 0:
        return spend / results, results
    return None, 0.0


def _percentile(values: list[float], target: float) -> float:
    """Percentil de `target` dentro de `values` (0-100)."""
    if not values:
        return 50.0
    below = sum(1 for v in values if v < target)
    return (below / len(values)) * 100


def _score_composto(
    hook: float, hold: float, ctr: float, cpa: float | None,
    hooks_all: list[float], holds_all: list[float], ctrs_all: list[float], cpas_all: list[float],
) -> float:
    hook_pct = _percentile(hooks_all, hook)
    hold_pct = _percentile(holds_all, hold)
    ctr_pct = _percentile(ctrs_all, ctr)

    # CPA invertido: CPA baixo = percentil alto
    cpa_pct = 0.0
    if cpa is not None and cpas_all:
        raw = _percentile(cpas_all, cpa)
        cpa_pct = 100 - raw

    return 0.40 * hook_pct + 0.30 * hold_pct + 0.20 * ctr_pct + 0.10 * cpa_pct


def ranquear_criativos(
    rows: list[dict[str, Any]],
    *,
    min_impressions: int = 500,
    min_spend_brl: float = 30.0,
) -> list[CreativeScore]:
    pre: list[CreativeScore] = []

    for r in rows:
        impressions = float(r.get("impressions") or 0)
        spend = float(r.get("spend") or 0)
        if impressions < min_impressions or spend < min_spend_brl:
            continue

        v3s, thruplay = _extract_video_metrics(r)
        inline = float(r.get("inline_link_clicks") or 0)
        ctr_atual = m.ctr(inline, impressions)
        hook = m.hook_rate(v3s, impressions)
        hold = m.hold_rate(thruplay, v3s) if v3s > 0 else 0
        cpa, results = _cpa_from_row(r)

        pre.append(
            CreativeScore(
                ad_id=r.get("ad_id") or "",
                ad_name=r.get("ad_name") or "(sem nome)",
                campaign_name=r.get("campaign_name") or "",
                spend=spend,
                impressions=impressions,
                hook_rate=hook,
                hold_rate=hold,
                ctr=ctr_atual,
                cpa=cpa,
                results=results,
            )
        )

    if not pre:
        return []

    hooks_all = [c.hook_rate for c in pre]
    holds_all = [c.hold_rate for c in pre]
    ctrs_all = [c.ctr for c in pre]
    cpas_all = [c.cpa for c in pre if c.cpa is not None]

    for c in pre:
        c.score = _score_composto(
            c.hook_rate, c.hold_rate, c.ctr, c.cpa,
            hooks_all, holds_all, ctrs_all, cpas_all,
        )

    pre.sort(key=lambda x: x.score, reverse=True)
    for i, c in enumerate(pre, 1):
        c.rank = i
        tier = vtsd.classify_tier(c.score)
        # Armazena a letra do tier (S/A/B/C/D) em `ranking_quality`.
        # O template pode reconstruir emoji e texto via `vtsd.classify_tier()` se precisar.
        c.ranking_quality = tier.letra

    return pre


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    account_alias: str,
    periodo: Period,
    produto_nome: str | None = None,
    top_n: int = 10,
    baixar_assets: bool = False,
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

    scores = ranquear_criativos(rows)

    # Top N para DNA
    top = scores[:top_n]

    # Opcional: baixa assets dos top N para extrair features visuais
    dna: dict[str, Any] = {}
    if baixar_assets and top:
        from trafego_analysis.analyses.criativos_taxonomia import (
            dna_do_ganhador,
            extrair_features,
        )
        from trafego_analysis.core import assets as assets_mod

        ad_ids = [c.ad_id for c in top[:3]]  # DNA só dos top 3 por custo
        locais = assets_mod.download_batch(meta, ad_ids, account_alias)

        features_list = []
        for c in top[:3]:
            creative = assets_mod.fetch_ad_creative(meta, c.ad_id)
            local = locais.get(c.ad_id)
            feat = extrair_features(
                c.ad_id,
                local.path if local else None,
                creative,
            )
            c.creative_features = feat
            features_list.append(feat)

        dna = dna_do_ganhador(features_list)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "ranking": scores,
        "top": top,
        "dna": dna,
        "tem_dna": bool(dna),
    }
    filename = report.build_output_filename("criativos-ranking", produto_nome)
    return report.render_markdown("criativos.md.j2", context, output_filename=filename)
