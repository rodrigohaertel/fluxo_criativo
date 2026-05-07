"""Classificação taxonômica de criativos — formato, cor, copy metrics.

V1 usa heurísticas leves:
  - aspect_ratio → formato (vertical/quadrado/horizontal)
  - Pillow dominant color → paleta hex (top 3)
  - copy metrics: comprimento, tem pergunta, tem número, emojis

v2 adicionará face detection (opencv), vision models e ranking de hook types.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CreativeFeatures:
    ad_id: str
    # Visual
    formato: str = "?"                # "vertical" | "quadrado" | "horizontal" | "?"
    aspect_ratio: float | None = None
    largura: int | None = None
    altura: int | None = None
    paleta_hex: list[str] = field(default_factory=list)
    paleta_luminosidade: str = "?"    # "clara" | "escura" | "media"
    # Copy
    title: str = ""
    body: str = ""
    title_len: int = 0
    body_len: int = 0
    copy_tem_pergunta: bool = False
    copy_tem_numero: bool = False
    copy_emoji_count: int = 0
    copy_cta_type: str = ""


EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"     # emoticons
    "\U0001F300-\U0001F5FF"     # symbols & pictographs
    "\U0001F680-\U0001F6FF"     # transport & map
    "\U0001F1E0-\U0001F1FF"     # flags
    "\U00002600-\U000026FF"     # misc symbols
    "\U00002700-\U000027BF"     # dingbats
    "]",
    flags=re.UNICODE,
)


def _classify_formato(largura: int, altura: int) -> tuple[str, float]:
    if not largura or not altura:
        return "?", 0.0
    ratio = altura / largura
    if ratio >= 1.3:
        return "vertical", ratio
    if 0.95 <= ratio <= 1.05:
        return "quadrado", ratio
    return "horizontal", ratio


def _classify_luminosidade(paleta: list[tuple[int, int, int]]) -> str:
    if not paleta:
        return "?"
    # Média ponderada (luma perceptual)
    luma = sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in paleta) / len(paleta)
    if luma < 80:
        return "escura"
    if luma > 170:
        return "clara"
    return "media"


def _extract_palette(img_path: Path, top_n: int = 3) -> list[tuple[int, int, int]]:
    try:
        from PIL import Image
    except ImportError:
        return []

    try:
        with Image.open(img_path) as img:
            # Reduz e quantiza para pegar cores dominantes baratas
            img = img.convert("RGB").resize((80, 80))
            paletted = img.quantize(colors=top_n, method=Image.Quantize.MAXCOVERAGE)
            palette = paletted.getpalette() or []
            counts = sorted(paletted.getcolors() or [], reverse=True)
            cores: list[tuple[int, int, int]] = []
            for _count, idx in counts[:top_n]:
                base = idx * 3
                if base + 2 < len(palette):
                    cores.append((palette[base], palette[base + 1], palette[base + 2]))
            return cores
    except Exception:
        return []


def _size_from_image(img_path: Path) -> tuple[int | None, int | None]:
    try:
        from PIL import Image

        with Image.open(img_path) as img:
            return img.size[0], img.size[1]
    except Exception:
        return None, None


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _analyze_copy(title: str, body: str) -> tuple[bool, bool, int]:
    combined = f"{title} {body}"
    tem_pergunta = "?" in combined
    tem_numero = bool(re.search(r"\d", combined))
    emojis = EMOJI_RE.findall(combined)
    return tem_pergunta, tem_numero, len(emojis)


def extrair_features(
    ad_id: str,
    asset_path: Path | None,
    creative: dict[str, Any],
) -> CreativeFeatures:
    f = CreativeFeatures(ad_id=ad_id)

    # Copy
    story = creative.get("object_story_spec") or {}
    page_post = story.get("link_data") or story.get("video_data") or {}
    f.title = creative.get("title") or page_post.get("name") or ""
    f.body = creative.get("body") or page_post.get("message") or ""
    f.title_len = len(f.title)
    f.body_len = len(f.body)
    f.copy_tem_pergunta, f.copy_tem_numero, f.copy_emoji_count = _analyze_copy(f.title, f.body)
    f.copy_cta_type = creative.get("call_to_action_type") or ""

    # Visual — requer asset baixado
    if asset_path and asset_path.exists():
        w, h = _size_from_image(asset_path)
        f.largura = w
        f.altura = h
        if w and h:
            f.formato, f.aspect_ratio = _classify_formato(w, h)
        paleta_rgb = _extract_palette(asset_path, top_n=3)
        f.paleta_hex = [_rgb_to_hex(rgb) for rgb in paleta_rgb]
        f.paleta_luminosidade = _classify_luminosidade(paleta_rgb)

    return f


def comum_em(lista_valores: list[Any]) -> tuple[Any, int]:
    """Retorna (valor_mais_comum, ocorrências). None se lista vazia."""
    from collections import Counter

    if not lista_valores:
        return None, 0
    c = Counter(lista_valores)
    val, n = c.most_common(1)[0]
    return val, n


def dna_do_ganhador(features_top: list[CreativeFeatures]) -> dict[str, Any]:
    """Dada lista de features de top N winners, extrai padrões comuns."""
    if not features_top:
        return {}

    n = len(features_top)
    formato_common, formato_count = comum_em([f.formato for f in features_top if f.formato != "?"])
    lum_common, lum_count = comum_em([f.paleta_luminosidade for f in features_top if f.paleta_luminosidade != "?"])
    cta_common, cta_count = comum_em([f.copy_cta_type for f in features_top if f.copy_cta_type])

    title_len_media = (
        sum(f.title_len for f in features_top) / n if n else 0
    )
    body_len_media = (
        sum(f.body_len for f in features_top) / n if n else 0
    )
    tem_pergunta_n = sum(1 for f in features_top if f.copy_tem_pergunta)
    tem_numero_n = sum(1 for f in features_top if f.copy_tem_numero)
    usa_emoji_n = sum(1 for f in features_top if f.copy_emoji_count > 0)

    return {
        "n_winners": n,
        "formato": {"valor": formato_common, "count": formato_count, "total": n},
        "luminosidade": {"valor": lum_common, "count": lum_count, "total": n},
        "cta": {"valor": cta_common, "count": cta_count, "total": n},
        "title_len_medio": round(title_len_media, 1),
        "body_len_medio": round(body_len_media, 1),
        "copy_com_pergunta_n": tem_pergunta_n,
        "copy_com_numero_n": tem_numero_n,
        "copy_com_emoji_n": usa_emoji_n,
    }
