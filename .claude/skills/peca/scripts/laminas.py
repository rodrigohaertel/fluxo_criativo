#!/usr/bin/env python3
"""Exporta as lâminas de um carrossel da Linha Editorial em PNG e monta a prévia.

Uso:
  py -3 laminas.py "meus-produtos/linha-editorial/entregas/carrosseis/Carrossel_012_Nome"
  py -3 laminas.py "<pasta>" --so 1,3        só algumas lâminas
  py -3 laminas.py "<pasta>" --espera 4000   mais tempo para a fonte carregar (ms)
  py -3 laminas.py "<pasta>" --saida <outra pasta>   grava em outro lugar (teste)
  py -3 laminas.py "<pasta>" --sem-previa

O HTML do carrossel (Carrossel_###_*.html) tem uma <div class="s"> por lâmina e um script
que, com ?s=N na URL, deixa só a lâmina N na tela (modo solo). Este script abre cada
?s=N no Chrome (ou Edge) sem janela, em 1080 x 1350, e grava Carrossel_###_Nome_0N.png.
Depois monta _previa_###.jpg com quatro lâminas por linha, na metade do tamanho.

Saída em JSON (UTF-8). Nenhum segredo é lido aqui.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LARGURA, ALTURA = 1080, 1350
POR_LINHA = 4


def falhar(msg: str) -> None:
    print(json.dumps({"erro": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)


def chrome() -> str:
    for p in (os.environ.get("CHROME"),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chrome")):
        if p and Path(p).exists():
            return p
    falhar("Chrome ou Edge não encontrado para exportar as lâminas.")


def achar_html(pasta: Path) -> Path:
    htmls = [h for h in pasta.glob("Carrossel_*.html") if not h.name.startswith("_")]
    if not htmls:
        falhar(f"Nenhum Carrossel_###_*.html em {pasta}")
    return sorted(htmls)[0]


def contar_laminas(doc: str) -> int:
    return len(re.findall(r'<div class="s[\s"]', doc))


def exportar(html: Path, indices, saida: Path, espera_ms: int):
    navegador = chrome()
    url = html.resolve().as_uri()
    prefixo = html.stem
    resultados = []
    with tempfile.TemporaryDirectory() as tmp:
        perfil = Path(tmp) / "perfil"
        for n in indices:
            destino = saida / f"{prefixo}_{n:02d}.png"
            cmd = [navegador, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                   "--force-device-scale-factor=1", f"--window-size={LARGURA},{ALTURA}",
                   f"--virtual-time-budget={espera_ms}", f"--user-data-dir={perfil}",
                   "--no-first-run", "--disable-extensions",
                   f"--screenshot={destino}", f"{url}?s={n}"]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            item = {"lamina": n, "arquivo": destino.name}
            if not destino.exists():
                item["erro"] = (r.stderr or "o Chrome não gravou o arquivo").strip()[-300:]
            else:
                try:
                    from PIL import Image
                    with Image.open(destino) as im:
                        item["tamanho"] = list(im.size)
                        if im.size != (LARGURA, ALTURA):
                            item["aviso"] = f"saiu em {im.size[0]} x {im.size[1]}, esperado {LARGURA} x {ALTURA}"
                except ImportError:
                    item["aviso"] = "Pillow ausente: tamanho não conferido"
            resultados.append(item)
    return resultados


def previa(pasta: Path, prefixo: str, total: int, saida: Path):
    try:
        from PIL import Image
    except ImportError:
        return None
    laminas = [saida / f"{prefixo}_{n:02d}.png" for n in range(1, total + 1)]
    laminas = [l for l in laminas if l.exists()]
    if not laminas:
        return None
    w, h = LARGURA // 2, ALTURA // 2
    linhas = (len(laminas) + POR_LINHA - 1) // POR_LINHA
    folha = Image.new("RGB", (w * POR_LINHA, h * linhas), (207, 207, 207))
    for i, l in enumerate(laminas):
        with Image.open(l) as im:
            folha.paste(im.convert("RGB").resize((w, h), Image.LANCZOS), ((i % POR_LINHA) * w, (i // POR_LINHA) * h))
    m = re.search(r"Carrossel_(\d{3})", prefixo)
    nome = f"_previa_{m.group(1) if m else 'carrossel'}.jpg"
    destino = saida / nome
    folha.save(destino, quality=88)
    return destino.name


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    pasta = Path(args[0])
    if not pasta.is_absolute():
        pasta = (Path.cwd() / pasta).resolve()
    if not pasta.is_dir():
        falhar(f"Pasta não encontrada: {pasta}")

    def opcao(flag, padrao=None):
        return args[args.index(flag) + 1] if flag in args else padrao

    html = achar_html(pasta)
    total = contar_laminas(html.read_text(encoding="utf-8", errors="replace"))
    if total == 0:
        falhar(f"Nenhuma <div class=\"s\"> em {html.name}")
    so = opcao("--so")
    indices = [int(x) for x in so.split(",")] if so else list(range(1, total + 1))
    fora = [i for i in indices if i < 1 or i > total]
    if fora:
        falhar(f"Lâmina fora do intervalo 1 a {total}: {fora}")
    espera = int(opcao("--espera", "3000"))
    saida = Path(opcao("--saida", str(pasta)))
    saida.mkdir(parents=True, exist_ok=True)

    resultados = exportar(html, indices, saida, espera)
    nome_previa = None if "--sem-previa" in args else previa(pasta, html.stem, total, saida)
    print(json.dumps({
        "html": html.name,
        "laminas_no_html": total,
        "exportadas": resultados,
        "previa": nome_previa,
        "saida": str(saida),
        "ok": all("erro" not in r and "aviso" not in r for r in resultados),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
