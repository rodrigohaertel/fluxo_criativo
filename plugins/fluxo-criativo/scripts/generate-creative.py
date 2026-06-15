# -*- coding: utf-8 -*-
"""
Gerador hibrido de criativos: IA (visual) + HTML (layout) + Edge (screenshot).

Camada 1: gera elemento visual via OpenRouter (modelo escolhido pelo router)
Camada 2: compoe no template HTML com texto, cores e layout
Camada 3: exporta PNG via Edge/Chrome headless

Uso:
  py -3 scripts/generate-creative.py --config slides.json --slug planilhas-pro
  py -3 scripts/generate-creative.py --config slides.json --slug planilhas-pro --skip-ai  (usa imagens ja geradas)
  py -3 scripts/generate-creative.py --config slides.json --slug planilhas-pro --dry-run
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from openrouter_model_router import classify_prompt, MODELS, DEFAULT_MODEL

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TEMPLATE_DIR = ROOT / "scripts" / "creative-templates"

import platform

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

# Browsers por plataforma (Chrome primeiro: mais estavel em headless)
BROWSER_PATHS = [
    # Windows (Chrome antes de Edge)
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    # Mac
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
    # Linux
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium-browser"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/microsoft-edge"),
]


def load_env_file(path: Path) -> None:
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


def find_browser() -> Path | None:
    for p in BROWSER_PATHS:
        if p.exists():
            return p
    return None


# ─── Geracao de imagem via OpenRouter ────────────────────────────────

def _extract_image_data(result: dict[str, Any]) -> str | None:
    choices = result.get("choices") or []
    if not choices:
        return None
    message = choices[0].get("message") or {}
    # Campo images
    images = message.get("images")
    if images:
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
    # Campo content multipart
    content = message.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                iu = part.get("image_url", {})
                url = iu.get("url", "") if isinstance(iu, dict) else ""
                if url.startswith("data:image"):
                    return url
    return None


def _save_from_data_url(data_url: str, dest: Path) -> None:
    m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,(.+)", data_url, re.DOTALL)
    if not m:
        raise ValueError("URL de imagem inesperada")
    raw = base64.b64decode(m.group(2))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)


FREEPIK_URL = "https://api.freepik.com/v1/ai/text-to-image"

# Mapeamento aspect_ratio -> Freepik size
FREEPIK_SIZE_MAP = {
    "1:1": "square_1_1",
    "4:5": "portrait_4_5",
    "9:16": "portrait_9_16",
    "16:9": "landscape_16_9",
    "3:2": "landscape_3_2",
}


def generate_ai_image_openrouter(api_key: str, model_id: str, prompt: str, dest: Path,
                                 aspect_ratio: str = "1:1") -> bool:
    """Gera imagem via OpenRouter (chat/completions com modalities image)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/workshop_inteligente",
        "X-Title": "Workshop Marketing IA - Creative Gen",
    }
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
        "image_config": {"aspect_ratio": aspect_ratio, "image_size": "1K"},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8")
        result = json.loads(body)
        if result.get("error"):
            print(f"      ERRO API: {json.dumps(result['error'], ensure_ascii=False)[:300]}", file=sys.stderr)
            return False
        img_url = _extract_image_data(result)
        if not img_url:
            print(f"      ERRO: sem imagem na resposta", file=sys.stderr)
            return False
        _save_from_data_url(img_url, dest)
        return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"      ERRO HTTP {e.code}: {err_body[:300]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"      ERRO: {e}", file=sys.stderr)
        return False


