"""Página Modo Demo — cenários D1-D7 para aula gravada."""

from __future__ import annotations

import streamlit as st

from trafego_analysis.analyses import demo as demo_mod
from trafego_analysis.ui.components import render_markdown_safe, sofia_header
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(page_title="Modo Demo — trafego", page_icon="🎓", layout="wide")
apply_theme()
sofia_header("🎓 Modo Demo — aula gravada")

st.warning(
    "⚠️ **Modo Demo ativo.** Os dados exibidos são fictícios para fins didáticos. "
    "Padrões reais do mercado BR infoproduto — úteis para demonstração em aula."
)

st.markdown(
    """
### Escolha o cenário:

| Cenário | O quê |
|---|---|
| **D1** | Análise completa — conta neutra típica |
| **D2-D5** | Módulos isolados (Campanhas / Criativos / Funil / Saúde) — mesmos dados, recortes diferentes |
| **D6** | 🔴 Cenário de CRISE — conta com problemas graves |
| **D7** | 🟢 Cenário de ESCALA — conta saudável, pronta para subir |
"""
)

cenario = st.selectbox(
    "Cenário",
    ["D1", "D2", "D3", "D4", "D5", "D6", "D7"],
    index=0,
    format_func=lambda c: {
        "D1": "D1 — Análise completa",
        "D2": "D2 — Só Campanhas",
        "D3": "D3 — Só Criativos",
        "D4": "D4 — Só Funil",
        "D5": "D5 — Só Saúde",
        "D6": "🔴 D6 — Cenário de Crise",
        "D7": "🟢 D7 — Cenário de Escala",
    }.get(c, c),
)

if st.button("Rodar demo", type="primary"):
    with st.spinner("Gerando análise fictícia..."):
        try:
            text, path = demo_mod.gerar_demo(cenario)
            render_markdown_safe(text)
            if path:
                st.caption(f"Salvo em: `{path}`")
        except Exception as e:
            st.error(f"Erro: {e}")
