"""Testes do módulo VTSD — terminologia e lógica central do método."""

from __future__ import annotations

from trafego_analysis.core import vtsd


class TestGlossario:
    def test_termos_principais_presentes(self):
        essenciais = [
            "Urgência Oculta", "Quadro na Parede", "Furadeira", "Decorados",
            "Identidade do Consumidor", "Identidade do Comunicador",
            "Identidade do Produto", "Pico de Vendas", "Caixa Rápido",
            "HOT", "COLD", "SUPERCOLD", "Mandala",
        ]
        for termo in essenciais:
            assert termo in vtsd.TERMOS_VTSD, f"termo VTSD ausente: {termo}"

    def test_cada_termo_tem_descricao(self):
        for termo, desc in vtsd.TERMOS_VTSD.items():
            assert len(desc) > 10, f"descrição muito curta: {termo}"


class TestElementoVtsd:
    def test_hook_rate_mapeia_para_urgencia_oculta(self):
        elemento, pergunta = vtsd.elemento_vtsd("hook_rate")
        assert elemento == "Urgência Oculta"
        assert "primeiro segundo" in pergunta.lower() or "dor" in pergunta.lower()

    def test_ctr_mapeia_para_identidade_produto(self):
        elemento, _ = vtsd.elemento_vtsd("ctr")
        assert elemento == "Identidade do Produto"

    def test_connect_rate_mapeia_para_furadeira_decorados(self):
        elemento, _ = vtsd.elemento_vtsd("connect_rate")
        assert "Furadeira" in elemento
        assert "Decorados" in elemento

    def test_metrica_inexistente_retorna_none(self):
        assert vtsd.elemento_vtsd("abc_inexistente") is None


class TestMandala:
    def test_exatamente_18_tipos(self):
        assert vtsd.mandala_total() == 18

    def test_tipos_classicos_presentes(self):
        ids = {t["id"] for t in vtsd.MANDALA_TIPOS}
        essenciais = {
            "problema_solucao", "prova_social", "curiosidade",
            "oportunidade", "contraste", "mito",
        }
        assert essenciais.issubset(ids)

    def test_cada_tipo_tem_nome_e_caract(self):
        for t in vtsd.MANDALA_TIPOS:
            assert "id" in t and t["id"]
            assert "nome" in t and t["nome"]
            assert "caract" in t and t["caract"]

    def test_por_id_retorna_tipo_correto(self):
        t = vtsd.mandala_por_id("problema_solucao")
        assert t is not None
        assert t["nome"] == "Problema-Solução"

    def test_por_id_nao_existe(self):
        assert vtsd.mandala_por_id("xyz_nao_existe") is None


class TestMixIdeal:
    def test_mix_pico_soma_100(self):
        mix = vtsd.MIX_IDEAL["pico"]
        soma_max = sum(maxp for _, maxp in mix.values())
        assert soma_max == 100

    def test_evergreen_cold_eh_maior(self):
        mix = vtsd.MIX_IDEAL["evergreen"]
        assert mix["COLD"][0] >= mix["HOT"][0]

    def test_caixa_rapido_supercold_pode_ser_maior(self):
        mix = vtsd.MIX_IDEAL["caixa_rapido"]
        # No Caixa Rápido, SUPERCOLD pode ir até 60%
        assert mix["SUPERCOLD"][1] == 60


class TestTiersSABCD:
    def test_cinco_tiers_presentes(self):
        letras = {t.letra for t in vtsd.TIERS}
        assert letras == {"S", "A", "B", "C", "D"}

    def test_classify_tier_boundaries(self):
        assert vtsd.classify_tier(85).letra == "S"
        assert vtsd.classify_tier(100).letra == "S"
        assert vtsd.classify_tier(84.9).letra == "A"
        assert vtsd.classify_tier(70).letra == "A"
        assert vtsd.classify_tier(55).letra == "B"
        assert vtsd.classify_tier(40).letra == "C"
        assert vtsd.classify_tier(39).letra == "D"
        assert vtsd.classify_tier(0).letra == "D"

    def test_classify_fora_range(self):
        # Acima de 100 ou abaixo de 0 → clampa
        assert vtsd.classify_tier(150).letra == "S"
        assert vtsd.classify_tier(-10).letra == "D"


class TestThresholds:
    def test_hook_rate_threshold_ideal_30(self):
        t = vtsd.threshold("hook_rate")
        assert t["ideal"] == 30.0
        assert t["critico"] == 15.0

    def test_connect_rate_threshold_critico_baixo(self):
        t = vtsd.threshold("connect_rate")
        assert t["critico"] < t["ideal"]

    def test_metrica_desconhecida_retorna_none(self):
        assert vtsd.threshold("xyz") is None

    def test_status_ideal(self):
        # Hook rate 35 (ideal é 30)
        assert vtsd.status_vs_threshold(35.0, "hook_rate") == "🟢"

    def test_status_atencao(self):
        # Hook rate 20 (entre critico 15 e ideal 30)
        assert vtsd.status_vs_threshold(20.0, "hook_rate") == "🟡"

    def test_status_critico(self):
        # Hook rate 10 (abaixo de critico 15)
        assert vtsd.status_vs_threshold(10.0, "hook_rate") == "🔴"


class TestRegras:
    def test_nunca_inventar_metricas_esta_na_lista(self):
        regras = " ".join(vtsd.REGRAS_ABSOLUTAS)
        assert "NUNCA inventar" in regras
        assert "SEMPRE usar terminologia VTSD" in regras
