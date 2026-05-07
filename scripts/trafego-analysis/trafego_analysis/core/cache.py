"""Cache SQLite local de respostas da Meta API.

Evita esbarrar no rate limit da Meta (200 chamadas/hora/usuário) e acelera
desenvolvimento. TTL padrão: 15 min para janelas que incluem hoje (hot data),
1h para janelas fechadas (cold data).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from trafego_analysis.core.config import get_paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS insights_cache (
    key        TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    ttl_s      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cache_created ON insights_cache(created_at);
"""


def _db_path() -> Path:
    return get_paths().insights_db


@contextmanager
def _conn():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _hash_key(parts: dict[str, Any]) -> str:
    """Chave determinística a partir de um dict de parâmetros da query."""
    payload = json.dumps(parts, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


def get(key_parts: dict[str, Any]) -> Any | None:
    """Retorna payload cacheado ou None se ausente/expirado."""
    key = _hash_key(key_parts)
    now = int(time.time())
    with _conn() as c:
        row = c.execute(
            "SELECT payload, created_at, ttl_s FROM insights_cache WHERE key = ?",
            (key,),
        ).fetchone()
    if not row:
        return None
    payload, created_at, ttl_s = row
    if now - created_at > ttl_s:
        return None
    return json.loads(payload)


def put(key_parts: dict[str, Any], payload: Any, *, ttl_s: int = 900) -> None:
    """Grava payload com TTL em segundos (default 15min)."""
    key = _hash_key(key_parts)
    now = int(time.time())
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO insights_cache (key, payload, created_at, ttl_s) "
            "VALUES (?, ?, ?, ?)",
            (key, json.dumps(payload, default=str), now, ttl_s),
        )


def invalidate_all() -> int:
    """Limpa o cache inteiro. Retorna número de entradas removidas."""
    with _conn() as c:
        cursor = c.execute("DELETE FROM insights_cache")
        return cursor.rowcount


def stats() -> dict[str, Any]:
    """Estatísticas rápidas — útil para `trafego cache status`."""
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM insights_cache").fetchone()[0]
        size_row = c.execute(
            "SELECT SUM(LENGTH(payload)) FROM insights_cache"
        ).fetchone()
        size_bytes = size_row[0] or 0
    return {
        "total_entries": total,
        "approx_size_kb": round(size_bytes / 1024, 1),
        "db_path": str(_db_path()),
    }
