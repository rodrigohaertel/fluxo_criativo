"""Análise Cross-canal — Meta + Google Ads + Hotmart agregados.

Agrega spend e conversões dos 3 canais para mostrar ROAS consolidado. Se Google
e/ou Hotmart não estiverem ativados no wizard, mostra apenas Meta com aviso.

Limitações conhecidas:
  - Atribuição é last-click (sem multi-touch na v1)
  - Hotmart é fonte de verdade da RECEITA (não soma receitas duplicadas do pixel Meta)
  - Cross-source canibalização é apenas estimada (via pixel Meta vs vendas Hotmart)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from trafego_analysis.core import config as cfg
from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.periods import Period


@dataclass
class CanalResumo:
    nome: str
    ativo: bool
    spend: float = 0.0
    impressions: float = 0.0
    clicks: float = 0.0
    conversions: float = 0.0       # pode ser leads ou vendas dependendo do canal
    revenue: float = 0.0
    share_spend: float = 0.0
    roas: float = 0.0
    observacoes: list[str] = field(default_factory=list)


def _meta_resumo(meta: mc.MetaClient | None, ad_account_id: str, periodo: Period) -> CanalResumo:
    canal = CanalResumo(nome="Meta Ads", ativo=meta is not None)
    if not meta:
        canal.observacoes.append("Meta client não disponível.")
        return canal
    try:
        rows = meta.get_campaign_insights(
            ad_account_id, since=periodo.since, until=periodo.until,
        )
    except Exception as e:
        canal.ativo = False
        canal.observacoes.append(f"Erro ao buscar Meta: {e}")
        return canal

    for r in rows:
        canal.spend += float(r.get("spend") or 0)
        canal.impressions += float(r.get("impressions") or 0)
        canal.clicks += float(r.get("inline_link_clicks") or r.get("clicks") or 0)
        purchases = mc.extract_action_count(r.get("actions"), "purchase")
        leads = mc.extract_action_count(r.get("actions"), "lead")
        canal.conversions += purchases or leads
        canal.revenue += mc.extract_action_value(r.get("action_values"), "purchase")

    canal.roas = canal.revenue / canal.spend if canal.spend else 0
    return canal


def _google_resumo(periodo: Period) -> CanalResumo:
    integracoes = cfg.get_integracoes()
    canal = CanalResumo(nome="Google Ads", ativo=bool(integracoes.get("google_ads")))
    if not canal.ativo:
        canal.observacoes.append("Integração desativada — `trafego setup --google-ads` para ativar.")
        return canal
    try:
        from trafego_analysis.core.google_client import GoogleAdsClient, agregar_totais

        client = GoogleAdsClient.from_saved_config()
        rows = client.get_campaign_insights(since=periodo.since, until=periodo.until)
        agg = agregar_totais(rows)
        canal.spend = agg["spend"]
        canal.impressions = agg["impressions"]
        canal.clicks = agg["clicks"]
        canal.conversions = agg["conversions"]
        canal.revenue = agg["revenue"]
        canal.roas = canal.revenue / canal.spend if canal.spend else 0
    except Exception as e:
        canal.ativo = False
        canal.observacoes.append(f"Erro Google Ads: {e}")
    return canal


def _hotmart_resumo(periodo: Period) -> CanalResumo:
    integracoes = cfg.get_integracoes()
    canal = CanalResumo(nome="Hotmart", ativo=bool(integracoes.get("hotmart")))
    if not canal.ativo:
        canal.observacoes.append("Integração desativada — `trafego setup --hotmart` para ativar.")
        return canal
    try:
        from trafego_analysis.core.hotmart_client import HotmartClient, agregar_totais

        client = HotmartClient.from_saved_config()
        vendas = client.get_sales(since=periodo.since, until=periodo.until)
        agg = agregar_totais(vendas)
        canal.conversions = agg["vendas_aprovadas"]
        canal.revenue = agg["receita"]
        canal.observacoes.append(
            f"{int(agg['vendas_aprovadas'])} vendas aprovadas · "
            f"ticket médio R$ {agg['ticket_medio']:.2f}"
        )
    except Exception as e:
        canal.ativo = False
        canal.observacoes.append(f"Erro Hotmart: {e}")
    return canal


def analisar(
    *,
    meta: mc.MetaClient | None,
    ad_account_id: str | None,
    periodo: Period,
    produto_nome: str | None = None,
) -> tuple[str, Any]:
    canais: list[CanalResumo] = []

    if meta and ad_account_id:
        canais.append(_meta_resumo(meta, ad_account_id, periodo))
    canais.append(_google_resumo(periodo))
    canais.append(_hotmart_resumo(periodo))

    total_spend = sum(c.spend for c in canais if c.ativo)
    total_conversions = sum(c.conversions for c in canais if c.ativo)
    # Receita: se Hotmart ativo, é a fonte de verdade; senão, soma o que houver
    hotmart_canal = next((c for c in canais if c.nome == "Hotmart" and c.ativo), None)
    if hotmart_canal and hotmart_canal.revenue > 0:
        total_revenue = hotmart_canal.revenue
        nota_receita = "Receita vem do Hotmart (fonte de verdade de vendas)."
    else:
        total_revenue = sum(c.revenue for c in canais if c.ativo)
        nota_receita = "Receita estimada pelo pixel de cada canal (pode ter duplicação)."

    # Share de spend por canal
    for c in canais:
        if c.ativo and total_spend > 0:
            c.share_spend = c.spend / total_spend * 100

    roas_blended = (total_revenue / total_spend) if total_spend else 0

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "canais": canais,
        "total_spend": total_spend,
        "total_conversions": total_conversions,
        "total_revenue": total_revenue,
        "roas_blended": roas_blended,
        "nota_receita": nota_receita,
    }
    filename = report.build_output_filename("cross-canal", produto_nome)
    return report.render_markdown("cross_canal.md.j2", context, output_filename=filename)
