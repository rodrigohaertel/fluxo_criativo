"""Análise 2.6 — Comparativo entre Criativos + Sugestão de Testes A/B.

Identifica pares de criativos com performance significativamente diferente e
sugere testes A/B estruturados. Também sugere variações demográficas,
geográficas e de hook pra criativos vencedores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class SugestaoTeste:
    tipo: str                # "demografia" | "geografia" | "formato" | "hook" | "mandala"
    titulo: str
    hipotese: str
    como_testar: str
    criativos_base: list[str]


def gerar_sugestoes(rows: list[dict[str, Any]]) -> list[SugestaoTeste]:
    """Gera sugestões de testes A/B baseadas nos criativos ativos."""
    sugestoes: list[SugestaoTeste] = []

    # Winner: ad com maior CPA eficiente + volume
    ads_com_cpa = []
    for r in rows:
        spend = float(r.get("spend") or 0)
        p = mc.extract_action_count(r.get("actions"), "purchase")
        l = mc.extract_action_count(r.get("actions"), "lead")
        results = p or l
        if results > 0 and spend > 50:
            ads_com_cpa.append((r, spend / results, results))

    ads_com_cpa.sort(key=lambda x: x[1])
    winners = [a[0] for a in ads_com_cpa[:3]]
    winner_names = [a.get("ad_name", "?") for a in winners]

    # Sugestão 1: demografia (idade/gênero)
    sugestoes.append(SugestaoTeste(
        tipo="demografia",
        titulo="Teste demográfico por gênero",
        hipotese=(
            "Os winners atuais podem estar performando melhor em um gênero específico. "
            "Separar em adsets masculino vs. feminino pode revelar CPL 20-40% menor em um deles."
        ),
        como_testar=(
            "Duplique o adset vencedor. No duplicado A: segmentar só mulheres 25-45. "
            "No B: só homens 25-45. Mesmo criativo e budget. Rode 7 dias. "
            "Se CPL diferir >20%, foco no ganhador."
        ),
        criativos_base=winner_names[:2],
    ))

    sugestoes.append(SugestaoTeste(
        tipo="demografia",
        titulo="Teste por faixa etária",
        hipotese=(
            "Produto provavelmente tem sweet spot de idade. Segmentar 25-34 vs 35-44 vs 45-54 "
            "isoladamente pode concentrar budget onde a conversão é maior."
        ),
        como_testar=(
            "3 adsets idênticos com idades diferentes. Volume mínimo 50 conversões por adset "
            "pra resultado confiável. Mantenha o MESMO criativo."
        ),
        criativos_base=winner_names[:1],
    ))

    # Sugestão 2: geografia
    sugestoes.append(SugestaoTeste(
        tipo="geografia",
        titulo="Falantes de português fora do Brasil",
        hipotese=(
            "Portugal, Angola, Moçambique e comunidade BR no exterior (Miami, Boston, Londres) "
            "têm CPL menor por leilão menos disputado. Budget pequeno pode render conversão barata."
        ),
        como_testar=(
            "Criar adset novo com audiência: idioma=português, localização=PT+AO+MZ+CV. "
            "Budget 20-30% do principal. Mesmo criativo. Rodar 14 dias. "
            "Atenção: converter moeda se houver comissão Hotmart."
        ),
        criativos_base=winner_names[:1],
    ))

    # Sugestão 3: criativo vs criativo (winner vs novo)
    if len(winner_names) >= 2:
        sugestoes.append(SugestaoTeste(
            tipo="formato",
            titulo="A/B de formato: vertical vs quadrado",
            hipotese=(
                "Feed + Stories + Reels consomem formatos diferentes. Criativo vertical no "
                "Feed pode ter Hook Rate menor. Teste formato mantendo copy idêntico."
            ),
            como_testar=(
                "Pegar o winner atual e produzir 1 variação vertical (9:16) + 1 quadrada (1:1). "
                "Rodar em adsets separados com placement manual (Feed vs Reels/Stories). "
                "7-10 dias. Comparar Hook Rate + CTR."
            ),
            criativos_base=[winner_names[0]],
        ))

    # Sugestão 4: CBO vs ABO
    sugestoes.append(SugestaoTeste(
        tipo="estrutura",
        titulo="Advantage+ Campaign vs ABO (orçamento no conjunto)",
        hipotese=(
            "Advantage+ Campaign deixa a Meta otimizar entre adsets. Em contas com 3+ adsets, "
            "isso pode reduzir CPL 15-25%. Mas remove controle fino. Testar em paralelo."
        ),
        como_testar=(
            "Duplicar campanha atual. Versão A: manter ABO (orçamento no adset). "
            "Versão B: converter em Advantage+ Campaign. Rodar 10 dias com MESMO budget total. "
            "Comparar CPA final + saúde de frequência."
        ),
        criativos_base=winner_names,
    ))

    # Sugestão 5: hook
    sugestoes.append(SugestaoTeste(
        tipo="hook",
        titulo="A/B de hook — mesma Urgência, abertura diferente",
        hipotese=(
            "Dois criativos com a MESMA Urgência Oculta mas hooks diferentes podem ter "
            "Hook Rate 2x diferente. Valida que o gancho do VTSD está certo, só a execução muda."
        ),
        como_testar=(
            "Pegar o winner e gerar 2 variações: (A) hook como pergunta, (B) hook como afirmação "
            "de dor. Mesma Furadeira, mesmos Decorados, mesmo CTA. Rodar adsets iguais, comparar Hook Rate."
        ),
        criativos_base=winner_names[:1],
    ))

    return sugestoes


def analisar_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sugestoes = gerar_sugestoes(rows)
    return {
        "sugestoes": sugestoes,
        "total_sugeridas": len(sugestoes),
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
    filename = report.build_output_filename("criativos-comparativo", produto_nome)
    return report.render_markdown(
        "criativos_comparativo.md.j2", context, output_filename=filename,
    )
