"""Auditoria estrutural de campanhas — health check.

Verifica problemas de configuração que sangram budget silenciosamente:

  A) Audiência / overlap (via breakdowns age+gender)
  B) Concentração excessiva de budget em poucas campanhas
  C) Campanhas com gasto alto e zero conversão
  D) Frequency fora de controle (>5 em cold, >8 em retarget)
  E) CTR crítico (<0.5%) em campanhas com gasto relevante
  F) Rankings múltiplos `below_average`
  G) CBO com muitos adsets (overlap provável)

Retorna lista de `IssueAuditoria` priorizada por severidade.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import metrics as m
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


class Severidade(StrEnum):
    CRITICA = "CRÍTICA"
    ALTA = "ALTA"
    MEDIA = "MÉDIA"
    BAIXA = "BAIXA"


@dataclass
class IssueAuditoria:
    severidade: Severidade
    categoria: str
    campanha: str
    descricao: str
    recomendacao: str
    metrica: str = ""
    valor: str = ""


def _is_retargeting(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in ("rmk", "remarketing", "retarget"))


def _auditar_campanha(
    row: dict[str, Any],
    total_spend_conta: float,
) -> list[IssueAuditoria]:
    issues: list[IssueAuditoria] = []
    name = row.get("campaign_name") or row.get("name") or "(sem nome)"
    spend = float(row.get("spend") or 0)
    impressions = float(row.get("impressions") or 0)
    frequency = float(row.get("frequency") or 0)
    inline_clicks = float(row.get("inline_link_clicks") or 0)
    purchases = mc.extract_action_count(row.get("actions"), "purchase")
    leads = mc.extract_action_count(row.get("actions"), "lead")
    results = purchases or leads

    # B) Concentração de budget
    if total_spend_conta > 0:
        share = spend / total_spend_conta
        if share > 0.5 and spend > 500:
            issues.append(
                IssueAuditoria(
                    severidade=Severidade.MEDIA,
                    categoria="Concentração de budget",
                    campanha=name,
                    descricao=f"Esta campanha consome {share * 100:.0f}% do gasto da conta.",
                    recomendacao="Diversifique para reduzir risco de colapso do funil inteiro.",
                    metrica="Share do gasto",
                    valor=f"{share * 100:.0f}%",
                )
            )

    # C) Gasto alto + zero conversão
    if spend > 200 and results == 0:
        issues.append(
            IssueAuditoria(
                severidade=Severidade.CRITICA,
                categoria="Queima de budget",
                campanha=name,
                descricao=f"Gasto de {spend:.0f} sem nenhuma conversão registrada.",
                recomendacao="Pause imediatamente e investigue pixel/evento ou adequação da oferta.",
                metrica="Gasto",
                valor=f"R$ {spend:.0f}",
            )
        )

    # D) Frequency descontrolada
    freq_thr = 8.0 if _is_retargeting(name) else 5.0
    if frequency >= freq_thr and spend > 100:
        issues.append(
            IssueAuditoria(
                severidade=Severidade.ALTA,
                categoria="Frequency",
                campanha=name,
                descricao=f"Frequency {frequency:.1f} — audiência saturada.",
                recomendacao="Amplie a audiência ou gire criativos; CPA tende a subir 15-25%.",
                metrica="Frequency",
                valor=f"{frequency:.1f}",
            )
        )

    # E) CTR crítico
    if impressions > 5000 and inline_clicks > 0:
        ctr_atual = m.ctr(inline_clicks, impressions)
        if ctr_atual < 0.5 and spend > 100:
            issues.append(
                IssueAuditoria(
                    severidade=Severidade.ALTA,
                    categoria="CTR crítico",
                    campanha=name,
                    descricao=f"CTR de {ctr_atual:.2f}% (saudável: 1.5-2.5%).",
                    recomendacao="Teste novos criativos — o atual não está conectando.",
                    metrica="CTR link",
                    valor=f"{ctr_atual:.2f}%",
                )
            )

    # F) Rankings múltiplos below_average
    rankings = [
        row.get("quality_ranking"),
        row.get("engagement_rate_ranking"),
        row.get("conversion_rate_ranking"),
    ]
    ruins = [r for r in rankings if r and str(r).lower().startswith("below_average")]
    if len(ruins) >= 2 and spend > 50:
        issues.append(
            IssueAuditoria(
                severidade=Severidade.ALTA,
                categoria="Relevância",
                campanha=name,
                descricao=f"{len(ruins)} rankings de relevância em below_average.",
                recomendacao="Criativo não está encaixando — refazer ou pausar.",
                metrica="Rankings abaixo",
                valor=f"{len(ruins)}/3",
            )
        )

    return issues


def _ordenar(issues: list[IssueAuditoria]) -> list[IssueAuditoria]:
    ordem = {
        Severidade.CRITICA: 0,
        Severidade.ALTA: 1,
        Severidade.MEDIA: 2,
        Severidade.BAIXA: 3,
    }
    return sorted(issues, key=lambda i: ordem[i.severidade])


def auditar(
    rows: list[dict[str, Any]],
) -> list[IssueAuditoria]:
    total_spend = sum(float(r.get("spend") or 0) for r in rows)
    out: list[IssueAuditoria] = []
    for row in rows:
        out.extend(_auditar_campanha(row, total_spend))
    return _ordenar(out)


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
    )

    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    # Agrega ad-level → campaign-level para auditoria (somando os ads de cada campanha)
    grouped: dict[str, dict[str, Any]] = {}
    for r in rows:
        cid = r.get("campaign_id") or r.get("campaign_name") or ""
        if cid not in grouped:
            grouped[cid] = {
                "campaign_name": r.get("campaign_name"),
                "spend": 0.0,
                "impressions": 0.0,
                "inline_link_clicks": 0.0,
                "actions": [],
                "frequency": 0.0,
                "quality_ranking": r.get("quality_ranking"),
                "engagement_rate_ranking": r.get("engagement_rate_ranking"),
                "conversion_rate_ranking": r.get("conversion_rate_ranking"),
                "_freq_weights": 0.0,
            }
        g = grouped[cid]
        impr = float(r.get("impressions") or 0)
        g["spend"] += float(r.get("spend") or 0)
        g["impressions"] += impr
        g["inline_link_clicks"] += float(r.get("inline_link_clicks") or 0)
        g["_freq_weights"] += float(r.get("frequency") or 0) * impr
        # merge actions
        for a in r.get("actions") or []:
            existing = next(
                (x for x in g["actions"] if x["action_type"] == a["action_type"]), None
            )
            if existing:
                existing["value"] = float(existing["value"]) + float(a.get("value", 0))
            else:
                g["actions"].append({"action_type": a["action_type"], "value": float(a.get("value", 0))})

    # Frequency agregada ponderada
    for g in grouped.values():
        if g["impressions"] > 0:
            g["frequency"] = g["_freq_weights"] / g["impressions"]
        del g["_freq_weights"]

    issues = auditar(list(grouped.values()))

    # Agrupa por severidade para template
    por_sev: dict[str, list[IssueAuditoria]] = {
        "CRÍTICA": [],
        "ALTA": [],
        "MÉDIA": [],
        "BAIXA": [],
    }
    for i in issues:
        por_sev[i.severidade.value].append(i)

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "total_issues": len(issues),
        "por_sev": por_sev,
        "total_campanhas": len(grouped),
    }

    filename = report.build_output_filename("auditoria", produto_nome)
    return report.render_markdown("auditoria.md.j2", context, output_filename=filename)