def generate_ai_image_freepik(api_key: str, prompt: str, dest: Path,
                              aspect_ratio: str = "1:1") -> bool:
    """Gera imagem via Freepik AI."""
    freepik_size = FREEPIK_SIZE_MAP.get(aspect_ratio, "square_1_1")
    headers = {
        "x-freepik-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "num_images": 1,
        "image": {"size": freepik_size},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(FREEPIK_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8")
        result = json.loads(body)
        images = result.get("data", [])
        if not images:
            print(f"      ERRO Freepik: sem imagens na resposta", file=sys.stderr)
            return False
        first = images[0]
        img_b64 = first.get("base64", "")
        if img_b64:
            raw = base64.b64decode(img_b64)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            return True
        img_url = first.get("url", "")
        if img_url:
            img_req = urllib.request.Request(img_url)
            with urllib.request.urlopen(img_req, timeout=120) as r:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.read())
            return True
        print(f"      ERRO Freepik: formato desconhecido", file=sys.stderr)
        return False
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"      ERRO Freepik HTTP {e.code}: {err_body[:300]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"      ERRO Freepik: {e}", file=sys.stderr)
        return False


REPLICATE_BASE = "https://api.replicate.com/v1"

# Modelos Replicate por categoria
# Formato: owner/name (endpoint: /models/owner/name/predictions)
REPLICATE_MODELS = {
    # Imagem
    "photo": "black-forest-labs/flux-1.1-pro",
    "photo-max": "black-forest-labs/flux-2-pro",
    "fast": "google/imagen-4-fast",
    "quality": "google/imagen-4",
    "artistic": "recraft-ai/recraft-v4",
    "default": "black-forest-labs/flux-1.1-pro",
    # Video (text-to-video)
    "video": "kwaivgi/kling-v2.5-turbo-pro",
    "video-quality": "google/veo-3",
    "video-fast": "wan-video/wan-2.7-t2v",
    # Video (image-to-video)
    "i2v": "kwaivgi/kling-v2.6",
    "i2v-fast": "wan-video/wan-2.7-i2v",
    # Avatar (foto + audio = video falante)
    "avatar": "kwaivgi/kling-avatar-v2",
    # TTS (texto para audio)
    "tts": "jaaari/kokoro-82m:f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13",
}


def _replicate_predict(api_key: str, model: str, inputs: dict[str, Any],
                       timeout_secs: int = 120) -> dict[str, Any] | None:
    """Cria prediction no Replicate e aguarda resultado.

    Usa Prefer: wait (sincrono ate 60s), depois polling se necessario.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "wait=60",
    }

    # Se model contem ":" e um hash, usar endpoint generico com version
    # Senao, tentar /models/ primeiro, fallback para generico
    if ":" in model:
        # Formato owner/name:version_hash
        url = f"{REPLICATE_BASE}/predictions"
        version = model.split(":")[-1]
        payload = {"version": version, "input": inputs}
    else:
        url = f"{REPLICATE_BASE}/models/{model}/predictions"
        payload = {"input": inputs}

    use_generic = False

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        # Retry com backoff para rate limit (429) e fallback para 404
        result = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    result = json.loads(resp.read().decode())
                break
            except urllib.error.HTTPError as e:
                if e.code == 404 and not use_generic:
                    # Fallback: modelos community usam /predictions com "version"
                    use_generic = True
                    url = f"{REPLICATE_BASE}/predictions"
                    # Remover "model" se existir, adicionar "version" como o model completo
                    payload.pop("model", None)
                    payload["version"] = model  # owner/name vira version (Replicate resolve)
                    data = json.dumps(payload).encode("utf-8")
                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    continue
                if e.code == 429 and attempt < 3:
                    retry_after = int(e.headers.get("Retry-After", "5"))
                    wait = max(retry_after, 3) * (attempt + 1)
                    print(f"      Rate limit. Aguardando {wait}s (tentativa {attempt + 2}/4)...", flush=True)
                    time.sleep(wait)
                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    continue
                raise
        if result is None:
            print(f"      ERRO Replicate: falhou apos 4 tentativas", file=sys.stderr)
            return None

        # Se Prefer: wait retornou resultado completo
        if result.get("status") == "succeeded":
            return result

        # Senao, polling
        poll_url = result.get("urls", {}).get("get", "")
        if not poll_url:
            print(f"      ERRO Replicate: sem URL de polling", file=sys.stderr)
            return None

        elapsed = 0
        while elapsed < timeout_secs:
            time.sleep(3)
            elapsed += 3
            poll_req = urllib.request.Request(poll_url, headers={"Authorization": f"Bearer {api_key}"})
            with urllib.request.urlopen(poll_req, timeout=15) as resp:
                status = json.loads(resp.read().decode())

            state = status.get("status", "")
            if state == "succeeded":
                return status
            elif state in ("failed", "canceled"):
                err = status.get("error", state)
                print(f"      ERRO Replicate: {err}", file=sys.stderr)
                return None

        print(f"      ERRO Replicate: timeout ({timeout_secs}s)", file=sys.stderr)
        return None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"      ERRO Replicate HTTP {e.code}: {err_body[:300]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"      ERRO Replicate: {e}", file=sys.stderr)
        return None


def _download_url(url: str, dest: Path) -> bool:
    """Baixa arquivo de URL para destino."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=120) as r:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"      ERRO download: {e}", file=sys.stderr)
        return False


def generate_ai_image_replicate(api_key: str, prompt: str, dest: Path,
                                aspect_ratio: str = "1:1",
                                replicate_model: str = "") -> bool:
    """Gera imagem via Replicate."""
    model = replicate_model or REPLICATE_MODELS["default"]
    inputs = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
    }
    result = _replicate_predict(api_key, model, inputs)
    if not result:
        return False

    output = result.get("output")
    img_url = output[0] if isinstance(output, list) else output
    if isinstance(img_url, str) and img_url.startswith("http"):
        return _download_url(img_url, dest)
    print(f"      ERRO Replicate: output inesperado: {str(output)[:200]}", file=sys.stderr)
    return False


