"""Página Campanhas — 6 análises VTSD em abas."""

from __future__ import annotations

import streamlit as st

from trafego_analysis.analyses import (
    auditoria_campanha,
    comparativo_conjuntos,
    dayparting,
    eficiencia_orcamento,
    escalabilidade,
    prospeccao_retargeting,
)
from trafego_analysis.core.meta_client import MetaAPIError, MetaClient
from trafego_analysis.core.periods import (
    PeriodComparison,
    resolve_period,
)
from trafego_analysis.ui.components import (
    render_markdown_safe,
    seletor_periodo,
    seletor_produto,
    sidebar_seletor_conta,
    sofia_header,
)
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(page_title="Campanhas — trafego", page_icon="📊", layout="wide")
apply_theme()
sofia_header("📊 Análise de Campanhas")

with st.sidebar:
    st.markdown("### Filtros")
    conta = sidebar_seletor_conta()
    produto_nome = seletor_produto()
    periodo_spec = seletor_periodo(default="last_7d")

if not conta:
    st.stop()

try:
    meta = MetaClient.from_saved_config()
except MetaAPIError as e:
    st.error(f"Problema com token Meta: {e}")
    st.stop()


def _get_period_single(spec: str):
    from datetime import date as _d
    p = resolve_period(spec, today=_d.today())
    if isinstance(p, PeriodComparison):
        return p.current
    return p


tabs = st.tabs([
    "1.1 Performance Geral",
    "1.2 Escalabilidade",
    "1.3 Conjuntos",
    "1.4 Eficiência Orçamento",
    "1.5 Prospecção × Retargeting",
    "1.6 Dayparting",
])

with tabs[0]:
    st.caption("Health check estrutural das campanhas vs. benchmarks VTSD-BR.")
    if st.button("Rodar", key="btn_perf_geral", type="primary"):
        periodo_obj = _get_period_single(periodo_spec)
        with st.spinner("Analisando..."):
            try:
                text, path = auditoria_campanha.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=periodo_obj,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[1]:
    st.caption("Público saturado? Posso escalar com segurança?")
    if st.button("Rodar", key="btn_escala", type="primary"):
        periodo_obj = _get_period_single(periodo_spec)
        with st.spinner("Verificando saturação..."):
            try:
                text, path = escalabilidade.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=periodo_obj,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[2]:
    st.caption("HOT / COLD / SUPERCOLD — distribuição adset-level.")
    if st.button("Rodar", key="btn_conjuntos", type="primary"):
        periodo_obj = _get_period_single(periodo_spec)
        with st.spinner("Classificando conjuntos..."):
            try:
                text, path = comparativo_conjuntos.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=periodo_obj,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[3]:
    st.caption("Pareto 80/20 — onde está o desperdício.")
    if st.button("Rodar", key="btn_orc", type="primary"):
        periodo_obj = _get_period_single(periodo_spec)
        with st.spinner("Aplicando Pareto..."):
            try:
                text, path = eficiencia_orcamento.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=periodo_obj,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[4]:
    st.caption("Mix HOT/COLD/SUPERCOLD vs. ideal da fase VTSD.")
    fase = st.selectbox(
        "Fase VTSD",
        ["evergreen", "pico", "caixa_rapido", "teste_inicial"],
        key="fase_vtsd",
    )
    if st.button("Rodar", key="btn_prosp", type="primary"):
        periodo_obj = _get_period_single(periodo_spec)
        with st.spinner("Comparando mix..."):
            try:
                text, path = prospeccao_retargeting.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=periodo_obj,
                    produto_nome=produto_nome,
                    fase=fase,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[5]:
    st.caption("Heatmap dia × hora + janela recomendada.")
    if st.button("Rodar (pode demorar — breakdown horário)", key="btn_dayparting", type="primary"):
        periodo_obj = _get_period_single(periodo_spec)
        with st.spinner("Montando heatmap..."):
            try:
                text, path = dayparting.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=periodo_obj,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")
