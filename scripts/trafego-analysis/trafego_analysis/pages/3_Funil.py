"""Página Funil — 6 análises VTSD em abas."""

from __future__ import annotations

from datetime import date

import streamlit as st

from trafego_analysis.analyses import (
    caixa_rapido,
    checkout_analise,
    fases_funil,
    funil_waterfall,
    pico_vs_evergreen,
    projecao_escala,
)
from trafego_analysis.core.meta_client import MetaAPIError, MetaClient
from trafego_analysis.core.periods import PeriodComparison, resolve_period
from trafego_analysis.ui.components import (
    render_markdown_safe,
    seletor_periodo,
    seletor_produto,
    sidebar_seletor_conta,
    sofia_header,
)
from trafego_analysis.ui.theme import apply_theme, plotly_layout_defaults

st.set_page_config(page_title="Funil — trafego", page_icon="🔻", layout="wide")
apply_theme()
sofia_header("🔻 Análise de Funil")

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

p = resolve_period(periodo_spec, today=date.today())
if isinstance(p, PeriodComparison):
    p = p.current


tabs = st.tabs([
    "3.1 Mapa Funil",
    "3.2 Gargalo",
    "3.3 Projeção Escala",
    "3.4 Caixa Rápido",
    "3.5 Pico × Evergreen",
    "3.6 Checkout",
])

with tabs[0]:
    st.caption("Mapa VTSD completo: Hook → CTR → LPVR → Opt-in → Offer → Connect → LTV.")
    if st.button("Rodar waterfall", key="btn_wf", type="primary"):
        with st.spinner("Construindo funil..."):
            try:
                text, path = funil_waterfall.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=p,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)

                # Plotly funnel visual
                try:
                    import plotly.graph_objects as go

                    from trafego_analysis.analyses.funil_waterfall import construir_waterfall
                    rows = meta.get_ad_insights(
                        conta["ad_account_id"], since=p.since, until=p.until,
                    )
                    if produto_nome:
                        nome_low = produto_nome.lower()
                        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]
                    wf = construir_waterfall(rows)
                    labels = [e.label for e in wf.etapas if e.tem_dados]
                    volumes = [int(e.volume) for e in wf.etapas if e.tem_dados]
                    fig = go.Figure(go.Funnel(
                        y=labels,
                        x=volumes,
                        textposition="inside",
                        textinfo="value+percent previous",
                    ))
                    fig.update_layout(
                        **plotly_layout_defaults(),
                        height=500,
                        margin=dict(t=20, b=20),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.info("Plotly não instalado — instale com `pip install plotly`.")

                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[1]:
    st.caption("Performance por fase do funil (TOPO/MEIO/FUNDO ou customizado).")
    if st.button("Rodar fases", key="btn_fases_funil", type="primary"):
        with st.spinner("Agregando por fase..."):
            try:
                text, path = fases_funil.analisar(
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

with tabs[2]:
    st.caption("Se dobrar / triplicar budget — qual CPA projetado?")
    if st.button("Projetar", key="btn_proj", type="primary"):
        with st.spinner("Projetando cenários..."):
            try:
                text, path = projecao_escala.analisar(
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

with tabs[3]:
    st.caption("Ticket baixo (≤ R$197) — ROAS 3x mínimo viável.")
    ticket = st.number_input("Ticket do produto (R$)", min_value=10.0, value=97.0)
    if st.button("Rodar Caixa Rápido", key="btn_cr", type="primary"):
        with st.spinner("Analisando Caixa Rápido..."):
            try:
                text, path = caixa_rapido.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=p,
                    produto_nome=produto_nome,
                    ticket=ticket,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[4]:
    st.caption("Comparar período de Pico (com urgência) vs. Evergreen.")
    col1, col2 = st.columns(2)
    with col1:
        pico_spec = st.selectbox(
            "Período de Pico",
            ["last_14d", "last_7d", "this_month", "last_month"],
            key="pico_sel",
        )
    with col2:
        ever_spec = st.selectbox(
            "Período Evergreen",
            ["last_30d", "last_14d", "last_90d"],
            key="ever_sel",
        )
    if st.button("Comparar", key="btn_pe", type="primary"):
        with st.spinner("Comparando..."):
            try:
                p_pico = resolve_period(pico_spec, today=date.today())
                p_ever = resolve_period(ever_spec, today=date.today())
                if isinstance(p_pico, PeriodComparison):
                    p_pico = p_pico.current
                if isinstance(p_ever, PeriodComparison):
                    p_ever = p_ever.current
                text, path = pico_vs_evergreen.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo_pico=p_pico,
                    periodo_evergreen=p_ever,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[5]:
    st.caption("Abandono antes do checkout vs. durante o checkout.")
    if st.button("Analisar checkout", key="btn_chk", type="primary"):
        with st.spinner("Diagnosticando..."):
            try:
                text, path = checkout_analise.analisar(
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
