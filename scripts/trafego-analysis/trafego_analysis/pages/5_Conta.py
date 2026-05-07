"""Página Conta — Health Score + 5 análises consolidadas."""

from __future__ import annotations

from datetime import date

import streamlit as st

from trafego_analysis.analyses import (
    advantage_plus,
    alertas_prioritarios,
    conta_health,
    criativos_comparativo,
    pausa_hierarquica,
    plano_executivo,
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
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(page_title="Conta — trafego", page_icon="🏥", layout="wide")
apply_theme()
sofia_header("🏥 Saúde da Conta")

with st.sidebar:
    st.markdown("### Filtros")
    conta = sidebar_seletor_conta()
    produto_nome = seletor_produto()
    periodo_spec = seletor_periodo(default="last_30d")
    ticket = st.number_input("Ticket de referência (R$)", min_value=10.0, value=297.0)

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
    "4.1 Health Score",
    "4.2 Alertas",
    "4.3 Advantage+",
    "4.4 Testes A/B",
    "4.5 Pausa Hierárquica",
    "4.6 Plano Executivo",
])

with tabs[0]:
    st.caption("Score 0-100 em 5 dimensões VTSD.")
    if st.button("Calcular Health Score", key="btn_health", type="primary"):
        with st.spinner("Coletando dimensões..."):
            try:
                text, path = conta_health.analisar(
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

with tabs[1]:
    st.caption("Consolidação dos sinais críticos da conta.")
    if st.button("Gerar alertas", key="btn_alertas", type="primary"):
        with st.spinner("Varrendo sinais..."):
            try:
                text, path = alertas_prioritarios.analisar(
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
    st.caption("Revisão de configuração das campanhas Advantage+.")
    if st.button("Auditar Advantage+", key="btn_adv", type="primary"):
        with st.spinner("Auditando A+..."):
            try:
                text, path = advantage_plus.analisar(
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
    st.caption("Demografia · idade · gênero · países PT · formato · CBO vs ABO · hook.")
    if st.button("Sugerir testes A/B", key="btn_ab_conta", type="primary"):
        with st.spinner("Gerando hipóteses..."):
            try:
                text, path = criativos_comparativo.analisar(
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

with tabs[4]:
    st.caption("Pausar no nível certo: ad / adset / campanha.")
    if st.button("Analisar pausas", key="btn_pausa", type="primary"):
        with st.spinner("Decidindo nível de pausa..."):
            try:
                text, path = pausa_hierarquica.analisar(
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

with tabs[5]:
    st.caption("Consolida tudo em um único relatório executivo para a semana.")
    if st.button("Gerar Plano Executivo", key="btn_plano", type="primary"):
        with st.spinner("Consolidando análises (pode levar 30-60s)..."):
            try:
                text, path = plano_executivo.analisar(
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
