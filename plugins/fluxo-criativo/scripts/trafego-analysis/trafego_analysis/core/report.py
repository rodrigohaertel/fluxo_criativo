"""Renderização de relatórios markdown via Jinja2.

Templates vivem em `templates/` (shipped com o package). Cada análise tem seu
template. A função `render_markdown` carrega o template, injeta contexto e
salva em `outputs/markdown/`.
"""

from __future__ import annotations

from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from trafego_analysis.core.config import get_paths


def _templates_dir() -> Path:
    """Localiza a pasta de templates dentro do package.

    Templates vivem em `trafego_analysis/templates/` — empacotados via
    `package-data` no pyproject.toml, funcionam tanto em `pip install -e`
    quanto em wheel regular.
    """
    # Caminho primário: dentro do package (funciona sempre)
    pkg_templates = Path(__file__).resolve().parent.parent / "templates"
    if pkg_templates.is_dir():
        return pkg_templates

    # Fallback via importlib.resources (caso a estrutura mude no futuro)
    try:
        with resources.as_file(resources.files("trafego_analysis.templates")) as p:
            if Path(p).is_dir():
                return Path(p)
    except (FileNotFoundError, ModuleNotFoundError):
        pass

    # Último recurso: templates na raiz do repo (legado, editable dev)
    repo_root = Path(__file__).resolve().parent.parent.parent
    legacy = repo_root / "templates"
    if legacy.is_dir():
        return legacy

    raise FileNotFoundError(
        "Diretório 'templates/' não encontrado no package. Reinstale: pip install -e ."
    )


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_templates_dir())),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _fmt_brl(v: float | None) -> str:
    """R$ 1.234 (sem decimais acima de 100) ou R$ 12,34 (com decimais abaixo)."""
    if v is None:
        return "N/A"
    if abs(v) >= 100:
        s = f"{v:,.0f}"
    else:
        s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(v: float | None, decimals: int = 2) -> str:
    if v is None:
        return "N/A"
    return f"{v:.{decimals}f}%"


def _fmt_num(v: float | None) -> str:
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
        s = f"{v:,.0f}".replace(",", ".")
        return s
    return f"{v:.2f}"


def _fmt_delta(v: float | None) -> str:
    """+12.34% ou -5.67%. Setas podem ser adicionadas no template por cor."""
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"


def render_markdown(
    template_name: str,
    context: dict[str, Any],
    *,
    output_filename: str | None = None,
) -> tuple[str, Path | None]:
    """Renderiza template e opcionalmente salva em outputs/markdown/.

    Retorna (texto_renderizado, caminho_salvo_ou_None).
    """
    env = _env()
    env.filters["brl"] = _fmt_brl
    env.filters["pct"] = _fmt_pct
    env.filters["num"] = _fmt_num
    env.filters["delta"] = _fmt_delta

    tpl = env.get_template(template_name)
    text = tpl.render(**context, now=datetime.now())

    saved_path: Path | None = None
    if output_filename:
        saved_path = get_paths().outputs_markdown_dir / output_filename
        saved_path.write_text(text, encoding="utf-8")

    return text, saved_path


def build_output_filename(analise: str, produto: str | None = None) -> str:
    """Padrão: YYYY-MM-DD_HHMM_<produto>_<analise>.md"""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    prod_slug = (produto or "geral").lower().replace(" ", "-")
    return f"{ts}_{prod_slug}_{analise}.md"
