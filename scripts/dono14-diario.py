#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitura diaria do funil Dono 14% (lado Meta + VSL).

Puxa, da Marketing API:
  - a campanha consolidada (insights diarios da ultima semana)
  - os eventos do VSL no pixel (VSL_Play / Unmute / retencao)

NAO conta leads aqui: a fonte de verdade dos leads e o BANCO
(contact_submissions), lido por fora via execute_sql.

Uso:  py -3 scripts/dono14-diario.py
Le FB_ACCESS_TOKEN_PERMANENTE do .env. Nenhum token fica escrito no script.
Saida em ASCII (consumida pelo assistente), por isso sem acentos.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

# Campanhas DONO14. A ABO de teste e a campanha VIVA desde 03/07/2026.
# O CBO foi pausado em 02/07 23:59, mas segue aqui na CAUDA DE ATRIBUICAO:
# a janela de atribuicao e de 7 dias, entao leads/conversoes de cliques antigos
# ainda pingam atribuidos ao CBO ate ~09/07/2026. Aposentar o CBO desta lista
# depois de 09/07 (deixar so a ABO).
CAMPANHAS = [
    ("CBO Vencedores (VIVA desde 07/07, A36/A37/A38, A32 pausado)", "120246284721790527"),
    ("ABO Teste de Criativos (ENCERRADA 07/07, so cauda de atribuicao)", "120247419652220527"),
]
ABO = "120247419652220527"
PIXEL = "223799232011558"
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
        if novo == cur:
            break
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
        print(f"[ERRO API] {path}: {body[:300]}", file=sys.stderr)
        return {"data": []}
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO REDE] {path}: {e}", file=sys.stderr)
        return {"data": []}
    if isinstance(data, dict) and data.get("error"):
        print(f"[ERRO API] {path}: {data['error'].get('message')}", file=sys.stderr)
        return {"data": []}
    return data


def act(actions, t):
    for a in actions or []:
        if a.get("action_type") == t:
            try:
                return int(float(a.get("value", 0)))
            except (TypeError, ValueError):
                return 0
    return 0


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def ts(d):
    return int(time.mktime(datetime(d.year, d.month, d.day).timetuple()))


hoje = date.today()
ontem = hoje - timedelta(days=1)
ini = hoje - timedelta(days=8)

print("=" * 70)
print(f"LEITURA DIARIA DONO 14%  |  gerado {hoje.isoformat()}  |  dia fechado {ontem.isoformat()}")
print("=" * 70)

# --- Campanhas: diario (ABO viva + CBO na cauda de atribuicao de 7 dias) ---
for rotulo, camp_id in CAMPANHAS:
    camp = get(
        f"{camp_id}/insights",
        {
            "time_increment": 1,
            "time_range": json.dumps({"since": ini.isoformat(), "until": hoje.isoformat()}),
            "fields": "date_start,spend,reach,frequency,inline_link_clicks,ctr,cpm,actions",
        },
    ).get("data", [])
    print(f"\n[{rotulo} - por dia]")
    print(f"{'dia':<7}{'gasto':>9}{'cliq':>6}{'LPV':>5}{'lead':>5}{'CTR':>7}{'CPM':>8}{'reach':>7}{'CPL*':>8}")
    if not camp:
        print("  (sem entrega no periodo)")
    for r in camp:
        d = r.get("date_start", "")[5:]
        gasto = num(r.get("spend"))
        lpv = act(r.get("actions"), "landing_page_view")
        lead = act(r.get("actions"), "onsite_web_lead") or act(r.get("actions"), "lead")
        cpl = (gasto / lead) if lead else 0.0
        print(
            f"{d:<7}{gasto:>9.2f}{int(num(r.get('inline_link_clicks'))):>6}{lpv:>5}{lead:>5}"
            f"{num(r.get('ctr')):>6.1f}%{num(r.get('cpm')):>8.1f}{int(num(r.get('reach'))):>7}{cpl:>8.1f}"
        )
print("(*) CPL aqui usa lead da Meta. CPL REAL = gasto / leads do BANCO.")

# --- ABO por anuncio: acumulado do periodo (o teste de criativos) ---
ads = get(
    f"{ABO}/insights",
    {
        "level": "ad",
        "time_range": json.dumps({"since": ini.isoformat(), "until": hoje.isoformat()}),
        "fields": "ad_name,spend,impressions,inline_link_clicks,inline_link_click_ctr,ctr,cpc,actions",
    },
).get("data", [])
if ads:
    print("\n[ABO POR ANUNCIO - acumulado do periodo de teste]")
    print(f"{'anuncio':<10}{'gasto':>8}{'impr':>7}{'cliq':>6}{'LPV':>5}{'lead':>5}{'CTRl':>7}{'CPC':>7}")
    for r in sorted(ads, key=lambda x: num(x.get("spend")), reverse=True):
        nome = (r.get("ad_name") or "")[:9]
        gasto = num(r.get("spend"))
        lpv = act(r.get("actions"), "landing_page_view")
        lead = act(r.get("actions"), "onsite_web_lead") or act(r.get("actions"), "lead")
        print(
            f"{nome:<10}{gasto:>8.2f}{int(num(r.get('impressions'))):>7}"
            f"{int(num(r.get('inline_link_clicks'))):>6}{lpv:>5}{lead:>5}"
            f"{num(r.get('inline_link_click_ctr')):>6.2f}%{num(r.get('cpc')):>7.2f}"
        )

# --- VSL + funil: eventos do pixel ---
vsl_ini = hoje - timedelta(days=4)
stats = get(
    f"{PIXEL}/stats",
    {"aggregation": "event", "start": ts(vsl_ini), "end": ts(hoje + timedelta(days=1))},
).get("data", [])

agg = {}
for bucket in stats:
    for e in bucket.get("data", []):
        agg[e.get("value")] = agg.get(e.get("value"), 0) + int(e.get("count", 0))

print(f"\n[VSL E FUNIL - eventos do pixel, {vsl_ini.isoformat()} a {hoje.isoformat()}]")
for k in ["PageView", "ViewContent", "VSL_Play", "VSL_Unmute", "VSL_25", "VSL_50", "VSL_75", "VSL_100", "Lead"]:
    if k in agg:
        print(f"  {k:<14} {agg[k]}")
plays = agg.get("VSL_Play", 0)
if plays:
    print(f"  -> taxa de ativar som (Unmute/Play): {agg.get('VSL_Unmute', 0) / plays * 100:.0f}%")

print("\n[LEMBRETE] Contar leads REAIS pelo BANCO (contact_submissions via execute_sql), nao pela Meta.")
print("=" * 70)
