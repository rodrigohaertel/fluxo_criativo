"""Google Ads API client (opcional).

Ativado via `trafego setup --google-ads`. Lê credenciais de:
  - Config: `user_data/config/integracoes.json` (customer_id, developer_token)
  - Secret: `secrets/google_ads_refresh_token`

Dependência opcional: `google-ads` (extra `[google]`).

Uso:
  client = GoogleAdsClient.from_saved_config()
  insights = client.get_campaign_insights(since=..., until=...)

O objetivo desta integração v1 é agregar métricas de spend/clicks/conversions
do Google Ads para compor análise cross-canal com Meta. Não pretende substituir
o dashboard nativo do Google Ads — só consolidar.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from trafego_analysis.core import config as cfg

log = logging.getLogger(__name__)


class GoogleAdsError(Exception):
    pass


@dataclass
class GoogleAdsConfig:
    customer_id: str                      # "1234567890" (sem hífens)
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    login_customer_id: str | None = None  # MCC, se aplicável


class GoogleAdsClient:
    """Wrapper mínimo sobre a google-ads lib.

    Em v1 suportamos apenas leitura de insights agregados. Escrita (criar/pausar
    campanha) fica fora do escopo.
    """

    def __init__(self, gcfg: GoogleAdsConfig):
        self.gcfg = gcfg
        self._client = None

    @classmethod
    def from_saved_config(cls) -> GoogleAdsClient:
        integracoes = cfg.get_integracoes()
        if not integracoes.get("google_ads"):
            raise GoogleAdsError(
                "Integração Google Ads desativada. Ative com: trafego setup --google-ads"
            )
        google_section = integracoes.get("google_ads_config") or {}
        refresh_token = cfg.load_secret(cfg.get_paths().google_ads_refresh_token_file)
        if not refresh_token:
            raise GoogleAdsError(
                "Refresh token do Google Ads não encontrado. Rode: trafego setup --google-ads"
            )
        return cls(
            GoogleAdsConfig(
                customer_id=google_section.get("customer_id", ""),
                developer_token=google_section.get("developer_token", ""),
                client_id=google_section.get("client_id", ""),
                client_secret=google_section.get("client_secret", ""),
                refresh_token=refresh_token,
                login_customer_id=google_section.get("login_customer_id"),
            )
        )

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        try:
            from google.ads.googleads.client import GoogleAdsClient as GAC
        except ImportError as e:
            raise GoogleAdsError(
                "Dependência 'google-ads' não instalada. Execute: "
                "pip install -e '.[google]'"
            ) from e

        cfg_dict = {
            "developer_token": self.gcfg.developer_token,
            "client_id": self.gcfg.client_id,
            "client_secret": self.gcfg.client_secret,
            "refresh_token": self.gcfg.refresh_token,
            "use_proto_plus": True,
        }
        if self.gcfg.login_customer_id:
            cfg_dict["login_customer_id"] = self.gcfg.login_customer_id

        try:
            self._client = GAC.load_from_dict(cfg_dict)
        except Exception as e:
            raise GoogleAdsError(f"Falha ao inicializar Google Ads client: {e}") from e

    def get_campaign_insights(
        self,
        *,
        since: date,
        until: date,
    ) -> list[dict[str, Any]]:
        """Campaign-level insights agregados no período."""
        self._ensure_client()
        assert self._client is not None

        ga_service = self._client.get_service("GoogleAdsService")
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.average_cpm
            FROM campaign
            WHERE segments.date BETWEEN '{since.isoformat()}' AND '{until.isoformat()}'
            AND campaign.status != 'REMOVED'
        """
        try:
            response = ga_service.search(
                customer_id=self.gcfg.customer_id,
                query=query,
            )
        except Exception as e:
            raise GoogleAdsError(f"Falha ao buscar insights Google Ads: {e}") from e

        rows = []
        for row in response:
            rows.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "status": str(row.campaign.status),
                "spend": row.metrics.cost_micros / 1_000_000,
                "impressions": int(row.metrics.impressions),
                "clicks": int(row.metrics.clicks),
                "conversions": float(row.metrics.conversions),
                "conversion_value": float(row.metrics.conversions_value),
                "ctr": float(row.metrics.ctr) * 100,
                "cpc": row.metrics.average_cpc / 1_000_000 if row.metrics.average_cpc else 0,
                "cpm": row.metrics.average_cpm / 1_000_000 if row.metrics.average_cpm else 0,
            })
        return rows


def agregar_totais(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Resumo agregado por período para uso no cross-canal."""
    return {
        "spend": sum(r.get("spend", 0) for r in rows),
        "impressions": sum(r.get("impressions", 0) for r in rows),
        "clicks": sum(r.get("clicks", 0) for r in rows),
        "conversions": sum(r.get("conversions", 0) for r in rows),
        "revenue": sum(r.get("conversion_value", 0) for r in rows),
    }
