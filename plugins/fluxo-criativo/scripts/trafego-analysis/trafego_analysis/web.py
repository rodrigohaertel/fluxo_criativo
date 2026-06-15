"""Entry point Streamlit — home + navegação (VTSD).

Executado via `trafego web`. Streamlit carrega automaticamente as páginas da
pasta `pages/` adjacente.

Persona: Sofia — Analista de Performance RTG · Método VTSD
"""

from __future__ import annotations

import streamlit as st

from trafego_analysis.core import config as cfg
from trafego_analysis.ui.components import sidebar_seletor_conta, sofia_header, status_setup
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(
    page_title="trafego — Sofia · VTSD",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

sofia_header()

if not cfg.is_setup_complete():
    st.warning(
        "Setup ainda não foi concluído. Abra um terminal e rode: `trafego setup`\n\n"
        "Você ainda pode explorar o **Modo Demo** sem setup (dados fictícios para aula)."
    )
    st.page_link("pages/6_Demo.py", label="🎓 Ir para Modo Demo", icon="🎓")
    st.stop()

with st.sidebar:
    st.markdown("### Conta ativa")
    sidebar_seletor_conta()
    st.markdown("---")
    status_setup()

st.markdown("## Módulos de Análise")

# Linha 1: 3 módulos principais
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📊 Campanhas")
    st.markdown(
        "**6 análises VTSD:**\n\n"
        "1.1 Performance Geral\n\n"
        "1.2 Escalabilidade\n\n"
        "1.3 Conjuntos (HOT/COLD)\n\n"
        "1.4 Eficiência Orçamento\n\n"
        "1.5 Prospecção × Retargeting\n\n"
        "1.6 Dayparting"
    )
    st.page_link("pages/1_Campanhas.py", label="Abrir", icon="📊")

with col2:
    st.markdown("### 🎨 Criativos")
    st.markdown(
        "**6 análises VTSD:**\n\n"
        "2.1 Performance\n\n"
        "2.2 Tier S/A/B/C/D\n\n"
        "2.3 Mandala VTSD (18 tipos)\n\n"
        "2.4 Fadiga Map\n\n"
        "2.5 DNA + Galeria HTML\n\n"
        "2.6 Testes A/B"
    )
    st.page_link("pages/2_Criativos.py", label="Abrir", icon="🎨")

with col3:
    st.markdown("### 🔻 Funil")
    st.markdown(
        "**6 análises VTSD:**\n\n"
        "3.1 Mapa do Funil\n\n"
        "3.2 Gargalo Detection\n\n"
        "3.3 Projeção de Escala\n\n"
        "3.4 Caixa Rápido\n\n"
        "3.5 Pico × Evergreen\n\n"
        "3.6 Análise Checkout"
    )
    st.page_link("pages/3_Funil.py", label="Abrir", icon="🔻")

st.markdown("---")

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("### 🏥 Saúde da Conta")
    st.markdown(
        "**6 análises VTSD:**\n\n"
        "4.1 Health Score 0-100\n\n"
        "4.2 Alertas Prioritários\n\n"
        "4.3 Revisão Advantage+\n\n"
        "4.4 Testes A/B\n\n"
        "4.5 Pausa Hierárquica\n\n"
        "4.6 Plano Executivo"
    )
    st.page_link("pages/5_Conta.py", label="Abrir", icon="🏥")

with col5:
    st.markdown("### 🌐 Cross-canal")
    st.markdown(
        "Meta + Google Ads + Hotmart consolidados.\n\n"
        "Google/Hotmart opcionais — ative com "
        "`trafego setup --google-ads` ou `--hotmart`."
    )
    st.page_link("pages/4_Cross_Canal.py", label="Abrir", icon="🌐")

with col6:
    st.markdown("### 🎓 Modo Demo")
    st.markdown(
        "**Dados fictícios D1-D7** para aula:\n\n"
        "D1-D5: cenários típicos\n\n"
        "**D6**: conta em crise 🔴\n\n"
        "**D7**: conta escalável 🟢\n\n"
        "Cada análise traz bloco **Ensine Isso**."
    )
    st.page_link("pages/6_Demo.py", label="Abrir", icon="🎓")

st.markdown("---")

col7, col8 = st.columns(2)
with col7:
    st.markdown("### ⚙️ Configurações")
    st.markdown("Contas, produtos, fases, perfis, tokens.")
    st.page_link("pages/7_Configuracoes.py", label="Abrir", icon="⚙️")
with col8:
    st.markdown("### 📜 Histórico")
    st.markdown("Relatórios markdown e galerias HTML geradas.")
    st.page_link("pages/8_Historico.py", label="Abrir", icon="📜")

st.markdown(
    """
<div style="margin-top:40px; padding-top:20px; border-top:1px solid #243047;
            text-align:center; color:#5a6a85; font-size:0.8rem;">
  Sofia · Método VTSD · Ready To Go · github.com/trafegopaid/skill-analise
</div>
    """,
    unsafe_allow_html=True,
)
