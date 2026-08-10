#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coleta insights nivel anuncio (com video) para a analise profunda diaria.
Salva resultado em /tmp/dono14-ad-insights.json
Uso: py -3 scripts/dono14-insights-adlevel.py
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error
from datetime import date, timedelta

ABO = "120247419652220527"
API = "https://graph.facebook.com/v19.0"

def carregar_token():
    cur = os.path.dirname(os.path.abspath(__file__))
    while True:
        env = os.path.join(cur, ".env")
        if os.path.exists(env):
            for linha in open(env, encoding="utf-8").read().splitlines():
                if linha.startswith("FB_ACCESS_TOKEN_PERMANENTE="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
        novo = os.path.dirname(cur)
        if novo == cur: break
        cur = novo
    sys.exit("FB_ACCESS_TOKEN_PERMANENTE nao encontrado no .env")

TOKEN = carregar_token()

def get(path, params):
    params = dict(params)
    params["access_token"] = TOKEN
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print(f"[ERRO] {path}: {body[:300]}", file=sys.stderr)
        return {"data": []}
    except Exception as e:
        print(f"[ERRO REDE] {e}", file=sys.stderr)
        return {"data": []}
    if isinstance(data, dict) and data.get("error"):
        print(f"[ERRO API] {data['error'].get('message')}", file=sys.stderr)
        return {"data": []}
    return data

def num(x):
    try: return float(x)
    except: return 0.0

def act(actions, t):
    for a in (actions or []):
        if a.get("action_type") == t:
            try: return float(a.get("value", 0))
            except: return 0.0
    return 0.0

def vact(vactions, t):
    for a in (vactions or []):
        if a.get("action_type") == t:
            try: return float(a.get("value", 0))
            except: return 0.0
    return 0.0

hoje = date.today()
ini60 = hoje - timedelta(days=60)
ini_teste = date(2026, 7, 21)  # inicio do A39

VIDEO_FIELDS = ",".join([
    "ad_name", "ad_id", "date_start",
    "spend", "impressions", "reach",
    "inline_link_clicks", "inline_link_click_ctr", "cpc", "cpm",
    "actions",
    "video_p25_watched_actions",
    "video_p50_watched_actions",
    "video_p75_watched_actions",
    "video_p95_watched_actions",
    "video_avg_time_watched_actions",
    "video_thruplay_watched_actions",
])

print(">>> Buscando: por anuncio, dia a dia (janela do teste)...")
# dia a dia, janela do teste (A39 e A40)
diario = get(f"{ABO}/insights", {
    "level": "ad",
    "time_increment": 1,
    "time_range": json.dumps({"since": ini_teste.isoformat(), "until": hoje.isoformat()}),
    "fields": VIDEO_FIELDS,
}).get("data", [])
print(f"    {len(diario)} registros retornados")

print(">>> Buscando: por anuncio, 60 dias acumulado...")
# acumulado 60 dias (tabela que decide)
acum60 = get(f"{ABO}/insights", {
    "level": "ad",
    "date_preset": "last_60_days",
    "fields": VIDEO_FIELDS,
}).get("data", [])
print(f"    {len(acum60)} registros retornados")

# salvar resultado
out = {
    "gerado_em": hoje.isoformat(),
    "diario_teste": diario,
    "acumulado_60d": acum60,
}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "meus-produtos", "dono-14", "trafego", "analise", "diario", ".ad-insights-cache.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f">>> Salvo em: {os.path.abspath(path)}")
