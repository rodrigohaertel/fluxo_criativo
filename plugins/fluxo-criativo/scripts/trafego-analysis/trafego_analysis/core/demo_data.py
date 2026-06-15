"""Dados fictícios dos cenários D1-D7 — replicados da skill markdown.

Usados pelo Modo Demo para gerar análises completas sem precisar de conta
Meta real. Valores realistas do mercado BR infoproduto.

**Aviso:** dados puramente didáticos — nenhum dado real de RTG ou clientes.
"""

from __future__ import annotations

from typing import Any

# --- Base: D1-D5 cenário comum (conta saudável neutra) --------------------

CENARIO_BASE = {
    "nome": "Curso de Marketing Digital (fictício)",
    "ticket": 297.0,
    "periodo_dias": 14,
    "investimento_total": 3200.0,
    "receita": 6534.0,
    "roas": 2.04,
}


# --- Adsets do cenário base -------------------------------------------------

ADSETS_BASE = [
    {
        "adset_name": "HOT_Engajamento_90d",
        "campaign_name": "CV_Curso_Principal_HOT",
        "temperatura": "HOT",
        "spend": 800.0,
        "impressions": 52000,
        "inline_link_clicks": 1040,
        "frequency": 2.1,
        "leads": 18,
        "purchases": 6,
        "cpl": 44.0,
        "cpa": 133.0,
    },
    {
        "adset_name": "COLD_LAL_2pct_Compradores",
        "campaign_name": "CV_Curso_Principal_COLD",
        "temperatura": "COLD",
        "spend": 1400.0,
        "impressions": 90000,
        "inline_link_clicks": 1620,
        "frequency": 1.9,
        "leads": 22,
        "purchases": 10,
        "cpl": 63.0,
        "cpa": 191.0,
    },
    {
        "adset_name": "SUPERCOLD_Broad_25a45",
        "campaign_name": "CV_Curso_Principal_SUPERCOLD",
        "temperatura": "SUPERCOLD",
        "spend": 1000.0,
        "impressions": 44000,
        "inline_link_clicks": 688,
        "frequency": 1.6,
        "leads": 11,
        "purchases": 6,
        "cpl": 91.0,
        "cpa": 275.0,
    },
]


# --- Ads / criativos do cenário base ---------------------------------------

ADS_BASE = [
    {
        "ad_id": "ad_01",
        "ad_name": "AD01_ProblemaSolucao_v3",
        "campaign_name": "CV_Curso_Principal_COLD",
        "adset_name": "COLD_LAL_2pct_Compradores",
        "tipo_mandala": "problema_solucao",
        "hook_rate": 38.0,
        "thumbstop_rate": 29.0,
        "hold_rate": 44.0,
        "ctr": 2.1,
        "cpa": 142.0,
        "frequency": 2.1,
        "tier": "A",
        "spend": 650.0,
        "impressions": 35000,
    },
    {
        "ad_id": "ad_02",
        "ad_name": "AD02_ProvaSocial_depoimento",
        "campaign_name": "CV_Curso_Principal_HOT",
        "adset_name": "HOT_Engajamento_90d",
        "tipo_mandala": "prova_social",
        "hook_rate": 22.0,
        "thumbstop_rate": 18.0,
        "hold_rate": 31.0,
        "ctr": 1.3,
        "cpa": 198.0,
        "frequency": 3.2,
        "tier": "C",
        "spend": 500.0,
        "impressions": 28000,
    },
    {
        "ad_id": "ad_03",
        "ad_name": "AD03_Oportunidade_ultimasVagas",
        "campaign_name": "CV_Curso_Principal_COLD",
        "adset_name": "COLD_LAL_2pct_Compradores",
        "tipo_mandala": "oportunidade",
        "hook_rate": 44.0,
        "thumbstop_rate": 36.0,
        "hold_rate": 51.0,
        "ctr": 2.8,
        "cpa": 118.0,
        "frequency": 1.8,
        "tier": "S",
        "spend": 750.0,
        "impressions": 55000,
    },
    {
        "ad_id": "ad_04",
        "ad_name": "AD04_Curiosidade_segredo",
        "campaign_name": "CV_Curso_Principal_SUPERCOLD",
        "adset_name": "SUPERCOLD_Broad_25a45",
        "tipo_mandala": "curiosidade",
        "hook_rate": 17.0,
        "thumbstop_rate": 14.0,
        "hold_rate": 28.0,
        "ctr": 0.8,
        "cpa": 312.0,
        "frequency": 4.6,
        "tier": "D",
        "spend": 700.0,
        "impressions": 32000,
    },
]