def _file_to_data_uri(file_path: str | Path) -> str:
    """Converte arquivo local para data URI base64."""
    p = Path(file_path)
    raw = p.read_bytes()
    b64 = base64.b64encode(raw).decode()
    ext = p.suffix.lstrip(".").lower()
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "webp": "image/webp", "gif": "image/gif",
        "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
        "ogg": "audio/ogg", "aac": "audio/aac",
        "mp4": "video/mp4", "webm": "video/webm",
    }
    mime = mime_map.get(ext, f"application/octet-stream")
    return f"data:{mime};base64,{b64}"


def generate_video_replicate(api_key: str, prompt: str, dest: Path,
                             replicate_model: str = "",
                             image_path: str = "") -> bool:
    """Gera video via Replicate (text-to-video ou image-to-video).

    Se image_path for passado, usa image-to-video. Senao, text-to-video.
    """
    if image_path:
        model = replicate_model or REPLICATE_MODELS["i2v"]
        inputs = {
            "prompt": prompt,
            "image": _file_to_data_uri(image_path),
        }
    else:
        model = replicate_model or REPLICATE_MODELS["video"]
        inputs = {"prompt": prompt}

    result = _replicate_predict(api_key, model, inputs, timeout_secs=300)
    if not result:
        return False

    output = result.get("output")
    video_url = output[0] if isinstance(output, list) else output
    if isinstance(video_url, str) and video_url.startswith("http"):
        return _download_url(video_url, dest)
    print(f"      ERRO Replicate video: output inesperado: {str(output)[:200]}", file=sys.stderr)
    return False


