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
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEM_PUSH = "--sem-push" in sys.argv
SEM_COMMIT = "--sem-commit" in sys.argv

# BACKUP AUTOMATICO (08/2026): o que a rotina pode commitar sozinha. Lista
# fechada de proposito. Nada fora daqui entra, para que lixo de terminal, arquivo
# temporario ou pasta nova nunca seja versionado por acidente.
PASTAS_BACKUP = ("scripts", ".claude/commands", ".claude/agents", ".claude/rules", ".claude/skills")
ARQUIVOS_BACKUP = (".claude/settings.json", "CLAUDE.md", "ARQUITETURA.md")

# Se qualquer coisa parecida com credencial aparecer no que seria commitado, o
# backup ABORTA. Melhor perder o backup de um dia do que vazar chave no GitHub.
PADRAO_SEGREDO = re.compile(
    r"EAA[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_\-]{20,}|eyJ[A-Za-z0-9_\-]{30,}"
    r"|xox[bp]-[A-Za-z0-9\-]{10,}|whsec_[A-Za-z0-9]{10,}|AIza[A-Za-z0-9_\-]{30,}"
)


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


def backup_automatico():
    """Commita as mudancas de script e configuracao, para o trabalho nao viver
    so no disco desta maquina. Conservador de proposito:
      - so os caminhos de PASTAS_BACKUP / ARQUIVOS_BACKUP entram;
      - aborta se aparecer algo parecido com credencial;
      - nao commita nada fora disso (lixo de terminal, pasta nova, temporario).
    O .env segue no .gitignore e nunca chega aqui.
    """
    if SEM_COMMIT:
        return
    alvos = [p for p in (*PASTAS_BACKUP, *ARQUIVOS_BACKUP) if (RAIZ / p).exists()]
    if not alvos:
        return

    git("add", "--", *alvos)
    staged = [l for l in git("diff", "--cached", "--name-only").stdout.split("\n") if l]
    if not staged:
        print("BACKUP: nada novo para salvar.")
        return

    # Trava de seguranca: le o conteudo que seria commitado.
    diff = git("diff", "--cached").stdout
    achado = PADRAO_SEGREDO.search(diff)
    if achado:
        git("reset", "-q")
        print(f"BACKUP ABORTADO: o conteudo parece conter credencial "
              f"({achado.group()[:6]}...). Nada foi commitado. Conferir a mao.")
        return

    resumo = ", ".join(sorted({p.split("/")[0] for p in staged}))
    corpo = "\n".join(f"- {p}" for p in staged[:40])
    if len(staged) > 40:
        corpo += f"\n- e mais {len(staged) - 40} arquivo(s)"
    msg = (f"chore(rotina): backup automatico de {date.today().strftime('%d/%m/%Y')}\n\n"
           f"Salvo pela rotina das 02h ({resumo}), para o trabalho nao viver so no\n"
           f"disco da maquina. Arquivos:\n\n{corpo}\n\n"
           f"Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n")
    r = git("commit", "-q", "-m", msg)
    if r.returncode == 0:
        print(f"BACKUP: {len(staged)} arquivo(s) salvos em commit automatico.")
    else:
        git("reset", "-q")
        print(f"BACKUP: falha ao commitar ({(r.stderr or '').strip()[:160]}). Nada foi alterado.")


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
    backup_automatico()
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
backup_automatico()
espelhar_fork()
sys.exit(0)
