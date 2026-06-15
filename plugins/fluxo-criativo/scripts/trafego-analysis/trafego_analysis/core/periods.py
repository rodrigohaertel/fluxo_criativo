"""Resolução de períodos e comparativos.

Transforma strings amigáveis (`last_7d`, `mom`, `2026-04-01..2026-04-15`) em
tuplas de datas absolutas. Todos os comparativos retornam duas janelas do mesmo
tamanho alinhadas para side-by-side.
"""

from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

ISO_FMT = "%Y-%m-%d"


@dataclass(frozen=True)
class Period:
    """Intervalo fechado [since, until] (ambos inclusivos, como o Meta espera)."""

    since: date
    until: date
    label: str

    @property
    def days(self) -> int:
        return (self.until - self.since).days + 1

    def to_meta_time_range(self) -> dict[str, str]:
        return {"since": self.since.isoformat(), "until": self.until.isoformat()}


@dataclass(frozen=True)
class PeriodComparison:
    """Duas janelas (current vs previous) alinhadas por tamanho."""

    current: Period
    previous: Period
    label: str


# Presets reconhecidos (exceto custom YYYY-MM-DD..YYYY-MM-DD e comparativos)
PRESETS = [
    "today", "yesterday",
    "last_3d", "last_7d", "last_14d", "last_28d", "last_30d", "last_90d",
    "this_week", "last_week", "week_to_date",
    "this_month", "last_month", "month_to_date", "last_month_closed",
    "this_year", "ytd", "last_year",
]

COMPARATIVES = [
    "last_7d_vs_prev_7d", "last_30d_vs_prev_30d",
    "wow", "mom", "yoy",
    "vs_prev_period", "vs_same_period_last_month", "vs_same_period_last_year",
]

LABELS_PT = {
    "today": "Hoje",
    "yesterday": "Ontem",
    "last_3d": "Últimos 3 dias",
    "last_7d": "Últimos 7 dias",
    "last_14d": "Últimos 14 dias",
    "last_28d": "Últimos 28 dias",
    "last_30d": "Últimos 30 dias",
    "last_90d": "Últimos 90 dias",
    "this_week": "Esta semana",
    "last_week": "Semana passada",
    "week_to_date": "Semana até hoje",
    "this_month": "Este mês",
    "last_month": "Mês passado",
    "month_to_date": "Mês até hoje",
    "last_month_closed": "Último mês fechado",
    "this_year": "Este ano",
    "ytd": "Ano até hoje",
    "last_year": "Ano passado",
    "wow": "Semana a semana",
    "mom": "Mês a mês",
    "yoy": "Ano a ano",
    "vs_prev_period": "vs período anterior",
    "vs_same_period_last_month": "vs mesmo período mês anterior",
    "vs_same_period_last_year": "vs mesmo período ano anterior",
    "last_7d_vs_prev_7d": "Últimos 7d vs 7d anteriores",
    "last_30d_vs_prev_30d": "Últimos 30d vs 30d anteriores",
}


def _monday_of(d: date) -> date:
    """Segunda-feira da semana que contém `d` (convenção ISO)."""
    return d - timedelta(days=d.weekday())


def _first_of_month(d: date) -> date:
    return d.replace(day=1)


def _last_of_month(d: date) -> date:
    last_day = monthrange(d.year, d.month)[1]
    return d.replace(day=last_day)


def _add_months(d: date, months: int) -> date:
    """Adiciona N meses (negativo p/ voltar), ajustando o dia quando necessário."""
    total = d.year * 12 + (d.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def _shift_period(p: Period, days: int, new_label: str) -> Period:
    return Period(
        since=p.since - timedelta(days=days),
        until=p.until - timedelta(days=days),
        label=new_label,
    )


def _parse_custom(spec: str) -> Period | None:
    """Reconhece `YYYY-MM-DD..YYYY-MM-DD`."""
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})", spec)
    if not m:
        return None
    since = date.fromisoformat(m.group(1))
    until = date.fromisoformat(m.group(2))
    if since > until:
        raise ValueError(f"since > until em período custom: {spec}")
    return Period(since=since, until=until, label=f"{spec} (custom)")


