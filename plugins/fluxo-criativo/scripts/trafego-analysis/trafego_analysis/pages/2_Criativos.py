"""Página Criativos — 6 análises VTSD em abas."""

from __future__ import annotations

from datetime import date

import streamlit as st

from trafego_analysis.analyses import (
    criativos_comparativo,
    criativos_galeria,
    criativos_ranking,
    fadiga_criativa,
    mandala_vtsd,
)
from trafego_analysis.core.meta_client import MetaAPIError, MetaClient
from trafego_analysis.core.periods import Period, PeriodComparison, resolve_period
from trafego_analysis.ui.components import (
    render_markdown_safe,
    seletor_periodo,
    seletor_produto,
    sidebar_seletor_conta,
    sofia_header,
)
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(page_title="Criativos — trafego", page_icon="🎨", layout="wide")
apply_theme()
sofia_header("🎨 Análise de Criativos")

with st.sidebar:
    st.markdown("### Filtros")
    conta = sidebar_seletor_conta()
    produto_nome = seletor_produto()
    periodo_spec = seletor_periodo(default="last_30d")
    top_n = st.slider("Top N", min_value=5, max_value=25, value=10, step=1)

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
    "2.1 Performance",
    "2.2 Tier S/A/B/C/D",
    "2.3 Mandala VTSD",
    "2.4 Fadiga Map",
    "2.5 DNA + Galeria HTML",
    "2.6 Testes A/B",
])

with tabs[0]:
    st.caption("Hook / Thumbstop / Hold / CTR / CPR dos criativos ativos.")
    if st.button("Rodar performance", key="btn_perf_crt", type="primary"):
        with st.spinner("Puxando métricas de criativos..."):
            try:
                text, path = criativos_ranking.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    account_alias=conta["alias"],
                    periodo=p,
                    produto_nome=produto_nome,
                    top_n=top_n,
                    baixar_assets=False,  # sem galeria nessa aba
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[1]:
    st.caption("Score composto + classificação S/A/B/C/D por criativo.")
    with_dna = st.checkbox("Também extrair DNA dos top 3", value=False, key="chk_dna")
    if st.button("Rodar tier ranking", key="btn_tier", type="primary"):
        with st.spinner("Ranqueando..."):
            try:
                text, path = criativos_ranking.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    account_alias=conta["alias"],
                    periodo=p,
                    produto_nome=produto_nome,
                    top_n=top_n,
                    baixar_assets=with_dna,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[2]:
    st.caption("Classifica cada criativo em 1 dos 18 tipos VTSD + mostra gaps.")
    if st.button("Rodar Mandala", key="btn_mandala", type="primary"):
        with st.spinner("Classificando via heurística de copy..."):
            try:
                text, path = mandala_vtsd.analisar(
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
    st.caption("Detecta criativos fatigados via 5 sinais. Decide pausar / substituir.")
    if st.button("Rodar Fadiga Map", key="btn_fadiga", type="primary"):
        from datetime import timedelta
        periodo_atual = p
        days = periodo_atual.days
        periodo_anterior = Period(
            since=periodo_atual.since - timedelta(days=days),
            until=periodo_atual.until - timedelta(days=days),
            label=f"{days} dias anteriores",
        )
        with st.spinner("Analisando fadiga..."):
            try:
                text, path = fadiga_criativa.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    periodo=periodo_atual,
                    periodo_anterior=periodo_anterior,
                    produto_nome=produto_nome,
                )
                render_markdown_safe(text)
                if path:
                    st.caption(f"Salvo em: `{path}`")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[4]:
    st.caption("DNA dos top 3 + galeria HTML visual standalone.")
    if st.button("Gerar galeria", key="btn_galeria", type="primary"):
        with st.spinner("Baixando assets (pode levar 30-60s)..."):
            try:
                out_path, _ = criativos_galeria.analisar(
                    meta=meta,
                    ad_account_id=conta["ad_account_id"],
                    account_alias=conta["alias"],
                    periodo=p,
                    produto_nome=produto_nome,
                    top_n=top_n,
                )
                if out_path:
                    st.success("Galeria gerada!")
                    st.markdown(f"**Caminho:** `{out_path}`")
                    with open(out_path, "rb") as f:
                        st.download_button(
                            "Baixar HTML",
                            data=f,
                            file_name=out_path.name,
                            mime="text/html",
                        )
                else:
                    st.warning("Nenhum criativo elegível.")
            except Exception as e:
                st.error(f"Erro: {e}")

with tabs[5]:
    st.caption("Sugere testes A/B — demografia, idade, gênero, formato, CBO vs ABO.")
    if st.button("Gerar sugestões de teste", key="btn_ab", type="primary"):
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
