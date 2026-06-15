"""Aplica os textos criativos (gerados em paralelo pelos subagentes) no HTML
do playbook comercial, substituindo os marcadores {{N.chave}} pelo texto
com escape HTML.

Formato do JSON (novo protocolo, texto puro, não HTML):
    {
      "7.b1.a": "Oi, [NOME], tudo bem?...",
      "7.b1.b": "...",
      "7.b1.nota": "Se responder com emoji, ...",
      "9.S.q1": "Me conta: como está sua rotina hoje...",
      ...
    }

Uso (Windows):
    py -3 scripts/playbook-aplicar-criativas.py --slug taro-para-iniciantes \\
        --json scripts/.tmp-criativas-7-8.json \\
        --json scripts/.tmp-criativas-9-10.json \\
        --json scripts/.tmp-criativas-13-14.json --cleanup

Uso (Mac/Linux):
    python3 scripts/playbook-aplicar-criativas.py --slug taro-para-iniciantes \\
        --json scripts/.tmp-criativas-7-8.json \\
        --json scripts/.tmp-criativas-9-10.json \\
        --json scripts/.tmp-criativas-13-14.json --cleanup

A flag --cleanup apaga os arquivos JSON após aplicar (evita depender de
rm/Remove-Item no shell).

Compatibilidade: se o JSON tiver chaves no formato antigo "secao_N": "<html>",
o script faz o fallback e substitui entre os marcadores
<!-- CREATIVE_N_START --> e <!-- CREATIVE_N_END --> (formato legado).
"""
from __future__ import annotations

import argparse
import html
import io
import json
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


def descobrir_slug_ativo() -> str:
    ativo = (PASTA_PRODUTOS / ".ativo").read_text(encoding="utf-8").strip()
    if not ativo:
        raise SystemExit("meus-produtos/.ativo está vazio.")
    return ativo


def carregar_json(caminhos: list[Path]) -> dict[str, str]:
    dados: dict[str, str] = {}
    for caminho in caminhos:
        if not caminho.exists():
            raise SystemExit(f"JSON não encontrado: {caminho}")
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
        if not isinstance(conteudo, dict):
            raise SystemExit(f"JSON inválido em {caminho}: esperado objeto.")
        for chave, valor in conteudo.items():
            if not isinstance(valor, str):
                raise SystemExit(
                    f"Valor não-string em {caminho} na chave '{chave}'."
                )
            if chave in dados:
                sys.stderr.write(
                    f"Aviso: chave '{chave}' duplicada, segundo valor vence.\n"
                )
            dados[chave] = valor
    return dados


# ============================================================================
# Limpeza determinística (substitui parte do trabalho da revisora)
# ============================================================================
# A regra "AUTO-REVISÃO OBRIGATÓRIA DE COPY" do CLAUDE.md exige que toda copy
# passe pelo Manual antes da entrega. Para o playbook comercial, em vez de
# rodar a revisora 6 vezes (uma vez dentro de cada sub-agente), aplicamos
# aqui as regras MECANIZÁVEIS do Manual (vícios óbvios) em uma única passada.
#
# Os 6 agentes recebem essas mesmas regras no prompt, então a maioria dos
# textos já chega limpa. Esta camada é o último filtro de segurança.

_PADROES_PROIBIDOS = [
    # (regex, pattern_descritivo). Apenas detecção, vira warning.
    (re.compile(r"\bn[aã]o\s+[eé]\s+\w[\w\s,]*?[.!?]\s*[ÉéEe]\s+\w", re.IGNORECASE), "estrutura 'não é X. é Y'"),
    (re.compile(r"\bmesmo\s+que\b", re.IGNORECASE), "muleta 'mesmo que'"),
    (re.compile(r"\bsem\s+precisar\b", re.IGNORECASE), "muleta 'sem precisar'"),
    (re.compile(r"\bquer\s+comprar\??", re.IGNORECASE), "frase proibida 'quer comprar?'"),
]


def _limpar_vicios(texto: str) -> tuple[str, list[str]]:
    """Aplica correções mecanizáveis e devolve avisos para o que não é seguro corrigir.

    Correções automáticas:
      - travessão (—) e en-dash (–) viram vírgula
      - "!" no fim de frase ou no meio vira "."

    Detecções (apenas avisos, sem reescrever):
      - "não é X. é Y."
      - "mesmo que" / "sem precisar"
      - "quer comprar?"
    """
    avisos: list[str] = []

    # Correção 1: travessões
    if "—" in texto or "–" in texto:
        texto = texto.replace(" — ", ", ").replace("—", ", ")
        texto = texto.replace(" – ", ", ").replace("–", ", ")
        # Limpa duplicatas "  " e " ," que possam ter sobrado
        texto = re.sub(r"\s{2,}", " ", texto)
        texto = re.sub(r"\s+,", ",", texto)

    # Correção 2: ponto de exclamação vira ponto final
    if "!" in texto:
        texto = texto.replace("!", ".")
        # Evita ".." caso já tivesse ponto antes
        texto = re.sub(r"\.{2,}", ".", texto)

    # Detecções (avisos)
    for padrao, descricao in _PADROES_PROIBIDOS:
        if padrao.search(texto):
            avisos.append(descricao)

    return texto, avisos


