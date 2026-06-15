"""Extrai a seção "Objeções de Compra (Framework dos 7 Argumentos)" do
idconsumidor.md e devolve HTML pronto com accordion (uma objeção por accordion,
fechado por padrão) mais tabela-resumo.

Uso:
    py -3 scripts/playbook-extrair-objecoes.py --slug taro-para-iniciantes
    py -3 scripts/playbook-extrair-objecoes.py   # usa meus-produtos/.ativo

Saída: imprime HTML no stdout. Se o arquivo não tiver a seção de objeções no
formato esperado, imprime uma mensagem de erro no stderr e sai com código 2.
"""
from __future__ import annotations

import argparse
import html
import io
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
PASTA_PRODUTOS = RAIZ / "meus-produtos"

TITULOS_ARGUMENTOS = [
    "Argumento Incontestável",
    "Argumento Lógico",
    "Argumento por Analogia",
    "Argumento por Exemplificação",
    "Argumento de Valor",
    "Argumento de Consequência",
    "Argumento de Contradição",
]


def descobrir_slug_ativo() -> str:
    ativo = (PASTA_PRODUTOS / ".ativo").read_text(encoding="utf-8").strip()
    if not ativo:
        raise SystemExit("meus-produtos/.ativo está vazio. Use /produto-trocar.")
    return ativo


def ler_idconsumidor(slug: str) -> str:
    caminho = PASTA_PRODUTOS / slug / "idconsumidor.md"
    if not caminho.exists():
        raise SystemExit(f"Não achei {caminho}. Rode /produto-concepcao antes.")
    return caminho.read_text(encoding="utf-8")


def extrair_bloco_objecoes(texto: str) -> str:
    """Isola o texto entre '## Objeções de Compra' e o próximo '## '."""
    padrao = re.compile(
        r"^##\s+Objeções de Compra.*?$(.*?)(?=^##\s+|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    m = padrao.search(texto)
    if not m:
        return ""
    return m.group(1).strip()


def dividir_objecoes(bloco: str) -> list[tuple[str, str]]:
    """Divide o bloco em [(titulo_objecao, corpo)]."""
    partes = re.split(r"^###\s+Objeção\s+\d+:\s*", bloco, flags=re.MULTILINE)
    resultado: list[tuple[str, str]] = []
    for trecho in partes[1:]:
        linhas = trecho.splitlines()
        titulo = linhas[0].strip().strip('"').strip("'")
        corpo = "\n".join(linhas[1:]).strip()
        corpo = re.sub(r"\n-{3,}\s*$", "", corpo).strip()
        if titulo and corpo:
            resultado.append((titulo, corpo))
    return resultado


def dividir_argumentos(corpo: str) -> list[tuple[str, list[str]]]:
    """Retorna [(titulo_argumento, [paragrafos])]."""
    padrao_titulo = re.compile(r"^\*\*\d+\.\s+(.+?)\*\*\s*$", re.MULTILINE)
    matches = list(padrao_titulo.finditer(corpo))
    argumentos: list[tuple[str, list[str]]] = []
    for i, m in enumerate(matches):
        titulo = m.group(1).strip()
        inicio = m.end()
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(corpo)
        trecho = corpo[inicio:fim].strip()
        paragrafos = [p.strip() for p in re.split(r"\n\s*\n", trecho) if p.strip()]
        argumentos.append((titulo, paragrafos))
    return argumentos


def argumento_principal(argumentos: list[tuple[str, list[str]]]) -> str:
    if not argumentos:
        return ""
    return argumentos[0][0]


def render_html(objecoes: list[tuple[str, str]]) -> str:
    linhas_tabela = []
    accordions = []

    for idx, (titulo, corpo) in enumerate(objecoes, start=1):
        argumentos = dividir_argumentos(corpo)
        principal = argumento_principal(argumentos)

        titulo_esc = html.escape(titulo)
        principal_esc = html.escape(principal)

        linhas_tabela.append(
            f'<tr><td class="num">{idx}</td>'
            f'<td>"{titulo_esc}"</td>'
            f'<td>{principal_esc}</td></tr>'
        )

        argumentos_html = []
        for i_arg, (arg_titulo, paragrafos) in enumerate(argumentos):
            arg_titulo_esc = html.escape(arg_titulo)
            paragrafos_html = "\n".join(
                f"<p>{html.escape(p)}</p>" for p in paragrafos
            )
            # Primeiro argumento (principal) abre por padrao; demais ficam colapsados
            open_attr = " open" if i_arg == 0 else ""
            argumentos_html.append(
                f'<details class="arg-card"{open_attr}>\n'
                f'  <summary>{arg_titulo_esc}</summary>\n'
                f'  <div class="arg-corpo">\n{paragrafos_html}\n  </div>\n'
                f'</details>'
            )

        accordions.append(
            f'<details class="objecao">\n'
            f'  <summary><span class="obj-num">{idx}</span>'
            f' <span class="obj-titulo">"{titulo_esc}"</span></summary>\n'
            f'  <div class="obj-corpo">\n'
            + "\n".join(argumentos_html)
            + "\n  </div>\n"
            + "</details>"
        )

    tabela = (
        '<table class="tabela-objecoes">\n'
        "  <thead><tr><th>#</th><th>Objeção</th>"
        "<th>Argumento principal</th></tr></thead>\n"
        "  <tbody>\n    "
        + "\n    ".join(linhas_tabela)
        + "\n  </tbody>\n</table>"
    )

    return (
        '<section class="secao-objecoes">\n'
        "  <h2>9. Quebra de objeções pelo Framework dos 7 Argumentos</h2>\n"
        '  <p class="ajuda">Tabela-resumo para leitura rápida no celular. '
        "Abra o accordion da objeção para ver os 7 argumentos completos.</p>\n"
        f"  {tabela}\n"
        '  <div class="objecoes-lista">\n    '
        + "\n    ".join(accordions)
        + "\n  </div>\n"
        "</section>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", help="Slug do produto (default: .ativo)")
    args = parser.parse_args()

    slug = args.slug or descobrir_slug_ativo()
    texto = ler_idconsumidor(slug)
    bloco = extrair_bloco_objecoes(texto)

    if not bloco:
        sys.stderr.write(
            "Não achei a seção '## Objeções de Compra (Framework dos 7 Argumentos)' "
            f"no idconsumidor.md de {slug}. Rode /produto-concepcao para gerar.\n"
        )
        return 2

    objecoes = dividir_objecoes(bloco)
    if len(objecoes) < 1:
        sys.stderr.write(
            "Seção de objeções existe mas não consegui dividir em objeções "
            "no formato '### Objeção N: ...'. Verifique o idconsumidor.md.\n"
        )
        return 2

    print(render_html(objecoes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
