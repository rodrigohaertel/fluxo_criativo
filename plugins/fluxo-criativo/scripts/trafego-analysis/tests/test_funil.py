"""Testes do waterfall do funil e detector de gargalo."""

from __future__ import annotations

from trafego_analysis.analyses.funil_waterfall import (
    BENCHMARKS_ETAPAS,
    construir_waterfall,
    diagnostico_playbook,
)


def _row(
    impressions: float = 100000,
    video_30s: float = 25000,         # hook 25% (bench exato)
    thruplay: float = 10000,
    video_p50: float = 1200,          # VSL 55% 75% (bench 55% — acima)
    inline_link_clicks: float = 2000, # link-click/3s 8% (bench 1.5% — acima)
    lp_views: float = 1600,           # connect 80% (bench 70% — acima)
    initiate_checkout: float = 320,   # 320/1200 = 26.7% (bench 20% — acima)
    purchases: float = 100,           # 100/320 = 31.25% (bench 30% — acima)
) -> dict:
    """Constrói um row de insight com todos os eventos do funil presentes."""
    return {
        "impressions": impressions,
        "inline_link_clicks": inline_link_clicks,
        "video_30_sec_watched_actions": [{"action_type": "video_view", "value": video_30s}],
        "video_thruplay_watched_actions": [{"action_type": "video_view", "value": thruplay}],
        "video_p50_watched_actions": [{"action_type": "video_view", "value": video_p50}],
        "video_p25_watched_actions": [{"action_type": "video_view", "value": video_30s * 1.1}],
        "actions": [
            {"action_type": "link_click", "value": inline_link_clicks},
            {"action_type": "landing_page_view", "value": lp_views},
            {"action_type": "initiate_checkout", "value": initiate_checkout},
            {"action_type": "purchase", "value": purchases},
        ],
    }


class TestConstruirWaterfall:
    def test_etapas_preenchidas_em_ordem(self):
        rows = [_row()]
        result = construir_waterfall(rows)
        nomes_esperados = [
            "Impressões", "3s views (hook)", "Cliques no link", "Landing page views",
            "VSL 55%+", "Início de checkout", "Compras",
        ]
        assert [e.label for e in result.etapas] == nomes_esperados

    def test_taxa_de_passagem_calculada(self):
        rows = [_row(impressions=100000, video_30s=25000)]
        result = construir_waterfall(rows)
        # Impressão → 3s: 25000/100000 = 25%
        hook = result.etapas[1]
        assert hook.taxa_passagem == 25.0
        assert hook.drop_pct == 75.0

    def test_sem_conversoes_registra_sem_dados(self):
        row = {
            "impressions": 100000,
            "inline_link_clicks": 2000,
            "actions": [],  # sem purchase/checkout
        }
        result = construir_waterfall([row])
        compras = [e for e in result.etapas if e.id == "purchase"][0]
        assert compras.tem_dados is False
        assert "Compras" in result.etapas_sem_dados

    def test_agrega_multiplos_rows(self):
        rows = [_row(impressions=50000, purchases=50), _row(impressions=50000, purchases=50)]
        result = construir_waterfall(rows)
        impressoes = [e for e in result.etapas if e.id == "impression"][0]
        assert impressoes.volume == 100000
        compras = [e for e in result.etapas if e.id == "purchase"][0]
        assert compras.volume == 100


class TestDeteccaoGargalo:
    def test_sem_gargalo_quando_tudo_saudavel(self):
        rows = [_row(
            impressions=100000, video_30s=35000, inline_link_clicks=3500,
            lp_views=3000, video_p50=2000, initiate_checkout=800, purchases=320,
        )]
        result = construir_waterfall(rows)
        assert result.gargalo is None

    def test_hook_baixo_vira_gargalo(self):
        # Só hook abaixo do benchmark; todas as outras etapas acima
        rows = [_row(
            impressions=100000,
            video_30s=10000,               # hook 10% (15 pts abaixo do bench 25%)
            inline_link_clicks=1500,       # 1500/10000 = 15% (bench 1.5% — acima)
            lp_views=1200,                 # 1200/1500 = 80% (bench 70% — acima)
            video_p50=900,                 # 900/1200 = 75% (bench 55% — acima)
            initiate_checkout=270,         # 270/900 = 30% (bench 20% — acima)
            purchases=100,                 # 100/270 = 37% (bench 30% — acima)
        )]
        result = construir_waterfall(rows)
        assert result.gargalo is not None
        assert result.gargalo.id == "view_3s"

    def test_connect_rate_baixo_vira_gargalo(self):
        # Só connect rate abaixo; resto saudável
        rows = [_row(
            inline_link_clicks=2000,
            lp_views=600,                  # connect 30% (40 pts abaixo do bench 70%)
            video_p50=400,                 # 400/600 = 67% (bench 55% — acima)
            initiate_checkout=130,         # 130/400 = 32.5% (bench 20% — acima)
            purchases=50,                  # 50/130 = 38.5% (bench 30% — acima)
        )]
        result = construir_waterfall(rows)
        assert result.gargalo is not None
        assert result.gargalo.id == "lp_view"


class TestPlaybook:
    def test_playbook_sem_gargalo(self):
        msg = diagnostico_playbook(None)
        assert "Nenhum gargalo" in msg

    def test_playbook_hook(self):
        # Só hook abaixo, outras acima
        rows = [_row(
            video_30s=5000, inline_link_clicks=750, lp_views=600,
            video_p50=450, initiate_checkout=140, purchases=50,
        )]
        result = construir_waterfall(rows)
        msg = diagnostico_playbook(result.gargalo)
        assert "hook" in msg.lower()

    def test_playbook_lp_view(self):
        # Só connect abaixo
        rows = [_row(
            inline_link_clicks=2000, lp_views=600,
            video_p50=400, initiate_checkout=130, purchases=50,
        )]
        result = construir_waterfall(rows)
        msg = diagnostico_playbook(result.gargalo)
        assert "landing page" in msg.lower()


class TestBenchmarks:
    def test_todos_benchmarks_presentes(self):
        # Sanity: benchmarks definidos para cada etapa rastreável
        for k in ["view_3s", "link_click", "lp_view", "vsl_55pct",
                  "initiate_checkout", "purchase"]:
            assert k in BENCHMARKS_ETAPAS
            assert BENCHMARKS_ETAPAS[k] > 0

    def test_hook_saudavel_bate_com_25(self):
        assert BENCHMARKS_ETAPAS["view_3s"] == 25.0
