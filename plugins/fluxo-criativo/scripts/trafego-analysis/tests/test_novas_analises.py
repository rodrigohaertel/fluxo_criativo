"""Testes smoke das 13 novas análises criadas nas Fases 8A/8B/8C/8D/9.

Focado em lógica pura (sem Meta API): helpers, cálculos, heurísticas.
Integração end-to-end exige conta real — fora do escopo aqui.
"""

from __future__ import annotations

from trafego_analysis.analyses.comparativo_conjuntos import (
    classificar_temperatura,
)
from trafego_analysis.analyses.conta_health import calcular_health
from trafego_analysis.analyses.escalabilidade import analisar_rows as escal_rows
from trafego_analysis.analyses.mandala_vtsd import classificar_copy
from trafego_analysis.analyses.pausa_hierarquica import _ad_ruim
from trafego_analysis.analyses.projecao_escala import projetar

# --- Comparativo de Conjuntos (1.3) --------------------------------------

class TestClassificarTemperatura:
    def test_hot_via_rmk(self):
        assert classificar_temperatura("CV_RMK_7d_compradores") == "HOT"

    def test_hot_via_engajamento(self):
        assert classificar_temperatura("CV_engajamento_90d") == "HOT"

    def test_cold_via_lookalike(self):
        assert classificar_temperatura("CV_COLD_lookalike_2pct") == "COLD"

    def test_supercold_via_broad(self):
        assert classificar_temperatura("CV_supercold_broad_25a45") == "SUPERCOLD"

    def test_indefinido(self):
        assert classificar_temperatura("CV_qualquer_coisa_sem_padrao") == "INDEFINIDO"


# --- Mandala (2.3) --------------------------------------------------------

class TestMandalaCopy:
    def test_problema_solucao(self):
        r = classificar_copy("", "sofrendo com vendas baixas? resolver em 30 dias")
        assert r == "problema_solucao"

    def test_prova_social(self):
        r = classificar_copy("", "mais de 5 mil alunos já aprovaram")
        assert r == "prova_social"

    def test_oportunidade(self):
        r = classificar_copy("", "últimas vagas — fecha hoje")
        assert r == "oportunidade"

    def test_curiosidade_via_voce_sabia(self):
        r = classificar_copy("você sabia?", "dá pra dobrar conversão só mudando uma coisa")
        assert r == "curiosidade"

    def test_sem_match(self):
        r = classificar_copy("lorem ipsum", "dolor sit amet")
        assert r is None


# --- Escalabilidade (1.2) -----------------------------------------------

class TestEscalabilidade:
    def _row(self, spend=500, impressions=30000, freq=2.0, clicks=500, name="COLD_v1"):
        return {
            "campaign_name": name,
            "spend": spend,
            "impressions": impressions,
            "frequency": freq,
            "inline_link_clicks": clicks,
        }

    def test_status_saudavel_sem_sinais(self):
        r = escal_rows([self._row()])
        assert r.status == "saudavel"
        assert r.incremento_sugerido_pct == 27.5

    def test_status_saturado_freq_alta(self):
        r = escal_rows([self._row(freq=5.5, name="COLD_v1")])
        assert r.status == "saturado"
        assert r.incremento_sugerido_pct is None

    def test_retarget_tolera_freq_maior(self):
        # Freq 4.0 em RMK não dispara freq_alta (só em cold)
        r = escal_rows([self._row(freq=4.0, name="RMK_retarget_7d")])
        # Cold rows estão vazias, então sinal freq_alta não avalia
        # Status saudavel OK
        assert r.status in ("saudavel", "monitorar")


# --- Projeção de Escala (3.3) -------------------------------------------

class TestProjetarEscala:
    def test_3_cenarios_retornados(self):
        cenarios = projetar(cpa_atual=100, frequencia=2.0, budget_atual=200)
        assert len(cenarios) == 3
        assert cenarios[0].multiplicador_budget == 1.5
        assert cenarios[2].multiplicador_budget == 3.0

    def test_cpa_sobe_progressivamente(self):
        cenarios = projetar(cpa_atual=100, frequencia=2.0, budget_atual=200)
        assert cenarios[0].cpa_estimado < cenarios[1].cpa_estimado < cenarios[2].cpa_estimado

    def test_freq_alta_gera_risco_alto_em_3x(self):
        cenarios = projetar(cpa_atual=100, frequencia=5.0, budget_atual=200)
        assert cenarios[2].nivel_risco == "alto"

    def test_freq_baixa_permite_escalar(self):
        cenarios = projetar(cpa_atual=100, frequencia=1.5, budget_atual=200)
        assert cenarios[0].nivel_risco == "baixo"


