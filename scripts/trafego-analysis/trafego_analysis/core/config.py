"""Gerenciamento de paths cross-OS e I/O de configurações do usuário.

Via `platformdirs`, isola as configurações do usuário do diretório do código.
Isso permite que a skill seja atualizada via `git pull` sem perder contas e
produtos cadastrados.

Paths típicos:
  Linux:   ~/.config/trafego-analysis/ e ~/.local/share/trafego-analysis/
  Mac:     ~/Library/Application Support/trafego-analysis/
  Windows: %LOCALAPPDATA%\\trafego-analysis\\
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "trafego-analysis"
APP_AUTHOR = "trafegopaid"


@dataclass(frozen=True)
class Paths:
    """Todos os caminhos usados pela skill em runtime."""

    config_dir: Path         # configs (accounts, produtos, fases, perfis, limiares)
    data_dir: Path           # assets, cache, outputs
    secrets_dir: Path
    cache_dir: Path
    assets_thumbs_dir: Path
    assets_images_dir: Path
    outputs_markdown_dir: Path
    outputs_galerias_dir: Path

    # Arquivos de config
    accounts_file: Path
    produtos_file: Path
    fases_file: Path
    perfis_file: Path
    limiares_file: Path
    integracoes_file: Path

    # Secrets
    meta_token_file: Path
    google_ads_refresh_token_file: Path
    hotmart_basic_token_file: Path

    # Cache
    insights_db: Path


def get_paths() -> Paths:
    """Retorna todos os caminhos, criando diretórios se ainda não existem."""
    config_root = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    data_root = Path(user_data_dir(APP_NAME, APP_AUTHOR))

    p = Paths(
        config_dir=config_root,
        data_dir=data_root,
        secrets_dir=config_root / "secrets",
        cache_dir=data_root / "cache",
        assets_thumbs_dir=data_root / "assets" / "thumbs",
        assets_images_dir=data_root / "assets" / "images",
        outputs_markdown_dir=data_root / "outputs" / "markdown",
        outputs_galerias_dir=data_root / "outputs" / "galerias_html",

        accounts_file=config_root / "accounts.json",
        produtos_file=config_root / "produtos.json",
        fases_file=config_root / "fases.json",
        perfis_file=config_root / "perfis.json",
        limiares_file=config_root / "limiares.json",
        integracoes_file=config_root / "integracoes.json",

        meta_token_file=config_root / "secrets" / "meta_system_user_token",
        google_ads_refresh_token_file=config_root / "secrets" / "google_ads_refresh_token",
        hotmart_basic_token_file=config_root / "secrets" / "hotmart_basic_token",

        insights_db=data_root / "cache" / "insights.sqlite",
    )

    for d in (
        p.config_dir,
        p.data_dir,
        p.secrets_dir,
        p.cache_dir,
        p.assets_thumbs_dir,
        p.assets_images_dir,
        p.outputs_markdown_dir,
        p.outputs_galerias_dir,
    ):
        d.mkdir(parents=True, exist_ok=True)

    return p


def load_json(path: Path, default: Any = None) -> Any:
    """Lê JSON. Retorna `default` (ou dict vazio) se arquivo não existe."""
    if not path.exists():
        return default if default is not None else {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any, *, secret: bool = False) -> None:
    """Escreve JSON com indentação e UTF-8. Se `secret`, aplica permissão 600 em Unix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")

    if secret and os.name == "posix":
        # 0o600: dono lê/escreve; mais ninguém.
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def load_secret(path: Path) -> str | None:
    """Lê um arquivo de secret (texto puro). Retorna None se não existe."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def save_secret(path: Path, value: str) -> None:
    """Salva secret em texto puro, permissão 600 em Unix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.strip() + "\n", encoding="utf-8")
    if os.name == "posix":
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


# --- Acessos de alto nível ---------------------------------------------------

def get_accounts() -> list[dict]:
    """Lista de contas cadastradas. `accounts.json` tem formato {default_account, accounts}."""
    data = load_json(get_paths().accounts_file, default={"default_account": None, "accounts": []})
    return data.get("accounts", [])


def get_default_account_alias() -> str | None:
    data = load_json(get_paths().accounts_file, default={})
    return data.get("default_account")


def get_account_by_alias(alias: str) -> dict | None:
    for a in get_accounts():
        if a.get("alias") == alias:
            return a
    return None


def get_produtos() -> list[dict]:
    return load_json(get_paths().produtos_file, default=[])


def get_fases() -> dict:
    """Dict com {fases: [...], regex_match: {...}}."""
    return load_json(get_paths().fases_file, default={"fases": [], "regex_match": {}})


def get_perfis() -> dict:
    return load_json(get_paths().perfis_file, default={"ativos": [], "perfis": {}})


def get_limiares() -> dict:
    return load_json(get_paths().limiares_file, default={})


def get_integracoes() -> dict:
    return load_json(
        get_paths().integracoes_file,
        default={"google_ads": False, "hotmart": False},
    )


def is_setup_complete() -> bool:
    """True se o setup wizard já rodou pelo menos uma vez."""
    p = get_paths()
    return (
        p.accounts_file.exists()
        and p.meta_token_file.exists()
        and len(get_accounts()) > 0
    )
