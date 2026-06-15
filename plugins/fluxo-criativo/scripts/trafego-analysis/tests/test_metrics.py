"""Testes unitários das 12 fórmulas — fonte da verdade numérica."""

from __future__ import annotations

import pytest

from trafego_analysis.core import metrics as m

# --- Métricas de criativo ----------------------------------------------------

class TestHookRate:
    def test_exemplo_saudavel(self):
        # 3000 visualizações de 3s sobre 10000 impressões = 30%
        assert m.hook_rate(3000, 10000) == 30.0

    def test_zero_impressions(self):
        assert m.hook_rate(100, 0) == 0.0

    def test_zero_views(self):
        assert m.hook_rate(0, 10000) == 0.0


class TestHoldRate:
    def test_exemplo(self):
        # 400 thruplays sobre 1000 views = 40%
        assert m.hold_rate(400, 1000) == 40.0

    def test_zero_3s(self):
        assert m.hold_rate(100, 0) == 0.0


class TestThumbStopRate:
    def test_alias_de_hook_rate(self):
        assert m.thumb_stop_rate(3000, 10000) == m.hook_rate(3000, 10000)


# --- Métricas de funil -------------------------------------------------------

class TestCTR:
    def test_ctr_20_por_cento(self):
        assert m.ctr(200, 1000) == 20.0

    def test_ctr_zero(self):
        assert m.ctr(0, 1000) == 0.0

    def test_ctr_sem_impressoes(self):
        assert m.ctr(100, 0) == 0.0


class TestConnectRate:
    def test_connect_rate_saudavel(self):
        # 800 LPV sobre 1000 clicks = 80%
        assert m.connect_rate(800, 1000) == 80.0

    def test_conexao_critica(self):
        # <60% considera-se crítico
        assert m.connect_rate(500, 1000) == 50.0


class TestOfferRate:
    def test_offer_saudavel(self):
        # 500 video plays sobre 1000 LPVs = 50%
        assert m.offer_rate(500, 1000) == 50.0


class TestTruePlayRate:
    def test_true_play(self):
        # 550 assistindo até 55% de 1000 que iniciaram = 55%
        assert m.true_play_rate(550, 1000) == pytest.approx(55.0)


class TestCheckoutConversion:
    def test_cr_checkout(self):
        # 40 compras de 100 checkouts iniciados = 40%
        assert m.checkout_conversion_rate(40, 100) == 40.0


# --- Custos e retorno --------------------------------------------------------

class TestCPM:
    def test_cpm_exemplo(self):
        # R$ 100 em 10000 impressões = R$ 10.00 CPM
        assert m.cpm(100, 10000) == 10.0

    def test_cpm_sem_impressoes(self):
        assert m.cpm(100, 0) == 0.0


class TestCPC:
    def test_cpc_exemplo(self):
        # R$ 200 em 100 clicks = R$ 2.00 CPC
        assert m.cpc(200, 100) == 2.0


class TestCPA:
    def test_cpa_exemplo(self):
        # R$ 1000 em 10 vendas = R$ 100 CPA
        assert m.cpa(1000, 10) == 100.0

    def test_cpa_sem_resultados(self):
        assert m.cpa(1000, 0) == 0.0


class TestROAS:
    def test_roas_25x(self):
        # R$ 2500 de receita sobre R$ 1000 gasto = 2.5x
        assert m.roas(2500, 1000) == 2.5

    def test_roas_negativo_impossivel(self):
        # Gasto zero → 0 (convenção, não ∞)
        assert m.roas(2500, 0) == 0.0


class TestROI:
    def test_roi_150_pct_equivale_a_roas_25(self):
        # ROAS 2.5x → ROI (250-100)/100 = 150%
        assert m.roi_pct(revenue=2500, spend=1000) == 150.0

    def test_roi_prejuizo(self):
        assert m.roi_pct(revenue=500, spend=1000) == -50.0

    def test_roi_sem_spend(self):
        assert m.roi_pct(revenue=1000, spend=0) == 0.0


# --- Deltas e drifts ---------------------------------------------------------

class TestCTRDeltaWoW:
    def test_subida_20_pct(self):
        # CTR passou de 2.0% para 2.4% = +20%
        assert m.ctr_delta_wow(2.4, 2.0) == pytest.approx(20.0)

    def test_queda_25_pct(self):
        # CTR caiu de 2.0% para 1.5% = -25%
        assert m.ctr_delta_wow(1.5, 2.0) == pytest.approx(-25.0)

    def test_sem_baseline(self):
        assert m.ctr_delta_wow(2.0, 0) == 0.0


class TestCPADriftPct:
    def test_alta_25_pct_atinge_threshold_fadiga(self):
        # CPA passou de R$ 100 para R$ 125 = +25% → threshold padrão de fadiga
        assert m.cpa_drift_pct(125, 100) == pytest.approx(25.0)

    def test_drift_critico(self):
        # Duplicou: CPA R$ 200 vs baseline R$ 100 = +100% → flag CPR crítico
        assert m.cpa_drift_pct(200, 100) == pytest.approx(100.0)

    def test_melhorou(self):
        # CPA baixou: atual R$ 80 vs baseline R$ 100 = -20%
        assert m.cpa_drift_pct(80, 100) == pytest.approx(-20.0)
