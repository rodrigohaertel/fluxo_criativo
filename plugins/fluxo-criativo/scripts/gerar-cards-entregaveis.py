# -*- coding: utf-8 -*-
"""
Gera 8 imagens para os cards de entregaveis via OpenRouter (Gemini Flash Image).
Salva em meus-produtos/clube-concurseiros-contabeis/entregas/paginas/assets/
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "meus-produtos/clube-concurseiros-contabeis/entregas/paginas/assets"
OR_URL     = "https://openrouter.ai/api/v1/chat/completions"
OR_MODEL   = "google/gemini-3.1-flash-image-preview"

SUFFIX = (
    ", abstract 3D render, dark navy background almost black (#08080f), "
    "purple and blue accent lighting, volumetric light rays, cinematic, "
    "ultra detailed, no text, no watermark, no logo"
)

CARDS = [
    {
        "id": "01",
        "nome": "diagnostico-perfil",
        "prompt": (
            "Glowing purple compass and custom study plan document floating in dark space, "
            "holographic blueprint lines, soft purple rim light, deep dark background"
        ),
    },
    {
        "id": "02",
        "nome": "lives-semanais",
        "prompt": (
            "Abstract glowing purple monitor screen broadcasting live session, "
            "dramatic light beams, dark studio, purple and blue neon glow"
        ),
    },
    {
        "id": "03",
        "nome": "banco-questoes",
        "prompt": (
            "Abstract organized rows of glowing question cards floating in dark space, "
            "purple and indigo data visualization, holographic database grid"
        ),
    },
    {
        "id": "04",
        "nome": "caderno-erros",
        "prompt": (
            "Abstract glowing notebook with highlighted correction marks and annotations, "
            "purple pen light trail, dark background, editorial cinematic"
        ),
    },
    {
        "id": "05",
        "nome": "simulado-mensal",
        "prompt": (
            "Abstract dramatic stopwatch and exam paper glowing purple in dark space, "
            "countdown light effect, tension atmosphere, deep dark navy background"
        ),
    },
    {
        "id": "06",
        "nome": "correcao-discursiva",
        "prompt": (
            "Abstract glowing quill pen writing on illuminated page with correction highlights, "
            "purple ink light trail, dark moody background, cinematic close-up"
        ),
    },
    {
        "id": "07",
        "nome": "sprint-reta-final",
        "prompt": (
            "Abstract glowing purple rocket launching with motion trail in dark space, "
            "countdown light beams, dramatic upward momentum, deep dark background"
        ),
    },
    {
        "id": "08",
        "nome": "grupo-mentor",
        "prompt": (
            "Abstract network of connected glowing purple nodes representing a community, "
            "one larger central node as mentor, dark background, holographic connections"
        ),
    },
]


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        if k and k not in os.environ:
            os.environ[k] = v


def extract_img(result: dict) -> str | None:
    msg = (result.get("choices") or [{}])[0].get("message", {})
    for img in (msg.get("images") or []):
        url = (img.get("image_url") or {}).get("url") if isinstance(img, dict) else None
        if isinstance(url, str) and url.startswith("data:image"):
            return url
    content = msg.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                url = (part.get("image_url") or {}).get("url", "")
                if url.startswith("data:image"):
                    return url
    if isinstance(content, str) and "data:image" in content:
        m = re.search(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", content)
        if m:
            return m.group(0)
    return None


def save_data_url(data_url: str, dest: Path) -> None:
    m = re.match(r"data:image/[^;]+;base64,(.+)", data_url, re.DOTALL)
    if not m:
        raise ValueError("data URL inesperado")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode(m.group(1)))


def gerar_imagem(api_key: str, card: dict) -> bool:
    dest = OUTPUT_DIR / f"card-entregavel-{card['id']}-{card['nome']}.png"
    if dest.exists():
        print(f"   [{card['id']}] Ja existe: {dest.name} — pulando")
        return True

    full_prompt = card["prompt"].rstrip() + SUFFIX
    print(f"   [{card['id']}] Gerando: {card['nome']}...", flush=True)

    data = json.dumps({
        "model":      OR_MODEL,
        "messages":   [{"role": "user", "content": full_prompt}],
        "modalities": ["image", "text"],
    }).encode("utf-8")

    req = urllib.request.Request(
        OR_URL,
        data=data,
        headers={
            "Authorization":  f"Bearer {api_key}",
            "Content-Type":   "application/json",
            "HTTP-Referer":   "https://workshop.inteligente",
            "X-Title":        "Workshop Marketing IA",
            "Content-Length": str(len(data)),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"   ERRO HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"   ERRO: {e}", file=sys.stderr)
        return False

    if result.get("error"):
        print(f"   ERRO OpenRouter: {str(result['error'])[:300]}", file=sys.stderr)
        return False

    url = extract_img(result)
    if not url:
        print(f"   ERRO: sem imagem na resposta. Chaves: {list(result.keys())}", file=sys.stderr)
        return False

    save_data_url(url, dest)
    print(f"   [{card['id']}] Salvo: {dest}")
    return True


def main() -> None:
    load_env()
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("ERRO: OPENROUTER_API_KEY nao encontrada no .env", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Destino: {OUTPUT_DIR}")
    print(f"Total de imagens: {len(CARDS)}\n")

    ok = 0
    falhas = []
    for card in CARDS:
        sucesso = gerar_imagem(api_key, card)
        if sucesso:
            ok += 1
        else:
            falhas.append(card["id"])
        time.sleep(1)

    print(f"\nConcluido: {ok}/{len(CARDS)} imagens geradas.")
    if falhas:
        print(f"Falhas nos cards: {', '.join(falhas)}")
    else:
        print("Todas as imagens foram geradas com sucesso.")


if __name__ == "__main__":
    main()
