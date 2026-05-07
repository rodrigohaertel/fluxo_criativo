"""Análise 1.5 — Prospecção vs. Retargeting.

Compara o balanço entre públicos frios (prospecção) e quentes (retargeting)
vs. o mix ideal para a fase VTSD atual. Complementa a análise 1.3 (comparativo
de conjuntos) com foco na decisão: "estou investindo demais em retargeting?"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from trafego_analysis.analyses.comparativo_conjuntos import classificar_temperatura
from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report, vtsd
from trafego_analysis.core.periods import Period


@dataclass
class MixAtual:
    hot_pct: float
    cold_pct: float
    supercold_pct: float
    indefinido_pct: float
    hot_cpl: float
    cold_cpl: float
    supercold_cpl: float


def _results(row: dict) -> float:
    p = mc.extract_action_count(row.get("actions"), "purchase")
    l = mc.extract_action_count(row.get("actions"), "lead")
    return p or l


def calcular_mix(rows: list[dict[str, Any]]) -> MixAtual:
    agg = {
        "HOT": {"spend": 0.0, "results": 0.0},
        "COLD": {"spend": 0.0, "results": 0.0},
        "SUPERCOLD": {"spend": 0.0, "results": 0.0},
        "INDEFINIDO": {"spend": 0.0, "results": 0.0},
    }
    for r in rows:
        nome = r.get("adset_name") or r.get("campaign_name") or ""
        temp = classificar_temperatura(nome)
        agg[temp]["spend"] += float(r.get("spend") or 0)
        agg[temp]["results"] += _results(r)

    total = sum(a["spend"] for a in agg.values())

    def pct(v: float) -> float:
        return (v / total * 100) if total else 0

    return MixAtual(
        hot_pct=pct(agg["HOT"]["spend"]),
        cold_pct=pct(agg["COLD"]["spend"]),
        supercold_pct=pct(agg["SUPERCOLD"]["spend"]),
        indefinido_pct=pct(agg["INDEFINIDO"]["spend"]),
        hot_cpl=m.cpa(agg["HOT"]["spend"], agg["HOT"]["results"]),
        cold_cpl=m.cpa(agg["COLD"]["spend"], agg["COLD"]["results"]),
        supercold_cpl=m.cpa(agg["SUPERCOLD"]["spend"], agg["SUPERCOLD"]["results"]),
    )


FaseVTSD = Literal["pico", "evergreen", "caixa_rapido", "teste_inicial"]


def diagnostico(mix: MixAtual, fase: FaseVTSD) -> list[str]:
    """Compara mix atual com ideal da fase e sugere ajustes."""
    ideal = vtsd.MIX_IDEAL[fase]
    diags: list[str] = []

    atual_pcts = {"HOT": mix.hot_pct, "COLD": mix.cold_pct, "SUPERCOLD": mix.supercold_pct}

    for temp, (min_p, max_p) in ideal.items():
        atual = atual_pcts[temp]
        if atual < min_p - 5:
            diags.append(
                f"⚠️ **{temp} abaixo do ideal** ({atual:.0f}% atual vs. {min_p}-{max_p}% ideal para {fase}). "
                f"Aumentar alocação em {temp}."
            )
        elif atual > max_p + 5:
            diags.append(
                f"⚠️ **{temp} acima do ideal** ({atual:.0f}% atual vs. {min_p}-{max_p}% ideal para {fase}). "
                f"Reduzir alocação em {temp} e realocar."
            )

    # Dependência excessiva em HOT
    if mix.hot_pct > 50 and fase != "pico":
        diags.append(
            "🔴 **Dependência excessiva em HOT** — conta 'saudável' no VTSD tem HOT < 40%. "
            "Se a lista quente esgotar, não há base de prospecção alimentando."
        )

    # Sem SUPERCOLD
    if mix.supercold_pct < 5 and fase in ("evergreen", "caixa_rapido"):
        diags.append(
            "💡 **SUPERCOLD praticamente ausente.** Perpetuo/Caixa Rápido se beneficia de público "
            "aberto — Meta acha Identidade do Consumidor sozinha. Testar SUPERCOLD é baixo risco."
        )

    if not diags:
        diags.append(f"✅ Mix dentro do ideal para fase **{fase}**. Manter distribuição.")

    return diags


def analisar_rows(rows: list[dict[str, Any]], fase: FaseVTSD = "evergreen") -> dict[str, Any]:
    mix = calcular_mix(rows)
    diags = diagnostico(mix, fase)
    return {
        "mix": mix,
        "fase": fase,
        "ideal": vtsd.MIX_IDEAL[fase],
        "diagnostico": diags,
    }


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    fase: FaseVTSD = "evergreen",
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows = meta.get_ad_insights(
        ad_account_id, since=periodo.since, until=periodo.until, filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    resultado = analisar_rows(rows, fase=fase)
    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        **resultado,
    }
    filename = report.build_output_filename("prospeccao-retargeting", produto_nome)
    return report.render_markdown(
        "prospeccao_retargeting.md.j2", context, output_filename=filename,
    )
