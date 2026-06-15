# -*- coding: utf-8 -*-
"""
DEPRECATED. Script descontinuado.

Criado na fase anterior da arquitetura (tema custom com 16 blocos atomicos
herdando design system global). O fluxo atual usa copias HTML isoladas em
paginas/copias/ geradas pela skill ui-reverse-engineer, sem tema base nem
harmonizacao global entre secoes. Cada copia preserva seu design literal.

Novo fluxo: /pagina-visual + scripts/montar-pagina-copias.py.

Mantido so por compatibilidade. Nao use em novos produtos.

---

Prepara um tema custom baseado em prints de referencia do aluno.

Pipeline:
1. Le meus-produtos/{slug}/entregas/paginas/referencias/*.png (prints numerados por bloco)
2. Le meus-produtos/{slug}/entregas/paginas/design-system.json (gerado pela analise da IA)
3. Copia o tema base (indicado no design-system.json) para templates-custom-{slug}/
4. Para blocos COM print: deixa o code.html vazio (marcado com <!-- TODO: preencher com IA -->)
                         aguardando o Claude gerar via skill ui-reverse-engineer
5. Para blocos SEM print: mantem o code.html do tema base, mas injeta CSS variables override
   do design-system no topo do <style> pra harmonizar com os blocos gerados.
6. Copia tambem o build_merge.py do tema base, ajustando o nome do tema para 'custom'.

Uso:
  py -3 scripts/criar-tema-custom.py --slug meu-produto

O arquivo design-system.json deve ter a estrutura:
{
  "tema_base": "flat_claro",
  "paleta": {"bg": "#fff", "ink": "#111", "accent": "#3b82f6", ...},
  "tipografia": {"fonte_heading": "'Plus Jakarta Sans', sans-serif", "fonte_body": "'Inter', sans-serif"},
  "border_radius": "16px",
  "blocos_com_print": ["01", "06"],
  "blocos_sem_print": ["02","03","04","05","07","08","09","10","11","12","13","14","15","16"]
}

Mapeamento bloco -> pasta atomica (por tema):
  01 hero, 02 dor, 03 paliativo, 04 provas_sociais, 05 cta, 06 metodo,
  07 para_quem, 08 entregaveis, 09 bonus, 10 stack_valor, 11 provas_sociais (2x),
  12 suporte, 13 garantia, 14 autoridade, 15 faq, 16 oferta_final
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_CANDIDATES = (
    ROOT / ".claude" / "skills" / "paginas" / "references" / "templates",
    ROOT / ".claude" / "plugins" / "workshop-marketing" / "skills" / "paginas" / "references" / "templates",
)
TEMPLATES = next((p for p in TEMPLATES_CANDIDATES if p.is_dir()), TEMPLATES_CANDIDATES[0])

BLOCO_PASTA = {
    "01": "hero",
    "02": "dor",
    "03": "paliativo",
    "04": "provas_sociais",
    "05": "cta",
    "06": "metodo",
    "07": "para_quem",
    "08": "entregaveis",
    "09": "bonus",
    "10": "stack_valor",
    "11": "provas_sociais",
    "12": "suporte",
    "13": "garantia",
    "14": "autoridade",
    "15": "faq",
    "16": "oferta_final",
}

THEMES = ("flat_claro", "minimal_claro", "glass_escuro", "teal_claro", "purple_escuro")


def gerar_css_variables(design: dict[str, Any]) -> str:
    """Gera um bloco :root com CSS variables override a partir do design-system.json."""
    paleta = design.get("paleta") or {}
    tipo = design.get("tipografia") or {}
    radius = design.get("border_radius", "")
    botao = design.get("botao") or {}
    linhas = [":root {"]
    for k, v in paleta.items():
        if v:
            linhas.append(f"  --ds-{k}: {v};")
    if tipo.get("fonte_heading"):
        linhas.append(f"  --ds-font-heading: {tipo['fonte_heading']};")
    if tipo.get("fonte_body"):
        linhas.append(f"  --ds-font-body: {tipo['fonte_body']};")
    if radius:
        linhas.append(f"  --ds-radius: {radius};")
    if botao.get("bg"):
        linhas.append(f"  --ds-btn-bg: {botao['bg']};")
    if botao.get("color"):
        linhas.append(f"  --ds-btn-color: {botao['color']};")
    linhas.append("}")
    # Harmoniza: sobrescreve variables comuns dos temas VTSD
    # (body background, cores de texto). Opcional: o aluno pode ajustar manualmente depois.
    if paleta.get("bg"):
        linhas.append(f"body {{ background: {paleta['bg']}; }}")
    if paleta.get("ink"):
        linhas.append(f".tpl-hero-flat, .tpl-flat-dor, .tpl-flat-paliativo, .tpl-flat-metodo, .tpl-flat-paraquem, .tpl-flat-entregaveis, .tpl-flat-bonus, .tpl-flat-stack, .tpl-flat-provas, .tpl-flat-suporte, .tpl-flat-garantia, .tpl-flat-autoridade, .tpl-flat-faq, .tpl-flat-oferta {{ color: {paleta['ink']}; }}")
    return "\n".join(linhas)


def injetar_css_override(code_html: str, css_override: str) -> str:
    """Injeta o bloco de CSS override dentro do <style> existente (no topo)."""
    if "<style>" in code_html:
        return code_html.replace(
            "<style>",
            f"<style>\n/* === DESIGN SYSTEM OVERRIDE (criar-tema-custom) === */\n{css_override}\n/* === FIM OVERRIDE === */\n",
            1,
        )
    # Sem style: adiciona um
    return code_html.replace(
        "</head>",
        f"<style>\n{css_override}\n</style>\n</head>",
        1,
    )


def placeholder_block_html(bloco: str, nome_pasta: str, print_nome: str | None) -> str:
    """HTML placeholder pra blocos que aguardam geracao pela IA a partir do print."""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Bloco {bloco}. Aguardando geracao via print</title>
</head>
<body>
<!-- TODO: preencher com IA usando a skill ui-reverse-engineer a partir do print: {print_nome or 'referencia'} -->
<!-- Bloco {bloco} ({nome_pasta}). Substituir todo o body por HTML fiel ao print. -->
<!-- Usar CSS variables do design-system.json (--ds-bg, --ds-ink, --ds-accent, etc.) -->
<section style="padding: 80px 24px; text-align: center;">
<h2>[Bloco {bloco} aguardando preenchimento pelo Claude]</h2>
<p>O Claude vai ler o print correspondente e gerar o HTML fiel aqui.</p>
</section>
</body>
</html>
"""


