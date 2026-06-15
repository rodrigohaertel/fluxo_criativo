"""Testes do cross-canal — agregação Meta + Google + Hotmart (stubs)."""

from __future__ import annotations

from trafego_analysis.analyses.cross_canal import CanalResumo


class TestCanalResumoDataclass:
    def test_default_inativo(self):
        c = CanalResumo(nome="Teste", ativo=False)
        assert c.spend == 0
        assert c.observacoes == []
        assert c.share_spend == 0

    def test_obs_mutavel(self):
        c = CanalResumo(nome="X", ativo=True)
        c.observacoes.append("msg")
        c2 = CanalResumo(nome="Y", ativo=True)
        # Cada instância tem sua lista (field(default_factory))
        assert c2.observacoes == []


class TestGoogleAggregate:
    def test_agregar_totais_google(self):
        from trafego_analysis.core.google_client import agregar_totais

        rows = [
            {"spend": 100, "impressions": 10000, "clicks": 150, "conversions": 3, "conversion_value": 300},
            {"spend": 200, "impressions": 20000, "clicks": 250, "conversions": 5, "conversion_value": 500},
        ]
        agg = agregar_totais(rows)
        assert agg["spend"] == 300
        assert agg["impressions"] == 30000
        assert agg["conversions"] == 8
        assert agg["revenue"] == 800

    def test_agregar_lista_vazia_google(self):
        from trafego_analysis.core.google_client import agregar_totais

        agg = agregar_totais([])
        assert agg["spend"] == 0
        assert agg["conversions"] == 0


class TestHotmartAggregate:
    def test_agregar_filtra_aprovadas(self):
        from trafego_analysis.core.hotmart_client import agregar_totais

        vendas = [
            {"value": 100, "status": "APPROVED"},
            {"value": 200, "status": "APPROVED"},
            {"value": 150, "status": "REFUNDED"},
            {"value": 50,  "status": "CANCELLED"},
        ]
        agg = agregar_totais(vendas)
        assert agg["vendas_total"] == 4
        assert agg["vendas_aprovadas"] == 2
        assert agg["receita"] == 300
        assert agg["ticket_medio"] == 150

    def test_agregar_sem_aprovadas(self):
        from trafego_analysis.core.hotmart_client import agregar_totais

        vendas = [{"value": 100, "status": "REFUNDED"}]
        agg = agregar_totais(vendas)
        assert agg["vendas_aprovadas"] == 0
        assert agg["ticket_medio"] == 0

    def test_agregar_case_insensitive_status(self):
        from trafego_analysis.core.hotmart_client import agregar_totais

        vendas = [
            {"value": 100, "status": "approved"},
            {"value": 200, "status": "Complete"},
        ]
        agg = agregar_totais(vendas)
        assert agg["vendas_aprovadas"] == 2
        assert agg["receita"] == 300
