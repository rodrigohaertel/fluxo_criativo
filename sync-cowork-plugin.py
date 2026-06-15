"""Ressincroniza o plugin do Cowork (plugins/fluxo-criativo/) a partir da fonte do projeto.

O que faz, de forma idempotente:
1. Copia para o plugin APENAS arquivos versionados no git (git ls-files) de
   .claude/skills, .claude/commands, .claude/agents, .claude/rules e scripts/.
   Isso exclui automaticamente cruft nao versionado (.tmp-*, logs, __pycache__,
   .DS_Store, agents-memory, .ps1 locais, etc.).
2. Preserva os arquivos que so existem no plugin (vtsd-base-rules, README.md, plugin.json).
3. Remove pastas de skill sem SKILL.md (conteineres vazios), por seguranca.
4. Reescreve caminhos scripts/ -> ${CLAUDE_PLUGIN_ROOT}/scripts/ em skills e commands.
5. Conserta frontmatter YAML (description de uma linha com ': ' vira bloco >-) e adiciona
   frontmatter nas skills que nao tem.

Uso: py -3 sync-cowork-plugin.py   (ou python3 sync-cowork-plugin.py)
"""
import os
import re
import shutil
import stat
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLUGIN = ROOT / "plugins" / "fluxo-criativo"
PROTECT_SKILL = "vtsd-base-rules"  # skill que so existe no plugin, nunca apagar

# (caminho da fonte relativo a raiz) -> (pasta destino no plugin)
COMPONENTS = [
    (".claude/skills", PLUGIN / "skills", (PROTECT_SKILL,)),
    (".claude/commands", PLUGIN / "commands", ()),
    (".claude/agents", PLUGIN / "agents", ()),
    (".claude/rules", PLUGIN / "rules", ()),
    ("scripts", PLUGIN / "scripts", ()),
]

# skills da fonte que historicamente nao tem frontmatter: slug -> (name, description)
NO_FRONTMATTER = {
    "copy-variacao-post": (
        "copy-variacao-post",
        "Gera variacoes de posts que ja funcionaram no algoritmo, a partir do historico "
        "do perfil e do dashboard, em vez de partir das urgencias ocultas. Use quando o "
        "perfil tem historico de publicacoes e o usuario quer novas versoes de conteudo "
        "validado.",
    ),
    "ferramentas": (
        "ferramentas",
        "Guia de integracoes e ferramentas externas do Workshop Marketing IA. Explica como "
        "o toolkit se conecta com cada ferramenta opcional. Use quando o usuario perguntar "
        "sobre ferramentas, integracoes ou como conectar servicos externos.",
    ),
}


def _onexc(func, path, exc):
    # Windows/OneDrive: limpa flag somente-leitura e tenta a operacao de novo
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def robust_rmtree(path: Path, attempts: int = 5):
    for _ in range(attempts - 1):
        try:
            shutil.rmtree(path, onexc=_onexc)
            return
        except FileNotFoundError:
            return
        except (PermissionError, OSError):
            time.sleep(0.5)  # espera o OneDrive soltar o handle
    shutil.rmtree(path, onexc=_onexc)  # ultima tentativa propaga o erro


def robust_remove(p: Path):
    if p.is_dir():
        robust_rmtree(p)
    else:
        try:
            p.unlink(missing_ok=True)
        except PermissionError:
            os.chmod(p, stat.S_IWRITE)
            p.unlink(missing_ok=True)


def git_tracked(rel_dir: str):
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", rel_dir],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [x for x in out.split("\0") if x]


def sync_component(src_rel: str, dest_dir: Path, preserve=()):
    dest_dir.mkdir(parents=True, exist_ok=True)
    for child in list(dest_dir.iterdir()):
        if child.name in preserve:
            continue
        robust_remove(child)
    prefix = src_rel.rstrip("/") + "/"
    count = 0
    for f in git_tracked(src_rel):
        if not f.startswith(prefix):
            continue
        target = dest_dir / f[len(prefix):]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, target)
        count += 1
    return count


def remove_empty_skill_dirs():
    removed = 0
    for d in list((PLUGIN / "skills").iterdir()):
        if d.is_dir() and not (d / "SKILL.md").exists():
            robust_rmtree(d)
            removed += 1
    return removed


def rewrite_script_paths():
    re_dotslash = re.compile(r"\./scripts/")
    re_bare = re.compile(r"(?<![\w./])scripts/")
    changed = 0
    for base in (PLUGIN / "skills", PLUGIN / "commands"):
        for md in base.rglob("*.md"):
            txt = md.read_text(encoding="utf-8")
            new = re_dotslash.sub("scripts/", txt)
            new = re_bare.sub("${CLAUDE_PLUGIN_ROOT}/scripts/", new)
            if new != txt:
                md.write_text(new, encoding="utf-8")
                changed += 1
    return changed


def fix_one_description(md: Path) -> bool:
    lines = md.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        return False
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return False
    for i in range(1, end):
        ln = lines[i]
        if ln.startswith("description: ") and not ln.rstrip().endswith(">-"):
            val = ln[len("description: "):]
            if ": " in val:  # so converte quando o valor tem o token que quebra o YAML
                lines[i] = "description: >-"
                lines.insert(i + 1, "  " + val)
                md.write_text("\n".join(lines), encoding="utf-8")
                return True
    return False


def add_missing_frontmatter() -> int:
    added = 0
    for slug, (name, desc) in NO_FRONTMATTER.items():
        p = PLUGIN / "skills" / slug / "SKILL.md"
        if not p.exists():
            continue
        body = p.read_text(encoding="utf-8")
        if body.lstrip().startswith("---"):
            continue  # ja tem frontmatter
        fm = f"---\nname: {name}\ndescription: >-\n  {desc}\n---\n\n"
        p.write_text(fm + body, encoding="utf-8")
        added += 1
    return added


def main():
    if not PLUGIN.exists():
        raise SystemExit(f"Pasta do plugin nao encontrada: {PLUGIN}")

    copied = {}
    for src_rel, dest, preserve in COMPONENTS:
        copied[src_rel] = sync_component(src_rel, dest, preserve)

    removed = remove_empty_skill_dirs()
    added_fm = add_missing_frontmatter()

    fixed_desc = 0
    for base in (PLUGIN / "skills", PLUGIN / "commands"):
        for md in base.rglob("*.md"):
            if fix_one_description(md):
                fixed_desc += 1

    rewrites = rewrite_script_paths()

    n_skills = sum(1 for d in (PLUGIN / "skills").iterdir() if d.is_dir())
    n_cmds = len(list((PLUGIN / "commands").glob("*.md")))
    n_agents = len(list((PLUGIN / "agents").glob("*.md")))

    print("Ressincronizacao concluida.")
    print(f"  arquivos versionados copiados: {sum(copied.values())}")
    print(f"  skills: {n_skills} | commands: {n_cmds} | agents: {n_agents}")
    print(f"  conteineres vazios removidos: {removed}")
    print(f"  frontmatter adicionado: {added_fm}")
    print(f"  descriptions convertidas para bloco YAML: {fixed_desc}")
    print(f"  arquivos com caminho de script reescrito: {rewrites}")


if __name__ == "__main__":
    main()