# --- Pausa Hierárquica (4.5) --------------------------------------------

class TestPausaHierarquica:
    def test_ad_ruim_gasto_alto_zero_conversao(self):
        ad = {"spend": 150, "actions": []}
        assert _ad_ruim(ad, cpa_mediano=None) is True

    def test_ad_bom_com_conversao_ok(self):
        ad = {
            "spend": 200,
            "actions": [{"action_type": "purchase", "value": 5}],
        }
        assert _ad_ruim(ad, cpa_mediano=100) is False

    def test_ad_gasto_baixo_nao_flaga(self):
        ad = {"spend": 20, "actions": []}
        assert _ad_ruim(ad, cpa_mediano=None) is False

    def test_ad_cpa_muito_alto_e_freq_alta_e_rankings_ruins(self):
        ad = {
            "spend": 300,
            "actions": [{"action_type": "purchase", "value": 1}],  # CPA 300
            "frequency": 5.0,
            "quality_ranking": "below_average_35",
        }
        assert _ad_ruim(ad, cpa_mediano=100) is True  # CPA > 2× mediano


# --- Health Score (4.1) -------------------------------------------------

class TestHealthScore:
    def test_score_100_em_tudo(self):
        r = calcular_health({
            "tipos_presentes_mandala": 18,
            "freq_media": 2.0,
            "mix_ok": True,
            "etapas_saudaveis": 7,
            "etapas_totais": 7,
            "roas": 4.0,
            "cpa_pct_ticket": 20,
            "variacao_cpl_pct": 10,
        })
        assert r.score_total >= 80
        assert r.classificacao in ("Excelente", "Boa")

    def test_score_baixo_em_crise(self):
        r = calcular_health({
            "tipos_presentes_mandala": 2,
            "freq_media": 6.5,
            "mix_ok": False,
            "etapas_saudaveis": 1,
            "etapas_totais": 5,
            "roas": 0.8,
            "cpa_pct_ticket": 120,
            "variacao_cpl_pct": 45,
        })
        assert r.score_total < 50
        assert r.classificacao == "Crítica"
        assert r.emoji == "🔴"

    def test_dimensoes_com_pesos_corretos(self):
        r = calcular_health({
            "tipos_presentes_mandala": 9,
            "freq_media": 2.5,
            "mix_ok": True,
            "etapas_saudaveis": 4,
            "etapas_totais": 7,
            "roas": 2.5,
            "cpa_pct_ticket": 28,
            "variacao_cpl_pct": 20,
        })
        pesos_total = sum(d.peso_pct for d in r.dimensoes)
        assert pesos_total == 100  # garante que pesos somam 100%


# --- Demo (Fase 9) ------------------------------------------------------

class TestDemoData:
    def test_cenario_base_tem_estrutura_esperada(self):
        from trafego_analysis.core import demo_data
        base = demo_data.get_cenario_base()
        assert "adsets" in base
        assert "ads" in base
        assert "funil" in base
        assert len(base["adsets"]) == 3  # HOT, COLD, SUPERCOLD
        assert len(base["ads"]) == 4

    def test_cenario_d6_eh_crise(self):
        from trafego_analysis.core import demo_data
        d6 = demo_data.get_cenario_d6()
        assert d6["roas"] < 1  # abaixo de 1x
        assert len(d6["problemas"]) >= 5

    def test_cenario_d7_eh_escalavel(self):
        from trafego_analysis.core import demo_data
        d7 = demo_data.get_cenario_d7()
        assert d7["roas"] >= 3.5
        assert len(d7["indicadores_positivos"]) >= 5

    def test_ensine_isso_tem_estrutura_completa(self):
        from trafego_analysis.core import demo_data
        blocos = demo_data.ensine_isso_todos()
        assert len(blocos) >= 5
        for b in blocos:
            assert "conceito" in b
            assert "explicacao_simples" in b
            assert "analogia" in b
            assert "pergunta_fixacao" in b
