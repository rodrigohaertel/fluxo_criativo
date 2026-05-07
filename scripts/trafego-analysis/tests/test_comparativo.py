"""Testes de agregação e classificação do comparativo período."""

from __future__ import annotations

import pytest

from trafego_analysis.analyses.comparativo_periodo import (
    DIRECTION,
    TipoDelta,
    _aggregate,
    _classify,
    _delta,
    comparar,
)


def _row(spend=100, impressions=10000, inline_link_clicks=200, purchases=5, revenue=500, frequency=2.0):
    return {
        "spend": spend,
        "impressions": impressions,
        "reach": impressions * 0.7,
        "clicks": inline_link_clicks,
        "inline_link_clicks": inline_link_clicks,
        "frequency": frequency,
        "actions": [
            {"action_type": "purchase", "value": purchases},
        ],
        "action_values": [
            {"action_type": "purchase", "value": revenue},
        ],
    }


class TestAggregate:
    def test_aggregate_soma_simples(self):
        rows = [_row(spend=100), _row(spend=200)]
        agg = _aggregate(rows)
        assert agg["spend"] == 300
        assert agg["impressions"] == 20000
        assert agg["results"] == 10  # 5 + 5

    def test_derivadas_calculadas(self):
        rows = [_row(spend=200, impressions=10000, inline_link_clicks=100, purchases=10)]
        agg = _aggregate(rows)
        assert agg["cpm"] == pytest.approx(20.0)  # 200/10000 * 1000
        assert agg["cpc"] == pytest.approx(2.0)   # 200/100
        assert agg["cpa"] == pytest.approx(20.0)  # 200/10

    def test_sem_rows(self):
        agg = _aggregate([])
        assert agg["spend"] == 0
        assert agg["cpm"] == 0
        assert agg["roas"] == 0


class TestDelta:
    def test_subida(self):
        abs_d, pct_d = _delta(120, 100)
        assert abs_d == 20
        assert pct_d == pytest.approx(20.0)

    def test_queda(self):
        abs_d, pct_d = _delta(80, 100)
        assert abs_d == -20
        assert pct_d == pytest.approx(-20.0)

    def test_anterior_zero(self):
        abs_d, pct_d = _delta(50, 0)
        assert abs_d == 50
        assert pct_d is None


class TestClassify:
    def test_roas_subindo_positivo(self):
        # ROAS direção up is good → subida = POSITIVO
        assert _classify("roas", 10) == TipoDelta.POSITIVO

    def test_cpa_subindo_negativo(self):
        # CPA direção up is bad → subida = NEGATIVO
        assert _classify("cpa", 10) == TipoDelta.NEGATIVO

    def test_cpa_caindo_positivo(self):
        assert _classify("cpa", -10) == TipoDelta.POSITIVO

    def test_pequena_variacao_neutra(self):
        # |Δ| < 3% = neutro
        assert _classify("ctr", 1.5) == TipoDelta.NEUTRO
        assert _classify("cpa", -2.0) == TipoDelta.NEUTRO

    def test_frequency_sempre_neutro(self):
        # Frequency não tem direção desejada absoluta
        assert _classify("frequency", 20) == TipoDelta.NEUTRO
        assert _classify("frequency", -20) == TipoDelta.NEUTRO

    def test_direction_vazio(self):
        # Spend marcado como None em DIRECTION → neutro
        assert _classify("spend", 50) == TipoDelta.NEUTRO


class TestCompararPipeline:
    def test_comparar_mesmos_rows_zera_deltas(self):
        rows = [_row()]
        deltas = comparar(rows, rows)
        for d in deltas:
            assert d.delta_abs == 0

    def test_comparar_atual_maior(self):
        atual = [_row(spend=200, purchases=10, revenue=1000)]
        anterior = [_row(spend=100, purchases=5, revenue=500)]
        deltas = comparar(atual, anterior)
        spend_d = next(d for d in deltas if d.nome == "Gasto")
        assert spend_d.delta_abs == 100
        assert spend_d.delta_pct == pytest.approx(100)


class TestDirectionMap:
    def test_cpa_up_is_bad(self):
        assert DIRECTION["cpa"] is False

    def test_roas_up_is_good(self):
        assert DIRECTION["roas"] is True

    def test_frequency_sem_direcao(self):
        assert DIRECTION["frequency"] is None