def generate_avatar_video_replicate(api_key: str, image_path: str, audio_path: str,
                                    dest: Path, replicate_model: str = "") -> bool:
    """Gera video de avatar falante via Replicate (foto + audio = video com lip sync).

    Modelos suportados:
      kwaivgi/kling-avatar-v2 (padrao, melhor lip sync)

    Inputs:
      image_path: foto do expert (frente, rosto visivel)
      audio_path: audio gravado (mp3, wav, m4a)
    """
    model = replicate_model or "kwaivgi/kling-avatar-v2"

    inputs = {
        "image": _file_to_data_uri(image_path),
        "audio": _file_to_data_uri(audio_path),
    }

    print(f"      Avatar: {model}", flush=True)
    print(f"      Foto: {Path(image_path).name}", flush=True)
    print(f"      Audio: {Path(audio_path).name}", flush=True)

    result = _replicate_predict(api_key, model, inputs, timeout_secs=600)
    if not result:
        return False

    output = result.get("output")
    video_url = output[0] if isinstance(output, list) else output
    if isinstance(video_url, str) and video_url.startswith("http"):
        return _download_url(video_url, dest)
    print(f"      ERRO Avatar: output inesperado: {str(output)[:200]}", file=sys.stderr)
    return False


def generate_tts_replicate(api_key: str, text: str, dest: Path,
                           voice: str = "pf_dora",
                           replicate_model: str = "") -> bool:
    """Gera audio de voz a partir de texto via Replicate (Kokoro TTS).

    Vozes disponiveis para portugues:
      pf_dora (feminina, natural)
      pm_alex (masculina)
      pm_santa (masculina, grave)
      pf_jenny (feminina, clara)

    Retorna True se o audio foi salvo com sucesso.
    """
    model = replicate_model or REPLICATE_MODELS["tts"]
    inputs = {
        "text": text,
        "voice": voice,
        "speed": 1.0,
        "lang_code": "p",
    }

    print(f"      TTS: {model} (voz: {voice})", flush=True)

    result = _replicate_predict(api_key, model, inputs, timeout_secs=120)
    if not result:
        return False

    output = result.get("output")
    audio_url = output if isinstance(output, str) else (output[0] if isinstance(output, list) else None)
    if isinstance(audio_url, str) and audio_url.startswith("http"):
        return _download_url(audio_url, dest)
    print(f"      ERRO TTS: output inesperado: {str(output)[:200]}", file=sys.stderr)
    return False


def generate_full_avatar_pipeline(api_key: str, text: str, image_path: str,
                                  dest: Path, voice: str = "pf_dora",
                                  tts_model: str = "", avatar_model: str = "") -> bool:
    """Pipeline completo: texto → TTS → avatar video.

    1. Converte texto em audio via Kokoro TTS
    2. Envia foto + audio para Kling Avatar V2
    3. Salva video final

    Ideal para gerar anuncio em video sem gravar audio manualmente.
    """
    # Pasta temporaria para o audio
    audio_dest = dest.parent / f".tts-{dest.stem}.wav"

    print("=== Pipeline: Texto > Audio > Video ===\n", flush=True)

    # Passo 1: TTS
    print("[1/2] Gerando audio...", flush=True)
    ok = generate_tts_replicate(api_key, text, audio_dest, voice=voice, replicate_model=tts_model)
    if not ok:
        print("      Pipeline falhou no TTS.", file=sys.stderr)
        return False
    print(f"      Audio: {audio_dest.name}\n", flush=True)

    # Passo 2: Avatar
    print("[2/2] Gerando video com avatar...", flush=True)
    ok = generate_avatar_video_replicate(api_key, image_path, str(audio_dest), dest, avatar_model)

    # Limpar audio temporario
    audio_dest.unlink(missing_ok=True)

    if ok:
        print(f"\n      Video salvo: {dest}", flush=True)
    return ok


