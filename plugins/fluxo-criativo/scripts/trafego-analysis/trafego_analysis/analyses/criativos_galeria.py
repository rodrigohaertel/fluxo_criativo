"""Galeria visual HTML interativa dos top criativos.

Gera um arquivo HTML standalone (sem dependências de CDN) com:
  - Grid responsivo dos criativos
  - Thumb grande por card
  - Métricas sobrepostas ao hover
  - Lightbox ao clicar
  - Dark mode por padrão (bom pra gravação)

As imagens são embutidas como `file://` (path absoluto local). Funciona offline
e não vaza dados — idela pra aula gravada.

Uso típico:
  trafego criativos --galeria --top 12 --produto "X"
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from trafego_analysis.analyses import criativos_ranking
from trafego_analysis.analyses.criativos_taxonomia import extrair_features
from trafego_analysis.core import assets as assets_mod
from trafego_analysis.core import meta_client as mc
from trafego_analysis.core import report
from trafego_analysis.core.config import get_paths
from trafego_analysis.core.periods import Period

log = logging.getLogger(__name__)


@dataclass
class GaleriaItem:
    rank: int
    ad_id: str
    ad_name: str
    campaign_name: str
    spend: float
    hook_rate: float
    hold_rate: float
    ctr: float
    cpa: float | None
    score: float
    ranking_quality: str
    img_b64: str | None = None  # data:image/jpeg;base64,...
    formato: str = ""
    paleta_hex: list[str] | None = None


def _encode_image(path: Path, max_width: int = 600) -> str | None:
    """Reduz a imagem pra max_width e retorna data URI base64."""
    try:
        from PIL import Image

        with Image.open(path) as img:
            img = img.convert("RGB")
            w, h = img.size
            if w > max_width:
                ratio = max_width / w
                img = img.resize((max_width, int(h * ratio)))
            import io

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=82)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        log.warning("Falha ao encodar imagem %s: %s", path, e)
        return None


def analisar(
    *,
    meta: mc.MetaClient,
    ad_account_id: str,
    account_alias: str,
    periodo: Period,
    produto_nome: str | None = None,
    top_n: int = 12,
    filtering: list[dict[str, Any]] | None = None,
) -> tuple[Path | None, Any]:
    """Pipeline completo da galeria. Retorna (html_path, metadata)."""
    rows = meta.get_ad_insights(
        ad_account_id,
        since=periodo.since,
        until=periodo.until,
        filtering=filtering,
    )
    if produto_nome:
        nome_low = produto_nome.lower()
        rows = [r for r in rows if nome_low in (r.get("campaign_name") or "").lower()]

    ranking = criativos_ranking.ranquear_criativos(rows)
    top = ranking[:top_n]

    if not top:
        log.warning("Nenhum criativo atende aos critérios de ranking.")
        return None, None

    # Baixa assets dos top
    ad_ids = [c.ad_id for c in top]
    locais = assets_mod.download_batch(meta, ad_ids, account_alias)

    items: list[GaleriaItem] = []
    for c in top:
        local = locais.get(c.ad_id)
        img_b64 = _encode_image(local.path) if local else None

        # Feature extraction leve pra formato e paleta
        formato = ""
        paleta_hex = None
        if local:
            creative = assets_mod.fetch_ad_creative(meta, c.ad_id)
            feat = extrair_features(c.ad_id, local.path, creative)
            formato = feat.formato
            paleta_hex = feat.paleta_hex or None

        items.append(
            GaleriaItem(
                rank=c.rank,
                ad_id=c.ad_id,
                ad_name=c.ad_name,
                campaign_name=c.campaign_name,
                spend=c.spend,
                hook_rate=c.hook_rate,
                hold_rate=c.hold_rate,
                ctr=c.ctr,
                cpa=c.cpa,
                score=c.score,
                ranking_quality=c.ranking_quality,
                img_b64=img_b64,
                formato=formato,
                paleta_hex=paleta_hex,
            )
        )

    context = {
        "produto": produto_nome or "todos",
        "periodo": periodo,
        "items": items,
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    # Renderiza e salva
    text, _ = report.render_markdown("criativos_galeria.html.j2", context)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    slug = (produto_nome or "geral").lower().replace(" ", "-")
    out_path = get_paths().outputs_galerias_dir / f"{ts}_{slug}_galeria.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    return out_path, {"n_itens": len(items), "periodo": periodo.label}
