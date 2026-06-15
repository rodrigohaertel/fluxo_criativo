"""Hotmart API client (opcional).

Ativado via `trafego setup --hotmart`. Lê credenciais de:
  - Config: `user_data/config/integracoes.json` (client_id)
  - Secret: `secrets/hotmart_basic_token` (client_id:client_secret em base64)

Sem dependência externa — usa `httpx` que já é dependência principal.

API Hotmart: https://developers.hotmart.com/docs/pt-BR/start/app-auth/
"""

from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from trafego_analysis.core import config as cfg

log = logging.getLogger(__name__)

TOKEN_URL = "https://api-sec-vlc.hotmart.com/security/oauth/token"
SALES_URL = "https://developers.hotmart.com/payments/api/v1/sales/history"


class HotmartError(Exception):
    pass


@dataclass
class HotmartConfig:
    client_id: str
    client_secret: str
    sandbox: bool = False


class HotmartClient:
    """Client minimalista para endpoints de vendas da Hotmart.

    Usa OAuth client_credentials flow — o token expira em 1h, renovamos
    automaticamente quando necessário.
    """

    def __init__(self, hcfg: HotmartConfig):
        self.hcfg = hcfg
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    @classmethod
    def from_saved_config(cls) -> HotmartClient:
        integracoes = cfg.get_integracoes()
        if not integracoes.get("hotmart"):
            raise HotmartError(
                "Integração Hotmart desativada. Ative com: trafego setup --hotmart"
            )
        hotmart_section = integracoes.get("hotmart_config") or {}
        token_raw = cfg.load_secret(cfg.get_paths().hotmart_basic_token_file)
        if not token_raw:
            raise HotmartError(
                "Credenciais Hotmart não encontradas. Rode: trafego setup --hotmart"
            )
        if ":" not in token_raw:
            raise HotmartError(
                "Formato de secret Hotmart inválido. Esperado: client_id:client_secret"
            )
        client_id, client_secret = token_raw.split(":", 1)
        return cls(
            HotmartConfig(
                client_id=client_id,
                client_secret=client_secret,
                sandbox=hotmart_section.get("sandbox", False),
            )
        )

    def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        try:
            import httpx
        except ImportError as e:
            raise HotmartError("httpx não instalado") from e

        basic = base64.b64encode(
            f"{self.hcfg.client_id}:{self.hcfg.client_secret}".encode("ascii")
        ).decode("ascii")

        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    TOKEN_URL,
                    headers={"Authorization": f"Basic {basic}"},
                    data={"grant_type": "client_credentials"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            raise HotmartError(f"Falha ao obter access_token Hotmart: {e}") from e

        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._token_expires_at = time.time() + expires_in
        return self._access_token

    def get_sales(
        self,
        *,
        since: date,
        until: date,
        max_pages: int = 20,
    ) -> list[dict[str, Any]]:
        """Retorna vendas do período.

        Formato de cada venda (campos principais normalizados):
          - transaction_id
          - created_at (ISO)
          - product_name
          - value (R$)
          - commission (R$, se afiliado)
          - status
        """
        try:
            import httpx
        except ImportError as e:
            raise HotmartError("httpx não instalado") from e

        token = self._ensure_token()
        start_ms = int(datetime.combine(since, datetime.min.time(), tzinfo=UTC).timestamp() * 1000)
        end_ms = int(datetime.combine(until, datetime.max.time(), tzinfo=UTC).timestamp() * 1000)

        out: list[dict[str, Any]] = []
        page_token: str | None = None

        with httpx.Client(timeout=30) as client:
            for _ in range(max_pages):
                params: dict[str, Any] = {
                    "start_date": start_ms,
                    "end_date": end_ms,
                    "max_results": 500,
                }
                if page_token:
                    params["page_token"] = page_token

                try:
                    resp = client.get(
                        SALES_URL,
                        headers={"Authorization": f"Bearer {token}"},
                        params=params,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    raise HotmartError(f"Falha ao buscar vendas Hotmart: {e}") from e

                items = data.get("items", [])
                for it in items:
                    purchase = it.get("purchase", {})
                    product = it.get("product", {})
                    price = purchase.get("price", {})
                    out.append({
                        "transaction_id": purchase.get("transaction"),
                        "created_at": purchase.get("order_date"),
                        "product_name": product.get("name", ""),
                        "product_id": product.get("id"),
                        "value": float(price.get("value") or 0),
                        "currency": price.get("currency_value", "BRL"),
                        "status": purchase.get("status", ""),
                    })

                page_token = data.get("page_info", {}).get("next_page_token")
                if not page_token:
                    break

        return out


def agregar_totais(vendas: list[dict[str, Any]]) -> dict[str, float]:
    """Resumo agregado das vendas Hotmart."""
    aprovadas = [v for v in vendas if str(v.get("status", "")).upper() in ("APPROVED", "COMPLETE")]
    return {
        "vendas_total": len(vendas),
        "vendas_aprovadas": len(aprovadas),
        "receita": sum(v.get("value", 0) for v in aprovadas),
        "ticket_medio": (
            sum(v.get("value", 0) for v in aprovadas) / len(aprovadas)
            if aprovadas else 0
        ),
    }
