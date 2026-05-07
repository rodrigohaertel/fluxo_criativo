"""Página Cross-canal — Meta + Google Ads + Hotmart."""

from __future__ import annotations

from datetime import date

import streamlit as st

from trafego_analysis.analyses import cross_canal
from trafego_analysis.core import config as cfg
from trafego_analysis.core.meta_client import MetaAPIError, MetaClient
from trafego_analysis.core.periods import PeriodComparison, resolve_period
from trafego_analysis.ui.components import (
    render_markdown_safe,
    seletor_periodo,
    seletor_produto,
    sidebar_seletor_conta,
    sofia_header,
)
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(page_title="Cross-canal — trafego", page_icon="🌐", layout="wide")
apply_theme()
sofia_header("🌐 Análise Cross-canal")

with st.sidebar:
    st.markdown("### Filtros")
    conta = sidebar_seletor_conta()
    produto_nome = seletor_produto()
    periodo_spec = seletor_periodo(default="last_30d")

if not conta:
    st.stop()

integracoes = cfg.get_integracoes()
col1, col2, col3 = st.columns(3)
col1.metric("Meta Ads", "ativo")
col2.metric(
    "Google Ads",
    "ativo" if integracoes.get("google_ads") else "inativo",
    help="Ative com `trafego setup --google-ads`" if not integracoes.get("google_ads") else None,
)
col3.metric(
    "Hotmart",
    "ativo" if integracoes.get("hotmart") else "inativo",
    help="Ative com `trafego setup --hotmart`" if not integracoes.get("hotmart") else None,
)

st.markdown("---")

try:
    meta = MetaClient.from_saved_config()
except MetaAPIError as e:
    st.error(f"Problema com token Meta: {e}")
    st.stop()

p = resolve_period(periodo_spec, today=date.today())
if isinstance(p, PeriodComparison):
    p = p.current

if st.button("Rodar análise cross-canal", type="primary"):
    with st.spinner("Consolidando dados dos canais ativos..."):
        try:
            text, path = cross_canal.analisar(
                meta=meta,
                ad_account_id=conta["ad_account_id"],
                periodo=p,
                produto_nome=produto_nome,
            )
            render_markdown_safe(text)
            if path:
                st.caption(f"Salvo em: `{path}`")
        except Exception as e:
            st.error(f"Erro: {e}")
