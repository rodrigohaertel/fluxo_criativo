"""Theme central VTSD — paleta + CSS aplicado em todas as páginas Streamlit.

Flat + Dark refinado. Zero dependência de CSS externa. Todas as páginas
devem chamar `apply_theme()` logo após `st.set_page_config()` para garantir
consistência visual.
"""

from __future__ import annotations

# --- Paleta VTSD ----------------------------------------------------------

COLORS = {
    # Fundo e containers
    "bg":          "#0b1220",      # ainda mais escuro que slate-900 — contraste alto
    "bg_card":     "#151f33",      # card um tom acima
    "bg_card_hover": "#1b2740",
    "bg_sidebar":  "#0b1220",

    # Bordas e divisores
    "border":      "#243047",
    "border_soft": "#1a2538",

    # Texto
    "text":        "#e8eef7",
    "text_muted":  "#8b9bb4",
    "text_faint":  "#5a6a85",

    # Acentos VTSD (semaforizados)
    "accent":      "#f97316",      # laranja VTSD — Sofia/brand
    "success":     "#22c55e",      # saudável
    "warn":        "#eab308",      # atenção
    "danger":      "#ef4444",      # crítico
    "info":        "#38bdf8",      # neutro informativo

    # Tier criativo S/A/B/C/D
    "tier_S":      "#22c55e",
    "tier_A":      "#38bdf8",
    "tier_B":      "#eab308",
    "tier_C":      "#f97316",
    "tier_D":      "#ef4444",
}


# --- CSS central ----------------------------------------------------------

