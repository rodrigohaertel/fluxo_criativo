"""Análise de Fadiga Criativa — 5 sinais combinados por ad.

Sinal dispara quando:
  1. frequency >= threshold do perfil (cold 3.0 / retarget 5.0)
  2. ctr_atual < 85% do ctr da janela anterior (queda >15% WoW)
  3. cpa_atual > 125% do cpa_baseline (+25%)
  4. 2+ rankings em "below_average" (quality / engagement / conversion)
  5. CPR crítico: cpa_atual >= 2× cpa_baseline → flag de pausa imediata

Score 0-5 por ad:
  0-1 = saudável
  2-3 = monitorar / substituir em breve
  4   = substituir em 48h
  5 OU flag crítico = pausar imediato

O baseline pode vir:
  - Do perfil: `rolling_30d` computado em `core/baseline.py` (v1 Fase 2)
  - Do CPA médio do produto/account do período anterior (fallback Fase 1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.perfis import PERFIL_PADRAO_FALLBACK, Perfil
from trafego_analysis.core.periods import Period


@dataclass
class SinalFadiga:
    tipo: str            # "freq_alta" | "ctr_drop" | "cpa_drift" | "rankings" | "cpr_critico"
    valor: float
    threshold: float
    descricao: str
    peso: int = 1


@dataclass
class AdFadiga:
    ad_id: str
    ad_name: str
    campaign_name: str
    spend: float
    impressions: float
    frequency: float
    ctr: float
    ctr_prev: float | None
    cpa: float | None
    cpa_baseline: float | None
    quality_ranking: str | None
    engagement_rate_ranking: str | None
    conversion_rate_ranking: str | None
    sinais: list[SinalFadiga] = field(default_factory=list)
    flag_critico: bool = False

    @property
    def score(self) -> int:
        return sum(s.peso for s in self.sinais)

    @property
    def veredicto(self) -> str:
        if self.flag_critico or self.score >= 5:
            return "PAUSAR IMEDIATO"
        if self.score >= 3:
            return "SUBSTITUIR EM 48H"
        if self.score == 2:
            return "MONITORAR"
        return "SAUDÁVEL"


def _is_below_average(ranking: str | None) -> bool:
    if not ranking:
        return False
    return ranking.lower().startswith("below_average")


def _cpa_from_row(row: dict[str, Any]) -> float | None:
    """Tenta extrair CPA de um insight row. Prioriza `purchase`, fallback para `lead`."""
    spend = float(row.get("spend") or 0)
    purchases = mc.extract_action_count(row.get("actions"), "purchase")
    if purchases > 0:
        return spend / purchases
    leads = mc.extract_action_count(row.get("actions"), "lead")
    if leads > 0:
        return spend / leads
    return None


def _ctr_from_row(row: dict[str, Any]) -> float:
    """CTR preferencial: `inline_link_click_ctr` se existir, fallback para `ctr` geral."""
    if row.get("inline_link_clicks") and row.get("impressions"):
        return m.ctr(
            float(row["inline_link_clicks"]),
            float(row["impressions"]),
        )
    return float(row.get("ctr") or 0)


def _is_retargeting_campaign(name: str) -> bool:
    """Heurística: nome contém `rmk`, `remarketing`, `retarget`."""
    n = name.lower()
    return any(k in n for k in ("rmk", "remarketing", "retarget"))


def detectar_fadiga(
    rows_atual: list[dict[str, Any]],
    rows_anterior: list[dict[str, Any]] | None,
    *,
    perfil: Perfil = PERFIL_PADRAO_FALLBACK,
    cpa_baseline_por_ad: dict[str, float] | None = None,
    cpa_baseline_fallback: float | None = None,
    min_impressions: int = 1000,
    min_spend_brl: float = 50.0,
) -> list[AdFadiga]:
    """Aplica os 5 sinais a cada ad; retorna lista ordenada por score desc."""
    cpa_baseline_por_ad = cpa_baseline_por_ad or {}

    # Indexa janela anterior por ad_id para lookup O(1)
    prev_by_ad: dict[str, dict[str, Any]] = {}
    for r in rows_anterior or []:
        if r.get("ad_id"):
            prev_by_ad[r["ad_id"]] = r

    results: list[AdFadiga] = []

    for row in rows_atual:
        impressions = float(row.get("impressions") or 0)
        spend = float(row.get("spend") or 0)

        if impressions < min_impressions or spend < min_spend_brl:
            continue  # volume insuficiente pra diagnóstico confiável

        ad_id = row.get("ad_id") or ""
        ad_name = row.get("ad_name") or "(sem nome)"
        campaign_name = row.get("campaign_name") or ""
        frequency = float(row.get("frequency") or 0)
        ctr_atual = _ctr_from_row(row)
        cpa_atual = _cpa_from_row(row)

        prev_row = prev_by_ad.get(ad_id)
        ctr_prev = _ctr_from_row(prev_row) if prev_row else None

        cpa_baseline = cpa_baseline_por_ad.get(ad_id, cpa_baseline_fallback)

        quality = row.get("quality_ranking")
        engagement = row.get("engagement_rate_ranking")
        conversion = row.get("conversion_rate_ranking")

        ad = AdFadiga(
            ad_id=ad_id,
            ad_name=ad_name,
            campaign_name=campaign_name,
            spend=spend,
            impressions=impressions,
            frequency=frequency,
            ctr=ctr_atual,
            ctr_prev=ctr_prev,
            cpa=cpa_atual,
            cpa_baseline=cpa_baseline,
            quality_ranking=quality,
            engagement_rate_ranking=engagement,
            conversion_rate_ranking=conversion,
        )

        # Sinal 1: frequency alta
        freq_thr = (
            perfil.fadiga.freq_rmk_perigo
            if _is_retargeting_campaign(campaign_name)
            else perfil.fadiga.freq_cold_perigo
        )
        if frequency >= freq_thr:
            ad.sinais.append(
                SinalFadiga(
                    tipo="freq_alta",
                    valor=frequency,
                    threshold=freq_thr,
                    descricao=f"Frequency {frequency:.2f} >= {freq_thr:.1f}",
                )
            )

        # Sinal 2: CTR drop WoW
        if ctr_prev and ctr_prev > 0:
            delta_pct = m.ctr_delta_wow(ctr_atual, ctr_prev)
            thr_drop = -perfil.fadiga.ctr_drop_wow_pct
            if delta_pct <= thr_drop:
                ad.sinais.append(
                    SinalFadiga(
                        tipo="ctr_drop",
                        valor=delta_pct,
                        threshold=thr_drop,
                        descricao=f"CTR caiu {delta_pct:.1f}% WoW",
                    )
                )

        # Sinal 3: CPA drift
        if cpa_atual and cpa_baseline:
            drift_pct = m.cpa_drift_pct(cpa_atual, cpa_baseline)
            thr_rise = perfil.fadiga.cpa_rise_vs_baseline_pct
            if drift_pct >= thr_rise:
                ad.sinais.append(
                    SinalFadiga(
                        tipo="cpa_drift",
                        valor=drift_pct,
                        threshold=thr_rise,
                        descricao=f"CPA +{drift_pct:.0f}% vs baseline",
                    )
                )
            if drift_pct >= (perfil.fadiga.cpr_critico_multiplicador - 1) * 100:
                ad.flag_critico = True
                ad.sinais.append(
                    SinalFadiga(
                        tipo="cpr_critico",
                        valor=drift_pct,
                        threshold=(perfil.fadiga.cpr_critico_multiplicador - 1) * 100,
                        descricao=f"CPR crítico: CPA {perfil.fadiga.cpr_critico_multiplicador:.1f}× baseline",
                        peso=2,
                    )
                )

        # Sinal 4: rankings
        rankings_ruins = sum(
            1
            for r in (quality, engagement, conversion)
            if _is_below_average(r)
        )
        if rankings_ruins >= 2:
            ad.sinais.append(
                SinalFadiga(
                    tipo="rankings",
                    valor=rankings_ruins,
                    threshold=2,
                    descricao=f"{rankings_ruins} rankings below_average",
                )
            )

        results.append(ad)

    results.sort(key=lambda a: (a.flag_critico, a.score, a.spend), reverse=True)
    return results


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    periodo_anterior: Period,
    produto_nome: str | None = None,
    perfil: Perfil = PERFIL_PADRAO_FALLBACK,
    cpa_baseline_fallback: float | None = None,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    """Executa pipeline completo: busca → detecta → renderiza markdown."""
    rows_atual = meta.get_ad_insights(
        ad_account_id,
        since=periodo.since,
        until=periodo.until,
        filtering=filtering,
    )
    rows_anterior = meta.get_ad_insights(
        ad_account_id,
        since=periodo_anterior.since,
        until=periodo_anterior.until,
        filtering=filtering,
    )

    # Baseline simples Fase 1: CPA médio da janela anterior (fallback).
    # Fase 2: substituído por baseline.py rolling_30d.
    if cpa_baseline_fallback is None and rows_anterior:
        cpas = [
            _cpa_from_row(r)
            for r in rows_anterior
            if _cpa_from_row(r) is not None
        ]
        cpas = [c for c in cpas if c]
        if cpas:
            cpa_baseline_fallback = sum(cpas) / len(cpas)

    resultados = detectar_fadiga(
        rows_atual,
        rows_anterior,
        perfil=perfil,
        cpa_baseline_fallback=cpa_baseline_fallback,
    )

    # Agrupa por veredicto para o template
    grupos: dict[str, list[AdFadiga]] = {
        "PAUSAR IMEDIATO": [],
        "SUBSTITUIR EM 48H": [],
        "MONITORAR": [],
        "SAUDÁVEL": [],
    }
    for ad in resultados:
        grupos[ad.veredicto].append(ad)

    context = {
        "produto": produto_nome or "todos os produtos",
        "periodo_atual": periodo,
        "periodo_anterior": periodo_anterior,
        "perfil": perfil,
        "cpa_baseline": cpa_baseline_fallback,
        "grupos": grupos,
        "total_ads_analisados": len(resultados),
        "total_com_fadiga": sum(len(v) for k, v in grupos.items() if k != "SAUDÁVEL"),
    }

    filename = report.build_output_filename("fadiga-criativa", produto_nome)
    return report.render_markdown("fadiga.md.j2", context, output_filename=filename)
