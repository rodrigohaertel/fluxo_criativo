"""Fórmulas canônicas de métricas de tráfego pago Meta Ads.

Fonte única da verdade. Todos os módulos de análise devem consumir deste arquivo
em vez de recalcular inline — garante consistência numérica entre relatórios.

Todas as funções são pure: recebem números, retornam números. Divisão por zero
retorna 0.0 por convenção (métrica indefinida) — quem consome decide se mostra
como "N/A" ou zero.
"""

from __future__ import annotations


def _safe_div(numerator: float, denominator: float) -> float:
    """Divisão segura: retorna 0.0 quando denominador é zero/None."""
    if not denominator:
        return 0.0
    return numerator / denominator


# --- Métricas de criativo (vídeo) --------------------------------------------

def hook_rate(video_3s_views: float, impressions: float) -> float:
    """Hook Rate (%): quantos param o scroll nos primeiros 3 segundos.

    Saudável BR: 25-35%. Crítico: <15%. Excelente: 35%+.
    """
    return _safe_div(video_3s_views, impressions) * 100


def hold_rate(thruplay: float, video_3s_views: float) -> float:
    """Hold Rate (%): dos que pararam em 3s, quantos assistiram até ThruPlay (15s ou fim).

    Saudável BR: 40-50%. Excelente: 60%+. Crítico: <30%.
    """
    return _safe_div(thruplay, video_3s_views) * 100


def thumb_stop_rate(video_3s_views: float, impressions: float) -> float:
    """Thumb-Stop Rate — sinônimo de Hook Rate, incluído por clareza semântica."""
    return hook_rate(video_3s_views, impressions)


# --- Métricas de funil / cliques ---------------------------------------------

def ctr(inline_link_clicks: float, impressions: float) -> float:
    """Link CTR (%): cliques no link sobre impressões.

    Saudável BR: 1.5-2.5% feed; 3%+ em Reels; lead gen 2.59%.
    """
    return _safe_div(inline_link_clicks, impressions) * 100


def ctr_outbound(outbound_clicks: float, impressions: float) -> float:
    """CTR Outbound (%): cliques que saíram do Facebook para fora."""
    return _safe_div(outbound_clicks, impressions) * 100


def connect_rate(landing_page_views: float, link_clicks: float) -> float:
    """Connect Rate (%): quantos cliques efetivamente viram a LP (não bounçaram).

    Saudável: 70-85%. <60% indica problema de LP (velocidade, expectativa quebrada).
    """
    return _safe_div(landing_page_views, link_clicks) * 100


def offer_rate(video_plays_on_lp: float, landing_page_views: float) -> float:
    """Offer / VSL Rate (%): quantos da LP iniciaram o vídeo de venda.

    Saudável infoproduto: 40-60%.
    """
    return _safe_div(video_plays_on_lp, landing_page_views) * 100


def true_play_rate(played_55pct: float, video_started: float) -> float:
    """True Play Rate (%): quantos dos que iniciaram ficaram até >=55% do VSL.

    Saudável: >55%. Abaixo disso VSL/oferta está rompendo na narrativa.
    """
    return _safe_div(played_55pct, video_started) * 100


def checkout_conversion_rate(purchases: float, initiate_checkout: float) -> float:
    """CR Checkout (%): dos que iniciaram checkout, quantos completaram.

    Saudável: 30-50%. Abaixo indica problema de checkout (formulário, preço, pagamento).
    """
    return _safe_div(purchases, initiate_checkout) * 100


# --- Métricas de custo / retorno ---------------------------------------------

def cpm(spend: float, impressions: float) -> float:
    """CPM (R$): custo por mil impressões.

    Benchmark BR 2026: R$17-20 médio.
    """
    return _safe_div(spend, impressions) * 1000


def cpc(spend: float, link_clicks: float) -> float:
    """CPC (R$): custo por clique no link.

    Benchmark BR 2026: R$1.80 médio.
    """
    return _safe_div(spend, link_clicks)


def cpa(spend: float, results: float) -> float:
    """CPA / CPR (R$): custo por resultado (purchase, lead, etc).

    Meta definida pelo usuário no produto (tipicamente 40% do ticket).
    """
    return _safe_div(spend, results)


def roas(conversion_value: float, spend: float) -> float:
    """ROAS: retorno por real gasto. 2.5 = R$ 2.50 de receita por R$ 1 gasto.

    Meta definida pelo usuário no produto (tipicamente 2.5x em infoproduto).
    """
    return _safe_div(conversion_value, spend)


def roi_pct(revenue: float, spend: float) -> float:
    """ROI (%): lucro sobre investimento. ROAS 2.5 equivale a ROI 150%."""
    if not spend:
        return 0.0
    return ((revenue - spend) / spend) * 100


# --- Conveniência ------------------------------------------------------------

def ctr_delta_wow(ctr_current: float, ctr_previous: float) -> float:
    """Delta % do CTR comparando janela atual com janela anterior.

    Retorno positivo = CTR subiu; negativo = caiu.
    """
    return _safe_div(ctr_current - ctr_previous, ctr_previous) * 100


def cpa_drift_pct(cpa_current: float, cpa_baseline: float) -> float:
    """Drift % do CPA vs baseline. Positivo = CPA piorou (subiu)."""
    return _safe_div(cpa_current - cpa_baseline, cpa_baseline) * 100
