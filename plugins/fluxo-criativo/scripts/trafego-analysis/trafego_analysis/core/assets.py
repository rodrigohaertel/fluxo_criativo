"""Download e cache de assets visuais dos ads (thumbs e imagens).

Para cada ad, baixa:
  - creative.image_url (se imagem estática) → assets/images/{account}/{ad_id}.jpg
  - creative.video_id → busca /{video_id}?fields=picture para pegar thumb

Cache determinístico por URL (hash do bytes de referência).
Se o arquivo já existe, pula o download.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trafego_analysis.core.config import get_paths

log = logging.getLogger(__name__)


@dataclass
class AssetLocal:
    ad_id: str
    path: Path
    tipo: str        # "image" | "video_thumb"
    source_url: str


def _sanitize_ad_id(ad_id: str) -> str:
    return "".join(c for c in ad_id if c.isalnum() or c in "_-")


def _slug_url(url: str) -> str:
    """Hash curto da URL — evita colisão quando creative muda."""
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]


def fetch_ad_creative(meta_client, ad_id: str) -> dict[str, Any]:
    """Busca creative + object_story_spec de um ad específico.

    Usa `facebook_business.adobjects.ad.Ad` para pegar:
      - creative{image_url, video_id, title, body, call_to_action_type}
    """
    meta_client._ensure_api()
    try:
        from facebook_business.adobjects.ad import Ad
    except ImportError:
        log.warning("facebook-business não disponível — creative fetch skipped")
        return {}

    try:
        ad = Ad(ad_id)
        creative_data = ad.api_get(
            fields=[
                "creative{id,image_url,video_id,title,body,"
                "object_story_spec,effective_object_story_id,"
                "image_hash,thumbnail_url,call_to_action_type}"
            ]
        )
        creative = creative_data.get("creative") or {}
        return dict(creative)
    except Exception as e:
        log.warning("Falha ao buscar creative do ad %s: %s", ad_id, e)
        return {}


def _download(url: str, destino: Path, timeout_s: int = 20) -> bool:
    """Baixa URL pra destino. Retorna True se sucesso."""
    if destino.exists() and destino.stat().st_size > 0:
        return True  # cache hit

    try:
        import httpx
    except ImportError:
        log.warning("httpx não instalado — download pulado")
        return False

    try:
        with httpx.Client(follow_redirects=True, timeout=timeout_s) as client:
            resp = client.get(url)
            resp.raise_for_status()
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(resp.content)
            return True
    except Exception as e:
        log.warning("Falha ao baixar %s: %s", url, e)
        return False


def fetch_video_thumb_url(meta_client, video_id: str) -> str | None:
    """Resolve video_id em URL do poster (thumb). Retorna None se falhar."""
    if not video_id:
        return None
    meta_client._ensure_api()
    try:
        from facebook_business.adobjects.advideo import AdVideo

        video = AdVideo(video_id)
        data = video.api_get(fields=["picture", "thumbnails"])
        # `picture` tende a ser a poster frame
        if data.get("picture"):
            return data["picture"]
        # fallback: primeiro thumbnail
        thumbs = data.get("thumbnails", {}).get("data") or []
        if thumbs:
            return thumbs[0].get("uri")
    except Exception as e:
        log.warning("Falha ao resolver video_id %s: %s", video_id, e)
    return None


def download_ad_asset(
    meta_client,
    ad_id: str,
    account_alias: str,
    *,
    creative: dict[str, Any] | None = None,
) -> AssetLocal | None:
    """Baixa o asset principal de um ad. Retorna None se não conseguir."""
    if creative is None:
        creative = fetch_ad_creative(meta_client, ad_id)
    if not creative:
        return None

    paths = get_paths()
    ad_id_safe = _sanitize_ad_id(ad_id)

    # Imagem direta
    if creative.get("image_url"):
        url = creative["image_url"]
        destino = paths.assets_images_dir / account_alias / f"{ad_id_safe}_{_slug_url(url)}.jpg"
        if _download(url, destino):
            return AssetLocal(ad_id=ad_id, path=destino, tipo="image", source_url=url)

    # Vídeo → thumb
    if creative.get("video_id"):
        thumb_url = fetch_video_thumb_url(meta_client, creative["video_id"])
        if thumb_url:
            destino = paths.assets_thumbs_dir / account_alias / f"{ad_id_safe}_{_slug_url(thumb_url)}.jpg"
            if _download(thumb_url, destino):
                return AssetLocal(
                    ad_id=ad_id,
                    path=destino,
                    tipo="video_thumb",
                    source_url=thumb_url,
                )

    # Fallback: thumbnail_url
    if creative.get("thumbnail_url"):
        url = creative["thumbnail_url"]
        destino = paths.assets_thumbs_dir / account_alias / f"{ad_id_safe}_{_slug_url(url)}.jpg"
        if _download(url, destino):
            return AssetLocal(ad_id=ad_id, path=destino, tipo="video_thumb", source_url=url)

    return None


def download_batch(
    meta_client,
    ad_ids: list[str],
    account_alias: str,
    *,
    max_workers: int = 6,
) -> dict[str, AssetLocal]:
    """Baixa assets de N ads em paralelo via thread pool.

    Uma chamada Meta por ad (para fetch creative) — rate limit pode gargalar.
    Use com parcimônia: idealmente para top 20-30 ads por análise.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    resultados: dict[str, AssetLocal] = {}

    def _work(ad_id: str) -> tuple[str, AssetLocal | None]:
        return ad_id, download_ad_asset(meta_client, ad_id, account_alias)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_work, aid): aid for aid in ad_ids}
        for fut in as_completed(futures):
            ad_id, asset = fut.result()
            if asset:
                resultados[ad_id] = asset

    return resultados