def resolve_period(spec: str, *, today: date | None = None) -> Period | PeriodComparison:
    """Converte string → Period ou PeriodComparison.

    >>> resolve_period("last_7d", today=date(2026, 4, 24))
    Period(since=datetime.date(2026, 4, 17), until=datetime.date(2026, 4, 23), ...)
    """
    today = today or date.today()

    # Comparativos primeiro (retornam PeriodComparison)
    if spec in COMPARATIVES:
        return _resolve_comparison(spec, today)

    # Custom range
    custom = _parse_custom(spec)
    if custom:
        return custom

    # Presets single-range
    label = LABELS_PT.get(spec, spec)

    if spec == "today":
        return Period(today, today, label)
    if spec == "yesterday":
        y = today - timedelta(days=1)
        return Period(y, y, label)

    if spec == "last_3d":
        return Period(today - timedelta(days=3), today - timedelta(days=1), label)
    if spec == "last_7d":
        return Period(today - timedelta(days=7), today - timedelta(days=1), label)
    if spec == "last_14d":
        return Period(today - timedelta(days=14), today - timedelta(days=1), label)
    if spec == "last_28d":
        return Period(today - timedelta(days=28), today - timedelta(days=1), label)
    if spec == "last_30d":
        return Period(today - timedelta(days=30), today - timedelta(days=1), label)
    if spec == "last_90d":
        return Period(today - timedelta(days=90), today - timedelta(days=1), label)

    if spec == "this_week":
        start = _monday_of(today)
        return Period(start, start + timedelta(days=6), label)
    if spec == "last_week":
        this_mon = _monday_of(today)
        last_mon = this_mon - timedelta(days=7)
        return Period(last_mon, last_mon + timedelta(days=6), label)
    if spec == "week_to_date":
        return Period(_monday_of(today), today, label)

    if spec == "this_month":
        return Period(_first_of_month(today), _last_of_month(today), label)
    if spec == "month_to_date":
        return Period(_first_of_month(today), today, label)
    if spec == "last_month":
        prev = _add_months(today, -1)
        return Period(_first_of_month(prev), _last_of_month(prev), label)
    if spec == "last_month_closed":
        # Sinônimo de last_month mas enfatiza "mês anterior completo"
        prev = _add_months(today, -1)
        return Period(_first_of_month(prev), _last_of_month(prev), label)

    if spec == "this_year":
        return Period(date(today.year, 1, 1), date(today.year, 12, 31), label)
    if spec == "ytd":
        return Period(date(today.year, 1, 1), today, label)
    if spec == "last_year":
        y = today.year - 1
        return Period(date(y, 1, 1), date(y, 12, 31), label)

    raise ValueError(
        f"Período desconhecido: {spec!r}. "
        f"Use um dos presets: {PRESETS + COMPARATIVES} ou custom YYYY-MM-DD..YYYY-MM-DD"
    )


def _resolve_comparison(spec: str, today: date) -> PeriodComparison:
    label = LABELS_PT.get(spec, spec)

    if spec in ("last_7d_vs_prev_7d", "wow"):
        current = resolve_period("last_7d", today=today)
        assert isinstance(current, Period)
        previous = _shift_period(current, days=7, new_label="7 dias anteriores")
        return PeriodComparison(current, previous, label)

    if spec in ("last_30d_vs_prev_30d", "vs_prev_period"):
        current = resolve_period("last_30d", today=today)
        assert isinstance(current, Period)
        previous = _shift_period(current, days=30, new_label="30 dias anteriores")
        return PeriodComparison(current, previous, label)

    if spec == "mom":
        current = resolve_period("last_month", today=today)
        assert isinstance(current, Period)
        prev_start = _add_months(current.since, -1)
        prev_end = _last_of_month(prev_start)
        previous = Period(prev_start, prev_end, "2 meses atrás")
        return PeriodComparison(current, previous, label)

    if spec == "yoy":
        current = resolve_period("last_30d", today=today)
        assert isinstance(current, Period)
        previous = Period(
            since=date(current.since.year - 1, current.since.month, current.since.day),
            until=date(current.until.year - 1, current.until.month, current.until.day),
            label="Mesmo período, ano passado",
        )
        return PeriodComparison(current, previous, label)

    if spec == "vs_same_period_last_month":
        current = resolve_period("last_7d", today=today)
        assert isinstance(current, Period)
        prev_since = _add_months(current.since, -1)
        prev_until = _add_months(current.until, -1)
        previous = Period(prev_since, prev_until, "Mesmo período, mês anterior")
        return PeriodComparison(current, previous, label)

    if spec == "vs_same_period_last_year":
        current = resolve_period("last_30d", today=today)
        assert isinstance(current, Period)
        previous = Period(
            since=date(current.since.year - 1, current.since.month, current.since.day),
            until=date(current.until.year - 1, current.until.month, current.until.day),
            label="Mesmo período, ano passado",
        )
        return PeriodComparison(current, previous, label)

    raise ValueError(f"Comparativo desconhecido: {spec!r}")


def list_presets() -> list[tuple[str, str]]:
    """Lista (spec, label_pt) para help de CLI e UI."""
    return [(p, LABELS_PT[p]) for p in PRESETS + COMPARATIVES]
