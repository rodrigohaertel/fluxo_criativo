"""Análise 1.4 — Eficiência de Orçamento (Pareto 80/20).

Ordena conjuntos/anúncios por resultados e identifica:
  - Quanto % do orçamento está nos top 20%
  - Quanto % dos resultados vem desses top 20%
  - Conjuntos que gastam muito e entregam pouco (desperdício)
  - Redistribuição sugerida

No VTSD:
  - Caixa Rápido: 70%+ do orçamento no conjunto vencedor
  - Pico: balancear HOT + COLD, máx 40% num único conjunto
  - Evergreen: máx 50% num único conjunto (evitar dependência)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class ConjuntoItem:
    nome: str
    spend: float
    results: float
    cpl: float
    share_spend: float
    share_results: float
    veredicto: str           # "escalar" | "manter" | "otimizar" | "pausar"


def _results(row: dict) -> float:
    p = mc.extract_action_count(row.get("actions"), "purchase")
    l = mc.extract_action_count(row.get("actions"), "lead")
    return p or l


def agrupar_por_adset(rows: list[dict[str, Any]]) -> list[ConjuntoItem]:
    """Agrupa rows ad-level por adset. Retorna lista ordenada por resultados desc."""
    buckets: dict[str, dict[str, float | str]] = {}
    for r in rows:
        key = r.get("adset_name") or r.get("campaign_name") or "(sem nome)"
        b = buckets.setdefault(key, {"nome": key, "spend": 0.0, "results": 0.0})
        b["spend"] = float(b["spend"]) + float(r.get("spend") or 0)
        b["results"] = float(b["results"]) + _results(r)

    total_spend = sum(float(b["spend"]) for b in buckets.values())
    total_results = sum(float(b["results"]) for b in buckets.values())

    items: list[ConjuntoItem] = []
    for b in buckets.values():
        spend = float(b["spend"])
        results = float(b["results"])
        cpl = m.cpa(spend, results)
        share_s = (spend / total_spend * 100) if total_spend else 0
        share_r = (results / total_results * 100) if total_results else 0
        items.append(ConjuntoItem(
            nome=str(b["nome"]),
            spend=spend,
            results=results,
            cpl=cpl,
            share_spend=share_s,
            share_results=share_r,
            veredicto="",  # preenche depois
        ))

    # Ordena por resultados desc
    items.sort(key=lambda x: x.results, reverse=True)

    # Classifica pareto
    cumulative_spend = 0.0
    cumulative_results = 0.0
    for i, item in enumerate(items):
        cumulative_spend += item.spend
        cumulative_results += item.results

    # Top 20% dos conjuntos
    cutoff_top = max(1, len(items) // 5)

    for i, item in enumerate(items):
        if i < cutoff_top and item.results > 0:
            item.veredicto = "escalar"
        elif item.results == 0 and item.spend > 0:
            item.veredicto = "pausar"
        elif item.cpl > 0 and items[0].cpl > 0 and item.cpl > items[0].cpl * 2:
            item.veredicto = "otimizar"
        else:
            item.veredicto = "manter"

    return items


def analisar_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    items = agrupar_por_adset(rows)
    if not items:
        return {"items": [], "total_spend": 0, "total_results": 0, "insights": []}

    total_spend = sum(i.spend for i in items)
    total_results = sum(i.results for i in items)

    # Top 20% stats
    cutoff = max(1, len(items) // 5)
    top20_spend = sum(i.spend for i in items[:cutoff])
    top20_results = sum(i.results for i in items[:cutoff])
    top20_spend_share = (top20_spend / total_spend * 100) if total_spend else 0
    top20_results_share = (top20_results / total_results * 100) if total_results else 0

    # Bottom 50%
    cutoff_bottom = max(1, len(items) // 2)
    bottom_items = items[-cutoff_bottom:]
    bottom_spend = sum(i.spend for i in bottom_items)
    bottom_results = sum(i.results for i in bottom_items)
    bottom_spend_share = (bottom_spend / total_spend * 100) if total_spend else 0
    bottom_results_share = (bottom_results / total_results * 100) if total_results else 0

    # Desperdício: spend sem conversão
    desperdicio = sum(i.spend for i in items if i.results == 0)
    desperdicio_pct = (desperdicio / total_spend * 100) if total_spend else 0

    # Maior concentração
    maior_share = max((i.share_spend for i in items), default=0)
    dep_nome = next((i.nome for i in items if i.share_spend == maior_share), "")

    insights: list[str] = []

    if top20_spend_share > 0:
        if top20_results_share >= top20_spend_share * 1.5:
            insights.append(
                f"🟢 **Concentração Pareto saudável:** top 20% ({cutoff} conjuntos) "
                f"consomem {top20_spend_share:.0f}% do budget e entregam {top20_results_share:.0f}% "
                f"dos resultados. Ambiente claro para alocar mais nos vencedores."
            )
        else:
            insights.append(
                f"🟡 **Pareto morno:** top 20% consomem {top20_spend_share:.0f}% do budget "
                f"mas só entregam {top20_results_share:.0f}% dos resultados. "
                "Falta diferenciação forte entre winners e resto — alguns podem ainda estar "
                "em fase de aprendizado."
            )

    if desperdicio_pct > 15:
        insights.append(
            f"🔴 **Desperdício identificado:** {desperdicio_pct:.0f}% do budget "
            f"({desperdicio:.0f} R$) está em conjuntos com ZERO conversão. "
            "Pausar esses agora libera budget para escalar winners."
        )

    if maior_share > 50:
        insights.append(
            f"⚠️ **Concentração alta:** `{dep_nome}` consome {maior_share:.0f}% do budget. "
            "Se esse conjunto cair (fadiga, bloqueio, mudança algoritmo), conta cai junto. "
            "Diversificar é prioridade de risco."
        )

    return {
        "items": items,
        "total_spend": total_spend,
        "total_results": total_results,
        "top20_count": cutoff,
        "top20_spend_share": top20_spend_share,
        "top20_results_share": top20_results_share,
        "bottom_count": cutoff_bottom,
        "bottom_spend_share": bottom_spend_share,
        "bottom_results_share": bottom_results_share,
        "desperdicio": desperdicio,
        "desperdicio_pct": desperdicio_pct,
        "maior_dependencia_nome": dep_nome,
        "maior_dependencia_share": maior_share,
        "insights": insights,
    }


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    rows = meta.get_ad_insights(
        ad_account_id, since=periodo.since, until=periodo.until, filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    resultado = analisar_rows(rows)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        **resultado,
    }
    filename = report.build_output_filename("eficiencia-orcamento", produto_nome)
    return report.render_markdown(
        "eficiencia_orcamento.md.j2", context, output_filename=filename,
    )
