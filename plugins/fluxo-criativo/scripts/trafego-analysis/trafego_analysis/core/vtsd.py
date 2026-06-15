"""Terminologia e lógica do método VTSD — Venda Todo Santo Dia (Leandro Ladeira).

Este módulo é a **fonte única da verdade** para a linguagem VTSD na CLI. Todos
os templates Jinja2 e mensagens do CLI devem consumir daqui para garantir
consistência com a skill Claude Code (pasta `skill/`).

Princípio fundamental do método aplicado ao tráfego:
    "Cada métrica que cai indica um elemento do método que está falhando."

Por exemplo: Hook Rate baixo não é "problema técnico do vídeo" — é
**Urgência Oculta fraca**. CTR baixo não é "criativo ruim" — é
**Identidade do Produto confusa**.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# --- Glossário VTSD --------------------------------------------------------

TERMOS_VTSD: dict[str, str] = {
    "Urgência Oculta":
        "Dor que o público sente mas não verbaliza — deve aparecer no hook do criativo",
    "Quadro na Parede":
        "Resultado final que o produto entrega — deve estar claro na promessa do anúncio",
    "Furadeira":
        "Método do produto — deve ser comunicado na página e nos criativos de meio/fundo",
    "Decorados":
        "Benefícios percebidos — aumentam Hold Rate e reduzem abandono de checkout",
    "Identidade do Consumidor":
        "Público ideal — define segmentação, temperatura e linguagem dos anúncios",
    "Identidade do Comunicador":
        "Tom, valores e estilo do criador — define como a mensagem é dita",
    "Identidade do Produto":
        "Posicionamento — define diferencial competitivo e angle dos criativos",
    "Pico de Vendas":
        "Período de lançamento — maior concentração de budget em HOT e COLD",
    "Evergreen/Perpétuo":
        "Funil sempre ativo — foco em eficiência e CPL estável",
    "Caixa Rápido":
        "Produto low ticket de conversão rápida — ROAS mínimo 3x",
    "HOT":
        "Público quente (engajamento, video views, lista de leads)",
    "COLD":
        "Público frio (interesses, lookalike)",
    "SUPERCOLD":
        "Público aberto (sem segmentação específica)",
    "Mandala":
        "Sistema de 18 tipos de anúncio — garante diversidade criativa",
    "Isca Digital":
        "Material de entrada (PDF, aula, planilha) que captura o lead",
    "VVV":
        "Video Vendas Vertical — formato de venda direta em vídeo",
    "Orderbump":
        "Oferta extra no momento do checkout que eleva o ticket médio",
    "Upsell":
        "Oferta complementar após a compra principal",
}


# --- Mapeamento métrica → elemento VTSD -----------------------------------

METRICA_PARA_VTSD: dict[str, tuple[str, str]] = {
    # (elemento VTSD, pergunta diagnóstica)
    "hook_rate": (
        "Urgência Oculta",
        "A Urgência Oculta está ativando a dor no primeiro segundo?",
    ),
    "thumbstop_rate": (
        "Identidade do Comunicador",
        "O visual/abertura comunica o tom certo para parar o scroll?",
    ),
    "hold_rate": (
        "Decorados + Furadeira",
        "Os benefícios e o método estão sendo percebidos no meio do vídeo?",
    ),
    "play_through_rate": (
        "Furadeira",
        "O método está tão claro que a pessoa assiste até o fim?",
    ),
    "ctr": (
        "Identidade do Produto",
        "A Identidade do Produto está clara no criativo?",
    ),
    "lpvr": (
        "Coerência anúncio↔página",
        "A promessa do anúncio está alinhada com o que a página entrega?",
    ),
    "opt_in_rate": (
        "Isca Digital / VVV",
        "A Isca Digital ou o VVV está convertendo quem chega?",
    ),
    "offer_rate": (
        "Oferta",
        "A Oferta está chegando para as pessoas certas no momento certo?",
    ),
    "connect_rate": (
        "Furadeira + Decorados",
        "A Furadeira e os Decorados estão sendo percebidos na página de vendas?",
    ),
    "ltv_rate": (
        "Orderbump + Upsell",
        "O Orderbump e o Upsell estão ativos e com oferta complementar clara?",
    ),
    "cpl": (
        "Identidade do Consumidor",
        "O público certo está sendo alcançado pelo valor certo?",
    ),
    "roas": (
        "Conjunto VTSD (Oferta + Furadeira + Decorados)",
        "O funil inteiro está entregando valor percebido acima do custo?",
    ),
}


def elemento_vtsd(metrica: str) -> tuple[str, str] | None:
    """Retorna (elemento, pergunta diagnóstica) da métrica, ou None."""
    return METRICA_PARA_VTSD.get(metrica.lower().replace(" ", "_"))


# --- Mandala — 18 tipos de anúncio ----------------------------------------

MANDALA_TIPOS: list[dict[str, str]] = [
    {"id": "comparacao", "nome": "Comparação", "caract": "'Antes X fazia isso, agora...'"},
    {"id": "apelo_emocional", "nome": "Apelo Emocional", "caract": "Conecta via emoção antes de falar do produto"},
    {"id": "certo_errado", "nome": "Certo vs. Errado", "caract": "Mostra o jeito errado que a maioria faz"},
    {"id": "curiosidade", "nome": "Curiosidade", "caract": "Abre um loop sem resolver no anúncio"},
    {"id": "demonstracao", "nome": "Demonstração", "caract": "Mostra o produto funcionando na prática"},
    {"id": "oportunidade", "nome": "Oportunidade", "caract": "Janela que pode ser perdida"},
    {"id": "visual", "nome": "Visual", "caract": "A imagem/cena faz o trabalho do hook"},
    {"id": "dilema", "nome": "Dilema", "caract": "Coloca o público num cenário de escolha"},
    {"id": "clickbait", "nome": "Clickbait", "caract": "Título ou abertura provocativa"},
    {"id": "prova_social", "nome": "Prova Social", "caract": "Depoimento, resultado, número de alunos"},
    {"id": "contraste", "nome": "Contraste", "caract": "Antes × Depois"},
    {"id": "historia", "nome": "História", "caract": "Narrativa pessoal ou de aluno"},
    {"id": "ultra_segmentado", "nome": "Ultra Segmentado", "caract": "Fala diretamente com um subnicho específico"},
    {"id": "reflexao", "nome": "Reflexão", "caract": "Pergunta que faz o público se questionar"},
    {"id": "explicacao", "nome": "Explicação", "caract": "Educa antes de vender"},
    {"id": "problema_solucao", "nome": "Problema-Solução", "caract": "Nomeia a dor → apresenta o caminho"},
    {"id": "sensacao", "nome": "Sensação", "caract": "Descreve a experiência de ter o resultado"},
    {"id": "mito", "nome": "Mito", "caract": "Derruba uma crença comum do nicho"},
]


def mandala_total() -> int:
    return len(MANDALA_TIPOS)


def mandala_por_id(tipo_id: str) -> dict[str, str] | None:
    for t in MANDALA_TIPOS:
        if t["id"] == tipo_id:
            return t
    return None


# --- Mix HOT/COLD/SUPERCOLD por fase VTSD --------------------------------

FaseVTSD = Literal["pico", "evergreen", "caixa_rapido", "teste_inicial"]

MIX_IDEAL: dict[FaseVTSD, dict[str, tuple[int, int]]] = {
    # fase → temperatura → (min%, max%)
    "pico": {
        "HOT": (40, 40),
        "COLD": (40, 40),
        "SUPERCOLD": (20, 20),
    },
    "evergreen": {
        "HOT": (20, 20),
        "COLD": (50, 50),
        "SUPERCOLD": (30, 30),
    },
    "caixa_rapido": {
        "HOT": (0, 20),
        "COLD": (40, 40),
        "SUPERCOLD": (40, 60),
    },
    "teste_inicial": {
        "HOT": (0, 0),
        "COLD": (50, 50),
        "SUPERCOLD": (50, 50),
    },
}


# --- Tier de criativos (escala S/A/B/C/D) ---------------------------------

@dataclass(frozen=True)
class Tier:
    letra: str
    nome: str
    score_min: int
    score_max: int
    acao: str
    emoji: str


TIERS: list[Tier] = [
    Tier("S", "Top Performer", 85, 100,
         "Duplicar, escalar budget, criar variações", "🏅"),
    Tier("A", "Sólido", 70, 84,
         "Manter, monitorar fadiga", "✅"),
    Tier("B", "Médio, potencial", 55, 69,
         "Testar novo CTA ou ângulo diferente", "🟡"),
    Tier("C", "Abaixo do esperado", 40, 54,
         "Pausar em 7 dias se não melhorar", "🟠"),
    Tier("D", "Não funciona", 0, 39,
         "Pausar agora, analisar por que falhou", "🔴"),
]


def classify_tier(score: float) -> Tier:
    """Classifica score (0-100) em um dos 5 tiers.

    TIERS está ordenado do mais alto (S) para o mais baixo (D). Usar `>=`
    com o score_min evita gaps causados por scores float (ex: 84.9).
    """
    s = max(0, min(100, score))
    for t in TIERS:
        if s >= t.score_min:
            return t
    return TIERS[-1]


# --- Thresholds VTSD para análise de funil --------------------------------

THRESHOLDS_FUNIL: dict[str, dict[str, float]] = {
    "hook_rate": {"ideal": 30.0, "critico": 15.0, "unidade": "%"},
    "thumbstop_rate": {"ideal": 25.0, "critico": 10.0, "unidade": "%"},
    "hold_rate": {"ideal": 40.0, "critico": 20.0, "unidade": "%"},
    "play_through_rate": {"ideal": 5.0, "critico": 2.0, "unidade": "%"},
    "ctr_frio": {"ideal": 1.5, "critico": 0.8, "unidade": "%"},
    "ctr_quente": {"ideal": 3.0, "critico": 1.5, "unidade": "%"},
    "lpvr": {"ideal": 70.0, "critico": 50.0, "unidade": "%"},
    "opt_in_rate_isca": {"ideal": 20.0, "critico": 10.0, "unidade": "%"},
    "opt_in_rate_vsl": {"ideal": 5.0, "critico": 2.0, "unidade": "%"},
    "offer_rate_leads": {"ideal": 5.0, "critico": 2.0, "unidade": "%"},
    "offer_rate_checkout": {"ideal": 30.0, "critico": 15.0, "unidade": "%"},
    "connect_rate": {"ideal": 2.0, "critico": 0.5, "unidade": "%"},
    "ltv_rate_orderbump": {"ideal": 20.0, "critico": 8.0, "unidade": "%"},
    "ltv_rate_upsell": {"ideal": 10.0, "critico": 3.0, "unidade": "%"},
}


def threshold(metrica: str) -> dict[str, float] | None:
    """Retorna dict com {'ideal', 'critico', 'unidade'} ou None."""
    return THRESHOLDS_FUNIL.get(metrica.lower())


def status_vs_threshold(valor: float, metrica: str) -> str:
    """Retorna '🟢', '🟡' ou '🔴' comparando valor com thresholds da métrica."""
    t = threshold(metrica)
    if not t:
        return "—"
    if valor >= t["ideal"]:
        return "🟢"
    if valor >= t["critico"]:
        return "🟡"
    return "🔴"


# --- Regras absolutas da skill --------------------------------------------

REGRAS_ABSOLUTAS: list[str] = [
    "NUNCA inventar métricas — se o dado não estiver disponível, informar e pedir",
    "SEMPRE usar terminologia VTSD nas análises",
    "NUNCA deixar uma análise sem ação recomendada concreta",
    "SEMPRE identificar o gargalo principal antes de listar secundários",
    "NUNCA usar jargão técnico sem explicar em linguagem do método",
    "No Modo Demo: deixar claro que os dados são fictícios para fins didáticos",
]
