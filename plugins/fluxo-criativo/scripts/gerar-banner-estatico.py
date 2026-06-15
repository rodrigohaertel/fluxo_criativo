# -*- coding: utf-8 -*-
"""
Banner Estático para Instagram (1080x1350px, portrait 4:5).

Pipeline:
  1. Gera foto cinematográfica via OpenRouter
  2. Renderiza banner-estatico.html com foto full-bleed + gradiente + texto
  3. Screenshot 1080x1350 via Chrome/Edge headless
  4. Salva PNG em output_dir

Uso (na raiz do projeto):
  py -3 scripts/gerar-banner-estatico.py --config config-banner.json
  py -3 scripts/gerar-banner-estatico.py --config config-banner.json --skip-ai

Schema do config-banner.json:
{
  "slug":        "slug-do-produto",
  "handle":      "@seuhandle",
  "output_dir":  "meus-produtos/slug/entregas/criativos",
  "filename":    "banner-01",
  "accent":      "#FF6B01",
  "credit":      "Nome do produto ou tagline curta",
  "headline":    "HEADLINE EM CAIXA ALTA",
  "headline_highlight": "PALAVRA",
  "subheadline": "Subtítulo em estilo pôster",
  "prompt_en":   "Epic cinematic scene..."
}
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).parent / "creative-templates" / "banner-estatico.html"

IS_WINDOWS = platform.system() == "Windows"

BROWSER_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium-browser"),
    Path("/usr/bin/chromium"),
]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_MODEL       = "google/gemini-3.1-flash-image-preview"

# Sufixo cinematográfico específico para banner estático (mais pesado que carrossel)
BANNER_PHOTO_SUFFIX = (
    ", epic cinematic movie poster photography, photorealistic, "
    "85mm telephoto lens, hero shot, low angle slightly upward tilt, "
    "strong warm golden-orange rim backlight from upper right, "
    "cool blue-purple atmospheric fill from left, cinematic halo effect, "
    "teal shadows and warm golden highlights, high contrast Hollywood color grade, "
    "volumetric clouds and dramatic sky in background, "
    "ultra detailed, hyper realistic, 8K resolution, "
    "no text, no watermark, no logo, no letters, "
    "anatomically correct, no distorted limbs, no distorted fingers"
)


# ── env ────────────────────────────────────────────────────────────────

def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        if k and k not in os.environ:
            os.environ[k] = v


# ── browser ────────────────────────────────────────────────────────────

def find_browser() -> Path | None:
    for p in BROWSER_PATHS:
        if p.exists():
            return p
    return None


# ── API helpers ────────────────────────────────────────────────────────

def _post(url: str, headers: dict, payload: dict, timeout: int = 300) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={**headers, "Content-Length": str(len(data))},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _save_data_url(data_url: str, dest: Path) -> None:
    m = re.match(r"data:image/[^;]+;base64,(.+)", data_url, re.DOTALL)
    if not m:
        raise ValueError("data URL inesperado")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode(m.group(1)))


def _extract_img(result: dict) -> str | None:
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


# ── geração de foto ────────────────────────────────────────────────────


def gerar_foto_openrouter(api_key: str, prompt: str, dest: Path,
                          ref_layout: Path | None = None,
                          ref_personagem: Path | None = None) -> bool:
    tem_ref = ref_layout and ref_layout.exists()
    print(f"   OpenRouter ({OR_MODEL}){' + referência' if tem_ref else ''}...", flush=True)

    if tem_ref:
        # Modo multimodal: imagem de referência como input visual
        full_prompt = prompt  # sufixo já vai no prompt de referência
        content: list = []
        content.append({"type": "image_url", "image_url": {"url": _foto_data_uri(ref_layout)}})
        if ref_personagem and ref_personagem.exists():
            content.append({"type": "image_url", "image_url": {"url": _foto_data_uri(ref_personagem)}})
        content.append({"type": "text", "text": full_prompt})
    else:
        full_prompt = prompt.rstrip() + BANNER_PHOTO_SUFFIX
        content = full_prompt

    try:
        result = _post(
            OPENROUTER_URL,
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://workshop.inteligente",
                "X-Title":      "Workshop Marketing IA",
            },
            {
                "model":      OR_MODEL,
                "messages":   [{"role": "user", "content": content}],
                "modalities": ["image", "text"],
            },
        )
        if result.get("error"):
            print(f"   ERRO OpenRouter: {str(result['error'])[:200]}", file=sys.stderr)
            return False
        url = _extract_img(result)
        if not url:
            print("   ERRO OpenRouter: sem imagem na resposta", file=sys.stderr)
            return False
        _save_data_url(url, dest)
        return True
    except urllib.error.HTTPError as e:
        print(f"   ERRO HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"   ERRO OpenRouter: {e}", file=sys.stderr)
        return False


def gerar_foto(prompt: str, dest: Path,
               ref_layout: Path | None = None,
               ref_personagem: Path | None = None) -> bool:
    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not or_key:
        print("   ERRO: configure OPENROUTER_API_KEY no .env", file=sys.stderr)
        return False
    return gerar_foto_openrouter(or_key, prompt, dest, ref_layout, ref_personagem)


# ── HTML ────────────────────────────────────────────────────────────────

def _foto_data_uri(path: Path) -> str:
    ext  = path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _headline_html(headline: str, highlight_word: str) -> str:
    if not highlight_word:
        return headline
    words  = headline.split()
    parts  = []
    hl_up  = highlight_word.upper()
    for w in words:
        clean = re.sub(r"[^\w]", "", w).upper()
        if clean == hl_up:
            parts.append(f'<span class="hl">{w}</span>')
        else:
            parts.append(w)
    return " ".join(parts)


def montar_banner_html(cfg: dict, foto_path: Path | None) -> str:
    accent      = cfg.get("accent", "#FF6B01")
    headline    = cfg.get("headline", "")
    hl_word     = cfg.get("headline_highlight", "")
    subheadline = cfg.get("subheadline", "")
    handle      = cfg.get("handle", "@seuhandle")
    credit      = cfg.get("credit", "")

    headline_html = _headline_html(headline, hl_word)
    foto_uri      = _foto_data_uri(foto_path) if foto_path and foto_path.exists() else ""
    foto_tag      = f'<img class="bg-photo" src="{foto_uri}" alt="">' if foto_uri else ""

    credit_html = f'<div class="credit">{credit}</div>' if credit else ""

    # outline escuro baseado na cor de destaque
    accent_outline = "rgba(0,0,0,0.85)"

    return f"""
