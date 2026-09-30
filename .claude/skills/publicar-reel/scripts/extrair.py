#!/usr/bin/env python3
"""Lê a pasta de um Reel da Linha Editorial e devolve (em JSON) tudo que a publicação precisa.

Uso: py -3 extrair.py R017            (código do Reel)
     py -3 extrair.py "caminho/da/pasta"

Saída: pasta, vídeo, capa, duração, tamanho, legenda do Instagram/Facebook,
título e descrição do YouTube já no padrão (cabeçalho da Sessão + rodapé de redes),
formato do YouTube (short ou normal) e alertas.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
REELS = RAIZ / "meus-produtos" / "linha-editorial" / "entregas" / "reels"

CABECALHO_YT = (
    "Seu restaurante vende bem e sobra pouco? Em 30 minutos eu te mostro o caminho "
    "para os 14% de lucro operacional.\n"
    "👉 Sessão Estratégica gratuita: https://docustoaolucro.com/yt"
)
RODAPE_YT = (
    "Me siga nas redes ↴\n"
    "Facebook ☛ https://facebook.com/rodrigohaertel\n"
    "Instagram ☛ https://instagram.com/rodrigohaertel\n"
    "Youtube ☛ https://youtube.com/rodrigohaertel\n\n"
    "Conheça o meu site ↴\n"
    "http://www.docustoaolucro.com"
)
LIMITE_SHORT = 180      # segundos, limite do YouTube Shorts
LIMITE_FB_API = 90      # segundos, limite da API de Reels do Facebook
LIMITE_CAPA_YT = 2_000_000  # bytes, limite da miniatura do YouTube


def achar_pasta(alvo: str) -> Path:
    p = Path(alvo)
    if p.is_dir():
        return p.resolve()
    m = re.search(r"(\d{3})", alvo)
    if not m:
        raise SystemExit(f"Não entendi qual Reel é: {alvo}")
    num = m.group(1)
    candidatas = [d for base in (REELS, REELS / "Publicados") if base.exists()
                  for d in base.iterdir() if d.is_dir() and re.match(rf"R{num}\b", d.name)]
    if not candidatas:
        raise SystemExit(f"Não encontrei a pasta do R{num} em {REELS} nem em Publicados/. "
                         "O vídeo final precisa estar numa pasta 'R{num} - Nome'.")
    return candidatas[0]


def texto_de(bloco: str) -> str:
    """Converte um <div class="legenda"> em texto: um parágrafo por <p>, linha em branco entre eles."""
    paragrafos = re.findall(r"<p[^>]*>(.*?)</p>", bloco, flags=re.S)
    saida = []
    for p in paragrafos:
        p = re.sub(r"<br\s*/?>", "\n", p)
        p = re.sub(r"<[^>]+>", "", p)
        p = html.unescape(p).strip()
        p = re.sub(r"[ \t]+", " ", p)
        if p:
            saida.append(p)
    return "\n\n".join(saida)


def secao(doc: str, numero: str) -> str:
    m = re.search(rf"<h2>\s*{numero}\.\s.*?(?=<h2>\s*\d+\.\s|</body>|$)", doc, flags=re.S)
    return m.group(0) if m else ""


def duracao(video: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(video)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        raise SystemExit("Uso: extrair.py R017")
    pasta = achar_pasta(sys.argv[1])
    alertas = []

    videos = sorted(pasta.glob("*.mp4"), key=lambda f: f.stat().st_size, reverse=True)
    if not videos:
        raise SystemExit(f"Nenhum .mp4 na pasta {pasta}")
    video = videos[0]
    if len(videos) > 1:
        alertas.append(f"Mais de um .mp4 na pasta; usei o maior: {video.name}")

    capas = [f for f in pasta.iterdir()
             if f.suffix.lower() in (".png", ".jpg", ".jpeg") and re.search(r"capa", f.name, re.I)]
    capa = sorted(capas, key=lambda f: f.stat().st_mtime, reverse=True)[0] if capas else None
    if not capa:
        alertas.append("Nenhuma imagem de capa (arquivo com 'capa' no nome) na pasta.")
    elif capa.stat().st_size > LIMITE_CAPA_YT:
        alertas.append("Capa acima de 2 MB: o script do YouTube converte para JPG antes de enviar.")

    htmls = list(pasta.glob("Reels_*.html"))
    if not htmls:
        num = re.search(r"R(\d{3})", pasta.name).group(1)
        htmls = list(REELS.glob(f"Reels_{num}_*.html"))
    if not htmls:
        raise SystemExit("Não encontrei o HTML Reels_###_*.html do Reel.")
    doc = htmls[0].read_text(encoding="utf-8")

    s3 = secao(doc, "3")
    m = re.search(r'<div class="legenda">(.*?)</div>', s3, flags=re.S)
    legenda = texto_de(m.group(1)) if m else ""
    if not legenda:
        alertas.append("Legenda (seção 3) não encontrada no HTML.")

    s5 = secao(doc, "5")
    # O rótulo é <p><b>Título</b> ...</p> e o título vem no <p> seguinte
    mt = re.search(r"<b>\s*T[íi]tulo[^<]*</b>.*?</p>\s*<p[^>]*>(.*?)</p>", s5, flags=re.S)
    titulo = html.unescape(re.sub(r"<[^>]+>", "", mt.group(1))).strip() if mt else ""
    md = re.search(r'<div class="legenda">(.*?)</div>', s5, flags=re.S)
    corpo = texto_de(md.group(1)) if md else ""
    if not titulo or not corpo:
        alertas.append("Título ou descrição do YouTube (seção 5) não encontrados no HTML.")

    seg = duracao(video)
    formato_yt = "short" if seg <= LIMITE_SHORT else "normal"
    if formato_yt == "normal" and "#shorts" in titulo.lower():
        titulo = re.sub(r"\s*#shorts", "", titulo, flags=re.I).strip()
        alertas.append("Vídeo acima de 3 min: tirei o #Shorts do título, entra como vídeo normal.")
    if formato_yt == "normal":
        corpo = re.sub(r"(^|\s)#shorts\b\s?", r"\1", corpo, flags=re.I)

    # Padrão da descrição: cabeçalho da Sessão no topo, rodapé de redes no final
    corpo = corpo.replace("Inscreva-se no canal. No Instagram eu sou @rodrigohaertel.", "Inscreva-se no canal.")
    if "docustoaolucro.com/yt" not in corpo:
        corpo = f"{CABECALHO_YT}\n\n{corpo}"
    if "Me siga nas redes" not in corpo:
        corpo = f"{corpo}\n\n{RODAPE_YT}"
    if len(corpo) > 5000:
        alertas.append(f"Descrição do YouTube com {len(corpo)} caracteres, acima do limite de 5.000.")
    if len(titulo) > 100:
        alertas.append(f"Título do YouTube com {len(titulo)} caracteres, acima do limite de 100.")
    if len(legenda) > 2200:
        alertas.append(f"Legenda com {len(legenda)} caracteres, acima do limite de 2.200 do Instagram.")

    print(json.dumps({
        "codigo": re.search(r"R\d{3}", pasta.name).group(0),
        "pasta": str(pasta),
        "html": str(htmls[0]),
        "video": str(video),
        "video_mb": round(video.stat().st_size / 1e6),
        "duracao_s": round(seg, 1),
        "duracao": f"{int(seg // 60)}min{int(seg % 60):02d}",
        "capa": str(capa) if capa else None,
        "formato_youtube": formato_yt,
        "facebook_reel_pela_api": seg <= LIMITE_FB_API,
        "legenda": legenda,
        "youtube_titulo": titulo,
        "youtube_descricao": corpo,
        "alertas": alertas,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
