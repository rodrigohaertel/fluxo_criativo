# -*- coding: utf-8 -*-
"""
DEPRECATED. Script descontinuado junto com os 5 temas VTSD.

Fluxo atual: /pagina-visual + scripts/montar-pagina-copias.py usa copias
HTML isoladas em paginas/copias/ (sem temas compartilhados). Este script
copiava temas VTSD com 16 blocos atomicos, arquitetura abandonada.

Mantido so por compatibilidade. Nao use em novos produtos.

---

Copia para meus-produtos/{slug}/entregas/ todos os blocos atômicos + pasta
pagina_completa_* de um tema, para editar a copy na cópia sem alterar os
originais do plugin.

Depois: edite os code.html em meus-produtos/{slug}/entregas/paginas/templates-{tema}/ e rode
workshop-merge-pagina.py com --templates-root apontando para essa pasta.

Uso (na raiz do repositório):
  py -3 scripts/workshop-copy-template-tema.py --tema flat_claro
  py -3 scripts/workshop-copy-template-tema.py --tema glass_escuro --slug meu-produto
  py -3 scripts/workshop-copy-template-tema.py --tema teal_claro --force
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_CANDIDATES = (
    ROOT / ".claude" / "skills" / "paginas" / "references" / "templates",
    ROOT
    / ".claude"
    / "plugins"
    / "workshop-marketing"
    / "skills"
    / "paginas"
    / "references"
    / "templates",
)
TEMPLATES = next(
    (p for p in TEMPLATES_CANDIDATES if p.is_dir()),
    TEMPLATES_CANDIDATES[0],
)

THEMES = (
    "flat_claro",
    "minimal_claro",
    "glass_escuro",
    "teal_claro",
    "purple_escuro",
)


def dirs_for_tema(tema: str) -> list[Path]:
    out: list[Path] = []
    suf = f"_{tema}"
    for p in sorted(TEMPLATES.iterdir()):
        if not p.is_dir():
            continue
        n = p.name
        if n == f"pagina_completa_{tema}" or n.endswith(suf):
            out.append(p)
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="Copia templates do tema para meus-produtos/{slug}/entregas/paginas/templates-{tema}/",
    )
    p.add_argument(
        "--tema",
        required=True,
        choices=sorted(THEMES),
        help="Sufixo do tema (ex.: flat_claro)",
    )
    p.add_argument(
        "--slug",
        default=None,
        help="Slug do produto (padrão: meus-produtos/.ativo)",
    )
    p.add_argument(
        "--dest",
        default=None,
        help="Pasta de destino completa (opcional; padrão: meus-produtos/{slug}/entregas/paginas/templates-{tema})",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Se a pasta de destino existir, apaga e copia de novo",
    )
    args = p.parse_args()

    tema = args.tema
    to_copy = dirs_for_tema(tema)
    if not to_copy:
        print("Nenhuma pasta encontrada para o tema:", tema, file=sys.stderr)
        sys.exit(1)

    slug = args.slug
    if not slug:
        ativo = ROOT / "meus-produtos" / ".ativo"
        if ativo.is_file():
            slug = ativo.read_text(encoding="utf-8").strip()
    if not slug and not args.dest:
        print(
            "Defina --slug, --dest ou crie meus-produtos/.ativo.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.dest:
        dest_root = Path(args.dest).resolve()
    else:
        dest_root = (
            ROOT / "meus-produtos" / slug / "entregas" / "paginas" / f"templates-{tema}"
        ).resolve()

    if dest_root.exists():
        if not args.force:
            print(
                "Já existe:",
                dest_root,
                "\nUse --force para substituir ou escolha outro --dest.",
                file=sys.stderr,
            )
            sys.exit(3)
        shutil.rmtree(dest_root)

    dest_root.mkdir(parents=True, exist_ok=True)

    for src in to_copy:
        dst = dest_root / src.name
        shutil.copytree(src, dst)

    print("Copiado tema", tema, "->", dest_root)
    print("Pastas:", len(to_copy))
    print()
    print("Próximo: edite os code.html nesta cópia (copy aprovada).")
    print("Merge:")
    print(
        f'  py -3 scripts/workshop-merge-pagina.py --tema {tema} '
        f'--templates-root "{dest_root}" --copiar-entregas'
    )
    if slug:
        print("  (slug:", slug + ")")


if __name__ == "__main__":
    main()