def generate_ai_image(prompt: str, dest: Path, aspect_ratio: str = "1:1",
                      model_id: str = "", provider: str = "auto") -> bool:
    """Gera imagem usando o provider disponivel.

    provider: "auto" (detecta pelo .env), "openrouter", "freepik", "replicate"
    Ordem auto: OpenRouter > Replicate > Freepik
    """
    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    fp_key = os.environ.get("FREEPIK_API_KEY", "").strip()
    rp_key = os.environ.get("REPLICATE_API_TOKEN", "").strip()

    # Para Replicate: so usa model_id se for um modelo Replicate valido (owner/name)
    # Ignora IDs do OpenRouter (google/gemini-*, openai/gpt-*)
    rp_model = ""
    if model_id and "/" in model_id and not model_id.startswith(("google/gemini", "openai/gpt")):
        rp_model = model_id

    if provider == "freepik" and fp_key:
        return generate_ai_image_freepik(fp_key, prompt, dest, aspect_ratio)
    elif provider == "openrouter" and or_key:
        return generate_ai_image_openrouter(or_key, model_id, prompt, dest, aspect_ratio)
    elif provider == "replicate" and rp_key:
        return generate_ai_image_replicate(rp_key, prompt, dest, aspect_ratio, replicate_model=rp_model)
    elif provider == "auto":
        if or_key:
            return generate_ai_image_openrouter(or_key, model_id, prompt, dest, aspect_ratio)
        elif rp_key:
            print(f"      (usando Replicate)", flush=True)
            return generate_ai_image_replicate(rp_key, prompt, dest, aspect_ratio)
        elif fp_key:
            print(f"      (usando Freepik)", flush=True)
            return generate_ai_image_freepik(fp_key, prompt, dest, aspect_ratio)

    print(f"      ERRO: nenhuma API configurada (OPENROUTER_API_KEY, REPLICATE_API_TOKEN ou FREEPIK_API_KEY)", file=sys.stderr)
    return False


# ─── Composicao HTML ─────────────────────────────────────────────────

def build_slide_html(template: str, slide: dict[str, Any],
                     slide_num: int, total: int, bg_path: str,
                     global_config: dict[str, Any] | None = None) -> str:
    """Substitui placeholders no template HTML."""
    theme = slide.get("theme", "theme-dark")
    layout = slide.get("layout", "layout-conteudo")
    progress = round((slide_num / total) * 100)

    # Monta o conteudo HTML baseado no layout
    content_html = build_content_html(slide, layout)

    width = slide.get("width", 1080)
    height = slide.get("height", 1080)

    html = template
    html = html.replace("{{THEME}}", theme)
    html = html.replace("{{LAYOUT}}", layout)
    html = html.replace("{{CONTENT}}", content_html)
    html = html.replace("{{SLIDE_NUM}}", str(slide_num))
    html = html.replace("{{TOTAL}}", str(total))
    html = html.replace("{{PROGRESS}}", str(progress))
    html = html.replace("{{WIDTH}}", str(width))
    html = html.replace("{{HEIGHT}}", str(height))

    # Remover tag <img> quando nao tem background (evita erro no browser)
    if bg_path:
        html = html.replace("{{BG_IMAGE}}", bg_path)
    else:
        html = re.sub(r'<img[^>]*\{\{BG_IMAGE\}\}[^>]*/?\s*>', '', html)

    # Injetar CSS variables para tema custom (cores do produto)
    custom_colors = slide.get("colors", {})
    if not custom_colors and global_config:
        custom_colors = global_config.get("colors", {})
    if custom_colors and "theme-custom" in theme:
        css_vars = []
        for key, val in custom_colors.items():
            css_vars.append(f"--{key}: {val};")
        vars_css = " ".join(css_vars)
        html = html.replace(
            '<div class="slide',
            f'<div style="{vars_css}" class="slide'
        )

    return html