def novo_build_merge(tema_base: str, slug: str, dest: Path) -> None:
    """Copia o build_merge.py do tema base e adapta referencias de path."""
    src = TEMPLATES / f"pagina_completa_{tema_base}" / "build_merge.py"
    conteudo = src.read_text(encoding="utf-8")
    # Substitui referencias a `_{tema_base}` por `_custom`
    conteudo = conteudo.replace(f"_{tema_base}", "_custom")
    conteudo = conteudo.replace(f"pagina_completa_{tema_base}", "pagina_completa_custom")
    dest.write_text(conteudo, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Prepara tema custom a partir de prints de referencia.")
    p.add_argument("--slug", default=None, help="Slug do produto (default: meus-produtos/.ativo)")
    p.add_argument("--force", action="store_true", help="Recria templates-custom-{slug} do zero")
    args = p.parse_args()

    slug = args.slug
    if not slug:
        ativo = ROOT / "meus-produtos" / ".ativo"
        if ativo.is_file():
            slug = ativo.read_text(encoding="utf-8").strip()
    if not slug:
        print("Defina --slug ou crie meus-produtos/.ativo.", file=sys.stderr)
        sys.exit(2)

    base_pagina = ROOT / "meus-produtos" / slug / "entregas" / "paginas"
    design_path = base_pagina / "design-system.json"
    ref_dir = base_pagina / "referencias"
    dest_dir = base_pagina / f"templates-custom-{slug}"

    if not design_path.is_file():
        print(f"design-system.json nao encontrado em: {design_path}", file=sys.stderr)
        print("Rode primeiro a analise dos prints via /pagina-visual.", file=sys.stderr)
        sys.exit(3)

    design = json.loads(design_path.read_text(encoding="utf-8"))
    tema_base = design.get("tema_base")
    if tema_base not in THEMES:
        print(f"tema_base invalido em design-system.json: {tema_base}. Deve ser um de {THEMES}.", file=sys.stderr)
        sys.exit(4)

    blocos_com_print = set(design.get("blocos_com_print") or [])
    if not blocos_com_print:
        # Tenta inferir de referencias/
        if ref_dir.is_dir():
            for f in ref_dir.iterdir():
                m = re.match(r"bloco-?(\d{2})", f.stem, re.IGNORECASE)
                if m:
                    blocos_com_print.add(m.group(1))
    blocos_sem_print = set(BLOCO_PASTA.keys()) - blocos_com_print

    print(f"Slug: {slug}")
    print(f"Tema base: {tema_base}")
    print(f"Blocos com print: {sorted(blocos_com_print)}")
    print(f"Blocos sem print (fallback): {sorted(blocos_sem_print)}")
    print(f"Destino: {dest_dir.relative_to(ROOT)}")

    if dest_dir.exists():
        if args.force:
            shutil.rmtree(dest_dir)
        else:
            print(f"Ja existe: {dest_dir}. Use --force para recriar.", file=sys.stderr)
            sys.exit(5)
    dest_dir.mkdir(parents=True, exist_ok=True)

    css_override = gerar_css_variables(design)

    # Gera cada bloco
    pastas_unicas_criadas: set[str] = set()
    for bloco, nome_pasta in BLOCO_PASTA.items():
        # Nome unico da pasta custom (nao duplica provas_sociais: usa _custom)
        pasta_custom_nome = f"{nome_pasta}_custom"
        pasta_custom = dest_dir / pasta_custom_nome
        # Provas_sociais aparece em bloco 04 e 11. No merge, e usado 2x a partir da mesma pasta.
        # Nao duplicamos a pasta. Se bloco 11 aparece, o conteudo da pasta provas_sociais_custom
        # vai ser o do print do bloco 11 (o merge usa a mesma pasta pra provas e provas2).
        # Se quiser depoimentos diferentes entre os dois blocos, isso e resolvido pelo
        # build-pagina-vendas.py no postprocess.
        if pasta_custom_nome in pastas_unicas_criadas:
            continue
        pastas_unicas_criadas.add(pasta_custom_nome)
        pasta_custom.mkdir(parents=True, exist_ok=True)

        if bloco in blocos_com_print:
            # Bloco tem print. Deixa placeholder pra Claude preencher via ui-reverse-engineer.
            print_match = None
            if ref_dir.is_dir():
                for f in ref_dir.iterdir():
                    if re.match(rf"bloco-?{bloco}", f.stem, re.IGNORECASE):
                        print_match = f.name
                        break
            code_html = placeholder_block_html(bloco, nome_pasta, print_match)
        else:
            # Bloco sem print. Copia do tema base e injeta CSS override.
            src = TEMPLATES / f"{nome_pasta}_{tema_base}" / "code.html"
            if not src.is_file():
                # Alguns blocos nao existem como pasta _{tema_base} isolada
                print(f"Aviso: {src} nao existe, pulando bloco {bloco}.", file=sys.stderr)
                continue
            code_html = src.read_text(encoding="utf-8")
            code_html = injetar_css_override(code_html, css_override)

        (pasta_custom / "code.html").write_text(code_html, encoding="utf-8")

    # Copia o build_merge.py adaptado
    merge_dest_dir = dest_dir / "pagina_completa_custom"
    merge_dest_dir.mkdir(parents=True, exist_ok=True)
    novo_build_merge(tema_base, slug, merge_dest_dir / "build_merge.py")

    print(f"\nTema custom criado em: {dest_dir.relative_to(ROOT)}")
    print(f"Pastas criadas: {len(pastas_unicas_criadas)}")
    print(f"\nProximos passos:")
    if blocos_com_print:
        print(f"1. Claude preenche via ui-reverse-engineer os blocos: {sorted(blocos_com_print)}")
        print(f"   (os code.html dos blocos com print estao marcados com <!-- TODO -->)")
    print(f"2. Rodar: py -3 scripts/build-pagina-vendas.py --slug {slug} --tema custom \\")
    print(f"          --templates-root {dest_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
