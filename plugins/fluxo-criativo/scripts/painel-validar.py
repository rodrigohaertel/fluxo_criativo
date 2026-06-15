#!/usr/bin/env python3
"""
Valida os JSONs da pasta `meus-produtos/{slug}/dados/` do painel de entregas.

Foco principal: `pesquisa.json`. Campos obrigatórios:
  1. KPI com rótulo contendo "Tamanho" e "Mercado" com valor real.
  2. KPI com rótulo contendo "Crescimento" com valor real.
  3. Pelo menos 5 concorrentes mapeados.

"Valor real" significa: string não vazia, não igual a "a mapear" e diferente
do texto-modelo presente em `assets/templates/painel-entregas/schemas/`.

Uso:
  py -3 scripts/painel-validar.py --arquivo meus-produtos/curso-x/dados/pesquisa.json
  py -3 scripts/painel-validar.py --slug curso-x
  py -3 scripts/painel-validar.py                  # usa o produto ativo

Saída:
  exit 0  => JSON válido (ou arquivo ignorado)
  exit 1  => JSON inválido, mensagens no stderr

Este script é chamado:
  a) Diretamente pelo aluno/Claude para validar manualmente.
  b) Pelo hook `.claude/hooks/painel-validar.js` (via Node) ao salvar o JSON.
  c) Por `scripts/painel-entregas-montar.py` antes de montar o HTML.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMAS_DIR_REL = Path("assets") / "templates" / "painel-entregas" / "schemas"

MIN_CONCORRENTES = 5

PLACEHOLDERS_PROIBIDOS = {
    "",
    "a mapear",
    "preencher",
    "tbd",
    "-",
}


def projeto_root() -> Path:
    return Path(__file__).resolve().parent.parent


def carregar_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Arquivo não encontrado: {p}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON inválido em {p}: {e}")


def valor_real(valor: object, valor_modelo: str | None) -> bool:
    if not isinstance(valor, (str, int, float)):
        return False
    s = str(valor).strip().lower()
    if s in PLACEHOLDERS_PROIBIDOS:
        return False
    if valor_modelo and s == str(valor_modelo).strip().lower():
        return False
    return True


def achar_kpi(kpis: list, termos: list[str]) -> dict | None:
    if not isinstance(kpis, list):
        return None
    termos_low = [t.lower() for t in termos]
    for item in kpis:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).lower()
        if all(t in label for t in termos_low):
            return item
    return None


def validar_pesquisa(dados: dict, schema: dict | None) -> list[str]:
    erros: list[str] = []

    kpis = dados.get("kpis")
    kpis_modelo = (schema or {}).get("kpis") or []

    def kpi_modelo_valor(termos: list[str]) -> str | None:
        item = achar_kpi(kpis_modelo, termos)
        if item:
            v = item.get("valor")
            if isinstance(v, (str, int, float)):
                return str(v)
        return None

    # 1. Tamanho do Mercado
    tm = achar_kpi(kpis or [], ["tamanho", "mercado"])
    modelo_tm = kpi_modelo_valor(["tamanho", "mercado"])
    if not tm:
        erros.append('KPI obrigatório ausente: "Tamanho do Mercado".')
    elif not valor_real(tm.get("valor"), modelo_tm):
        erros.append(
            f'KPI "Tamanho do Mercado" sem valor real '
            f'(recebido: {tm.get("valor")!r}). '
            f"Preencha com o dado concreto da pesquisa."
        )

    # 2. Crescimento Anual
    ca = achar_kpi(kpis or [], ["crescimento"])
    modelo_ca = kpi_modelo_valor(["crescimento"])
    if not ca:
        erros.append('KPI obrigatório ausente: "Crescimento Anual".')
    elif not valor_real(ca.get("valor"), modelo_ca):
        erros.append(
            f'KPI "Crescimento Anual" sem valor real '
            f'(recebido: {ca.get("valor")!r}). '
            f"Preencha com o dado concreto da pesquisa."
        )

    # 3. Top 5 concorrentes
    concorrentes = dados.get("concorrentes")
    if not isinstance(concorrentes, list) or len(concorrentes) < MIN_CONCORRENTES:
        qtd = len(concorrentes) if isinstance(concorrentes, list) else 0
        erros.append(
            f"Lista de concorrentes incompleta: {qtd} encontrados, "
            f"mínimo {MIN_CONCORRENTES}."
        )
    else:
        # cada concorrente precisa de nome + promessa
        modelo_concorrente = ((schema or {}).get("concorrentes") or [{}])[0]
        for i, c in enumerate(concorrentes, start=1):
            if not isinstance(c, dict):
                erros.append(f"Concorrente {i}: formato inválido (esperado objeto).")
                continue
            if not valor_real(c.get("nome"), modelo_concorrente.get("nome")):
                erros.append(f'Concorrente {i}: campo "nome" vazio ou modelo.')
            if not valor_real(c.get("promessa"), modelo_concorrente.get("promessa")):
                erros.append(
                    f'Concorrente {i}: campo "promessa" vazio ou modelo.'
                )

    return erros


def carregar_schema(root: Path, nome_arquivo: str) -> dict | None:
    p = root / SCHEMAS_DIR_REL / nome_arquivo
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def validar_arquivo(path: Path, root: Path) -> list[str]:
    nome = path.name.lower()
    if not nome.endswith(".json"):
        return []
    # Só valida pesquisa.json por enquanto. Outros arquivos passam direto.
    if nome != "pesquisa.json":
        return []
    dados = carregar_json(path)
    schema = carregar_schema(root, "pesquisa.json")
    return validar_pesquisa(dados, schema)


def resolver_caminho(args: argparse.Namespace, root: Path) -> Path:
    if args.arquivo:
        p = Path(args.arquivo)
        if not p.is_absolute():
            p = root / p
        return p
    slug = args.slug
    if not slug:
        ativo = root / "meus-produtos" / ".ativo"
        if not ativo.exists():
            raise SystemExit(
                "Passe --arquivo ou --slug, ou crie meus-produtos/.ativo."
            )
        slug = ativo.read_text(encoding="utf-8").strip()
        if not slug:
            raise SystemExit("meus-produtos/.ativo está vazio.")
    return root / "meus-produtos" / slug / "dados" / "pesquisa.json"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Valida campos obrigatórios dos JSONs do painel de entregas."
    )
    ap.add_argument(
        "--arquivo",
        help="Caminho do JSON a validar. Se omitido, usa pesquisa.json do produto.",
    )
    ap.add_argument(
        "--slug",
        help="Slug do produto. Se omitido, usa meus-produtos/.ativo.",
    )
    args = ap.parse_args()

    root = projeto_root()
    caminho = resolver_caminho(args, root)

    if not caminho.exists():
        print(
            f"[painel-validar] Arquivo não existe, nada a validar: {caminho}",
            file=sys.stderr,
        )
        return 0

    erros = validar_arquivo(caminho, root)
    if not erros:
        print(f"[painel-validar] OK: {caminho}")
        return 0

    print(
        f"[painel-validar] Reprovado: {caminho}\n"
        f"Corrija os itens abaixo antes de seguir:",
        file=sys.stderr,
    )
    for e in erros:
        print(f"  . {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
