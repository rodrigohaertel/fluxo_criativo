#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Placar do TESTE DE CRIATIVOS (campanha ABO Dono 14%).

Gera um dashboard HTML dedicado ao teste ABO: os 9 anuncios (A30-A38), um por
conjunto com orcamento igual, acumulando dia a dia. Mostra as metricas primarias
(lead, CPL, visitas) e secundarias (CTR, custo por clique, hook de video, retencao).

O teste comecou em 2026-07-03 e roda ~5 dias. Enquanto o volume por anuncio for
pequeno, o ranking se decide pelas secundarias (o topo estabiliza mais rapido).

Uso:    py -3 scripts/dono14-teste-criativos.py
Saida:  meus-produtos/dono-14/trafego/analise/teste-criativos-abo.html
Token lido do .env. Nenhum token fica no codigo.
"""
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

ABO = "120247419652220527"            # ABO - Teste de Criativos
TESTE_INICIO = "2026-07-03"           # dia 1 do teste
TESTE_DIAS = 5
API = "https://graph.facebook.com/v21.0"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "meus-produtos", "dono-14", "trafego", "analise", "teste-criativos-abo.html")


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
    out = []
    try:
        while url:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, dict) and data.get("error"):
                print(f"[ERRO API] {path}: {data['error'].get('message')}", file=sys.stderr)
                break
            out.extend(data.get("data", []))
            url = (data.get("paging") or {}).get("next")
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO API] {path}: {e}", file=sys.stderr)
    return out


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def act(actions, t):
    for a in actions or []:
        if a.get("action_type") == t:
            return int(num(a.get("value")))
    return 0


def vv(block):
    """valor 'video_view' de um bloco de video_*_watched_actions."""
    return act(block, "video_view")


def esc(s):
    return html.escape(str(s))


def brl(v):
    return ("R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")) if v else "-"


def brl0(v):
    return ("R$ " + f"{v:,.0f}".replace(",", ".")) if v else "-"


hoje = date.today()
dia_teste = (hoje - datetime.strptime(TESTE_INICIO, "%Y-%m-%d").date()).days + 1
dia_teste = max(1, min(dia_teste, TESTE_DIAS + 3))

rows = get(
    f"{ABO}/insights",
    {
        "level": "ad",
        "time_range": json.dumps({"since": TESTE_INICIO, "until": hoje.isoformat()}),
        "limit": 50,
        "fields": (
            "ad_name,spend,impressions,reach,frequency,inline_link_clicks,"
            "inline_link_click_ctr,ctr,actions,video_play_actions,"
            "video_p25_watched_actions,video_p50_watched_actions,"
            "video_p75_watched_actions,video_p100_watched_actions,"
            "video_thruplay_watched_actions"
        ),
    },
)

ads = []
for r in rows:
    spend = num(r.get("spend"))
    impr = int(num(r.get("impressions")))
    clicks = int(num(r.get("inline_link_clicks")))
    lpv = act(r.get("actions"), "landing_page_view")
    lead = act(r.get("actions"), "onsite_web_lead") or act(r.get("actions"), "lead")
    plays = vv(r.get("video_play_actions"))
    p25 = vv(r.get("video_p25_watched_actions"))
    p50 = vv(r.get("video_p50_watched_actions"))
    p100 = vv(r.get("video_p100_watched_actions"))
    thru = vv(r.get("video_thruplay_watched_actions"))
    ads.append({
        "nome": r.get("ad_name", "?"),
        "spend": spend,
        "impr": impr,
        "clicks": clicks,
        "ctr_link": num(r.get("inline_link_click_ctr")),
        "cpl_click": (spend / clicks) if clicks else None,
        "hook15": (thru / impr * 100) if impr else 0.0,
        "ret": (p50 / p25 * 100) if p25 else 0.0,
        "p100": p100,
        "lpv": lpv,
        "connect": (lpv / clicks * 100) if clicks else 0.0,
        "lead": lead,
        "cpl": (spend / lead) if lead else None,
    })

# Ranking: primeiro por lead, depois por visita, depois por clique (o topo decide enquanto nao ha lead).
ads.sort(key=lambda a: (a["lead"], a["lpv"], a["clicks"]), reverse=True)

tot_spend = sum(a["spend"] for a in ads)
tot_lpv = sum(a["lpv"] for a in ads)
tot_lead = sum(a["lead"] for a in ads)
tot_clicks = sum(a["clicks"] for a in ads)

CSS = """<style>
:root{--ink-0:#0a0a0b;--ink-1:#101013;--ink-2:#16161a;--ink-3:#1d1d22;
--line-1:rgba(255,255,255,.08);--line-2:rgba(255,255,255,.14);
--text-hi:#f4f4f5;--text-mid:#c1c1c6;--text-dim:#7a7a82;--text-faint:#52525a;
--neon:#c4ff5e;--neon-dim:#a3d94a;--neon-deep:#6b8f1f;--rust:#d97757;--ochre:#e3b04b;
--font-display:'Space Grotesk',sans-serif;--font-body:'Inter',sans-serif;--font-mono:'JetBrains Mono',monospace;
--s-2:8px;--s-3:12px;--s-4:16px;--s-5:20px;--s-6:24px;--s-7:32px;--s-8:40px;--s-9:56px;--s-10:80px;--r-lg:10px;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ink-0);color:var(--text-mid);font-family:var(--font-body);font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1040px;margin:0 auto;padding:0 var(--s-5)}
h1,h2{color:var(--text-hi);font-family:var(--font-display);font-weight:700;line-height:1.15}
h1{font-size:clamp(28px,5vw,44px);letter-spacing:-.02em}
h2{font-size:22px;margin-bottom:var(--s-3)}
strong{color:var(--text-hi);font-weight:600}
.label{font-family:var(--font-mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--neon)}
.snap{font-family:var(--font-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ochre);background:rgba(227,176,75,.08);border:1px solid rgba(227,176,75,.25);border-radius:6px;padding:7px 12px;display:inline-block;margin-top:var(--s-5)}
.capa{border-top:3px solid var(--neon);padding:var(--s-9) 0 var(--s-7);background:linear-gradient(180deg,var(--ink-1),var(--ink-0))}
.capa h1{margin:var(--s-4) 0 var(--s-3)}
section{padding:var(--s-8) 0;border-top:1px solid var(--line-1)}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--s-4);margin:var(--s-5) 0}
@media(max-width:720px){.cards{grid-template-columns:1fr 1fr}}
.card{background:var(--ink-1);border:1px solid var(--line-1);border-top:2px solid var(--line-2);border-radius:var(--r-lg);padding:var(--s-5)}
.card .ct{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-dim)}
.card .big{font-family:var(--font-display);font-size:34px;font-weight:700;color:var(--text-hi);margin:var(--s-3) 0 2px;line-height:1}
.card .sm{font-size:12.5px;color:var(--text-dim)}
.card.hl{border-top-color:var(--neon)}.card.hl .big{color:var(--neon)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;margin:var(--s-4) 0;font-size:13px;min-width:820px}
th,td{text-align:right;padding:9px 10px;border-bottom:1px solid var(--line-1);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
thead th{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-dim);border-bottom:1px solid var(--line-2)}
tbody tr:hover{background:var(--ink-1)}
td.nm{color:var(--text-hi);font-weight:600;font-family:var(--font-mono)}
tr.top td{background:rgba(196,255,94,.06)}
tr.top td.nm{color:var(--neon)}
.win{color:var(--neon)}.lose{color:var(--rust)}
.note{font-family:var(--font-mono);font-size:12.5px;line-height:1.6;color:var(--text-dim);margin-top:var(--s-3);padding-left:var(--s-4);border-left:2px solid var(--neon-deep)}
.leg{font-size:12.5px;color:var(--text-dim);margin-top:var(--s-3)}
.leg b{color:var(--text-mid)}
footer{padding:var(--s-7) 0 var(--s-10);border-top:1px solid var(--line-1);color:var(--text-faint);font-family:var(--font-mono);font-size:12px}
@media print{body{background:#fff;color:#111;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style>"""


def linha(a, i):
    top = " class=top" if i == 0 and (a["lead"] > 0 or a["lpv"] > 0 or a["clicks"] > 0) else ""
    ctr_cls = "win" if a["ctr_link"] >= 1.5 else ("lose" if a["ctr_link"] < 0.8 else "")
    cpl_txt = brl0(a["cpl"]) if a["cpl"] else "-"
    cpc_txt = brl(a["cpl_click"]) if a["cpl_click"] else "-"
    lead_cls = "win" if a["lead"] > 0 else ""
    return (
        f"<tr{top}><td class=nm>{esc(a['nome'])}</td>"
        f"<td>{brl0(a['spend'])}</td><td>{a['impr']}</td>"
        f"<td>{a['clicks']}</td>"
        f"<td class=\"{ctr_cls}\">{a['ctr_link']:.2f}%</td>"
        f"<td>{cpc_txt}</td>"
        f"<td>{a['hook15']:.1f}%</td>"
        f"<td>{a['ret']:.0f}%</td>"
        f"<td>{a['lpv']}</td>"
        f"<td>{a['connect']:.0f}%</td>"
        f"<td class=\"{lead_cls}\"><b>{a['lead']}</b></td>"
        f"<td>{cpl_txt}</td></tr>"
    )


trs = "".join(linha(a, i) for i, a in enumerate(ads))

doc = f"""<!DOCTYPE html>
<html lang="pt-BR" dir="ltr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Teste de criativos ABO - Dono 14%</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
{CSS}
</head><body>
<header class="capa"><div class="wrap">
<span class="label">DONO14 . Teste de criativos ABO . 9 anuncios</span>
<h1>Placar do teste</h1>
<p style="font-size:17px;color:var(--text-mid);max-width:66ch">Campanha ABO, um anuncio por conjunto, orcamento igual (R$ 20/dia cada). O ranking se decide pelo topo de funil enquanto o lead nao acumula.</p>
<span class="snap">Dia {dia_teste} de {TESTE_DIAS} . acumulado desde {esc(TESTE_INICIO)} . gerado {esc(hoje.isoformat())}</span>
</div></header>
<main class="wrap">

<section>
<div class="cards">
  <div class="card hl"><div class="ct">Dia do teste</div><div class="big">{min(dia_teste,TESTE_DIAS)}/{TESTE_DIAS}</div><div class="sm">desde {esc(TESTE_INICIO)}</div></div>
  <div class="card"><div class="ct">Gasto do teste</div><div class="big">{brl0(tot_spend)}</div><div class="sm">9 anuncios x R$ 20/dia</div></div>
  <div class="card"><div class="ct">Visitas (LPV)</div><div class="big">{tot_lpv}</div><div class="sm">{tot_clicks} cliques</div></div>
  <div class="card"><div class="ct">Leads no teste</div><div class="big">{tot_lead}</div><div class="sm">contagem Meta; lead real = banco</div></div>
</div>
</section>

<section>
<h2>Placar por anuncio</h2>
<div class="scroll">
<table><thead><tr>
<th>anuncio</th><th>gasto</th><th>impr</th><th>cliques</th><th>CTR link</th><th>R$/clique</th><th>hook 15s</th><th>ret. 50/25</th><th>visitas</th><th>connect</th><th>lead</th><th>CPL</th>
</tr></thead><tbody>
{trs}
</tbody></table>
</div>
<div class="leg">
<b>Como ler:</b> enquanto cada anuncio tiver poucas centenas de impressoes, um clique a mais mexe muito no CTR. Julgue primeiro pelas <b>secundarias</b> (CTR link, R$/clique, hook, retencao), que estabilizam antes. O <b>lead e a CPL</b> sao a metrica que decide, mas so ganham confianca com mais dias e mais verba. Verde no CTR = 1,5%+; vermelho = abaixo de 0,8%. Linha destacada = topo do ranking atual.
</div>
<div class="note">
Hook 15s = quantos assistiram 15s do video por impressao (fisgou). Retencao 50/25 = dos que chegaram a 25% do video, quantos chegaram a 50% (segurou). Connect = visitas por clique (quantos cliques viraram visita de pagina). Lead aqui e a contagem da Meta; o lead REAL se conta pelo banco na leitura diaria.
</div>
</section>

</main>
<footer><div class="wrap">Placar do teste de criativos ABO . Dono 14% . gerado {esc(hoje.isoformat())} . dados Meta ao vivo (campanha {ABO}) . teste-criativos-abo.html</div></footer>
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"OK placar salvo: {OUT}")