CSS = f"""
<style>
  /* --- Página base --- */
  .main, .stApp {{
    background: {COLORS["bg"]};
  }}
  .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1400px;
  }}

  /* --- Tipografia --- */
  h1 {{
    color: {COLORS["text"]};
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
  }}
  h2 {{
    color: {COLORS["text"]};
    font-weight: 600;
    letter-spacing: -0.01em;
    margin-top: 1.5rem;
  }}
  h3 {{
    color: {COLORS["text"]};
    font-weight: 500;
  }}
  p, li, span, div {{
    color: {COLORS["text"]};
  }}
  .stCaption, caption, small {{
    color: {COLORS["text_muted"]} !important;
  }}

  /* --- Sidebar --- */
  section[data-testid="stSidebar"] {{
    background: {COLORS["bg_sidebar"]};
    border-right: 1px solid {COLORS["border_soft"]};
  }}
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 {{
    color: {COLORS["text"]};
  }}

  /* --- Cards (nossos) --- */
  .vtsd-card {{
    background: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
    transition: border-color 0.15s ease, transform 0.15s ease;
  }}
  .vtsd-card:hover {{
    border-color: {COLORS["accent"]};
    transform: translateY(-1px);
  }}
  .vtsd-card-title {{
    font-size: 0.85rem;
    color: {COLORS["text_muted"]};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
  }}
  .vtsd-card-value {{
    font-size: 1.85rem;
    font-weight: 700;
    color: {COLORS["text"]};
    line-height: 1.1;
  }}
  .vtsd-card-delta {{
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 4px;
  }}
  .vtsd-card-delta.positive {{ color: {COLORS["success"]}; }}
  .vtsd-card-delta.negative {{ color: {COLORS["danger"]}; }}
  .vtsd-card-delta.neutral  {{ color: {COLORS["text_muted"]}; }}

  /* --- Status chips (saudável / atenção / crítico) --- */
  .vtsd-chip {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }}
  .vtsd-chip.saudavel {{ background: rgba(34,197,94,0.15);  color: {COLORS["success"]}; }}
  .vtsd-chip.atencao  {{ background: rgba(234,179,8,0.15);  color: {COLORS["warn"]};    }}
  .vtsd-chip.critico  {{ background: rgba(239,68,68,0.15);  color: {COLORS["danger"]};  }}
  .vtsd-chip.info     {{ background: rgba(56,189,248,0.15); color: {COLORS["info"]};    }}

  /* --- Tier badges S/A/B/C/D --- */
  .vtsd-tier {{
    display: inline-block;
    width: 24px; height: 24px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.8rem;
    text-align: center;
    line-height: 24px;
    color: white;
  }}
  .vtsd-tier-S {{ background: {COLORS["tier_S"]}; }}
  .vtsd-tier-A {{ background: {COLORS["tier_A"]}; }}
  .vtsd-tier-B {{ background: {COLORS["tier_B"]}; color: #1a1a1a; }}
  .vtsd-tier-C {{ background: {COLORS["tier_C"]}; }}
  .vtsd-tier-D {{ background: {COLORS["tier_D"]}; }}

  /* --- Botões --- */
  .stButton button, .stDownloadButton button {{
    background: {COLORS["accent"]};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
    transition: all 0.15s ease;
  }}
  .stButton button:hover, .stDownloadButton button:hover {{
    background: #ea580c;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(249,115,22,0.3);
  }}
  /* Botão "secondary" fica escuro */
  .stButton button[kind="secondary"] {{
    background: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
  }}

  /* --- Tabs --- */
  .stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: {COLORS["bg_card"]};
    padding: 4px;
    border-radius: 10px;
    border: 1px solid {COLORS["border_soft"]};
  }}
  .stTabs [data-baseweb="tab"] {{
    height: 42px;
    background: transparent;
    color: {COLORS["text_muted"]};
    font-weight: 500;
    border-radius: 7px;
    padding: 0 14px;
  }}
  .stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background: {COLORS["accent"]} !important;
    color: white !important;
  }}

  /* --- Inputs / Select / Number --- */
  .stSelectbox > div > div, .stTextInput > div > div input,
  .stNumberInput > div > div input {{
    background: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    color: {COLORS["text"]};
  }}

  /* --- Tabelas do st.dataframe --- */
  .stDataFrame {{
    border: 1px solid {COLORS["border_soft"]};
    border-radius: 8px;
    overflow: hidden;
  }}

  /* --- Expander --- */
  .streamlit-expanderHeader {{
    background: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border_soft"]};
    border-radius: 8px;
    color: {COLORS["text"]};
    font-weight: 500;
  }}

  /* --- Info/Warning/Error/Success boxes --- */
  .stAlert {{
    border-radius: 10px;
    border: 1px solid {COLORS["border"]};
  }}

  /* --- Divisor VTSD --- */
  .vtsd-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, {COLORS["accent"]}, transparent);
    margin: 24px 0;
    border: 0;
    opacity: 0.4;
  }}

  /* --- Header Sofia (brand) --- */
  .sofia-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    background: linear-gradient(135deg, {COLORS["bg_card"]}, {COLORS["bg_card_hover"]});
    border: 1px solid {COLORS["border"]};
    border-left: 3px solid {COLORS["accent"]};
    border-radius: 10px;
    margin-bottom: 18px;
  }}
  .sofia-avatar {{
    width: 40px; height: 40px;
    background: {COLORS["accent"]};
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    color: white;
    font-size: 1.1rem;
  }}
  .sofia-info .nome {{ font-weight: 600; color: {COLORS["text"]}; font-size: 0.95rem; }}
  .sofia-info .papel {{ font-size: 0.8rem; color: {COLORS["text_muted"]}; }}

  /* --- Scrollbar dark --- */
  ::-webkit-scrollbar {{
    width: 10px; height: 10px;
  }}
  ::-webkit-scrollbar-track {{ background: {COLORS["bg"]}; }}
  ::-webkit-scrollbar-thumb {{
    background: {COLORS["border"]};
    border-radius: 5px;
  }}
  ::-webkit-scrollbar-thumb:hover {{ background: {COLORS["accent"]}; }}

  /* --- Esconder footer do Streamlit --- */
  footer, .stDeployButton {{ display: none; }}
</style>
"""


def apply_theme() -> None:
    """Aplica o CSS central. Chamar logo após `st.set_page_config()`."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def plotly_layout_defaults() -> dict:
    """Defaults Plotly alinhados com o theme (usar em fig.update_layout())."""
    return {
        "template": "plotly_dark",
        "paper_bgcolor": COLORS["bg"],
        "plot_bgcolor": COLORS["bg_card"],
        "font": {"color": COLORS["text"], "family": "-apple-system, BlinkMacSystemFont, sans-serif"},
        "colorway": [
            COLORS["accent"],
            COLORS["success"],
            COLORS["info"],
            COLORS["warn"],
            COLORS["danger"],
            "#a855f7",  # roxo extra
        ],
        "xaxis": {"gridcolor": COLORS["border_soft"]},
        "yaxis": {"gridcolor": COLORS["border_soft"]},
    }
