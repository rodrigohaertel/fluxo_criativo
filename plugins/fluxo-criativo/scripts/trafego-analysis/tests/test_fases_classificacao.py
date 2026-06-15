"""Testes do classificador de campanhas em fases do funil."""

from __future__ import annotations

from trafego_analysis.analyses.fases_funil import classificar_campanha

REGEX_GENERICO = {
    "topo": ["topo", "awareness", "cold", "prospecting", "desc"],
    "meio": ["meio", "consideration", "mid"],
    "fundo": ["fundo", "conversion", "hot", "retarget", "rmk", "venda"],
}


REGEX_TOFU = {
    "tofu": ["tofu", "top", "awareness"],
    "mofu": ["mofu", "middle", "consideration"],
    "bofu": ["bofu", "bottom", "conversion", "purchase"],
}


REGEX_PERPETUO = {
    "desc":      ["desc", "descoberta", "awareness"],
    "rel_prosp": ["rel.?prosp", "relacionamento.?prospect"],
    "cv_lead":   ["cv.?lead", "captura.?lead", "cpl"],
    "rel_lead":  ["rel.?lead", "relacionamento.?lead"],
    "cv":        [r"^cv[\s_-]", "conversao", "venda"],
    "rmk":       ["rmk", "remarketing", "retarget"],
}


class TestGenerico:
    def test_topo_bate_com_cold(self):
        assert classificar_campanha("COLD - CURSO XYZ", REGEX_GENERICO) == "topo"

    def test_fundo_bate_com_rmk(self):
        assert classificar_campanha("RMK 7d - XYZ", REGEX_GENERICO) == "fundo"

    def test_outros_quando_nao_bate(self):
        assert classificar_campanha("algum_nome_aleatorio", REGEX_GENERICO) == "outros"


class TestTOFU:
    def test_tofu_match_top(self):
        assert classificar_campanha("TOP - Meta Campaign", REGEX_TOFU) == "tofu"

    def test_mofu_match(self):
        assert classificar_campanha("MOFU - Conversao Lead", REGEX_TOFU) == "mofu"

    def test_bofu_purchase(self):
        assert classificar_campanha("BOFU - Purchase Pixel", REGEX_TOFU) == "bofu"


class TestPerpetuo6Fases:
    def test_desc(self):
        assert classificar_campanha("DESC - Topo Funnel", REGEX_PERPETUO) == "desc"

    def test_rel_prosp(self):
        assert classificar_campanha("REL PROSP - 7 dias", REGEX_PERPETUO) == "rel_prosp"

    def test_cv_lead(self):
        assert classificar_campanha("CV LEAD - Captura Ebook", REGEX_PERPETUO) == "cv_lead"

    def test_rel_lead(self):
        assert classificar_campanha("REL LEAD - Aquecimento", REGEX_PERPETUO) == "rel_lead"

    def test_cv_isolado(self):
        assert classificar_campanha("CV - Purchase", REGEX_PERPETUO) == "cv"

    def test_cv_nao_casa_com_cvlead(self):
        # "cv_lead" deve casar com cv_lead, NÃO com cv isolado
        result = classificar_campanha("CV_LEAD_OPC1", REGEX_PERPETUO)
        assert result == "cv_lead"

    def test_rmk(self):
        assert classificar_campanha("RMK 14d all visitors", REGEX_PERPETUO) == "rmk"


class TestEdgeCases:
    def test_campaign_name_vazio(self):
        assert classificar_campanha("", REGEX_GENERICO) == "outros"

    def test_regex_vazio(self):
        # Sem regex configurado, tudo vai pra outros
        assert classificar_campanha("qualquer nome", {}) == "outros"

    def test_regex_invalido_nao_quebra(self):
        # Regex com erro de sintaxe é silenciosamente ignorado
        regex_bugado = {"x": ["[invalid(regex"]}
        assert classificar_campanha("qualquer coisa", regex_bugado) == "outros"

    def test_case_insensitive(self):
        assert classificar_campanha("rmk teste", REGEX_PERPETUO) == "rmk"
        assert classificar_campanha("RMK TESTE", REGEX_PERPETUO) == "rmk"
        assert classificar_campanha("Rmk Teste", REGEX_PERPETUO) == "rmk"
