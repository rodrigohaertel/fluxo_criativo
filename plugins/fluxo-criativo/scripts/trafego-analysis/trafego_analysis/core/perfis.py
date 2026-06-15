"""Perfis de análise — regras de fadiga, escalada e baseline por tipo de operação.

Ship com 2 templates (perpetuo, lancamento). Usuário pode criar N perfis próprios
em `user_data/config/perfis.json`. Cada produto ou campanha (via regex) pode ser
associado a um perfil.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from trafego_analysis.core.config import get_perfis


@dataclass
class FadigaThresholds:
    freq_cold_perigo: float = 3.0
    freq_rmk_perigo: float = 5.0
    ctr_drop_wow_pct: float = 15.0
    cpa_rise_vs_baseline_pct: float = 25.0
    cpr_critico_multiplicador: float = 2.0


@dataclass
class EscaladaThresholds:
    cpa_max_pct_media: float = 70.0
    freq_max_pra_escalar: float = 2.0
    incremento_budget_pct: float = 25.0
    min_conversoes: int = 50


@dataclass
class Perfil:
    nome: str
    descricao: str = ""
    baseline: str = "rolling_30d"  # ou "janela_lancamento_atual"
    fadiga: FadigaThresholds = field(default_factory=FadigaThresholds)
    escalada: EscaladaThresholds = field(default_factory=EscaladaThresholds)
    match_regex: list[str] = field(default_factory=list)  # regex no nome da campanha

    @classmethod
    def from_dict(cls, nome: str, raw: dict[str, Any]) -> Perfil:
        fadiga = FadigaThresholds(**raw.get("fadiga", {}))
        escalada = EscaladaThresholds(**raw.get("escalada", {}))
        return cls(
            nome=nome,
            descricao=raw.get("descricao", ""),
            baseline=raw.get("baseline", "rolling_30d"),
            fadiga=fadiga,
            escalada=escalada,
            match_regex=raw.get("match_regex", []),
        )


PERFIL_PADRAO_FALLBACK = Perfil(
    nome="default",
    descricao="Perfil de fallback quando nenhum outro está cadastrado.",
)


def load_perfis() -> dict[str, Perfil]:
    """Carrega todos os perfis do user_data. Retorna dict {nome: Perfil}."""
    raw = get_perfis()
    ativos = raw.get("ativos", [])
    perfis_raw = raw.get("perfis", {})

    out: dict[str, Perfil] = {}
    for nome in ativos:
        if nome in perfis_raw:
            out[nome] = Perfil.from_dict(nome, perfis_raw[nome])
    return out


def get_perfil(nome: str) -> Perfil:
    """Retorna perfil por nome. Se não existe, retorna fallback sem erro."""
    perfis = load_perfis()
    return perfis.get(nome, PERFIL_PADRAO_FALLBACK)


def match_perfil_for_campaign(campaign_name: str) -> Perfil:
    """Tenta casar o nome da campanha contra `match_regex` de cada perfil ativo.

    Primeiro match ganha. Se nada casar, retorna o primeiro perfil ativo ou fallback.
    """
    import re

    perfis = load_perfis()
    for perfil in perfis.values():
        for pattern in perfil.match_regex:
            if re.search(pattern, campaign_name, re.IGNORECASE):
                return perfil

    # Fallback: primeiro perfil ativo (ordem de inserção preservada em dict py3.7+)
    for perfil in perfis.values():
        return perfil
    return PERFIL_PADRAO_FALLBACK
