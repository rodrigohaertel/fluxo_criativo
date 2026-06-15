"""Dayparting — heatmap 7×24 de performance por dia da semana × hora.

Usa breakdown `hourly_stats_aggregated_by_advertiser_time_zone` da Meta.
Identifica janela de melhor CPA e janela queimando budget.

Observação: dayparting requer ad-level + breakdown `hourly_*` — custo maior de
quota da Meta. Cache é agressivo (1h) pois padrões horários mudam devagar.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


@dataclass
class HourStats:
    dia_idx: int        # 0 = segunda, 6 = domingo
    hora: int           # 0-23
    spend: float = 0.0
    impressions: float = 0.0
    clicks: float = 0.0
    results: float = 0.0

    @property
    def cpa(self) -> float:
        return m.cpa(self.spend, self.results)

    @property
    def ctr(self) -> float:
        return m.ctr(self.clicks, self.impressions)


def _parse_hour_bucket(bucket: str) -> int:
    """Meta retorna `hourly_stats_aggregated_by_advertiser_time_zone` como 'HH:MM:SS - HH:MM:SS'."""
    try:
        return int(bucket.split(":")[0])
    except (ValueError, IndexError, AttributeError):
        return -1


def _parse_date_weekday(date_str: str) -> int:
    """Meta retorna `date_start` como 'YYYY-MM-DD'. Retorna 0 (segunda) a 6 (domingo)."""
    try:
        from datetime import date as _d

        y, mo, da = [int(x) for x in date_str.split("-")]
        return _d(y, mo, da).weekday()
    except Exception:
        return -1


def agregar_heatmap(rows: list[dict[str, Any]]) -> dict[tuple[int, int], HourStats]:
    """Agrega rows (já com breakdown hourly) em grid dia×hora."""
    grid: dict[tuple[int, int], HourStats] = {}

    for r in rows:
        date_str = r.get("date_start") or ""
        hour_bucket = r.get("hourly_stats_aggregated_by_advertiser_time_zone") or ""

        dia = _parse_date_weekday(date_str)
        hora = _parse_hour_bucket(hour_bucket)
        if dia < 0 or hora < 0:
            continue

        key = (dia, hora)
        if key not in grid:
            grid[key] = HourStats(dia_idx=dia, hora=hora)

        cell = grid[key]
        cell.spend += float(r.get("spend") or 0)
        cell.impressions += float(r.get("impressions") or 0)
        cell.clicks += float(r.get("inline_link_clicks") or r.get("clicks") or 0)
        purchases = mc.extract_action_count(r.get("actions"), "purchase")
        leads = mc.extract_action_count(r.get("actions"), "lead")
        cell.results += purchases or leads

    return grid


def _janela_melhor_pior(grid: dict[tuple[int, int], HourStats]) -> tuple[HourStats | None, HourStats | None]:
    com_resultado = [s for s in grid.values() if s.results >= 3]
    if not com_resultado:
        return None, None
    melhor = min(com_resultado, key=lambda s: s.cpa)
    pior = max(com_resultado, key=lambda s: s.cpa)
    return melhor, pior


def _spend_por_dia(grid: dict[tuple[int, int], HourStats]) -> list[tuple[str, float, float, int]]:
    """Retorna (dia_label, spend, cpa, results) por dia da semana, ordenado segunda→domingo."""
    por_dia: dict[int, tuple[float, float, float]] = defaultdict(lambda: (0.0, 0.0, 0.0))
    for s in grid.values():
        spend, results, _prev_cpa_ignored = por_dia[s.dia_idx]
        por_dia[s.dia_idx] = (spend + s.spend, results + s.results, 0.0)
    out = []
    for i in range(7):
        spend, results, _ = por_dia.get(i, (0.0, 0.0, 0.0))
        cpa = (spend / results) if results else 0.0
        out.append((DIAS_SEMANA_PT[i], spend, cpa, int(results)))
    return out


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
        breakdowns=["hourly_stats_aggregated_by_advertiser_time_zone"],
        cache_ttl_s=3600,
        extra_fields=["date_start"],
    )

    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    grid = agregar_heatmap(rows)
    melhor, pior = _janela_melhor_pior(grid)
    spend_por_dia = _spend_por_dia(grid)

    # Monta linhas do heatmap para o template (7 linhas, 24 colunas)
    matriz_cpa: list[list[float | None]] = [[None] * 24 for _ in range(7)]
    matriz_spend: list[list[float]] = [[0.0] * 24 for _ in range(7)]
    for (dia, hora), s in grid.items():
        if 0 <= dia < 7 and 0 <= hora < 24:
            matriz_cpa[dia][hora] = s.cpa if s.results > 0 else None
            matriz_spend[dia][hora] = s.spend

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "dias_pt": DIAS_SEMANA_PT,
        "horas": list(range(24)),
        "matriz_cpa": matriz_cpa,
        "matriz_spend": matriz_spend,
        "melhor": melhor,
        "pior": pior,
        "spend_por_dia": spend_por_dia,
    }
    filename = report.build_output_filename("dayparting", produto_nome)
    return report.render_markdown("dayparting.md.j2", context, output_filename=filename)