def _fmt(text: str) -> str:
    """Converte **bold** para accent span e \\n para <br>."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<span class="accent">\1</span>', text)
    text = text.replace("\\n", "<br>").replace("\n", "<br>")
    return text


def build_content_html(slide: dict[str, Any], layout: str) -> str:
    """Gera o HTML do conteudo baseado no tipo de layout."""
    parts: list[str] = []

    if layout == "layout-evento":
        # Layout para captura de evento: foto do expert, data grande, nome, detalhes, CTA
        expert_photo = slide.get("expert_photo", "")
        event_name = slide.get("event_name", "")
        event_date = slide.get("event_date", "")
        details = slide.get("details", "")
        cta_text = slide.get("cta_text", "Quero participar")
        if expert_photo:
            photo_path = Path(expert_photo)
            if photo_path.exists():
                parts.append(f'<img class="expert-photo" src="{photo_path.as_uri()}" alt="">')
            else:
                parts.append(f'<img class="expert-photo" src="{expert_photo}" alt="" onerror="this.style.display=\'none\'">')
        parts.append(f'<div class="event-name">{_fmt(event_name)}</div>')
        parts.append(f'<div class="event-date accent">{_fmt(event_date)}</div>')
        if details:
            parts.append(f'<div class="event-details">{_fmt(details)}</div>')
        parts.append(f'<div class="cta-button">{cta_text}</div>')

    elif layout == "layout-gancho":
        headline = slide.get("headline", "")
        subtitle = slide.get("subtitle", "")
        parts.append(f'<h1 class="headline">{_fmt(headline)}</h1>')
        if subtitle:
            parts.append(f'<p class="subtitle">{_fmt(subtitle)}</p>')

    elif layout == "layout-conteudo":
        headline = slide.get("headline", "")
        body = slide.get("body", "")
        parts.append(f'<h2 class="headline">{_fmt(headline)}</h2>')
        if body:
            parts.append(f'<p class="body-text">{_fmt(body)}</p>')

    elif layout == "layout-dado":
        number = slide.get("number", "")
        headline = slide.get("headline", "")
        parts.append(f'<div class="big-number accent">{_fmt(number)}</div>')
        parts.append(f'<h2 class="headline">{_fmt(headline)}</h2>')

    elif layout == "layout-checklist":
        headline = slide.get("headline", "")
        items = slide.get("items", [])
        parts.append(f'<h2 class="headline">{_fmt(headline)}</h2>')
        for item in items:
            parts.append(f'<div class="check-item">{_fmt(item)}</div>')

    elif layout == "layout-cta":
        headline = slide.get("headline", "")
        cta_text = slide.get("cta_text", "Seguir")
        social = slide.get("social_text", "")
        parts.append(f'<h2 class="headline">{_fmt(headline)}</h2>')
        parts.append(f'<div class="cta-button">{cta_text}</div>')
        if social:
            parts.append(f'<div class="social-icons">{social}</div>')

    elif layout == "layout-comparacao":
        left_label = slide.get("left_label", "ERRADO")
        left_text = slide.get("left_text", "")
        right_label = slide.get("right_label", "CERTO")
        right_text = slide.get("right_text", "")
        parts.append(
            f'<div class="col col-wrong">'
            f'  <div class="col-label accent">{left_label}</div>'
            f'  <div class="col-text">{left_text}</div>'
            f'</div>'
            f'<div class="col col-right">'
            f'  <div class="col-label accent">{right_label}</div>'
            f'  <div class="col-text">{right_text}</div>'
            f'</div>'
        )

    return "\n    ".join(parts)


# ─── Screenshot via Edge/Chrome ──────────────────────────────────────

def screenshot_html(browser: Path, html_path: Path, output_path: Path,
                    width: int = 1080, height: int = 1080) -> bool:
    """Usa Edge/Chrome headless para capturar screenshot do HTML.

    Compativel com Windows, Mac e Linux.
    Usa janela ligeiramente maior (+50px) para evitar gutter de scrollbar do
    Chrome no Windows, depois recorta o PNG para as dimensoes exatas.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Margem extra só na largura para acomodar o gutter de scrollbar
    # (~17px reservado pelo Chrome no Windows para barra vertical).
    # Altura não precisa de gutter: o --screenshot captura o documento
    # na altura exata e não reserva espaço para scrollbar horizontal.
    GUTTER = 50
    win_w = width + GUTTER
    win_h = height

    # Caminho do screenshot: nativo no Windows, posix no resto
    if IS_WINDOWS:
        screenshot_path = str(output_path.resolve()).replace("/", "\\")
    else:
        screenshot_path = str(output_path.resolve())

    file_url = html_path.as_uri()

    cmd = [
        str(browser),
        "--headless",
        f"--screenshot={screenshot_path}",
        f"--window-size={win_w},{win_h}",
        "--hide-scrollbars",
        "--disable-gpu",
        "--no-sandbox",
        "--force-device-scale-factor=1",
        file_url,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, timeout=30,
            cwd=str(output_path.parent.resolve()),
        )
        if not (output_path.exists() and output_path.stat().st_size > 0):
            stderr = result.stderr.decode("utf-8", errors="replace")
            if stderr.strip():
                print(f"      STDERR: {stderr[:200]}", file=sys.stderr)
            return False

        # Recortar para dimensoes exatas (remove gutter e qualquer sobra)
        try:
            from PIL import Image as PilImage
            img = PilImage.open(output_path)
            img_w, img_h = img.size
            if img_w != width or img_h != height:
                crop_w = min(width, img_w)
                crop_h = min(height, img_h)
                img = img.crop((0, 0, crop_w, crop_h))
                img.save(output_path, "PNG")
        except ImportError:
            pass  # Pillow nao instalado, mantém o arquivo original
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"      ERRO screenshot: {e}", file=sys.stderr)
        return False


