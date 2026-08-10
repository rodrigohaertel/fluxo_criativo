#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincroniza o projeto com o repositorio do Workshop e espelha no fork pessoal.

CONTEXTO (esclarecido em 07/08/2026)
  origin = ReadyToGo-Education/fluxo_criativo  -> SOMENTE LEITURA para o Rodrigo.
  fork   = rodrigohaertel/fluxo_criativo       -> dele, recebe o espelho.
Os commits locais nunca vao para o origin por definicao. Entao "commits dos dois
lados" NAO e divergencia a resolver: e atualizacao nova a receber.

O QUE ESTE SCRIPT FAZ (nesta ordem)
  1. fetch
  2. se nao ha nada novo no origin, so espelha o fork (se preciso) e sai
  3. guarda o trabalho em aberto no stash
  4. merge do origin
  5. conflito: unica excecao automatica e o .gitignore (uniao dos dois blocos,
     politica aprovada pelo Rodrigo em 07/08). Qualquer outro conflito ABORTA
     o merge, devolve o stash e para, deixando a decisao para a sessao interativa.
  6. devolve o stash
  7. espelha no fork (desligue com --sem-push)

NUNCA usa reset, checkout --, clean, rebase nem push --force.

Uso:  py -3 scripts/sincronizar-repo.py [--sem-push]
Saida: 0 = tudo certo (com ou sem novidade) | 2 = precisa de decisao humana
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEM_PUSH = "--sem-push" in sys.argv


def git(*args, check=False):
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        print(f"[ERRO] git {' '.join(args)}: {(r.stderr or '').strip()[:300]}")
        sys.exit(2)
    return r


def contar(intervalo):
    r = git("rev-list", "--count", intervalo)
    try:
        return int((r.stdout or "0").strip())
    except ValueError:
        return 0


def tem_remote(nome):
    return nome in git("remote").stdout.split()


def unir_gitignore():
    """Resolve o conflito do .gitignore mantendo os DOIS blocos, na ordem
    local primeiro e origin depois. Retorna True se resolveu."""
    caminho = RAIZ / ".gitignore"
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    saida, nosso, deles, estado = [], [], [], "fora"
    for linha in linhas:
        if linha.startswith("<<<<<<<"):
            estado, nosso, deles = "nosso", [], []
        elif linha.startswith("=======") and estado == "nosso":
            estado = "deles"
        elif linha.startswith(">>>>>>>") and estado == "deles":
            saida.extend(nosso)
            if nosso and deles:
                saida.append("")
            saida.extend(deles)
            estado = "fora"
        elif estado == "nosso":
            nosso.append(linha)
        elif estado == "deles":
            deles.append(linha)
        else:
            saida.append(linha)
    if estado != "fora":
        return False  # marcador malformado: nao arrisca
    caminho.write_text("\n".join(saida) + "\n", encoding="utf-8")
    return True


def espelhar_fork():
    if SEM_PUSH or not tem_remote("fork"):
        return
    if contar("fork/main..HEAD") == 0:
        print("FORK: ja estava em dia.")
        return
    r = git("push", "fork", "main")
    if r.returncode == 0:
        print("FORK: espelhado com sucesso.")
    else:
        print(f"FORK: falha ao espelhar ({(r.stderr or '').strip()[:200]}). "
              "Nao e critico, o projeto local esta correto.")


print("=" * 66)
print("SINCRONIZACAO DO PROJETO COM O REPOSITORIO DO WORKSHOP")
print("=" * 66)

git("fetch", "--all", "--prune", check=True)
atras = contar("HEAD..origin/main")
frente = contar("origin/main..HEAD")
print(f"Novidades do Workshop a receber: {atras}")
print(f"Commits locais (customizacoes, nunca vao para o Workshop): {frente}")

if atras == 0:
    print("\nEM DIA: nao ha atualizacao nova do Workshop.")
    espelhar_fork()
    sys.exit(0)

novidades = git("log", "HEAD..origin/main", "--no-merges", "--oneline").stdout.strip()
print("\nChegando:")
print(novidades or "  (sem commits fora de merge)")

sujo = bool(git("status", "--porcelain").stdout.strip())
if sujo:
    git("stash", "push", "-u", "-m", "auto-stash-sincronizar-repo", check=True)
    print("\nTrabalho em aberto guardado no stash.")

merge = git("merge", "origin/main", "--no-edit")
conflitos = [c for c in git("diff", "--name-only", "--diff-filter=U").stdout.split("\n") if c]

if conflitos:
    if conflitos == [".gitignore"] and unir_gitignore():
        git("add", ".gitignore", check=True)
        git("commit", "--no-edit", check=True)
        print("\nConflito do .gitignore resolvido por uniao (politica de 07/08).")
    else:
        print(f"\nPARADO: conflito que exige decisao humana em {', '.join(conflitos)}.")
        git("merge", "--abort")
        if sujo:
            git("stash", "pop")
        print("Merge desfeito e trabalho devolvido. Nada foi perdido.")
        print("ACAO: resolver na sessao interativa com o Rodrigo.")
        sys.exit(2)
elif merge.returncode != 0:
    print(f"\nPARADO: o merge falhou ({(merge.stderr or '').strip()[:200]}).")
    git("merge", "--abort")
    if sujo:
        git("stash", "pop")
    sys.exit(2)

if sujo:
    git("stash", "pop")
    restantes = [c for c in git("diff", "--name-only", "--diff-filter=U").stdout.split("\n") if c]
    if restantes:
        print(f"\nATENCAO: a atualizacao entrou, mas o trabalho em aberto conflitou em "
              f"{', '.join(restantes)}. Resolver na sessao interativa.")
        sys.exit(2)
    print("Trabalho em aberto devolvido sem conflito.")

print("\nATUALIZADO com sucesso.")
espelhar_fork()
sys.exit(0)
