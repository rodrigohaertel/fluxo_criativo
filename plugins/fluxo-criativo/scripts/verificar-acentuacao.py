#!/usr/bin/env python3
"""
Verificador de acentuação pt_BR.

Escaneia arquivos textuais (.md, .html, .json, .txt) em busca de palavras
que, em português brasileiro, DEVEM aparecer acentuadas em texto corrido,
mas que foram encontradas sem acento.

Ignora blocos de código, URLs, inline code, valores de atributo HTML
com classes/IDs/src/href e trechos explicitamente marcados como slug ou
nome de arquivo, que podem legitimamente aparecer em ASCII.

Uso:
    py -3 scripts/verificar-acentuacao.py                 # escaneia o projeto
    py -3 scripts/verificar-acentuacao.py caminho/arq.md  # escaneia um arquivo
    py -3 scripts/verificar-acentuacao.py --corrigir      # aplica correções automáticas

Saída: lista de arquivos com as linhas suspeitas e palavras encontradas.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Pares (palavra sem acento → palavra com acento correta em contexto padrão).
# Quando a palavra sem acento também é válida em outro contexto (ex: "publica" verbo
# vs "pública" adjetivo), incluímos no MAPA_AMBIGUO para apenas sinalizar, não corrigir.
MAPA_DIRETO = {
    "nao": "não",
    "sao": "são",
    "voce": "você",
    "voces": "vocês",
    "esta": "está",
    "estao": "estão",
    "tambem": "também",
    "tres": "três",
    "estrategia": "estratégia",
    "estrategias": "estratégias",
    "duvida": "dúvida",
    "duvidas": "dúvidas",
    "introducao": "introdução",
    "conclusao": "conclusão",
    "metodo": "método",
    "metodos": "métodos",
    "pratica": "prática",
    "praticas": "práticas",
    "analise": "análise",
    "analises": "análises",
    "especifico": "específico",
    "especifica": "específica",
    "basico": "básico",
    "basica": "básica",
    "unico": "único",
    "unica": "única",
    "numero": "número",
    "numeros": "números",
    "codigo": "código",
    "codigos": "códigos",
    "pagina": "página",
    "paginas": "páginas",
    "video": "vídeo",
    "videos": "vídeos",
    "area": "área",
    "areas": "áreas",
    "historia": "história",
    "historias": "histórias",
    "memoria": "memória",
    "memorias": "memórias",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "proximo": "próximo",
    "proxima": "próxima",
    "ultimo": "último",
    "ultima": "última",
    "critico": "crítico",
    "critica": "crítica",
    "facil": "fácil",
    "dificil": "difícil",
    "possivel": "possível",
    "impossivel": "impossível",
    "automatico": "automático",
    "automatica": "automática",
    "sabado": "sábado",
    "indice": "índice",
    "inicio": "início",
    "sessao": "sessão",
    "decisao": "decisão",
    "opcao": "opção",
    "opcoes": "opções",
    "funcao": "função",
    "funcoes": "funções",
    "acao": "ação",
    "acoes": "ações",
    "reacao": "reação",
    "situacao": "situação",
    "situacoes": "situações",
    "solucao": "solução",
    "solucoes": "soluções",
}

# Palavras sinalizadas (sem correção automática porque a forma sem acento
# também pode ser válida em outro contexto gramatical).
MAPA_AMBIGUO = {
    "ja": "já (advérbio) ou forma rara",
    "publico": "público (adjetivo/substantivo) ou publico (verbo publicar)",
    "logico": "lógico (adjetivo) ou logico (raro)",
    "pratico": "prático (adjetivo) ou pratico (verbo praticar)",
}

EXTENSOES_ALVO = {".md", ".html", ".json", ".txt"}

PASTAS_IGNORAR = {
    ".git",
    "node_modules",
    ".vercel",
    "_prompts-gpt",
    "meus-produtos",
    "meus-produtos copy",
    "deploy-painel-workshop",
    "deploy-playbook-eff",
    "galeria-furadeira",
    "produtos",
    "assets",
    "tutoriais",
}

# Regex de contextos a ignorar (blocos de código, inline code, URLs, atributos HTML).
BLOCO_CODIGO = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODIGO = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://\S+")
ATRIBUTO_HTML = re.compile(r'\b(class|id|src|href|name|data-[\w-]+)="[^"]*"')
CAMINHO_ARQUIVO = re.compile(r"[\w./\\-]+\.(md|html|json|txt|py|js|css|ps1|pdf|jpg|png|mp4)")


def remover_ignorados(texto: str) -> str:
    """Substitui blocos de código, URLs e atributos HTML por espaços em branco."""
    texto = BLOCO_CODIGO.sub(lambda m: " " * len(m.group()), texto)
    texto = INLINE_CODIGO.sub(lambda m: " " * len(m.group()), texto)
    texto = URL.sub(lambda m: " " * len(m.group()), texto)
    texto = ATRIBUTO_HTML.sub(lambda m: " " * len(m.group()), texto)
    texto = CAMINHO_ARQUIVO.sub(lambda m: " " * len(m.group()), texto)
    return texto


def construir_regex() -> re.Pattern:
    palavras = list(MAPA_DIRETO.keys()) + list(MAPA_AMBIGUO.keys())
    padrao = r"(?<![\w-])(" + "|".join(palavras) + r")(?![\w-])"
    return re.compile(padrao, flags=re.IGNORECASE)


def listar_arquivos(base: Path) -> list[Path]:
    arquivos: list[Path] = []
    for caminho in base.rglob("*"):
        if not caminho.is_file():
            continue
        if caminho.suffix.lower() not in EXTENSOES_ALVO:
            continue
        if any(parte in PASTAS_IGNORAR for parte in caminho.parts):
            continue
        arquivos.append(caminho)
    return arquivos


def analisar_arquivo(caminho: Path, regex: re.Pattern) -> list[tuple[int, str, list[str]]]:
    """Retorna lista de (numero_linha, texto_linha, palavras_suspeitas)."""
    try:
        conteudo = caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    linhas_originais = conteudo.splitlines()
    conteudo_filtrado = remover_ignorados(conteudo)
    linhas_filtradas = conteudo_filtrado.splitlines()

    resultados: list[tuple[int, str, list[str]]] = []
    for idx, (original, filtrada) in enumerate(zip(linhas_originais, linhas_filtradas), start=1):
        achados = regex.findall(filtrada)
        if achados:
            # Preserva caixa original somente se palavra aparece em letras minúsculas
            palavras_minusculas = [p.lower() for p in achados]
            resultados.append((idx, original, palavras_minusculas))
    return resultados


def corrigir_arquivo(caminho: Path) -> int:
    """Aplica correções automáticas apenas para palavras de MAPA_DIRETO.
    Retorna quantidade de substituições feitas."""
    try:
        conteudo_original = caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0

    # Isola trechos ignoráveis substituindo por placeholders únicos.
    placeholders: dict[str, str] = {}

    def proteger(match: re.Match) -> str:
        chave = f"\x00PROT{len(placeholders)}\x00"
        placeholders[chave] = match.group()
        return chave

    texto = BLOCO_CODIGO.sub(proteger, conteudo_original)
    texto = INLINE_CODIGO.sub(proteger, texto)
    texto = URL.sub(proteger, texto)
    texto = ATRIBUTO_HTML.sub(proteger, texto)
    texto = CAMINHO_ARQUIVO.sub(proteger, texto)

    total = 0
    for palavra_sem, palavra_com in MAPA_DIRETO.items():
        padrao = re.compile(r"(?<![\w-])" + palavra_sem + r"(?![\w-])", flags=re.IGNORECASE)

        def substituir(match: re.Match, destino: str = palavra_com) -> str:
            original = match.group()
            if original.isupper():
                return destino.upper()
            if original[0].isupper():
                return destino.capitalize()
            return destino

        texto, n = padrao.subn(substituir, texto)
        total += n

    for chave, valor in placeholders.items():
        texto = texto.replace(chave, valor)

    if total > 0 and texto != conteudo_original:
        caminho.write_text(texto, encoding="utf-8")
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificador de acentuação pt_BR.")
    parser.add_argument(
        "caminhos",
        nargs="*",
        help="Arquivos ou pastas a verificar. Padrão: raiz do projeto.",
    )
    parser.add_argument(
        "--corrigir",
        action="store_true",
        help="Aplica correções automáticas no lugar de apenas sinalizar.",
    )
    parser.add_argument(
        "--silencioso",
        action="store_true",
        help="Só imprime saída se encontrar problemas (uso como hook).",
    )
    args = parser.parse_args()

    alvos: list[Path] = []
    if args.caminhos:
        for c in args.caminhos:
            p = Path(c)
            if p.is_dir():
                alvos.extend(listar_arquivos(p))
            elif p.is_file():
                alvos.append(p)
    else:
        alvos = listar_arquivos(RAIZ)

    regex = construir_regex()
    total_arquivos_com_problema = 0
    total_ocorrencias = 0
    arquivos_corrigidos = 0

    for arq in alvos:
        if args.corrigir:
            n = corrigir_arquivo(arq)
            if n > 0:
                arquivos_corrigidos += 1
                total_ocorrencias += n
                print(f"✏️  {arq.relative_to(RAIZ)}: {n} correção(ões)")
        else:
            resultados = analisar_arquivo(arq, regex)
            if resultados:
                total_arquivos_com_problema += 1
                print(f"\n⚠️  {arq.relative_to(RAIZ)}")
                for numero, linha, palavras in resultados:
                    palavras_unicas = sorted(set(palavras))
                    total_ocorrencias += len(palavras)
                    trecho = linha.strip()[:120]
                    print(f"   linha {numero}: {palavras_unicas} → {trecho}")

    if args.corrigir:
        if arquivos_corrigidos == 0:
            if not args.silencioso:
                print("✅ Nenhuma correção automática necessária.")
        else:
            print(
                f"\n✅ {arquivos_corrigidos} arquivo(s) corrigido(s), "
                f"{total_ocorrencias} substituição(ões) aplicada(s)."
            )
        return 0

    if total_arquivos_com_problema == 0:
        if not args.silencioso:
            print("✅ Nenhuma palavra suspeita encontrada. Acentuação em dia.")
        return 0

    print(
        f"\n⚠️  Possível erro de acentuação em {total_arquivos_com_problema} arquivo(s), "
        f"{total_ocorrencias} ocorrência(s). Rode `py -3 scripts/verificar-acentuacao.py --corrigir` "
        f"para aplicar correções automáticas."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
