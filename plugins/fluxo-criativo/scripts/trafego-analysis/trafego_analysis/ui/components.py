"""Widgets reutilizáveis do Streamlit.

Componentes pensados para rodar dentro de `with st.sidebar:` ou na página.
Stateless — lêem direto do `core.config`, não mantêm state entre interações.

Inclui helpers visuais do theme VTSD: `sofia_header`, `card_kpi`, `card_status`,
`tier_badge`, `divider`.
"""

from __future__ import annotations

import streamlit as st

from trafego_analysis.core import config as cfg
from trafego_analysis.core.periods import list_presets
from trafego_analysis.ui.theme import COLORS

# --- Seletores de sidebar -------------------------------------------------

def sidebar_seletor_conta() -> dict | None:
    """Seletor da conta ativa. Retorna o dict da conta selecionada."""
    contas = cfg.get_accounts()
    if not contas:
        st.error("Nenhuma conta cadastrada. Rode `trafego setup`.")
        return None

    default = cfg.get_default_account_alias()
    default_idx = 0
    aliases = [c["alias"] for c in contas]
    if default in aliases:
        default_idx = aliases.index(default)

    escolhido = st.selectbox(
        "Conta",
        aliases,
        index=default_idx,
        format_func=lambda a: f"{a} — {next(c['display_name'] for c in contas if c['alias'] == a)}",
        key="conta_alias",
    )
    return next(c for c in contas if c["alias"] == escolhido)


def seletor_produto() -> str | None:
    """Selectbox de produto (None = todos)."""
    produtos = cfg.get_produtos()
    if not produtos:
        return None
    opts = ["— todos —"] + [p["nome"] for p in produtos]
    escolhido = st.selectbox("Produto", opts, key="produto_sel")
    return escolhido if escolhido != "— todos —" else None


def seletor_periodo(default: str = "last_7d", key_suffix: str = "") -> str:
    """Selectbox do período (preset ou custom)."""
    presets = list_presets()
    opts = [p[0] for p in presets]
    labels = {spec: label for spec, label in presets}

    default_idx = opts.index(default) if default in opts else opts.index("last_7d")
    return st.selectbox(
        "Período",
        opts,
        index=default_idx,
        format_func=lambda s: f"{s} — {labels.get(s, s)}",
        key=f"periodo_sel{key_suffix}",
    )


def seletor_perfil(default: str = "perpetuo") -> str:
    """Selectbox de perfil de análise."""
    perfis = cfg.get_perfis().get("ativos", ["perpetuo"])
    if not perfis:
        perfis = ["perpetuo"]
    default_idx = perfis.index(default) if default in perfis else 0
    return st.selectbox("Perfil", perfis, index=default_idx, key="perfil_sel")


def status_setup() -> None:
    """Mostra indicadores de setup (conta, produtos, integrações)."""
    contas = len(cfg.get_accounts())
    produtos = len(cfg.get_produtos())
    integracoes = cfg.get_integracoes()

    st.markdown("**Setup**")
    st.text(f"  Contas:  {contas}")
    st.text(f"  Produtos: {produtos}")
    if integracoes.get("google_ads"):
        st.text("  Google:  ativo")
    if integracoes.get("hotmart"):
        st.text("  Hotmart: ativo")


def render_markdown_safe(texto: str) -> None:
    """Renderiza markdown mantendo tabelas (wrapper de st.markdown)."""
    st.markdown(texto, unsafe_allow_html=False)


# --- Helpers visuais VTSD -------------------------------------------------

def sofia_header(modulo: str | None = None) -> None:
    """Cabeçalho com avatar + identidade Sofia. Usar no topo de cada página."""
    extra = f" · {modulo}" if modulo else ""
    st.markdown(
        f"""
<div class="sofia-header">
  <div class="sofia-avatar">S</div>
  <div class="sofia-info">
    <div class="nome">Sofia — Analista de Performance RTG</div>
    <div class="papel">Método VTSD{extra}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def divider_vtsd() -> None:
    """Divisor com gradient laranja (mais sutil que hr padrão)."""
    st.markdown('<div class="vtsd-divider"></div>', unsafe_allow_html=True)


def card_kpi(
    titulo: str,
    valor: str,
    delta: str | None = None,
    delta_tipo: str = "neutral",
) -> None:
    """Card de KPI consistente: título pequeno em caps + valor grande + delta.

    delta_tipo: 'positive' | 'negative' | 'neutral'
    """
    delta_html = ""
    if delta:
        delta_html = f'<div class="vtsd-card-delta {delta_tipo}">{delta}</div>'
    st.markdown(
        f"""
<div class="vtsd-card">
  <div class="vtsd-card-title">{titulo}</div>
  <div class="vtsd-card-value">{valor}</div>
  {delta_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def chip_status(label: str, tipo: str = "info") -> str:
    """Retorna HTML de chip colorido. tipo: 'saudavel' | 'atencao' | 'critico' | 'info'."""
    return f'<span class="vtsd-chip {tipo}">{label}</span>'


def tier_badge(letra: str) -> str:
    """Retorna HTML de badge de tier criativo (S/A/B/C/D)."""
    letra = letra.upper()
    if letra not in ("S", "A", "B", "C", "D"):
        letra = "D"
    return f'<span class="vtsd-tier vtsd-tier-{letra}">{letra}</span>'


def card_status_funil(
    etapa: str, taxa: float, saudavel_min: float | None,
) -> None:
    """Card para etapa do funil VTSD. Cor do chip depende da comparação."""
    if saudavel_min is None:
        chip = chip_status("—", "info")
    elif taxa >= saudavel_min:
        chip = chip_status("Saudável", "saudavel")
    elif taxa >= saudavel_min * 0.7:
        chip = chip_status("Atenção", "atencao")
    else:
        chip = chip_status("Crítico", "critico")

    thresh_txt = f"≥ {saudavel_min:.1f}%" if saudavel_min else "—"

    st.markdown(
        f"""
<div class="vtsd-card">
  <div class="vtsd-card-title">{etapa}</div>
  <div class="vtsd-card-value">{taxa:.1f}%</div>
  <div style="margin-top:8px; display:flex; gap:10px; align-items:center;">
    {chip}
    <span style="color:{COLORS['text_faint']}; font-size:0.8rem;">saudável {thresh_txt}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