# ─── Orquestrador principal ──────────────────────────────────────────

def process_slides(config: dict[str, Any], slug: str, skip_ai: bool = False,
                   dry_run: bool = False, force_model: str = "",
                   provider: str = "auto") -> int:
    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    fp_key = os.environ.get("FREEPIK_API_KEY", "").strip()
    if not or_key and not fp_key and not skip_ai and not dry_run:
        print("Nenhuma API configurada. Defina OPENROUTER_API_KEY ou FREEPIK_API_KEY no .env", file=sys.stderr)
        return 1

    browser = find_browser()
    if not browser and not dry_run:
        print("Edge ou Chrome nao encontrado. Necessario para exportar PNG.", file=sys.stderr)
        return 1

    # Carregar template
    template_name = config.get("template", "carrossel-slide.html")
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        print(f"Template nao encontrado: {template_path}", file=sys.stderr)
        return 1
    template_html = template_path.read_text(encoding="utf-8")

    slides = config.get("slides", [])
    total = len(slides)
    out_dir = ROOT / "meus-produtos" / slug / "entregas" / "anuncios"
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="creative-"))

    print(f"Slides: {total}")
    print(f"Saida: {out_dir}")
    if browser:
        print(f"Browser: {browser.name}")
    print()

    if dry_run:
        for i, slide in enumerate(slides, 1):
            ai_prompt = slide.get("ai_prompt", "")
            if ai_prompt:
                result = classify_prompt(ai_prompt)
                model_name = result["model_id"]
                cat = result["category"]
            else:
                model_name = "(sem IA)"
                cat = "none"
            print(f"  [{i}/{total}] {slide.get('output', '?')} | {model_name} ({cat}) | {slide.get('layout', '?')}")
        print("\n(dry-run: nenhuma imagem gerada)")
        return 0

    # Pasta persistente para backgrounds IA (reutilizavel com --skip-ai)
    bg_dir = out_dir / ".backgrounds"
    bg_dir.mkdir(parents=True, exist_ok=True)

    errors = 0
    for i, slide in enumerate(slides, 1):
        output_name = slide.get("output", f"slide-{i}.png")
        output_path = out_dir / output_name
        ai_prompt = slide.get("ai_prompt", "")
        bg_path = ""

        print(f"[{i}/{total}] {output_name}", flush=True)

        # Camada 1: gerar imagem IA (se tiver prompt)
        if ai_prompt:
            bg_file = bg_dir / f"bg-{output_name}"

            if skip_ai and bg_file.exists():
                # Reutiliza background salvo anteriormente
                bg_path = bg_file.as_uri()
                print(f"      IA: reutilizada ({bg_file.name})", flush=True)
            elif not skip_ai:
                if force_model:
                    model_id = force_model
                else:
                    result = classify_prompt(ai_prompt)
                    model_id = result["model_id"]

                aspect = slide.get("aspect_ratio", "1:1")
                print(f"      IA: {model_id} ...", flush=True)

                ok = generate_ai_image(ai_prompt, bg_file, aspect, model_id=model_id, provider=provider)
                if ok:
                    bg_path = bg_file.as_uri()
                    print(f"      IA: OK", flush=True)
                else:
                    print(f"      IA: falhou, seguindo sem background", flush=True)
            else:
                print(f"      IA: pulada (sem cache anterior)", flush=True)

        # Camada 2: montar HTML (salva na pasta de saida para evitar problemas com temp)
        slide_html = build_slide_html(template_html, slide, i, total, bg_path, config)
        html_file = out_dir / f".tmp-slide-{i}.html"
        html_file.write_text(slide_html, encoding="utf-8")

        # Camada 3: screenshot
        width = slide.get("width", 1080)
        height = slide.get("height", 1080)
        ok = screenshot_html(browser, html_file, output_path, width, height)
        if ok:
            print(f"      PNG: OK -> {output_path.relative_to(ROOT)}", flush=True)
        else:
            print(f"      PNG: FALHOU", file=sys.stderr)
            errors += 1

        if i < total:
            # Replicate free tier: 6 req/min. Esperar mais entre slides.
            wait = 10.0 if provider == "replicate" else 1.0
            time.sleep(wait)

    # Limpar temp e HTMLs temporarios (backgrounds persistem em .backgrounds/)
    shutil.rmtree(temp_dir, ignore_errors=True)
    for f in out_dir.glob(".tmp-slide-*.html"):
        f.unlink(missing_ok=True)

    print()
    if errors:
        print(f"Concluido com {errors} erro(s). {total - errors}/{total} imagens salvas.")
    else:
        print(f"Concluido. {total} imagens salvas em {out_dir.relative_to(ROOT)}")
    return 1 if errors else 0


