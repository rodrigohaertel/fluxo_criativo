"""Testes de resolução de períodos e comparativos."""

from __future__ import annotations

from datetime import date

import pytest

from trafego_analysis.core.periods import (
    Period,
    PeriodComparison,
    list_presets,
    resolve_period,
)

# Data fixa para testes determinísticos: uma sexta-feira
TODAY = date(2026, 4, 24)


class TestAtalhosRapidos:
    def test_today(self):
        p = resolve_period("today", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == TODAY == p.until
        assert p.days == 1

    def test_yesterday(self):
        p = resolve_period("yesterday", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 4, 23)
        assert p.until == date(2026, 4, 23)


class TestRolling:
    def test_last_7d(self):
        p = resolve_period("last_7d", today=TODAY)
        assert isinstance(p, Period)
        assert p.until == date(2026, 4, 23)  # ontem
        assert p.since == date(2026, 4, 17)  # 7 dias antes de ontem
        assert p.days == 7

    def test_last_30d(self):
        p = resolve_period("last_30d", today=TODAY)
        assert isinstance(p, Period)
        assert p.days == 30
        assert p.until == date(2026, 4, 23)

    def test_last_90d(self):
        p = resolve_period("last_90d", today=TODAY)
        assert isinstance(p, Period)
        assert p.days == 90


class TestSemanasEMeses:
    def test_this_week(self):
        # Sexta → this_week = segunda (20/04) a domingo (26/04)
        p = resolve_period("this_week", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 4, 20)
        assert p.until == date(2026, 4, 26)

    def test_last_week(self):
        p = resolve_period("last_week", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 4, 13)
        assert p.until == date(2026, 4, 19)

    def test_this_month(self):
        p = resolve_period("this_month", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 4, 1)
        assert p.until == date(2026, 4, 30)

    def test_last_month(self):
        p = resolve_period("last_month", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 3, 1)
        assert p.until == date(2026, 3, 31)

    def test_month_to_date(self):
        p = resolve_period("month_to_date", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 4, 1)
        assert p.until == TODAY


class TestAno:
    def test_this_year(self):
        p = resolve_period("this_year", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 1, 1)
        assert p.until == date(2026, 12, 31)

    def test_ytd(self):
        p = resolve_period("ytd", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 1, 1)
        assert p.until == TODAY

    def test_last_year(self):
        p = resolve_period("last_year", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2025, 1, 1)
        assert p.until == date(2025, 12, 31)


class TestCustomRange:
    def test_custom_valido(self):
        p = resolve_period("2026-04-01..2026-04-15", today=TODAY)
        assert isinstance(p, Period)
        assert p.since == date(2026, 4, 1)
        assert p.until == date(2026, 4, 15)
        assert p.days == 15

    def test_custom_invertido_erra(self):
        with pytest.raises(ValueError):
            resolve_period("2026-04-15..2026-04-01", today=TODAY)

    def test_spec_desconhecida_erra(self):
        with pytest.raises(ValueError):
            resolve_period("next_week", today=TODAY)


class TestComparativos:
    def test_wow_retorna_comparison(self):
        p = resolve_period("wow", today=TODAY)
        assert isinstance(p, PeriodComparison)
        # Current = last_7d
        assert p.current.since == date(2026, 4, 17)
        assert p.current.until == date(2026, 4, 23)
        # Previous = 7 dias antes do current
        assert p.previous.since == date(2026, 4, 10)
        assert p.previous.until == date(2026, 4, 16)
        assert p.current.days == p.previous.days == 7

    def test_last_7d_vs_prev_7d_equivalente_a_wow(self):
        a = resolve_period("last_7d_vs_prev_7d", today=TODAY)
        b = resolve_period("wow", today=TODAY)
        assert isinstance(a, PeriodComparison)
        assert isinstance(b, PeriodComparison)
        assert a.current.since == b.current.since
        assert a.previous.since == b.previous.since

    def test_mom(self):
        p = resolve_period("mom", today=TODAY)
        assert isinstance(p, PeriodComparison)
        # current = last_month = março 2026
        assert p.current.since == date(2026, 3, 1)
        assert p.current.until == date(2026, 3, 31)
        # previous = fevereiro 2026
        assert p.previous.since == date(2026, 2, 1)
        assert p.previous.until == date(2026, 2, 28)

    def test_yoy(self):
        p = resolve_period("yoy", today=TODAY)
        assert isinstance(p, PeriodComparison)
        # current = last_30d
        assert p.current.until == date(2026, 4, 23)
        # previous = mesma janela do ano passado
        assert p.previous.until == date(2025, 4, 23)


class TestListPresets:
    def test_lista_nao_vazia(self):
        presets = list_presets()
        assert len(presets) >= 15
        labels = {p[0] for p in presets}
        assert "last_7d" in labels
        assert "wow" in labels
        assert "yoy" in labels


class TestToMetaTimeRange:
    def test_formato_iso(self):
        p = resolve_period("last_7d", today=TODAY)
        assert isinstance(p, Period)
        tr = p.to_meta_time_range()
        assert tr == {"since": "2026-04-17", "until": "2026-04-23"}
