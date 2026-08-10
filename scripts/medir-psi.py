#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
medir-psi.py — Mede a performance de uma pagina via PageSpeed Insights API (Google).

Vantagem: quem busca a pagina e o servidor do Google (Lighthouse na infra deles),
nao este ambiente. Por isso a medicao passa mesmo quando o WAF bloqueia a nuvem.

Uso:
    python3 scripts/medir-psi.py <URL> [mobile|desktop|ambos]

Exemplos:
    python3 scripts/medir-psi.py https://seudominio.com.br/sessao
    python3 scripts/medir-psi.py https://seudominio.com.br/sessao desktop
    python3 scripts/medir-psi.py https://seudominio.com.br/sessao ambos

A chave e lida de PAGESPEED_API_KEY no .env (nunca fica escrita neste arquivo).
"""

import os
import sys
import json
import urllib.parse
import urllib.request
from pathlib import Path


def carregar_chave_do_env():
    """Le PAGESPEED_API_KEY do .env, subindo pastas ate encontrar."""
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        candidato = cur / ".env"
        if candidato.exists():
            for linha in candidato.read_text(encoding="utf-8").splitlines():
                if linha.startswith("PAGESPEED_API_KEY="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
        cur = cur.parent
    raise SystemExit("PAGESPEED_API_KEY nao encontrado no .env")


CHAVE = os.environ.get("PAGESPEED_API_KEY") or carregar_chave_do_env()

RATING = {"FAST": "bom", "AVERAGE": "medio", "SLOW": "ruim",
          "good": "bom", "needs-improvement": "medio", "poor": "ruim"}


def medir(url, strategy):
    params = urllib.parse.urlencode({
        "url": url,
        "strategy": strategy,
        "category": "performance",
        "key": CHAVE,
    })
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + params
    req = urllib.request.Request(endpoint, headers={"User-Agent": "medir-psi/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def fmt_ms(valor_ms):
    try:
        v = float(valor_ms)
    except (TypeError, ValueError):
        return "-"
    if v >= 1000:
        return f"{v/1000:.2f} s"
    return f"{int(round(v))} ms"


def mostrar(url, strategy, dados):
    if "error" in dados:
        print(f"\n[{strategy.upper()}] ERRO: {dados['error'].get('message','desconhecido')}")
        return

    lr = dados.get("lighthouseResult", {})
    score = lr.get("categories", {}).get("performance", {}).get("score")
    score_txt = f"{int(round(score*100))}/100" if score is not None else "-"
    audits = lr.get("audits", {})

    def audit(chave):
        return audits.get(chave, {}).get("displayValue", "-")

    rotulo = "MOBILE" if strategy == "mobile" else "DESKTOP"
    print(f"\n========== {rotulo} ==========")
    print(f"URL: {url}")
    print(f"Score de Performance: {score_txt}")
    print("\n-- Metricas de laboratorio (Lighthouse) --")
    print(f"  LCP (Maior Conteudo):        {audit('largest-contentful-paint')}")
    print(f"  FCP (Primeiro Conteudo):     {audit('first-contentful-paint')}")
    print(f"  TBT (Bloqueio Total):        {audit('total-blocking-time')}")
    print(f"  CLS (Estabilidade Visual):   {audit('cumulative-layout-shift')}")
    print(f"  Speed Index:                 {audit('speed-index')}")

    # Dados de campo (CrUX) — usuarios reais nos ultimos 28 dias
    campo = dados.get("loadingExperience", {}).get("metrics", {})
    if campo:
        print("\n-- Dados de campo (usuarios reais, CrUX 28 dias) --")
        mapa = {
            "LARGEST_CONTENTFUL_PAINT_MS": "LCP",
            "FIRST_CONTENTFUL_PAINT_MS": "FCP",
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": "CLS",
            "INTERACTION_TO_NEXT_PAINT": "INP",
            "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "TTFB",
        }
        for chave, nome in mapa.items():
            if chave in campo:
                m = campo[chave]
                p75 = m.get("percentile")
                cat = RATING.get(m.get("category", ""), m.get("category", ""))
                if chave == "CUMULATIVE_LAYOUT_SHIFT_SCORE":
                    valor = f"{p75/100:.2f}" if p75 is not None else "-"
                else:
                    valor = fmt_ms(p75)
                print(f"  {nome:6}: {valor:>10}  ({cat})")
    else:
        print("\n-- Dados de campo (CrUX): sem dados suficientes para esta URL --")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/medir-psi.py <URL> [mobile|desktop|ambos]")
        sys.exit(1)

    url = sys.argv[1]
    modo = (sys.argv[2].lower() if len(sys.argv) > 2 else "mobile")

    if modo == "ambos":
        estrategias = ["mobile", "desktop"]
    elif modo in ("mobile", "desktop"):
        estrategias = [modo]
    else:
        print("Modo invalido. Use: mobile, desktop ou ambos.")
        sys.exit(1)

    for strategy in estrategias:
        try:
            dados = medir(url, strategy)
            mostrar(url, strategy, dados)
        except Exception as e:
            print(f"\n[{strategy.upper()}] Falha na medicao: {e}")

    print()


if __name__ == "__main__":
    main()