def _aplicar_placeholders(html_str: str, textos: dict[str, str]) -> tuple[str, int, list[str], dict[str, list[str]]]:
    """Substitui {{chave}} pelo texto LIMPO e escapado.

    Retorna (html, substituídas, faltantes, avisos_por_chave).
    avisos_por_chave: {chave: [vícios detectados]} — útil pro usuário revisar.
    """
    substituidas = 0
    faltantes: list[str] = []
    avisos_por_chave: dict[str, list[str]] = {}
    for chave, texto in textos.items():
        marcador = "{{" + chave + "}}"
        if marcador not in html_str:
            faltantes.append(chave)
            continue
        texto_limpo, avisos = _limpar_vicios(texto)
        if avisos:
            avisos_por_chave[chave] = avisos
        substituto = html.escape(texto_limpo)
        ocorrencias = html_str.count(marcador)
        html_str = html_str.replace(marcador, substituto)
        substituidas += ocorrencias
    return html_str, substituidas, faltantes, avisos_por_chave


def _aplicar_legado(html_str: str, secoes: dict[str, str]) -> tuple[str, int]:
    """Formato antigo: {"secao_N": "<html completo do bloco>"}. Substitui
    entre <!-- CREATIVE_N_START --> e <!-- CREATIVE_N_END -->."""
    substituidas = 0
    for chave, conteudo in secoes.items():
        if not chave.startswith("secao_"):
            continue
        n = chave.split("_", 1)[1]
        padrao = re.compile(
            rf"<!-- CREATIVE_{n}_START -->.*?<!-- CREATIVE_{n}_END -->",
            re.DOTALL,
        )
        if not padrao.search(html_str):
            raise SystemExit(
                f"Marcador CREATIVE_{n}_START/END não encontrado no HTML."
            )
        substituto = (
            f"<!-- CREATIVE_{n}_START -->\n  {conteudo}\n  "
            f"<!-- CREATIVE_{n}_END -->"
        )
        html_str = padrao.sub(lambda _m, s=substituto: s, html_str, count=1)
        substituidas += 1
    return html_str, substituidas


def aplicar(html_str: str, dados: dict[str, str]) -> tuple[str, int, list[str], dict[str, list[str]]]:
    # Separa chaves no formato novo (contém ponto, ex: "7.b1.a") das legadas
    textos = {k: v for k, v in dados.items() if not k.startswith("secao_")}
    legado = {k: v for k, v in dados.items() if k.startswith("secao_")}

    total = 0
    faltantes: list[str] = []
    avisos_por_chave: dict[str, list[str]] = {}

    if textos:
        html_str, sub_novo, faltantes, avisos_por_chave = _aplicar_placeholders(html_str, textos)
        total += sub_novo

    if legado:
        html_str, sub_legado = _aplicar_legado(html_str, legado)
        total += sub_legado

    return html_str, total, faltantes, avisos_por_chave


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", help="Slug do produto (default: .ativo)")
    parser.add_argument(
        "--json",
        action="append",
        dest="jsons",
        required=True,
        help="Caminho de um JSON de criativas. Pode repetir.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Apaga os arquivos JSON de entrada após aplicar com sucesso.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falha se algum marcador {{chave}} do JSON não existir no HTML.",
    )
    args = parser.parse_args()

    slug = args.slug or descobrir_slug_ativo()
    html_path = (
        PASTA_PRODUTOS / slug / "entregas" / "comercial"
        / f"playbook-{slug}.html"
    )
    if not html_path.exists():
        raise SystemExit(
            f"HTML não encontrado: {html_path}. Rode playbook-montar.py antes."
        )

    caminhos = [Path(p) for p in args.jsons]
    dados = carregar_json(caminhos)
    html_str = html_path.read_text(encoding="utf-8")
    novo_html, n, faltantes, avisos_por_chave = aplicar(html_str, dados)
    html_path.write_text(novo_html, encoding="utf-8")

    print(f"{n} textos aplicados em {html_path}")
    if faltantes:
        sys.stderr.write(
            f"Aviso: {len(faltantes)} chaves do JSON não acharam marcador no HTML: "
            f"{', '.join(faltantes[:10])}{'...' if len(faltantes) > 10 else ''}\n"
        )
        if args.strict:
            return 1

    # Avisos de vícios de Light Copy detectados nos textos (já corrigidos os
    # mecanizáveis, esses são os que precisam de revisão humana)
    if avisos_por_chave:
        sys.stderr.write(
            f"\nAviso: {len(avisos_por_chave)} textos ainda têm vícios que dependem "
            "de reescrita (não foi seguro corrigir automaticamente):\n"
        )
        for chave, vicios in list(avisos_por_chave.items())[:8]:
            sys.stderr.write(f"  - {chave}: {', '.join(vicios)}\n")
        if len(avisos_por_chave) > 8:
            sys.stderr.write(f"  ... e mais {len(avisos_por_chave) - 8} chaves.\n")

    # Detecta marcadores {{...}} que sobraram no HTML (não preenchidos)
    restantes = re.findall(r"\{\{([0-9]+\.[^}\s]+)\}\}", novo_html)
    if restantes:
        unicos = sorted(set(restantes))
        sys.stderr.write(
            f"Aviso: {len(unicos)} marcadores ainda não preenchidos no HTML: "
            f"{', '.join(unicos[:10])}{'...' if len(unicos) > 10 else ''}\n"
        )

    if args.cleanup:
        for caminho in caminhos:
            try:
                caminho.unlink()
            except OSError as exc:
                sys.stderr.write(f"Falhou ao apagar {caminho}: {exc}\n")
        print(f"{len(caminhos)} arquivos JSON temporários removidos.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
