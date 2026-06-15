#!/usr/bin/env python3
"""
abrir-html.py — abre um arquivo HTML local no navegador padrão do sistema.

Cross-platform: Windows, macOS, Linux. Usa stdlib `webbrowser` como primeira
tentativa (mais confiável) e cai pra comandos nativos como fallback.

Uso:
    python3 scripts/abrir-html.py "caminho/para/arquivo.html"

Exit codes:
    0 = abriu com sucesso
    1 = arquivo não encontrado ou não conseguiu abrir
    2 = uso incorreto (argumentos faltando)

Falha silenciosa amigável: se não conseguir abrir, imprime instrução pra
abertura manual em vez de quebrar o fluxo da skill que chamou.
"""
import os
import platform
import subprocess
import sys
from pathlib import Path

# Forçar UTF-8 no stdout/stderr pra evitar UnicodeEncodeError com emojis no Windows
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def abrir(path_str: str) -> int:
    path = Path(path_str).expanduser().resolve()

    if not path.exists():
        print(f"[ERRO] Arquivo nao encontrado: {path}", file=sys.stderr)
        return 1

    if path.suffix.lower() != ".html":
        print(f"[AVISO] Extensao nao e .html ({path.suffix})", file=sys.stderr)

    so = platform.system()

    # Estratégia por SO — comandos nativos primeiro (mais robustos que webbrowser stdlib)
    try:
        if so == "Windows":
            # os.startfile abre com o app padrão do .html (browser default)
            os.startfile(str(path))
        elif so == "Darwin":
            subprocess.run(["open", str(path)], check=True)
        else:  # Linux e outros
            subprocess.run(["xdg-open", str(path)], check=True)
        print(f"Abrindo no navegador: {path}")
        return 0
    except Exception as nativo_err:
        # Fallback: tenta webbrowser stdlib
        try:
            import webbrowser
            url = path.as_uri()
            if webbrowser.open(url, new=2):
                print(f"Abrindo no navegador: {path}")
                return 0
            raise RuntimeError("webbrowser.open() retornou False")
        except Exception as wb_err:
            print(f"[ERRO] Nao consegui abrir o navegador automaticamente.", file=sys.stderr)
            print(f"  Tentativa nativa: {nativo_err}", file=sys.stderr)
            print(f"  Tentativa webbrowser: {wb_err}", file=sys.stderr)
            print(f"  Abra manualmente este arquivo:", file=sys.stderr)
            print(f"  {path}", file=sys.stderr)
            return 1


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 abrir-html.py <caminho-do-arquivo.html>", file=sys.stderr)
        return 2
    return abrir(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
