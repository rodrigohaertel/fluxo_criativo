"""Análise 2.3 — Mandala VTSD (18 tipos + Gap Finder).

Classifica cada criativo ativo em um dos 18 tipos da Mandala VTSD via análise
heurística do copy. Identifica tipos ausentes na conta e sugere ângulos
concretos para fechar gap.

A Mandala garante que o produto seja comunicado por múltiplos ângulos para
múltiplos perfis de consumidor. Uma conta com 3 tipos ativos está deixando
**15 portas fechadas**.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report, vtsd
from trafego_analysis.core.periods import Period

# Patterns heurísticos para classificar copy em um tipo da Mandala.
# Ordem importa: mais específico vem primeiro.
PATTERNS: dict[str, list[str]] = {
    "comparacao": [r"\bantes\b.*\bagora\b", r"\bdeixa(?:r|ram) de\b", r"\bmudou tudo\b"],
    "certo_errado": [r"\bt[áa] errado\b", r"\bjeito errado\b", r"\bpar(?:a|e) de fazer\b", r"\b99% faz\b"],
    "contraste": [r"\bantes\b.*\bdepois\b", r"antes x depois", r"antes vs depois"],
    "problema_solucao": [r"sofrendo com", r"problema de", r"solu[cç][ãa]o", r"resolver"],
    "prova_social": [r"\d+ alunos?\b", r"\d+ mil\b", r"depoimento", r"resultado de", r"caso real"],
    "oportunidade": [r"\b[áa]ltimas? (vagas|horas?|d+ias?)\b", r"\benquanto d[áa] tempo\b", r"\bfecha (hoje|amanh[ãa])\b", r"\boferta\b"],
    "clickbait": [r"\bchocante\b", r"\bninguém te contou\b", r"\bsegredo\b", r"\binacredit[áa]vel\b"],
    "curiosidade": [r"\bvoc[êe] sabia\b", r"\b[0-9]+ coisas? que\b", r"\bpor que\b"],
    "dilema": [r"\bou .* ou\b", r"\bescolha entre\b", r"\bdecis[ãa]o\b"],
    "reflexao": [r"\?$", r"\bpense\b", r"\breflita\b", r"\be se\b"],
    "mito": [r"\bmito\b", r"\bverdade que\b", r"\bn[ãa]o é verdade\b"],
    "historia": [r"\bquando eu comecei\b", r"\bhist[óo]ria\b", r"\bjornada\b", r"\b(minha|meu) \w+ (era|foi)\b"],
    "ultra_segmentado": [r"\bse voc[êe] [éeé]\b", r"\bpara .* de (\d+|[0-9]+\+)\b"],
    "apelo_emocional": [r"\bme senti\b", r"\bsentimento\b", r"\bemocionante\b", r"\bchorei\b"],
    "demonstracao": [r"\bveja (como|eu) fa[çc]o\b", r"\bao vivo\b", r"\bdemonstra(?:ç|c)[ãa]o\b"],
    "explicacao": [r"\baprend[aei]\b", r"\bentenda\b", r"\bsignifica que\b"],
    "sensacao": [r"\bimagina\b", r"\bsint(?:a|o)\b", r"\bvoc[êe] vai sentir\b"],
    "visual": [r"\bolha (isso|essa)\b", r"\bveja (isso|essa)\b"],  # típico de ads visuais
}


def classificar_copy(title: str, body: str) -> str | None:
    """Retorna id do tipo Mandala ou None se nenhum padrão casar."""
    combined = f"{title} {body}".lower()
    for tipo_id, patterns in PATTERNS.items():
        for p in patterns:
            try:
                if re.search(p, combined):
                    return tipo_id
            except re.error:
                continue
    return None


@dataclass
class CriativoClassificado:
    ad_id: str
    ad_name: str
    title: str
    body: str
    tipo_mandala: str | None
    tipo_nome: str
    spend: float
    results: float


def _results(row: dict) -> float:
    p = mc.extract_action_count(row.get("actions"), "purchase")
    l = mc.extract_action_count(row.get("actions"), "lead")
    return p or l


def analisar_rows(rows: list[dict[str, Any]], creative_fetcher=None) -> dict[str, Any]:
    """Classifica cada row na Mandala. Opcionalmente usa `creative_fetcher(ad_id)`
    para buscar copy da creative (quando ad-level insights não trazem title/body).
    """
    classificados: list[CriativoClassificado] = []
    sem_copy = 0

    for r in rows:
        ad_id = r.get("ad_id") or ""
        title = r.get("title") or ""
        body = r.get("body") or ""

        # Se não temos copy e há fetcher, busca.
        if not title and not body and creative_fetcher and ad_id:
            try:
                creative = creative_fetcher(ad_id) or {}
                title = creative.get("title") or ""
                body = creative.get("body") or ""
            except Exception:
                pass

        if not title and not body:
            sem_copy += 1
            continue

        tipo_id = classificar_copy(title, body)
        tipo = vtsd.mandala_por_id(tipo_id) if tipo_id else None

        classificados.append(CriativoClassificado(
            ad_id=ad_id,
            ad_name=r.get("ad_name") or "(sem nome)",
            title=title[:60],
            body=body[:120],
            tipo_mandala=tipo_id,
            tipo_nome=tipo["nome"] if tipo else "(não classificado)",
            spend=float(r.get("spend") or 0),
            results=_results(r),
        ))

    # Conta tipos presentes
    contador = Counter(c.tipo_mandala for c in classificados if c.tipo_mandala)
    tipos_presentes = {tipo_id: {
        "nome": vtsd.mandala_por_id(tipo_id)["nome"],
        "count": count,
        "spend": sum(c.spend for c in classificados if c.tipo_mandala == tipo_id),
        "results": sum(c.results for c in classificados if c.tipo_mandala == tipo_id),
    } for tipo_id, count in contador.items()}

    # Gap
    todos_ids = {t["id"] for t in vtsd.MANDALA_TIPOS}
    presentes_ids = set(contador.keys())
    ausentes = sorted(todos_ids - presentes_ids)

    return {
        "classificados": classificados,
        "tipos_presentes": tipos_presentes,
        "tipos_ausentes": [vtsd.mandala_por_id(i) for i in ausentes],
        "cobertura_atual": len(presentes_ids),
        "cobertura_total": len(todos_ids),
        "sem_copy": sem_copy,
    }


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    periodo: Period,
    produto_nome: str | None = None,
    filtering: list[dict[str, Any]] | None = None,
    baixar_creative_copy: bool = True,
) -> tuple[str, Any]:
    rows = meta.get_ad_insights(
        ad_account_id, since=periodo.since, until=periodo.until, filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    # Busca copy dos criativos se disponível
    fetcher = None
    if baixar_creative_copy:
        from trafego_analysis.core.assets import fetch_ad_creative
        def fetcher(ad_id):
            return fetch_ad_creative(meta, ad_id)

    resultado = analisar_rows(rows, creative_fetcher=fetcher)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        **resultado,
    }
    filename = report.build_output_filename("mandala", produto_nome)
    return report.render_markdown("mandala.md.j2", context, output_filename=filename)