def main() -> int:
    load_env_file(ROOT / ".env")

    ap = argparse.ArgumentParser(description="Gerador hibrido de criativos (IA + HTML + Screenshot)")
    ap.add_argument("--config", required=True, help="Arquivo JSON com definicao dos slides")
    ap.add_argument("--slug", default="", help="Pasta em meus-produtos/{slug}")
    ap.add_argument("--force-model", default="", help="Forca um modelo especifico (ignora router)")
    ap.add_argument("--provider", default="auto", choices=["auto", "openrouter", "freepik", "replicate"],
                    help="Provider de imagem: auto (detecta .env), openrouter, replicate, freepik")
    ap.add_argument("--skip-ai", action="store_true", help="Pula geracao IA (usa backgrounds existentes)")
    ap.add_argument("--dry-run", action="store_true", help="Mostra o que faria sem executar")
    args = ap.parse_args()

    if not args.slug:
        ativo_file = ROOT / "meus-produtos" / ".ativo"
        if ativo_file.exists():
            args.slug = ativo_file.read_text(encoding="utf-8").strip()
        else:
            print("Informe --slug ou crie meus-produtos/.ativo", file=sys.stderr)
            return 1

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    if not config_path.exists():
        print(f"Config nao encontrado: {config_path}", file=sys.stderr)
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))

    return process_slides(config, args.slug, skip_ai=args.skip_ai,
                          dry_run=args.dry_run, force_model=args.force_model,
                          provider=args.provider)


if __name__ == "__main__":
    raise SystemExit(main())
