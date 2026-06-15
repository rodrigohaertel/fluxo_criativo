"""Testes dos 5 sinais de fadiga criativa."""

from __future__ import annotations

from trafego_analysis.analyses.fadiga_criativa import (
    _ctr_from_row,
    _is_below_average,
    _is_retargeting_campaign,
    detectar_fadiga,
)


def _ad_row(
    ad_id="ad1", ad_name="Test Ad", campaign_name="Test CV", impressions=5000,
    spend=200, frequency=2.0, inline_link_clicks=100, ctr=2.0,
    purchases=10, revenue=500,
    quality_ranking=None, engagement_rate_ranking=None, conversion_rate_ranking=None,
):
    return {
        "ad_id": ad_id,
        "ad_name": ad_name,
        "campaign_name": campaign_name,
        "impressions": impressions,
        "spend": spend,
        "frequency": frequency,
        "inline_link_clicks": inline_link_clicks,
        "ctr": ctr,
        "actions": [{"action_type": "purchase", "value": purchases}] if purchases else [],
        "action_values": [{"action_type": "purchase", "value": revenue}] if revenue else [],
        "quality_ranking": quality_ranking,
        "engagement_rate_ranking": engagement_rate_ranking,
        "conversion_rate_ranking": conversion_rate_ranking,
    }


class TestHelpers:
    def test_is_retargeting_rmk(self):
        assert _is_retargeting_campaign("RMK_v7") is True

    def test_is_retargeting_remarketing(self):
        assert _is_retargeting_campaign("Remarketing 14d") is True

    def test_is_retargeting_cold_false(self):
        assert _is_retargeting_campaign("COLD_prospecting") is False

    def test_is_below_average_true(self):
        assert _is_below_average("below_average_35") is True
        assert _is_below_average("Below_Average_20") is True

    def test_is_below_average_false(self):
        assert _is_below_average("average") is False
        assert _is_below_average("above_average") is False
        assert _is_below_average(None) is False

    def test_ctr_from_row_prefere_inline(self):
        row = _ad_row(impressions=10000, inline_link_clicks=200, ctr=0.5)
        assert _ctr_from_row(row) == 2.0  # inline_clicks / impressions

    def test_ctr_from_row_fallback_ctr(self):
        row = _ad_row(impressions=0, inline_link_clicks=0, ctr=1.5)
        assert _ctr_from_row(row) == 1.5


class TestSinalFrequencyAlta:
    def test_freq_alta_cold_dispara(self):
        row = _ad_row(frequency=3.5, campaign_name="COLD prospecting")
        result = detectar_fadiga([row], None)
        assert len(result) == 1
        tipos = [s.tipo for s in result[0].sinais]
        assert "freq_alta" in tipos

    def test_freq_alta_rmk_threshold_maior(self):
        # Em RMK, threshold é 5.0 — freq 4.0 não dispara
        row = _ad_row(frequency=4.0, campaign_name="RMK 7d")
        result = detectar_fadiga([row], None)
        tipos = [s.tipo for s in result[0].sinais]
        assert "freq_alta" not in tipos

    def test_freq_alta_rmk_dispara_em_5(self):
        row = _ad_row(frequency=5.5, campaign_name="RMK 7d")
        result = detectar_fadiga([row], None)
        tipos = [s.tipo for s in result[0].sinais]
        assert "freq_alta" in tipos


class TestSinalCTRDrop:
    def test_ctr_caiu_20pct_dispara(self):
        atual = _ad_row(ad_id="x", impressions=10000, inline_link_clicks=160)  # CTR 1.6%
        anterior = _ad_row(ad_id="x", impressions=10000, inline_link_clicks=200)  # CTR 2.0%
        result = detectar_fadiga([atual], [anterior])
        tipos = [s.tipo for s in result[0].sinais]
        assert "ctr_drop" in tipos

    def test_ctr_estavel_nao_dispara(self):
        atual = _ad_row(ad_id="x", impressions=10000, inline_link_clicks=195)  # 1.95%
        anterior = _ad_row(ad_id="x", impressions=10000, inline_link_clicks=200)  # 2.0%
        result = detectar_fadiga([atual], [anterior])
        tipos = [s.tipo for s in result[0].sinais]
        assert "ctr_drop" not in tipos


class TestSinalCPADrift:
    def test_cpa_drift_positivo_dispara(self):
        # baseline R$50; atual R$70 = +40% (threshold 25%)
        atual = _ad_row(spend=140, purchases=2)  # CPA 70
        result = detectar_fadiga([atual], None, cpa_baseline_fallback=50)
        tipos = [s.tipo for s in result[0].sinais]
        assert "cpa_drift" in tipos

    def test_cpa_dentro_threshold_nao_dispara(self):
        # baseline R$100; atual R$110 = +10% (não dispara 25%)
        atual = _ad_row(spend=110, purchases=1)  # CPA 110
        result = detectar_fadiga([atual], None, cpa_baseline_fallback=100)
        tipos = [s.tipo for s in result[0].sinais]
        assert "cpa_drift" not in tipos

    def test_cpr_critico_dispara_flag(self):
        # baseline R$50; atual R$120 = +140% → CPR crítico (>100% = 2× baseline)
        atual = _ad_row(spend=120, purchases=1)
        result = detectar_fadiga([atual], None, cpa_baseline_fallback=50)
        assert result[0].flag_critico is True


class TestSinalRankings:
    def test_dois_rankings_below_dispara(self):
        row = _ad_row(
            quality_ranking="below_average_35",
            engagement_rate_ranking="below_average_20",
            conversion_rate_ranking="average",
        )
        result = detectar_fadiga([row], None)
        tipos = [s.tipo for s in result[0].sinais]
        assert "rankings" in tipos

    def test_um_ranking_below_nao_dispara(self):
        row = _ad_row(
            quality_ranking="below_average_35",
            engagement_rate_ranking="average",
            conversion_rate_ranking="above_average",
        )
        result = detectar_fadiga([row], None)
        tipos = [s.tipo for s in result[0].sinais]
        assert "rankings" not in tipos


class TestVeredictos:
    def test_score_1_saudavel(self):
        row = _ad_row(
            quality_ranking="below_average_35",
            engagement_rate_ranking="average",  # só 1 ranking ruim → 0 sinais de rankings
        )
        # Sem outros sinais → score 0
        result = detectar_fadiga([row], None)
        assert result[0].veredicto == "SAUDÁVEL"

    def test_score_alto_e_critico_pausar(self):
        atual = _ad_row(
            frequency=4.0,
            campaign_name="COLD",
            quality_ranking="below_average_35",
            engagement_rate_ranking="below_average_20",
            spend=300,
            purchases=1,  # CPA 300
        )
        result = detectar_fadiga([atual], None, cpa_baseline_fallback=50)
        # Freq + rankings + cpa_drift + cpr_critico = 5 (com peso 2 do critico)
        assert result[0].veredicto == "PAUSAR IMEDIATO"


class TestFiltroVolumeMinimo:
    def test_ad_com_pouco_spend_ignorado(self):
        row = _ad_row(impressions=500, spend=20)  # abaixo dos mínimos
        result = detectar_fadiga([row], None)
        assert result == []

    def test_ad_com_spend_suficiente_analisado(self):
        row = _ad_row(impressions=10000, spend=200)
        result = detectar_fadiga([row], None)
        assert len(result) == 1
