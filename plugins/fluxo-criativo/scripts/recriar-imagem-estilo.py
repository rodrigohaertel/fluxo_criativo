# -*- coding: utf-8 -*-
"""
Recria uma imagem mantendo o estilo visual de uma referencia e substituindo o personagem.

Envia duas imagens para o Gemini via OpenRouter e solicita a combinacao:
  - Imagem 1: referencia de estilo (fundo, iluminacao, composicao)
  - Imagem 2: foto do personagem (rosto, cabelo, feicoes)

Uso:
  py -3 scripts/recriar-imagem-estilo.py --referencia caminho/estilo.jpg --foto caminho/pessoa.jpg
  py -3 scripts/recriar-imagem-estilo.py --referencia ref.jpg --foto foto.jpg --saida saida.png
  py -3 scripts/recriar-imagem-estilo.py --referencia ref.jpg --foto foto.jpg --modelo google/gemini-2.0-flash-exp:free
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELOS_SUPORTADOS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-2.5-flash-preview-05-20",
    "google/gemini-2.5-flash-image",
]


def carregar_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, _, val = s.partition("=")
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val


def imagem_para_data_uri(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower()

    # AVIF e formatos menos suportados: converter para JPEG via Pillow
    if ext in ("avif", "heic", "heif", "tiff", "bmp"):
        try:
            from PIL import Image as PilImage
            import io
            img = PilImage.open(path).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            raw = buf.getvalue()
            return f"data:image/jpeg;base64,{base64.b64encode(raw).decode()}"
        except Exception as e:
            print(f"  Aviso: conversao {ext.upper()} falhou ({e}). Enviando como raw.", flush=True)

    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode()
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "avif": "image/avif",
    }
    mime = mime_map.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def extrair_imagem_da_resposta(result: dict) -> str | None:
    choices = result.get("choices") or []
    if not choices:
        return None

    message = choices[0].get("message") or {}

    # Campo images (formato Gemini via OpenRouter)
    images = message.get("images") or []
    if images:
        first = images[0]
        if isinstance(first, dict):
            iu = first.get("image_url") or first.get("imageUrl")
            if isinstance(iu, dict):
                url = iu.get("url", "")
            elif isinstance(iu, str):
                url = iu
            else:
                url = ""
            if url.startswith("data:image"):
                return url

    # Campo content multipart
    content = message.get("content") or []
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                iu = part.get("image_url", {})
                url = iu.get("url", "") if isinstance(iu, dict) else ""
                if url.startswith("data:image"):
                    return url

    # Fallback: content como string (texto com data URI inline)
    if isinstance(content, str) and "data:image" in content:
        match = re.search(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", content)
        if match:
            return match.group(0)

    return None


def gerar_imagem(api_key: str, modelo: str, referencia: Path, foto: Path,
                 saida: Path, proporcao: str = "2:3") -> bool:

    print(f"  Modelo: {modelo}")
    print(f"  Proporcao: {proporcao}")
    print(f"  Convertendo imagens para base64...", flush=True)

    ref_uri = imagem_para_data_uri(referencia)
    foto_uri = imagem_para_data_uri(foto)

    instrucao = (
        "You are an AI image editor. I will provide two reference images.\n\n"
        "IMAGE 1 — STYLE REFERENCE:\n"
        "This defines the visual style of the output:\n"
        "- Background: smooth orange-to-pink gradient (warm tones, vibrant)\n"
        "- Lighting: cinematic, with cool blue/teal tones on the subject contrasting with the warm background\n"
        "- Composition: portrait framing, subject slightly off-center, dramatic low-key mood\n"
        "- Overall feel: high-end editorial photography\n\n"
        "IMAGE 2 — PERSON REFERENCE:\n"
        "This is the person who must appear in the output image.\n"
        "Faithfully reproduce their face, hair (curly brown), beard, and general physical appearance.\n\n"
        "OUTPUT REQUIREMENTS:\n"
        "1. Recreate the exact visual style from Image 1 (gradient background, color grading, lighting setup)\n"
        "2. The person must be from Image 2 (their face and features, not the person in Image 1)\n"
        "3. Pose: the person looks upward and slightly to the side, with a calm, aspirational, introspective expression\n"
        "4. Outfit: dark jacket or coat with a high collar (similar to Image 1)\n"
        "5. Photo quality: high-resolution, professional editorial portrait\n\n"
        "Generate a single portrait image combining these two references."
    )

    payload: dict = {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instrucao},
                    {"type": "image_url", "image_url": {"url": ref_uri}},
                    {"type": "image_url", "image_url": {"url": foto_uri}},
                ],
            }
        ],
        "modalities": ["image", "text"],
        "image_config": {"aspect_ratio": proporcao, "image_size": "1K"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/workshop_inteligente",
        "X-Title": "Workshop Marketing IA",
    }

    print(f"  Enviando para OpenRouter...", flush=True)

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8")

    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"\nERRO HTTP {e.code}: {err[:500]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\nERRO na requisicao: {e}", file=sys.stderr)
        return False

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        print(f"\nERRO: resposta invalida da API:\n{body[:400]}", file=sys.stderr)
        return False

    if result.get("error"):
        err = result["error"]
        print(f"\nERRO da API: {json.dumps(err, ensure_ascii=False)[:400]}", file=sys.stderr)
        return False

    img_url = extrair_imagem_da_resposta(result)
    if not img_url:
        # Mostrar resposta para debug
        print(f"\nERRO: imagem nao encontrada na resposta.", file=sys.stderr)
        print(f"Resposta bruta (primeiros 800 chars):\n{body[:800]}", file=sys.stderr)
        return False

    # Decodificar e salvar
    m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,(.+)", img_url, re.DOTALL)
    if not m:
        print("\nERRO: formato de data URI desconhecido.", file=sys.stderr)
        return False

    raw = base64.b64decode(m.group(2))
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_bytes(raw)
    return True


def main() -> int:
    carregar_env()

    ap = argparse.ArgumentParser(
        description="Recria imagem mantendo estilo de referencia e trocando o personagem"
    )
    ap.add_argument("--referencia", required=True, help="Imagem de referencia de estilo (.jpg/.png)")
    ap.add_argument("--foto", required=True, help="Foto do personagem a inserir (.jpg/.png)")
    ap.add_argument("--saida", default="", help="Caminho de saida (.png). Padrao: entregas/criativos/")
    ap.add_argument(
        "--modelo",
        default="google/gemini-2.0-flash-exp:free",
        help=f"Modelo OpenRouter. Opcoes: {', '.join(MODELOS_SUPORTADOS)}",
    )
    ap.add_argument(
        "--proporcao",
        default="2:3",
        choices=["1:1", "2:3", "9:16", "3:2", "16:9"],
        help="Proporcao da imagem gerada (padrao: 2:3 para retrato)",
    )
    args = ap.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("ERRO: OPENROUTER_API_KEY nao encontrada no .env", file=sys.stderr)
        return 1

    referencia = Path(args.referencia)
    foto = Path(args.foto)

    if not referencia.exists():
        print(f"ERRO: arquivo nao encontrado: {referencia}", file=sys.stderr)
        return 1
    if not foto.exists():
        print(f"ERRO: arquivo nao encontrado: {foto}", file=sys.stderr)
        return 1

    # Definir saida
    if args.saida:
        saida = Path(args.saida)
    else:
        ativo_file = ROOT / "meus-produtos" / ".ativo"
        slug = ativo_file.read_text(encoding="utf-8").strip() if ativo_file.exists() else "produto"
        saida = ROOT / "meus-produtos" / slug / "entregas" / "criativos" / "imagem-estilo-recriada.png"

    print("=" * 55)
    print("Recriando imagem com novo personagem")
    print("=" * 55)
    print(f"  Referencia de estilo: {referencia.name}")
    print(f"  Foto do personagem:   {foto.name}")
    print(f"  Saida:                {saida}")
    print()

    ok = gerar_imagem(api_key, args.modelo, referencia, foto, saida, args.proporcao)

    if ok:
        print(f"\nConcluido. Imagem salva em:\n  {saida}")
        return 0
    else:
        print("\nFalhou. Verifique os erros acima.")
        print("\nDica: tente outro modelo com --modelo google/gemini-2.5-flash-preview-05-20")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
