#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dono14-clarity.py — Métricas do Microsoft Clarity direto pela Data Export API,
sem depender do conector MCP (que não carrega em sessões automáticas).

Cobre: sessões, scroll médio, tempo de engajamento, dead/rage clicks por URL
(último dia fechado). Gravações de sessão NÃO saem por esta API (ficam para a
sessão interativa via conector, quando necessário).

ATENÇÃO: a API do Clarity aceita no MÁXIMO 10 chamadas por projeto por dia.
Este script faz 1 chamada por execução. Não rodar em loop.

Chave lida do .env (nunca fica neste arquivo):
  CLARITY_API_TOKEN=...   (Clarity > projeto > Settings > Data Export > Generate new API token)

Uso: py -3 scripts/dono14-clarity.py [numOfDays 1-3]   (padrão: 1)
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def carregar_token():
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        env = cur / ".env"
        if env.exists():
            for linha in env.read_text(encoding="utf-8").splitlines():
                if linha.startswith("CLARITY_API_TOKEN="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
        cur = cur.parent
    sys.exit("ERRO: CLARITY_API_TOKEN nao encontrado no .env. "
             "Gere em Clarity > projeto docustoaolucro > Settings > Data Export > Generate new API token "
             "e adicione a linha CLARITY_API_TOKEN=... no .env.")


TOK = carregar_token()
num_days = sys.argv[1] if len(sys.argv) > 1 else "1"

url = "https://www.clarity.ms/export-data/api/v1/project-live-insights?" + urllib.parse.urlencode({
    "numOfDays": num_days,
    "dimension1": "URL",
})
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOK}", "Accept": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    corpo = e.read().decode("utf-8", "replace")[:300]
    sys.exit(f"ERRO Clarity API: HTTP {e.code}. {corpo}")

# Estrutura esperada: lista de metricas, cada uma com "metricName" e "information" (lista por URL).
# Agrega por CAMINHO (descarta querystring/UTM) para o relatorio ficar legivel.
def caminho(u):
    u = (u or "").split("?", 1)[0]
    u = u.replace("https://docustoaolucro.com", "")
    return u or "(total)"


def num_ou_zero(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


agreg = {}
for metrica in data if isinstance(data, list) else []:
    nome = metrica.get("metricName", "?")
    for linha in metrica.get("information", []) or []:
        u = caminho(linha.get("URL") or linha.get("Url") or linha.get("url"))
        alvo = agreg.setdefault(u, {"sess": 0.0, "scroll_pond": 0.0, "ativo": 0.0, "dead": 0.0, "rage": 0.0, "sess_scroll": 0.0})
        if nome == "Traffic":
            alvo["sess"] += num_ou_zero(linha.get("totalSessionCount"))
        elif nome == "ScrollDepth":
            s = num_ou_zero(linha.get("totalSessionCount") or 1)
            alvo["scroll_pond"] += num_ou_zero(linha.get("averageScrollDepth")) * s
            alvo["sess_scroll"] += s
        elif nome == "EngagementTime":
            alvo["ativo"] += num_ou_zero(linha.get("activeTime") or linha.get("totalTime"))
        elif nome == "DeadClickCount":
            alvo["dead"] += num_ou_zero(linha.get("subTotal"))
        elif nome == "RageClickCount":
            alvo["rage"] += num_ou_zero(linha.get("subTotal"))

print("=" * 78)
print(f"CLARITY (Data Export API, direto) | ultimo(s) {num_days} dia(s) fechado(s) | por caminho")
print("=" * 78)
print(f"  {'caminho':<28}{'sessoes':>8}{'scroll_medio':>14}{'tempo_ativo_s':>15}{'dead':>6}{'rage':>6}")
for u in sorted(agreg, key=lambda x: -agreg[x]["sess"]):
    v = agreg[u]
    if v["sess"] == 0 and u == "(total)":
        continue
    scroll = (v["scroll_pond"] / v["sess_scroll"]) if v["sess_scroll"] else 0
    print(f"  {u[:26]:<28}{int(v['sess']):>8}{scroll:>13.1f}%{int(v['ativo']):>15}{int(v['dead']):>6}{int(v['rage']):>6}")
print("-" * 78)
print("Metricas agregadas: Traffic, ScrollDepth, EngagementTime, DeadClickCount, RageClickCount.")
print("Limite da API: 10 chamadas/dia. Gravacoes de sessao: so pelo conector, na sessao interativa.")
