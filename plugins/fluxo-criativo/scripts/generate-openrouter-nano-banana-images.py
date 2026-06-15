# -*- coding: utf-8 -*-
"""
Gera imagens via OpenRouter usando o modelo Gemini Flash Image (Nano Banana)
e grava em meus-produtos/{slug}/entregas/paginas/assets/.

Chave da API (facil e seguro):
  1. Copie .env.example para .env na RAIZ do projeto (se ainda nao tiver).
  2. Abra o .env e preencha OPENROUTER_API_KEY= com sua chave (openrouter.ai/settings/keys).
  3. Salve. O .env nao vai para o Git.

Opcional: OPENROUTER_MODEL no mesmo .env (padrao: google/gemini-2.5-flash-image).

Uso na raiz do repositorio:
  py -3 scripts/generate-openrouter-nano-banana-images.py --slug planilhas-pro

Imagem unica (prompt livre): --output nome.png --prompt "..." --aspect 16:9
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

FALLBACK_MODEL = "google/gemini-2.5-flash-image"


def load_env_file(path: Path) -> None:
    """Carrega VAR=valor no processo. Nao sobrescreve variavel ja definida no sistema."""
    if not path.is_file():
        return
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, _, rest = s.partition("=")
        key = key.strip()
        val = rest.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val

# Prompts em inglês costumam responder melhor; estilo alinhado à marca (verde #0f7937, gestão, MEI).
JOBS: list[dict[str, Any]] = [
    {
        "file": "paliativo-banco.png",
        "aspect_ratio": "16:9",
        "image_size": "1K",
        "prompt": (
            "Photorealistic editorial photo: Brazilian small business owner checking "
            "a bank app on smartphone next to a laptop with a simple spreadsheet, "
            "clean desk, soft daylight, subtle green accent #0f7937 in UI highlights, "
            "no text overlays, no logos."
        ),
    },
    {
        "file": "paliativo-blog.png",
        "aspect_ratio": "16:9",
        "image_size": "1K",
        "prompt": (
            "Photorealistic: messy desktop with multiple overlapping generic Excel "
            "windows and printed tables, slight chaos, neutral office, no readable text, "
            "no brand logos."
        ),
    },
    {
        "file": "paliativo-pack.png",
        "aspect_ratio": "16:9",
        "image_size": "1K",
        "prompt": (
            "Photorealistic: huge stack of random file folders and USB drives on a "
            "desk, overwhelming clutter, metaphor for too many files, no text, no logos."
        ),
    },
    {
        "file": "paliativo-curso.png",
        "aspect_ratio": "16:9",
        "image_size": "1K",
        "prompt": (
            "Photorealistic: long boring online course interface on monitor showing "
            "endless Excel lesson thumbnails, tired mood, no readable text, no logos."
        ),
    },
    {
        "file": "depo-marina.png",
        "aspect_ratio": "1:1",
        "image_size": "1K",
        "prompt": (
            "Professional headshot of a Brazilian woman, small business owner, "
            "30s, warm smile, neutral studio background, soft light, photorealistic, "
            "natural skin, no text."
        ),
    },
    {
        "file": "depo-roberto.png",
        "aspect_ratio": "1:1",
        "image_size": "1K",
        "prompt": (
            "Professional headshot of a Brazilian man, shop owner, 40s, friendly, "
            "neutral background, soft light, photorealistic, no text."
        ),
    },
    {
        "file": "depo-fernanda.png",
        "aspect_ratio": "1:1",
        "image_size": "1K",
        "prompt": (
            "Professional headshot of a Brazilian woman freelancer, 30s, confident, "
            "neutral background, photorealistic, no text."
        ),
    },
    {
        "file": "metodo-passo1.png",
        "aspect_ratio": "3:2",
        "image_size": "1K",
        "prompt": (
            "Photorealistic: laptop screen showing a clean financial dashboard "
            "spreadsheet, shallow depth of field, modern desk, subtle green #0f7937 "
            "accent in chart, no readable text, no logos."
        ),
    },
    {
        "file": "metodo-passo2.png",
        "aspect_ratio": "3:2",
        "image_size": "1K",
        "prompt": (
            "Photorealistic: hands typing on laptop keyboard with spreadsheet visible, "
            "office context, warm light, no readable text, no logos."
        ),
    },
    {
        "file": "metodo-passo3.png",
        "aspect_ratio": "3:2",
        "image_size": "1K",
        "prompt": (
            "Photorealistic: split view tutorial style, small video player beside "
            "spreadsheet on screen, productivity mood, no readable text, no logos."
        ),
    },
    {
        "file": "autoridade-criador.png",
        "aspect_ratio": "4:5",
        "image_size": "1K",
        "prompt": (
            "Photorealistic portrait of a Brazilian digital product creator, business "
            "casual, trustworthy, neutral background, soft light, no text, no logos."
        ),
    },
    {
        "file": "depois-compra-membros-fluent.png",
        "aspect_ratio": "4:3",
        "image_size": "1K",
        "prompt": (
            "Microsoft Fluent Design inspired 3D illustration: abstract frosted glass "
            "panels and floating UI cards suggesting a member portal, soft blue and "
            "teal gradients, subtle green accent #0f7937, clean studio lighting, "
            "isometric, professional enterprise aesthetic, no cartoon characters, "
            "no mascots, no readable text, no logos."
        ),
    },
    {
        "file": "depois-compra-arquivos-fluent.png",
        "aspect_ratio": "4:3",
        "image_size": "1K",
        "prompt": (
            "Microsoft 365 marketing style 3D render: layered folders and spreadsheet "
            "tiles, glass morphism, soft shadows, cool gray and blue palette, subtle "
            "green accent #0f7937, productivity metaphor, no characters, no mascots, "
            "no readable text, no logos."
        ),
    },
    {
        "file": "depois-compra-suporte-fluent.png",
        "aspect_ratio": "4:3",
        "image_size": "1K",
        "prompt": (
            "Fluent Design 3D scene: abstract geometric headset and chat bubble icons, "
            "frosted glass slabs, calm blue gradient background, enterprise customer "
            "support metaphor, no cartoon animals, no cute characters, no readable text, "
            "no logos."
        ),
    },
]


def _extract_data_url(message: dict[str, Any]) -> str | None:
    images = message.get("images")
    if not images:
        return None
    first = images[0]
    url = None
    if isinstance(first, dict):
        iu = first.get("image_url") or first.get("imageUrl")
        if isinstance(iu, dict):
            url = iu.get("url")
        elif isinstance(iu, str):
            url = iu
    if isinstance(url, str) and url.startswith("data:image"):
        return url
    return None


def _save_from_data_url(data_url: str, dest: Path) -> None:
    m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,(.+)", data_url, re.DOTALL)
    if not m:
        raise ValueError("URL de imagem inesperada (esperado data:image/...;base64,...)")
    raw = base64.b64decode(m.group(2))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def generate_one(
    api_key: str,
    model: str,
    prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        },
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/workshop_inteligente",
        "X-Title": "Workshop Marketing IA image gen",
    }
    result = _post_json(OPENROUTER_URL, headers, payload)
    if result.get("error"):
        raise RuntimeError(json.dumps(result["error"], ensure_ascii=False))
    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError("Resposta sem choices: " + json.dumps(result)[:800])
    message = choices[0].get("message") or {}
    url = _extract_data_url(message)
    if not url:
        raise RuntimeError(
            "Sem imagem na resposta. Conteúdo: "
            + json.dumps(message, ensure_ascii=False)[:1200]
        )
    return url


def main() -> int:
    load_env_file(ROOT / ".env")
    default_model = (os.environ.get("OPENROUTER_MODEL") or "").strip() or FALLBACK_MODEL

    ap = argparse.ArgumentParser(description="Gera imagens Nano Banana via OpenRouter.")
    ap.add_argument("--slug", default="planilhas-pro", help="Pasta em meus-produtos/{slug}")
    ap.add_argument(
        "--model",
        default=default_model,
        help="Modelo OpenRouter com saida image (default: .env OPENROUTER_MODEL ou Nano Banana)",
    )
    ap.add_argument(
        "--max",
        type=int,
        default=0,
        help="Limita quantidade de imagens (0 = todas)",
    )
    ap.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Pula as N primeiras entradas da lista (ex.: --skip 1 --max 1 gera so a segunda)",
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Pausa em segundos entre chamadas",
    )
    ap.add_argument(
        "--output",
        default="",
        help="Gera uma unica imagem: nome do arquivo dentro de paginas/assets (ex.: destaque.png)",
    )
    ap.add_argument(
        "--prompt",
        default="",
        help="Prompt para modo --output (obrigatorio junto com --output)",
    )
    ap.add_argument(
        "--aspect",
        default="16:9",
        help="Proporcao no modo --output (default 16:9)",
    )
    args = ap.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        env_path = ROOT / ".env"
        print(
            "Nao encontrei OPENROUTER_API_KEY.\n\n"
            "Faca assim (uma vez):\n"
            "  1. Na raiz do projeto, copie o arquivo .env.example para .env\n"
            "  2. Abra o .env com o Bloco de Notas e cole sua chave na linha OPENROUTER_API_KEY=\n"
            "  3. Salve o arquivo\n\n"
            f"Chave em: https://openrouter.ai/settings/keys\n"
            f"Arquivo esperado: {env_path}\n\n"
            "O .env nao vai para o Git. Nao envie sua chave para ninguem.",
            file=sys.stderr,
        )
        return 1

    out_dir = ROOT / "meus-produtos" / args.slug / "entregas" / "paginas" / "assets"

    if args.output.strip():
        prompt_one = (args.prompt or "").strip()
        if not prompt_one:
            print("Com --output, use tambem --prompt com o texto da imagem.", file=sys.stderr)
            return 1
        raw_out = args.output.strip().replace("\\", "/")
        if ".." in raw_out or raw_out.startswith("/"):
            print("Caminho de --output invalido. Use so o nome do arquivo.", file=sys.stderr)
            return 1
        dest = out_dir / raw_out
        print(f"Modelo: {args.model}")
        print(f"Arquivo: {dest.relative_to(ROOT)}")
        print(f"Aspect: {args.aspect}")
        try:
            data_url = generate_one(
                api_key,
                args.model,
                prompt_one,
                aspect_ratio=args.aspect,
                image_size="1K",
            )
            _save_from_data_url(data_url, dest)
            print("Concluido.")
            return 0
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"ERRO HTTP {e.code}: {err_body[:500]}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"ERRO: {e}", file=sys.stderr)
            return 1

    skip = max(0, args.skip)
    if skip >= len(JOBS):
        print(f"Nada a gerar: --skip {skip} passa de todas as {len(JOBS)} imagens.", file=sys.stderr)
        return 1
    tail = JOBS[skip:]
    if args.max and args.max > 0:
        jobs = tail[: args.max]
    else:
        jobs = tail
    total_lista = len(JOBS)

    print(f"Modelo: {args.model}")
    print(f"Pasta: {out_dir}")
    print(f"Imagens nesta execucao: {len(jobs)}")

    for i, job in enumerate(jobs):
        dest = out_dir / job["file"]
        ar = job["aspect_ratio"]
        sz = job.get("image_size", "1K")
        n_global = skip + i + 1
        print(f"[{n_global}/{total_lista}] {job['file']} ({ar}) ...", flush=True)
        try:
            data_url = generate_one(
                api_key,
                args.model,
                job["prompt"],
                aspect_ratio=ar,
                image_size=sz,
            )
            _save_from_data_url(data_url, dest)
            print(f"      OK -> {dest.relative_to(ROOT)}", flush=True)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"      ERRO HTTP {e.code}: {err_body[:500]}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"      ERRO: {e}", file=sys.stderr)
            return 1
        if args.sleep and i < len(jobs) - 1:
            time.sleep(args.sleep)

    print("Concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
