"""Análise 4.3 — Revisão Advantage+ (campos e configurações).

Identifica campanhas em Advantage+ e avalia se a configuração está
maximizando o que ele foi projetado pra fazer. Checklist VTSD:

  - Campanha com tipo `ADVANTAGE_PLUS_SHOPPING` ou similar?
  - Criativos suficientes no pool (mínimo 6 para A+ dar folga)?
  - Mandala diversa dentro da campanha A+?
  - Budget adequado para A+ aprender (>R$ 150/dia)?
  - Sem audiência salva manual (deixar a Meta decidir — esse é o ponto do A+)?

Nota: alguns campos não vêm 100% via Insights API. A análise é por inferência
de nome + padrões observados.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class Diagnostico:
    campanha: str
    pontos_positivos: list[str]
    pontos_atencao: list[str]
    recomendacoes: list[str]


def _is_advantage_plus(nome: str) -> bool:
    n = nome.lower()
    return any(k in n for k in ("advantage", "asc", "a+", "advantage+", "adv_plus"))


def analisar_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Agrupa por campanha
    by_camp: dict[str, dict[str, Any]] = {}
    for r in rows:
        cname = r.get("campaign_name") or "(sem nome)"
        c = by_camp.setdefault(cname, {"spend": 0.0, "ads": [], "adsets": set()})
        c["spend"] = float(c["spend"]) + float(r.get("spend") or 0)
        c["ads"].append(r)
        if r.get("adset_name"):
            c["adsets"].add(r["adset_name"])

    # Filtra só campanhas Advantage+ (ou que parecem ser)
    apenas_ap = {k: v for k, v in by_camp.items() if _is_advantage_plus(k)}

    diagnosticos: list[Diagnostico] = []

    for cname, dados in apenas_ap.items():
        positivos: list[str] = []
        atencao: list[str] = []
        recs: list[str] = []

        n_ads = len(dados["ads"])
        n_adsets = len(dados["adsets"])
        spend = float(dados["spend"])
        budget_diario_est = spend / 7  # estimativa pro último período

        # Check 1: Pool de criativos
        if n_ads >= 6:
            positivos.append(f"Pool de criativos OK ({n_ads} ads)")
        elif n_ads >= 3:
            atencao.append(f"Pool magro ({n_ads} ads) — Advantage+ funciona melhor com 6+")
            recs.append("Adicionar 3-4 criativos novos na campanha A+ — variando tipos da Mandala")
        else:
            atencao.append(f"Pool INSUFICIENTE ({n_ads} ads) — A+ precisa de variedade pra otimizar")
            recs.append("Advantage+ com menos de 3 criativos é quase uma campanha tradicional. Adicionar ads.")

        # Check 2: Budget
        if budget_diario_est >= 150:
            positivos.append(f"Budget diário suficiente (~{budget_diario_est:.0f} R$/dia)")
        elif budget_diario_est >= 80:
            atencao.append(f"Budget estreito (~{budget_diario_est:.0f} R$/dia) — A+ precisa de volume pra aprender")
            recs.append("Considerar R$ 150+/dia pra A+ ter fase de aprendizado saudável")
        else:
            atencao.append(f"Budget muito baixo (~{budget_diario_est:.0f} R$/dia) — A+ não aprende")

        # Check 3: Fragmentação por adset
        if n_adsets > 1:
            atencao.append(f"{n_adsets} adsets dentro de uma campanha A+ — o ponto do A+ é deixar a Meta decidir")
            recs.append("Consolidar em um único adset com audiência broad — o A+ funciona melhor assim")

        # Se não tem nada pra reclamar
        if not atencao:
            positivos.append("Configuração aparentemente dentro do padrão VTSD para Advantage+")

        diagnosticos.append(Diagnostico(
            campanha=cname,
            pontos_positivos=positivos,
            pontos_atencao=atencao,
            recomendacoes=recs,
        ))

    # Observações gerais
    obs_gerais: list[str] = []
    if not apenas_ap:
        obs_gerais.append(
            "Nenhuma campanha Advantage+ identificada (filtro por nome contendo "
            "'advantage', 'asc', 'a+' ou 'adv_plus'). Se você usa A+ com nomes diferentes, "
            "padronize ou essa análise não conseguirá mapear."
        )
    else:
        total_spend = sum(float(v["spend"]) for v in apenas_ap.values())
        total_geral = sum(float(v["spend"]) for v in by_camp.values())
        if total_geral:
            share = total_spend / total_geral * 100
            obs_gerais.append(
                f"Advantage+ representa {share:.0f}% do gasto total "
                f"({len(apenas_ap)} campanhas A+)."
            )

    return {
        "diagnosticos": diagnosticos,
        "observacoes_gerais": obs_gerais,
        "total_campanhas_ap": len(apenas_ap),
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
    filename = report.build_output_filename("advantage-plus", produto_nome)
    return report.render_markdown("advantage_plus.md.j2", context, output_filename=filename)