<div class="banner" style="--accent:{accent};--accent-outline:{accent_outline};">
  {foto_tag}
  <div class="gradient"></div>
  <div class="text-block">
    {credit_html}
    <div class="divider"></div>
    <div class="headline">{headline_html}</div>
    <div class="subheadline">{subheadline}</div>
    <div class="handle">{handle}</div>
  </div>
</div>"""


# ── screenshot ──────────────────────────────────────────────────────────

def _crop_png(path: Path, w: int, h: int) -> None:
    """Recorta o PNG para exatamente w×h a partir do canto superior esquerdo."""
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        iw, ih = img.size
        print(f"   Dimensões capturadas: {iw}×{ih}", flush=True)

        amostra_b = [img.getpixel((x, ih - 1)) for x in range(0, iw, 40)]
        amostra_r = [img.getpixel((iw - 1, y)) for y in range(0, ih, 40)]
        brancos_b = sum(1 for p in amostra_b if p[0] > 240 and p[1] > 240 and p[2] > 240)
        brancos_r = sum(1 for p in amostra_r if p[0] > 240 and p[1] > 240 and p[2] > 240)
        if brancos_b > len(amostra_b) // 2:
            print(f"   Borda inferior branca detectada ({brancos_b}/{len(amostra_b)})", flush=True)
        if brancos_r > len(amostra_r) // 2:
            print(f"   Borda direita branca detectada ({brancos_r}/{len(amostra_r)})", flush=True)

        if iw < w or ih < h:
            print(f"   Aviso: imagem menor que esperado (esperado {w}×{h})", flush=True)
            return
        img = img.crop((0, 0, w, h))
        img.save(path, "PNG")
        if iw != w or ih != h:
            print(f"   Recortado: {iw}×{ih} → {w}×{h}", flush=True)
    except ImportError:
        print("   Aviso: instale Pillow para remover bordas (pip install Pillow)", flush=True)
    except Exception as e:
        print(f"   Aviso recorte: {e}", flush=True)


def screenshot(browser: Path, html_path: Path, out_png: Path) -> bool:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_str = str(out_png.resolve()).replace("/", "\\") if IS_WINDOWS else str(out_png.resolve())
    cmd = [
        str(browser), "--headless",
        f"--screenshot={out_str}",
        "--window-size=1160,1450",
        "--hide-scrollbars", "--disable-gpu",
        "--no-sandbox", "--force-device-scale-factor=1",
        "--run-all-compositor-stages-before-draw",
        html_path.as_uri(),
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=30)
        if not (out_png.exists() and out_png.stat().st_size > 0):
            return False
        _crop_png(out_png, 1080, 1350)
        return True
    except Exception as e:
        print(f"   ERRO screenshot: {e}", file=sys.stderr)
        return False


# ── main ────────────────────────────────────────────────────────────────

def main() -> None:
    load_env(ROOT / ".env")

    ap = argparse.ArgumentParser(description="Gera banner estático para Instagram.")
    ap.add_argument("--config",        required=True, help="Caminho para o config-banner.json")
    ap.add_argument("--skip-ai",       action="store_true", help="Pular geração de foto (usa existente)")
    ap.add_argument("--skip-html",     action="store_true", help="Pular overlay HTML e salvar a imagem gerada diretamente (usar em modo referência)")
    ap.add_argument("--ref-layout",    help="LAYOUT REFERÊNCIA: caminho da imagem base (ativa modo multimodal via OpenRouter)")
    ap.add_argument("--ref-personagem",help="PERSONAGEM: caminho da foto do personagem para trocar (opcional, junto com --ref-layout)")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    if not cfg_path.exists():
        sys.exit(f"ERRO: config não encontrado: {cfg_path}")

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    out_dir = Path(cfg.get("output_dir", f"meus-produtos/{cfg.get('slug','produto')}/entregas/criativos"))
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_html:
        if not TEMPLATE.exists():
            sys.exit(f"ERRO: template não encontrado: {TEMPLATE}")
        template_html = TEMPLATE.read_text(encoding="utf-8")

        browser = find_browser()
        if not browser:
            sys.exit("ERRO: Chrome ou Edge não encontrado. Instale e tente novamente.")
    else:
        template_html = ""
        browser = None

    slug     = cfg.get("slug", "produto")
    filename = cfg.get("filename", f"banner-{slug}")

    print(f"\n=== Banner Estático — {slug} ===")

    foto_path = out_dir / "_foto-banner.png"

    ref_layout = Path(args.ref_layout).resolve() if args.ref_layout else None
    ref_personagem = Path(args.ref_personagem).resolve() if args.ref_personagem else None

    if ref_layout and ref_layout.exists():
        print(f"   LAYOUT REFERÊNCIA: {ref_layout.name}", flush=True)
    if ref_personagem and ref_personagem.exists():
        print(f"   PERSONAGEM: {ref_personagem.name}", flush=True)

    if not args.skip_ai:
        prompt = cfg.get("prompt_en", "")
        if not prompt:
            print("   Sem prompt_en no config — pulando foto.", flush=True)
            foto_path = None
        else:
            print("   Gerando foto...", flush=True)
            ok = gerar_foto(prompt, foto_path, ref_layout, ref_personagem)
            if not ok:
                foto_path = None
    else:
        foto_path = foto_path if foto_path.exists() else None

    out_png = out_dir / f"{filename}.png"

    if args.skip_html:
        # Modo referência: salva a imagem gerada diretamente, sem overlay HTML
        if foto_path and foto_path.exists():
            import shutil
            shutil.copy2(foto_path, out_png)
            foto_path.unlink(missing_ok=True)
            print(f"\nBanner salvo em: {out_png}")
        else:
            print("\nERRO: imagem não gerada.", file=sys.stderr)
            sys.exit(1)
    else:
        banner_html = montar_banner_html(cfg, foto_path)
        html        = template_html.replace("{{BANNER_HTML}}", banner_html)

        tmp_html = out_dir / "_tmp-banner.html"
        tmp_html.write_text(html, encoding="utf-8")

        print("   Gerando PNG...", flush=True)
        ok = screenshot(browser, tmp_html, out_png)

        tmp_html.unlink(missing_ok=True)

        if ok:
            print(f"\nBanner salvo em: {out_png}")
        else:
            print(f"\nERRO: screenshot falhou.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
