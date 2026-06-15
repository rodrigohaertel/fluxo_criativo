"""
painel-atualizar.py

Varre a pasta meus-produtos/ e gera o manifest meus-produtos/index.js usado
pelo painel global (painel/index.html) para listar produtos e seus paineis
de entregas.

Formato do arquivo gerado (carregado via <script src> para funcionar offline
direto via file://, sem servidor local):

    window.MEUS_PRODUTOS = {
        "schema_version": 1,
        "ativo": "guia-produtividade-real",
        "atualizado_em": "2026-04-17T13:00:00Z",
        "produtos": [
            {
                "slug": "guia-produtividade-real",
                "nome": "Guia Produtividade Real",
                "url": "guia-produtividade-real/painel-entregas.html"
            }
        ]
    };

As URLs sao relativas a pasta meus-produtos/ (onde o manifest vive). Quem
consome (hoje painel/index.html) resolve prefixando com "../meus-produtos/".

Regras:
- Ignora pastas que comecam com "_" (ex: _legado) e arquivos ocultos.
- Para cada produto, procura o painel na seguinte ordem:
    1. painel-entregas.html (padrao)
    2. painel-*.html (qualquer outro, primeiro em ordem alfabetica)
- Se o produto nao tem nenhum painel, entra no manifest com url=null
  (o painel exibe uma mensagem amigavel).
- O nome do produto vem do primeiro titulo H1 do perfil.md; se nao existir,
  cai numa versao "Title Case" do slug.
- O produto ativo e lido de meus-produtos/.ativo.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PRODUTOS_DIR = REPO_ROOT / "meus-produtos"
MANIFEST_OUT = PRODUTOS_DIR / "index.js"
ATIVO_FILE = PRODUTOS_DIR / ".ativo"
SCHEMA_VERSION = 1


def ler_ativo() -> str | None:
    if not ATIVO_FILE.exists():
        return None
    txt = ATIVO_FILE.read_text(encoding="utf-8").strip()
    return txt or None


def descobrir_painel(produto_dir: Path) -> str | None:
    """Retorna o nome do arquivo de painel, ou None se nao encontrar."""
    padrao = produto_dir / "painel-entregas.html"
    if padrao.exists():
        return padrao.name
    paineis = sorted(produto_dir.glob("painel-*.html"))
    if paineis:
        return paineis[0].name
    return None


def extrair_nome(produto_dir: Path, slug: str) -> str:
    """Descobre o nome amigavel do produto, nessa ordem de prioridade:

    1. Arquivo nome.txt no produto (uma linha com o nome).
    2. H1 do perfil.md apos um separador (ex: "# Perfil do Negocio: Planilhas Pro").
    3. Campo **Produto ativo:** / **Produto:** / **Nome:** no perfil.md.
    4. Fallback: slug em Title Case (sem acentos).
    """
    nome_file = produto_dir / "nome.txt"
    if nome_file.exists():
        nome = nome_file.read_text(encoding="utf-8").strip()
        if nome:
            return nome

    perfil = produto_dir / "perfil.md"
    if perfil.exists():
        texto = perfil.read_text(encoding="utf-8")
        for linha in texto.splitlines():
            m = re.match(r"^#\s+(.+?)\s*$", linha)
            if not m:
                continue
            titulo = m.group(1).strip()
            for sep in (" — ", " – ", " - ", ": "):
                if sep in titulo:
                    candidato = titulo.split(sep, 1)[1].strip()
                    if candidato:
                        return candidato
            if titulo and not titulo.lower().startswith(("perfil", "# perfil")):
                return titulo
            break

        for linha in texto.splitlines():
            m = re.match(r"^\*\*(?:Produto ativo|Produto|Nome)\s*:\*\*\s*(.+?)\s*$", linha, re.IGNORECASE)
            if m:
                candidato = m.group(1).strip().rstrip(".")
                candidato = re.sub(r"\s*\(.*?\)\s*$", "", candidato).strip()
                if candidato:
                    return candidato

    return slug.replace("-", " ").title()


def listar_produtos() -> list[dict]:
    produtos: list[dict] = []
    if not PRODUTOS_DIR.exists():
        return produtos
    for p in sorted(PRODUTOS_DIR.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("_") or p.name.startswith("."):
            continue
        slug = p.name
        painel = descobrir_painel(p)
        url = f"{slug}/{painel}" if painel else None
        produtos.append({
            "slug": slug,
            "nome": extrair_nome(p, slug),
            "url": url,
        })
    return produtos


def gerar_manifest() -> dict:
    produtos = listar_produtos()
    ativo = ler_ativo()
    if ativo and not any(prod["slug"] == ativo for prod in produtos):
        ativo = produtos[0]["slug"] if produtos else None
    if not ativo and produtos:
        ativo = produtos[0]["slug"]
    return {
        "schema_version": SCHEMA_VERSION,
        "ativo": ativo,
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "produtos": produtos,
    }


def escrever_manifest(dados: dict) -> None:
    PRODUTOS_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dados, ensure_ascii=False, indent=2)
    conteudo = (
        "// Gerado automaticamente por scripts/painel-atualizar.py.\n"
        "// Nao edite a mao. Rode /painel-atualizar ou os commands de produto\n"
        "// (/produto-novo, /produto-excluir, /produto-trocar) para regenerar.\n"
        f"window.MEUS_PRODUTOS = {payload};\n"
    )
    MANIFEST_OUT.write_text(conteudo, encoding="utf-8")


def main() -> int:
    dados = gerar_manifest()
    escrever_manifest(dados)
    total = len(dados["produtos"])
    com_painel = sum(1 for p in dados["produtos"] if p["url"])
    ativo = dados["ativo"] or "(nenhum)"
    print(f"Manifest gerado: {MANIFEST_OUT.relative_to(REPO_ROOT)}")
    print(f"Produtos: {total} (com painel: {com_painel}, sem painel: {total - com_painel})")
    print(f"Ativo: {ativo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
