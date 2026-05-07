"""Página Configurações — visualiza estado do setup."""

from __future__ import annotations

import streamlit as st

from trafego_analysis.core import config as cfg
from trafego_analysis.ui.components import sofia_header
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(page_title="Configurações — trafego", page_icon="⚙️", layout="wide")
apply_theme()
sofia_header("⚙️ Configurações")

st.markdown(
    "Esta página é **read-only** na v1. Para alterar configurações, edite os "
    "arquivos JSON em `user_data/config/` ou rode novamente o wizard.\n\n"
    "**Localização dos configs:**"
)
paths = cfg.get_paths()
st.code(str(paths.config_dir), language="text")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Contas",
    "Produtos",
    "Fases do funil",
    "Perfis",
    "Integrações",
])

with tab1:
    contas = cfg.get_accounts()
    default = cfg.get_default_account_alias()
    if not contas:
        st.warning("Nenhuma conta cadastrada. Rode `trafego setup`.")
    else:
        st.dataframe(
            [
                {
                    "Apelido": c["alias"],
                    "ID": c["ad_account_id"],
                    "Nome": c["display_name"],
                    "Moeda": c.get("currency", "BRL"),
                    "Padrão": "✓" if c["alias"] == default else "",
                }
                for c in contas
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab2:
    produtos = cfg.get_produtos()
    if not produtos:
        st.warning("Nenhum produto cadastrado.")
    else:
        st.dataframe(
            [
                {
                    "Nome": p["nome"],
                    "Ticket": f"R$ {p['ticket']:.2f}",
                    "CPA meta": f"R$ {p['cpa_meta']:.2f}",
                    "ROAS meta": f"{p['roas_meta']:.1f}x",
                    "Tipo": p.get("tipo", "-"),
                }
                for p in produtos
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab3:
    fases = cfg.get_fases()
    if not fases.get("fases"):
        st.warning("Nenhuma fase configurada.")
    else:
        st.dataframe(
            [
                {
                    "ID": f["id"],
                    "Label": f["label"],
                    "Cor": f.get("cor", "-"),
                    "Ordem": f.get("ordem", 0),
                    "Regex match": ", ".join(fases["regex_match"].get(f["id"], [])),
                }
                for f in fases["fases"]
            ],
            use_container_width=True,
            hide_index=True,
        )

with tab4:
    perfis = cfg.get_perfis()
    ativos = perfis.get("ativos", [])
    st.markdown(f"**Perfis ativos:** {', '.join(ativos) or '(nenhum)'}")
    for nome, raw in perfis.get("perfis", {}).items():
        with st.expander(nome):
            st.json(raw)

with tab5:
    integracoes = cfg.get_integracoes()
    st.markdown("- **Meta Ads:** ativo (obrigatório)")
    st.markdown(
        f"- **Google Ads:** {'ativo' if integracoes.get('google_ads') else 'inativo'}"
    )
    st.markdown(
        f"- **Hotmart:** {'ativo' if integracoes.get('hotmart') else 'inativo'}"
    )
    st.markdown("---")
    st.caption(
        "Para ativar/reconfigurar: \n"
        "`trafego setup --google-ads` \n"
        "`trafego setup --hotmart`"
    )