# --- Funil do cenário base -------------------------------------------------

FUNIL_BASE = {
    "impressoes": 186000,
    "thruplay_3s": 65100,
    "hook_rate": 35.0,
    "cliques_link": 3348,
    "ctr": 1.8,
    "lp_views": 2578,
    "lpvr": 77.0,
    "leads": 51,
    "opt_in_rate": 2.0,
    "checkout_iniciado": 89,
    "offer_rate": 3.4,
    "compras": 22,
    "connect_rate": 43.0,  # compras/leads
    "conversao_geral": 0.66,
}


# --- D6: Conta em CRISE ---------------------------------------------------

CENARIO_D6 = {
    "nome": "Conta em Crise — fictícia",
    "ticket": 297.0,
    "periodo_dias": 7,
    "investimento_total": 2800.0,
    "receita": 2378.0,     # ROAS 0.85
    "roas": 0.85,
    "compras": 4,
    "cpa": 700.0,
    "problemas": [
        "CPM subiu 40% em 10 dias (R$ 28 → R$ 39)",
        "Frequência média 6.2 (altamente saturado)",
        "Apenas 2 criativos ativos, ambos >90 dias",
        "Nenhum criativo com Hook Rate > 20%",
        "Funil travado no Offer Rate: 1.2%",
        "Connect Rate: 0.14%",
    ],
    "plano_recuperacao": [
        "1. **Público** — pausar HOT saturado e criar nova Identidade do Consumidor em SUPERCOLD",
        "2. **Criativo** — produzir 4-5 ads novos em 3 tipos diferentes da Mandala",
        "3. **Oferta** — revisar se ainda está clara; pode ser bônus fraco ou urgência inexistente",
    ],
}


# --- D7: Conta em ESCALA ---------------------------------------------------

CENARIO_D7 = {
    "nome": "Conta Escalável — fictícia",
    "ticket": 297.0,
    "periodo_dias": 21,
    "investimento_total": 4800.0,
    "receita": 19680.0,    # ROAS 4.1
    "roas": 4.1,
    "compras": 67,
    "cpa": 72.0,
    "indicadores_positivos": [
        "Frequência média 2.3 (saudável)",
        "5 criativos ativos, 3 em tier A ou S",
        "Hook Rate médio: 41%",
        "LPVR 82% · Opt-in 24% · Connect Rate 3.8%",
        "HOT CPL R$ 31 vs COLD R$ 58 (saudável)",
        "Mandala: 8/18 tipos cobertos",
    ],
    "plano_escala": [
        "1. **Escalar winners gradualmente** (+25% no conjunto de CPL R$ 31 — HOT)",
        "2. **Completar Mandala** com 4-5 tipos ausentes (priorizar Problema-Solução, Prova Social, Contraste)",
        "3. **Ampliar SUPERCOLD** em 40% — espaço confirmado pela Meta achando público sozinha",
    ],
}


# --- Ensine Isso ----------------------------------------------------------

ENSINE_ISSO_HOOK_RATE = {
    "conceito": "Hook Rate",
    "explicacao_simples": (
        "Hook Rate é a porcentagem de pessoas que pararam para assistir pelo menos "
        "3 segundos do seu vídeo. Se de cada 100 pessoas que viram o anúncio, "
        "30 pararam para assistir, seu Hook Rate é 30%."
    ),
    "analogia": (
        "É como uma vitrine de loja: quantas pessoas que passaram na frente pararam "
        "para olhar? Se a vitrine não chama atenção, não adianta ter o melhor produto "
        "lá dentro."
    ),
    "pergunta_fixacao": "Se o Hook Rate está em 15%, o problema está no produto ou no criativo?",
}


