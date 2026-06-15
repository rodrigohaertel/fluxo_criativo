"""Testes da taxonomia de criativos (copy metrics + classificação de formato)."""

from __future__ import annotations

from trafego_analysis.analyses.criativos_taxonomia import (
    CreativeFeatures,
    _analyze_copy,
    _classify_formato,
    _classify_luminosidade,
    comum_em,
    dna_do_ganhador,
)


class TestClassifyFormato:
    def test_vertical(self):
        fmt, ratio = _classify_formato(1080, 1920)  # 9:16
        assert fmt == "vertical"
        assert ratio > 1.7

    def test_quadrado(self):
        fmt, _ = _classify_formato(1080, 1080)
        assert fmt == "quadrado"

    def test_horizontal(self):
        fmt, _ = _classify_formato(1920, 1080)  # 16:9
        assert fmt == "horizontal"

    def test_sem_dimensoes(self):
        fmt, ratio = _classify_formato(0, 0)
        assert fmt == "?"
        assert ratio == 0


class TestClassifyLuminosidade:
    def test_escura(self):
        # RGB perto do preto
        assert _classify_luminosidade([(20, 20, 20), (30, 30, 30), (40, 40, 40)]) == "escura"

    def test_clara(self):
        # RGB perto do branco
        assert _classify_luminosidade([(220, 220, 220), (240, 240, 240), (230, 230, 230)]) == "clara"

    def test_media(self):
        # cinza médio
        assert _classify_luminosidade([(128, 128, 128), (120, 130, 140)]) == "media"

    def test_vazio(self):
        assert _classify_luminosidade([]) == "?"


class TestAnalyzeCopy:
    def test_tem_pergunta(self):
        tp, _, _ = _analyze_copy("Você quer dobrar suas vendas?", "Descubra como.")
        assert tp is True

    def test_sem_pergunta(self):
        tp, _, _ = _analyze_copy("Aumente suas vendas", "Descubra como.")
        assert tp is False

    def test_tem_numero(self):
        _, tn, _ = _analyze_copy("10x mais vendas", "Método 2026")
        assert tn is True

    def test_sem_numero(self):
        _, tn, _ = _analyze_copy("Aumente vendas agora", "Descubra o método")
        assert tn is False

    def test_emoji_count(self):
        _, _, ec = _analyze_copy("Vendas em alta! 🚀", "Descubra 💰🔥")
        assert ec == 3

    def test_sem_emoji(self):
        _, _, ec = _analyze_copy("Texto puro sem emoji", "nada aqui")
        assert ec == 0


class TestComumEm:
    def test_valor_majoritario(self):
        val, n = comum_em(["a", "a", "a", "b"])
        assert val == "a"
        assert n == 3

    def test_lista_vazia(self):
        val, n = comum_em([])
        assert val is None
        assert n == 0

    def test_empate_retorna_primeiro(self):
        val, n = comum_em(["x", "y"])
        assert val in ("x", "y")
        assert n == 1


class TestDnaDoGanhador:
    def test_dna_vazio(self):
        assert dna_do_ganhador([]) == {}

    def test_dna_3_winners_vertical(self):
        winners = [
            CreativeFeatures(
                ad_id=str(i), formato="vertical",
                paleta_luminosidade="escura",
                copy_cta_type="LEARN_MORE",
                title_len=40, body_len=120,
                copy_tem_pergunta=True, copy_tem_numero=True,
                copy_emoji_count=2,
            )
            for i in range(3)
        ]
        dna = dna_do_ganhador(winners)
        assert dna["n_winners"] == 3
        assert dna["formato"]["valor"] == "vertical"
        assert dna["formato"]["count"] == 3
        assert dna["luminosidade"]["valor"] == "escura"
        assert dna["cta"]["valor"] == "LEARN_MORE"
        assert dna["copy_com_pergunta_n"] == 3
        assert dna["copy_com_numero_n"] == 3
        assert dna["copy_com_emoji_n"] == 3
        assert dna["title_len_medio"] == 40
        assert dna["body_len_medio"] == 120

    def test_dna_misto(self):
        winners = [
            CreativeFeatures(ad_id="1", formato="vertical", copy_tem_pergunta=True),
            CreativeFeatures(ad_id="2", formato="vertical", copy_tem_pergunta=False),
            CreativeFeatures(ad_id="3", formato="quadrado", copy_tem_pergunta=True),
        ]
        dna = dna_do_ganhador(winners)
        assert dna["n_winners"] == 3
        # vertical é maioria (2/3)
        assert dna["formato"]["valor"] == "vertical"
        assert dna["formato"]["count"] == 2
        assert dna["copy_com_pergunta_n"] == 2
