"""Página Histórico — últimas análises geradas."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from trafego_analysis.core.config import get_paths
from trafego_analysis.ui.components import sofia_header
from trafego_analysis.ui.theme import apply_theme

st.set_page_config(page_title="Histórico — trafego", page_icon="📜", layout="wide")
apply_theme()
sofia_header("📜 Histórico de análises")

paths = get_paths()

tab1, tab2 = st.tabs(["📄 Markdown", "🎨 Galerias HTML"])


def _listar_arquivos(diretorio, ext: str) -> list[dict]:
    if not diretorio.exists():
        return []
    arquivos = []
    for f in sorted(diretorio.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.is_file() and f.suffix == ext:
            arquivos.append({
                "nome": f.name,
                "path": str(f),
                "tamanho_kb": round(f.stat().st_size / 1024, 1),
                "modificado": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
            })
    return arquivos


with tab1:
    mds = _listar_arquivos(paths.outputs_markdown_dir, ".md")
    if not mds:
        st.info("Nenhuma análise gerada ainda. Vá em Campanhas/Criativos/Funil e rode uma.")
    else:
        st.markdown(f"**{len(mds)} relatório(s) encontrado(s)** — clique para expandir")
        for arq in mds[:20]:
            with st.expander(f"{arq['nome']}  ·  {arq['modificado']}  ·  {arq['tamanho_kb']} KB"):
                try:
                    with open(arq["path"], encoding="utf-8") as f:
                        texto = f.read()
                    st.markdown(texto)
                    with open(arq["path"], "rb") as f:
                        st.download_button(
                            "Baixar",
                            data=f,
                            file_name=arq["nome"],
                            mime="text/markdown",
                            key=f"dl_{arq['nome']}",
                        )
                except Exception as e:
                    st.error(f"Erro ao ler: {e}")

with tab2:
    htmls = _listar_arquivos(paths.outputs_galerias_dir, ".html")
    if not htmls:
        st.info("Nenhuma galeria gerada ainda. Vá em Criativos → Galeria e gere uma.")
    else:
        st.markdown(f"**{len(htmls)} galeria(s) encontrada(s)**")
        for arq in htmls[:20]:
            col1, col2 = st.columns([4, 1])
            col1.text(f"{arq['nome']}  —  {arq['modificado']}")
            try:
                with open(arq["path"], "rb") as f:
                    col2.download_button(
                        "Baixar",
                        data=f,
                        file_name=arq["nome"],
                        mime="text/html",
                        key=f"dl_gal_{arq['nome']}",
                    )
            except Exception:
                col2.text("—")
