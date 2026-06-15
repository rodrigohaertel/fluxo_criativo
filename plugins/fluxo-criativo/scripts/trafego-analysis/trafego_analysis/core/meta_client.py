"""Wrapper sobre `facebook-business` SDK — multi-conta + cache + modo teste.

Encapsula autenticação com System User Token, seleção de ad account por alias,
e coleta de insights com campos padronizados. Todas as chamadas passam pelo
cache SQLite local (TTL configurável) para economizar quota.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from trafego_analysis.core import cache, config

log = logging.getLogger(__name__)


# Campos padrão cobrindo todas as análises; ad-level.
AD_FIELDS_BASE: list[str] = [
    "ad_id",
    "ad_name",
    "adset_id",
    "adset_name",
    "campaign_id",
    "campaign_name",
    "spend",
    "impressions",
    "reach",
    "frequency",
    "clicks",
    "inline_link_clicks",
    "outbound_clicks",
    "cpm",
    "cpc",
    "ctr",
    "actions",
    "action_values",
    "cost_per_action_type",
    "video_p25_watched_actions",
    "video_p50_watched_actions",
    "video_p75_watched_actions",
    "video_p100_watched_actions",
    "video_30_sec_watched_actions",
    "video_thruplay_watched_actions",
    "quality_ranking",
    "engagement_rate_ranking",
    "conversion_rate_ranking",
]


CAMPAIGN_FIELDS_BASE: list[str] = [
    "campaign_id",
    "campaign_name",
    "spend",
    "impressions",
    "reach",
    "frequency",
    "clicks",
    "inline_link_clicks",
    "cpm",
    "cpc",
    "ctr",
    "actions",
    "action_values",
    "cost_per_action_type",
]


@dataclass
class MetaClientConfig:
    access_token: str
    api_version: str = "v25.0"
    app_id: str | None = None
    app_secret: str | None = None


class MetaAPIError(Exception):
    """Erro de comunicação com Meta. Original exception disponível em `.cause`."""

    def __init__(self, message: str, *, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


class MetaClient:
    """Cliente Meta com multi-conta.

    Use `from_saved_config()` para construir a partir das credenciais salvas
    pelo setup wizard. Para testes, instancie direto com `MetaClient(config)`.
    """

    def __init__(self, cfg: MetaClientConfig):
        self.cfg = cfg
        self._api = None  # lazy init do SDK

    @classmethod
    def from_saved_config(cls) -> MetaClient:
        token = config.load_secret(config.get_paths().meta_token_file)
        if not token:
            raise MetaAPIError(
                "System User Token não encontrado. Execute: trafego setup"
            )
        return cls(MetaClientConfig(access_token=token))

    def _ensure_api(self) -> None:
        if self._api is not None:
            return
        try:
            from facebook_business.api import FacebookAdsApi
        except ImportError as e:
            raise MetaAPIError(
                "Dependência 'facebook-business' não instalada. Execute: "
                "pip install -e '.[web]' na pasta do projeto."
            ) from e

        try:
            self._api = FacebookAdsApi.init(
                access_token=self.cfg.access_token,
                api_version=self.cfg.api_version,
                app_id=self.cfg.app_id,
                app_secret=self.cfg.app_secret,
            )
        except Exception as e:
            raise MetaAPIError(
                "Falha ao inicializar Meta SDK — verifique o token.",
                cause=e,
            ) from e

    # -- Low-level --------------------------------------------------------------

    def list_ad_accounts(self) -> list[dict[str, Any]]:
        """Lista todas as ad accounts acessíveis pelo token atual.

        Útil no wizard de setup para mostrar opções ao usuário.
        """
        self._ensure_api()
        from facebook_business.adobjects.user import User

        try:
            me = User(fbid="me")
            accounts = me.get_ad_accounts(fields=["id", "name", "account_status", "currency", "timezone_name"])
            return [
                {
                    "ad_account_id": a["id"],
                    "name": a.get("name", ""),
                    "account_status": a.get("account_status"),
                    "currency": a.get("currency"),
                    "timezone": a.get("timezone_name"),
                }
                for a in accounts
            ]
        except Exception as e:
            raise MetaAPIError(f"Falha ao listar ad accounts: {e}", cause=e) from e

    # -- Insights --------------------------------------------------------------

    def get_ad_insights(
        self,
        ad_account_id: str,
        *,
        since: date,
        until: date,
        filtering: list[dict[str, Any]] | None = None,
        breakdowns: list[str] | None = None,
        cache_ttl_s: int = 900,
        extra_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Ad-level insights. Usa cache SQLite local. Sempre retorna lista de dicts.

        >>> client = MetaClient.from_saved_config()
        >>> rows = client.get_ad_insights("act_1001", since=..., until=...)
        >>> rows[0]["ad_name"]
        'VTSD_CV_v7_mulher40'
        """
        key = {
            "level": "ad",
            "account": ad_account_id,
            "since": since.isoformat(),
            "until": until.isoformat(),
            "filtering": filtering,
            "breakdowns": breakdowns,
            "extra_fields": extra_fields,
            "api_version": self.cfg.api_version,
        }
        cached = cache.get(key)
        if cached is not None:
            log.info("meta_client cache HIT level=ad account=%s", ad_account_id)
            return cached

        self._ensure_api()
        from facebook_business.adobjects.adaccount import AdAccount

        fields = list(AD_FIELDS_BASE)
        if extra_fields:
            fields.extend(f for f in extra_fields if f not in fields)

        params: dict[str, Any] = {
            "level": "ad",
            "time_range": {"since": since.isoformat(), "until": until.isoformat()},
            "limit": 500,
        }
        if filtering:
            params["filtering"] = filtering
        if breakdowns:
            params["breakdowns"] = breakdowns

        try:
            account = AdAccount(ad_account_id)
            insights = account.get_insights(fields=fields, params=params)
            rows = [dict(row) for row in insights]
        except Exception as e:
            raise MetaAPIError(f"Falha ao buscar ad insights: {e}", cause=e) from e

        cache.put(key, rows, ttl_s=cache_ttl_s)
        return rows

    def get_campaign_insights(
        self,
        ad_account_id: str,
        *,
        since: date,
        until: date,
        filtering: list[dict[str, Any]] | None = None,
        cache_ttl_s: int = 900,
    ) -> list[dict[str, Any]]:
        """Campaign-level insights (menos volumoso que ad-level)."""
        key = {
            "level": "campaign",
            "account": ad_account_id,
            "since": since.isoformat(),
            "until": until.isoformat(),
            "filtering": filtering,
            "api_version": self.cfg.api_version,
        }
        cached = cache.get(key)
        if cached is not None:
            return cached

        self._ensure_api()
        from facebook_business.adobjects.adaccount import AdAccount

        params: dict[str, Any] = {
            "level": "campaign",
            "time_range": {"since": since.isoformat(), "until": until.isoformat()},
            "limit": 500,
        }
        if filtering:
            params["filtering"] = filtering

        try:
            insights = AdAccount(ad_account_id).get_insights(fields=CAMPAIGN_FIELDS_BASE, params=params)
            rows = [dict(row) for row in insights]
        except Exception as e:
            raise MetaAPIError(f"Falha ao buscar campaign insights: {e}", cause=e) from e

        cache.put(key, rows, ttl_s=cache_ttl_s)
        return rows


# --- Extratores de actions --------------------------------------------------

def extract_action_count(actions: list[dict[str, Any]] | None, action_type: str) -> float:
    """Extrai valor numérico de um `action_type` específico do array `actions` da Meta."""
    if not actions:
        return 0.0
    for a in actions:
        if a.get("action_type") == action_type:
            return float(a.get("value", 0) or 0)
    return 0.0


def extract_action_value(action_values: list[dict[str, Any]] | None, action_type: str) -> float:
    """Extrai valor em R$ (para ROAS) de um `action_type` específico."""
    return extract_action_count(action_values, action_type)