ENSINE_ISSO_GARGALO = {
    "conceito": "Gargalo de Funil",
    "explicacao_simples": (
        "Gargalo é a etapa onde você está perdendo mais pessoas do que devia. "
        "É o buraco principal por onde o dinheiro escapa antes de chegar na venda."
    ),
    "analogia": (
        "Imagina um balde com furos. Você pode encher de água (investir mais), "
        "mas enquanto o furo principal não for tampado, o nível nunca sobe. "
        "O gargalo é o maior furo."
    ),
    "pergunta_fixacao": "Como você identifica qual é o gargalo principal de um funil?",
}


ENSINE_ISSO_MANDALA = {
    "conceito": "Mandala VTSD (18 tipos de anúncio)",
    "explicacao_simples": (
        "A Mandala é um sistema com 18 tipos diferentes de anúncio (Prova Social, "
        "Curiosidade, Problema-Solução, etc). Cada tipo conversa com um perfil diferente "
        "de pessoa. Uma conta com só 3 tipos ativos está deixando 15 portas fechadas."
    ),
    "analogia": (
        "É como ter um cardápio: um restaurante que só serve 3 pratos afasta clientes "
        "que queriam comer outra coisa. Com 18 pratos, você serve tipos diferentes "
        "de cliente no mesmo restaurante."
    ),
    "pergunta_fixacao": "Se sua conta está cansando rápido, pode ser falta de Mandala ou fadiga de um tipo só?",
}


ENSINE_ISSO_FREQUENCIA = {
    "conceito": "Frequência (Frequency)",
    "explicacao_simples": (
        "Frequência é quantas vezes a mesma pessoa, em média, viu seu anúncio no período. "
        "Frequência 3.0 = cada pessoa do seu alcance viu o anúncio 3 vezes."
    ),
    "analogia": (
        "É tipo propaganda na TV: uma vez é informação, duas é lembrete, três é insistência, "
        "cinco começa a virar perseguição. Frequência alta cansa a audiência."
    ),
    "pergunta_fixacao": (
        "Frequência subindo de 2 pra 4 em uma semana — o que deveria ter feito antes?"
    ),
}


ENSINE_ISSO_ROAS = {
    "conceito": "ROAS (Return on Ad Spend)",
    "explicacao_simples": (
        "ROAS é quanto você recebe de volta para cada R$ 1 investido em anúncio. "
        "ROAS 3x = cada R$ 1 gasto gera R$ 3 em vendas. ROAS menor que 1x = você está perdendo dinheiro."
    ),
    "analogia": (
        "É o retorno do cofrinho. Coloca R$ 1, tira R$ 3 — cofre bom. "
        "Coloca R$ 1, tira R$ 0,80 — cofre furado."
    ),
    "pergunta_fixacao": "ROAS 2x é bom pra Caixa Rápido? E para Pico escalado?",
}


def get_cenario_base() -> dict[str, Any]:
    """Retorna o cenário base (D1-D5) completo."""
    return {
        **CENARIO_BASE,
        "adsets": ADSETS_BASE,
        "ads": ADS_BASE,
        "funil": FUNIL_BASE,
    }


def get_cenario_d6() -> dict[str, Any]:
    return CENARIO_D6


def get_cenario_d7() -> dict[str, Any]:
    return CENARIO_D7


def ensine_isso_todos() -> list[dict[str, str]]:
    """Retorna todos os blocos Ensine Isso disponíveis."""
    return [
        ENSINE_ISSO_HOOK_RATE,
        ENSINE_ISSO_GARGALO,
        ENSINE_ISSO_MANDALA,
        ENSINE_ISSO_FREQUENCIA,
        ENSINE_ISSO_ROAS,
    ]
