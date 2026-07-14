#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera o dashboard diario do funil Dono 14% em HTML (self-contained, tema escuro),
no mesmo estilo dos dashboards do projeto.

Le ao vivo da Meta (campanha consolidada + eventos do VSL no pixel) e um JSON de
contexto com os leads REAIS do banco + as consideracoes (escritas pelo assistente,
porque exigem julgamento).

Uso:    py -3 scripts/dono14-dashboard.py
Contexto: meus-produtos/dono-14/trafego/analise/diario/.contexto.json
Saida:    meus-produtos/dono-14/trafego/analise/dashboard-dono14.html
Token lido do .env. Nenhum token fica no codigo.
"""
import json
import os
import sys
import time
import html
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

# Este dashboard NAO le uma campanha fixa: agrega no nivel da conta todas as
# campanhas com objetivo OUTCOME_LEADS por dia (ver bloco de insights abaixo).
# Assim a ABO de teste (120247419652220527, viva desde 03/07) entra automatica,
# e o CBO (120246284721790527, pausado 02/07) segue somado na cauda de atribuicao.
PIXEL = "223799232011558"
API = "https://graph.facebook.com/v19.0"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = os.path.join(RAIZ, "meus-produtos", "dono-14", "trafego", "analise", "diario", ".contexto.json")
OUT = os.path.join(RAIZ, "meus-produtos", "dono-14", "trafego", "analise", "dashboard-dono14.html")


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
            if isinstance(data, dict) and "data" in data:
                out.extend(data["data"])
                url = (data.get("paging") or {}).get("next")  # segue a paginacao
            else:
                return data
    except Exception as e:  # noqa: BLE001
        print(f"[ERRO API] {path}: {e}", file=sys.stderr)
    return {"data": out}


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


def esc(s):
    return html.escape(str(s))


def ddmm_of(iso):
    p = (iso or "").split("-")
    return f"{p[2]}/{p[1]}" if len(p) == 3 else (iso or "")


# ---------- contexto (banco + consideracoes) ----------
ctx = {}
if os.path.exists(CTX):
    try:
        ctx = json.load(open(CTX, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"[AVISO] contexto invalido: {e}", file=sys.stderr)

hoje = date.today()
gerado_em = ctx.get("gerado_em", hoje.isoformat())
dia_fechado = ctx.get("dia_fechado", (hoje - timedelta(days=1)).isoformat())
ddmm_fechado = ddmm_of(dia_fechado)
leads_banco = ctx.get("leads_banco", {})  # {"DD/MM": int}
consideracoes = ctx.get("consideracoes", [])
veredito_titulo = ctx.get("veredito_titulo", "")

# ---------- dados Meta (todas as campanhas de LEADS, agregadas por dia desde o inicio) ----------
START = ctx.get("inicio", "2026-06-09")
ACCOUNT = "act_760723921231720"
rows = get(
    f"{ACCOUNT}/insights",
    {
        "level": "campaign",
        "time_increment": 1,
        "limit": 500,
        "time_range": json.dumps({"since": START, "until": hoje.isoformat()}),
        "fields": "date_start,objective,spend,impressions,inline_link_clicks,actions",
    },
).get("data", [])

por_dia = {}
for r in rows:
    if r.get("objective") != "OUTCOME_LEADS":
        continue  # so campanhas de LEADS (ignora reconhecimento/engajamento)
    d = r.get("date_start", "")
    a = por_dia.setdefault(d, {"spend": 0.0, "cliq": 0, "lpv": 0, "lead_meta": 0, "impr": 0})
    a["spend"] += num(r.get("spend"))
    a["cliq"] += int(num(r.get("inline_link_clicks")))
    a["lpv"] += act(r.get("actions"), "landing_page_view")
    a["lead_meta"] += act(r.get("actions"), "onsite_web_lead") or act(r.get("actions"), "lead")
    a["impr"] += int(num(r.get("impressions")))

linhas = []
for d in sorted(por_dia):
    a = por_dia[d]
    ddmm = ddmm_of(d)
    lb = leads_banco.get(ddmm)
    linhas.append({
        "ddmm": ddmm, "gasto": a["spend"], "cliq": a["cliq"], "lpv": a["lpv"], "impr": a["impr"],
        "connect": (a["lpv"] / a["cliq"] * 100) if a["cliq"] else 0.0,
        "lead_meta": a["lead_meta"], "lead_banco": lb,
        "ctr": (a["cliq"] / a["impr"] * 100) if a["impr"] else 0.0,
        "cpm": (a["spend"] / a["impr"] * 1000) if a["impr"] else 0.0,
        "cpl_real": (a["spend"] / lb) if lb else None,
    })

# Nunca mostrar o dia corrente (parcial): so dias fechados.
hoje_ddmm = ddmm_of(hoje.isoformat())
linhas = [l for l in linhas if l["ddmm"] != hoje_ddmm]

# Totais e medias da serie historica (dias fechados). Taxas sao blended (sobre os totais).
t_gasto = sum(l["gasto"] for l in linhas)
t_cliq = sum(l["cliq"] for l in linhas)
t_lpv = sum(l["lpv"] for l in linhas)
t_impr = sum(l["impr"] for l in linhas)
t_lead_meta = sum(l["lead_meta"] for l in linhas)
t_lead_banco = sum(l["lead_banco"] for l in linhas if isinstance(l["lead_banco"], int))
t_connect = (t_lpv / t_cliq * 100) if t_cliq else 0.0
t_ctr = (t_cliq / t_impr * 100) if t_impr else 0.0
t_cpm = (t_gasto / t_impr * 1000) if t_impr else 0.0
cpl_blended = (t_gasto / t_lead_banco) if t_lead_banco else None
cpl_blended_txt = (f"R$ {cpl_blended:,.0f}".replace(",", ".")) if cpl_blended else "-"
gasto_total = t_gasto
leads_total = t_lead_banco
START_DDMM = ddmm_of(START)

# ---------- VSL (pixel) ----------
vsl_ini = hoje - timedelta(days=4)
stats = get(f"{PIXEL}/stats", {"aggregation": "event", "start": ts(vsl_ini), "end": ts(hoje + timedelta(days=1))}).get("data", [])
agg = {}
for bucket in stats:
    for e in bucket.get("data", []):
        agg[e.get("value")] = agg.get(e.get("value"), 0) + int(e.get("count", 0))

# ---------- KPIs ----------
fechado = next((l for l in linhas if l["ddmm"] == ddmm_fechado), None)
leads_ontem = (fechado or {}).get("lead_banco")
cpl_ontem = (fechado or {}).get("cpl_real")
leads_7d = sum(v for v in leads_banco.values() if isinstance(v, int))
melhor = max(((k, v) for k, v in leads_banco.items() if isinstance(v, int)), key=lambda kv: kv[1], default=("-", 0))
plays = agg.get("VSL_Play", 0)
unmute = agg.get("VSL_Unmute", 0)
tx_som = (unmute / plays * 100) if plays else 0

def fmt_brl(v):
    return ("R$ " + f"{v:,.0f}".replace(",", ".")) if v is not None else "-"

def cpl_classe(v):
    if v is None:
        return "", "-"
    cls = "win" if v <= 75 else "lose"
    return cls, f"R$ {v:,.0f}".replace(",", ".")

# ---------- HTML ----------
CSS = """<style>
:root{--ink-0:#0a0a0b;--ink-1:#101013;--ink-2:#16161a;--ink-3:#1d1d22;
--line-1:rgba(255,255,255,.08);--line-2:rgba(255,255,255,.14);
--text-hi:#f4f4f5;--text-mid:#c1c1c6;--text-dim:#7a7a82;--text-faint:#52525a;
--neon:#c4ff5e;--neon-dim:#a3d94a;--neon-deep:#6b8f1f;--rust:#d97757;--ochre:#e3b04b;--sky:#7dc8e8;
--font-display:'Space Grotesk',sans-serif;--font-body:'Inter',sans-serif;--font-mono:'JetBrains Mono',monospace;
--s-2:8px;--s-3:12px;--s-4:16px;--s-5:20px;--s-6:24px;--s-7:32px;--s-8:40px;--s-9:56px;--s-10:80px;--r-lg:10px;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ink-0);color:var(--text-mid);font-family:var(--font-body);font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:980px;margin:0 auto;padding:0 var(--s-5)}
h1,h2{color:var(--text-hi);font-family:var(--font-display);font-weight:700;line-height:1.15}
h1{font-size:clamp(28px,5vw,46px);letter-spacing:-.02em}
h2{font-size:22px;margin-bottom:var(--s-3)}
strong{color:var(--text-hi);font-weight:600}
.label{font-family:var(--font-mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--neon-dim)}
.snap{font-family:var(--font-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ochre);background:rgba(227,176,75,.08);border:1px solid rgba(227,176,75,.25);border-radius:6px;padding:7px 12px;display:inline-block;margin-top:var(--s-5)}
.capa{border-top:3px solid var(--neon);padding:var(--s-9) 0 var(--s-7);background:linear-gradient(180deg,var(--ink-1),var(--ink-0))}
.capa .label{color:var(--neon)}.capa h1{margin:var(--s-4) 0 var(--s-3)}
section{padding:var(--s-8) 0;border-top:1px solid var(--line-1)}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--s-4);margin:var(--s-5) 0}
@media(max-width:720px){.cards{grid-template-columns:1fr 1fr}}
.card{background:var(--ink-1);border:1px solid var(--line-1);border-top:2px solid var(--line-2);border-radius:var(--r-lg);padding:var(--s-5)}
.card .ct{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-dim)}
.card .big{font-family:var(--font-display);font-size:34px;font-weight:700;color:var(--text-hi);margin:var(--s-3) 0 2px;line-height:1}
.card .sm{font-size:12.5px;color:var(--text-dim)}
.card.hl{border-top-color:var(--neon)}.card.hl .big{color:var(--neon)}
.win{color:var(--neon)}.lose{color:var(--rust)}
table{width:100%;border-collapse:collapse;margin:var(--s-4) 0;font-size:13.5px}
th,td{text-align:right;padding:9px 10px;border-bottom:1px solid var(--line-1)}
th:first-child,td:first-child{text-align:left}
thead th{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-dim);border-bottom:1px solid var(--line-2)}
tbody tr:hover{background:var(--ink-1)}
td.hi{color:var(--text-hi);font-weight:600}
tr.fechado{background:rgba(196,255,94,.05)}
tfoot td{border-top:2px solid var(--line-2);font-weight:600;color:var(--text-hi)}
tfoot .tot td:first-child{color:var(--neon);font-family:var(--font-mono);font-size:11px;letter-spacing:.06em}
.tlrow{display:flex;gap:var(--s-4);padding:9px 0;border-top:1px solid var(--line-1)}
.tlrow:first-child{border-top:0}
.tld{font-family:var(--font-mono);font-size:12px;color:var(--neon-dim);width:108px;flex-shrink:0}
.tlt{color:var(--text-mid)}
.barwrap{display:flex;align-items:center;gap:8px;justify-content:flex-end}
.bar{height:8px;background:var(--ink-3);border-radius:4px;overflow:hidden;width:90px}
.bar>i{display:block;height:100%;background:var(--neon)}
.funil{display:grid;gap:var(--s-2);margin:var(--s-4) 0;max-width:560px}
.frow{display:flex;align-items:center;gap:var(--s-3)}
.frow .fl{font-family:var(--font-mono);font-size:12px;color:var(--text-dim);width:130px}
.fbar{flex:1;height:22px;background:var(--ink-2);border-radius:5px;overflow:hidden}
.fbar>i{display:block;height:100%;background:linear-gradient(90deg,var(--neon-deep),var(--neon));border-radius:5px}
.fv{font-family:var(--font-mono);font-size:13px;color:var(--text-hi);width:46px;text-align:right}
.verdict{background:rgba(196,255,94,.06);border:1px solid var(--neon-deep);border-radius:var(--r-lg);padding:var(--s-5) var(--s-6);margin:var(--s-5) 0}
.verdict h2{color:var(--neon);font-size:20px}
.verdict ul{list-style:none;margin-top:var(--s-3)}
.verdict li{padding:7px 0 7px var(--s-5);position:relative;color:var(--text-hi);border-top:1px solid var(--line-1)}
.verdict li:first-child{border-top:0}
.verdict li:before{content:'>';position:absolute;left:0;color:var(--neon);font-family:var(--font-mono)}
.note{font-family:var(--font-mono);font-size:12.5px;line-height:1.55;color:var(--text-dim);margin-top:var(--s-3);padding-left:var(--s-4);border-left:2px solid var(--neon-deep)}
footer{padding:var(--s-7) 0 var(--s-10);border-top:1px solid var(--line-1);color:var(--text-faint);font-family:var(--font-mono);font-size:12px}
@media print{body{background:#fff;color:#111;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style>"""

# linhas da tabela
maxlead = max([(l["lead_banco"] or 0) for l in linhas] + [1])
trs = []
for l in linhas:
    fechado_cls = " class=\"fechado\"" if l["ddmm"] == ddmm_fechado else ""
    lb = l["lead_banco"]
    lb_txt = str(lb) if isinstance(lb, int) else "-"
    largura = int((lb or 0) / maxlead * 100)
    cpl_cls, cpl_txt = cpl_classe(l["cpl_real"])
    trs.append(
        f"<tr{fechado_cls}><td class=hi>{esc(l['ddmm'])}</td>"
        f"<td><div class=barwrap><span class=bar><i style=\"width:{largura}%\"></i></span><b class=hi>{lb_txt}</b></div></td>"
        f"<td class=\"{cpl_cls}\">{cpl_txt}</td>"
        f"<td>{fmt_brl(l['gasto'])}</td>"
        f"<td>{l['cliq']}</td><td>{l['lpv']}</td><td>{l['connect']:.0f}%</td>"
        f"<td>{l['ctr']:.1f}%</td><td>{fmt_brl(l['cpm'])}</td>"
        f"<td>{l['lead_meta']}</td></tr>"
    )

# funil VSL
def frow(nome, val, base):
    pct = int(val / base * 100) if base else 0
    return f"<div class=frow><span class=fl>{esc(nome)}</span><span class=fbar><i style=\"width:{pct}%\"></i></span><span class=fv>{val}</span></div>"

vsl_html = ""
if plays:
    vsl_html = (
        frow("Play (chegou)", plays, plays)
        + frow("Ativou o som", unmute, plays)
        + frow("25% (~2min)", agg.get("VSL_25", 0), plays)
        + frow("50% (~4min)", agg.get("VSL_50", 0), plays)
        + frow("75% (~6min)", agg.get("VSL_75", 0), plays)
        + frow("100% (fim)", agg.get("VSL_100", 0), plays)
    )
else:
    vsl_html = "<p style=\"color:var(--text-dim)\">Sem dados de VSL no periodo.</p>"

cons_html = "".join(f"<li>{esc(c)}</li>" for c in consideracoes) or "<li>Sem consideracoes registradas hoje.</li>"
tl = ctx.get("linha_do_tempo", [])
tl_html = "".join(f"<div class=tlrow><span class=tld>{esc(i.get('data',''))}</span><span class=tlt>{esc(i.get('texto',''))}</span></div>" for i in tl) or "<p style=\"color:var(--text-dim)\">Sem linha do tempo registrada.</p>"
cpl_ontem_cls, cpl_ontem_txt = cpl_classe(cpl_ontem)

# Bloco comercial (do CRM). O assistente escreve ctx["comercial"]; CAC/ROAS sao calculados aqui sobre o gasto.
com = ctx.get("comercial")
comercial_html = ""
if com:
    vd = com.get("vendas_dono14", 0)
    rd = com.get("receita_dono14", 0)
    vp = com.get("vendas_painel", 0)
    rp = com.get("receita_painel", 0)
    cac = (gasto_total / vd) if vd else 0
    roas = ((rd + rp) / gasto_total) if gasto_total else 0
    perdas = ", ".join(com.get("principais_perdas", []))
    comercial_html = (
        '<section>\n<h2>Comercial (do CRM)</h2>\n<div class="cards">\n'
        f'  <div class="card hl"><div class="ct">Mentorias vendidas</div><div class="big">{vd}</div><div class="sm">{fmt_brl(rd)} fechado</div></div>\n'
        f'  <div class="card"><div class="ct">Painel do Dono (R$ 97)</div><div class="big">{vp}</div><div class="sm">{fmt_brl(rp)}</div></div>\n'
        f'  <div class="card"><div class="ct">CAC por mentoria</div><div class="big">{fmt_brl(cac)}</div><div class="sm">ROAS {roas:.1f}x</div></div>\n'
        f'  <div class="card"><div class="ct">Em recuperacao</div><div class="big">{com.get("em_recuperacao",0)}</div><div class="sm">pipeline aberto</div></div>\n'
        '</div>\n'
        f'<div class="note">{esc(com.get("detalhe",""))} {com.get("total_cards",0)} cards no CRM: {com.get("perdidos",0)} perdidos, {com.get("em_recuperacao",0)} em recuperacao, {com.get("agendada_pendente",0)} agendada. Maiores perdas: {esc(perdas)}. Fonte: {esc(com.get("fonte","CRM"))}.</div>\n'
        '</section>\n'
    )

doc = f"""<!DOCTYPE html>
<html lang="pt-BR" dir="ltr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard diario Dono 14% - {esc(gerado_em)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
{CSS}
</head><body>
<header class="capa"><div class="wrap">
<span class="label">DONO14 . Funil de captacao . Leitura diaria</span>
<h1>Dashboard do dia</h1>
<p style="font-size:17px;color:var(--text-mid);max-width:64ch">Dia fechado: <strong>{esc(dia_fechado)}</strong>. Leads contados pelo banco (fonte de verdade), nao pela Meta.</p>
<span class="snap">Gerado em {esc(gerado_em)} . conta act_760723921231720 . o dia corrente pode estar parcial</span>
</div></header>
<main class="wrap">

<section>
<div class="cards">
  <div class="card hl"><div class="ct">Leads ontem (banco)</div><div class="big">{leads_ontem if isinstance(leads_ontem,int) else '-'}</div><div class="sm">dia {esc(ddmm_fechado)}</div></div>
  <div class="card"><div class="ct">CPL real ontem</div><div class="big {cpl_ontem_cls}">{cpl_ontem_txt}</div><div class="sm">teto R$ 75</div></div>
  <div class="card"><div class="ct">Gasto total (leads)</div><div class="big">{fmt_brl(gasto_total)}</div><div class="sm">desde {esc(START_DDMM)} . CPL medio {esc(cpl_blended_txt)}</div></div>
  <div class="card"><div class="ct">Leads reais no periodo</div><div class="big">{leads_total}</div><div class="sm">melhor dia {melhor[1]} ({esc(melhor[0])})</div></div>
</div>
</section>

<section>
<h2>Evolucao diaria</h2>
<table><thead><tr>
<th>dia</th><th>leads (banco)</th><th>CPL real</th><th>gasto</th><th>cliques</th><th>LPV</th><th>connect</th><th>CTR</th><th>CPM</th><th>lead Meta</th>
</tr></thead><tbody>
{''.join(trs)}
</tbody>
<tfoot><tr class="tot">
<td>TOTAL / MEDIA</td><td>{t_lead_banco}</td><td>{cpl_blended_txt}</td><td>{fmt_brl(t_gasto)}</td><td>{t_cliq}</td><td>{t_lpv}</td><td>{t_connect:.0f}%</td><td>{t_ctr:.1f}%</td><td>{fmt_brl(t_cpm)}</td><td>{t_lead_meta}</td>
</tr></tfoot>
</table>
<div class="note">CPL real = gasto / leads do BANCO. Connect = LPV / cliques (quantos cliques viraram visita de pagina; saudavel 80%+). Verde = CPL dentro do teto de R$ 75. Linha destacada = dia fechado. Soma todas as campanhas de LEADS (antigas + consolidada).</div>
</section>

{comercial_html}
<section>
<h2>VSL e funil do video</h2>
<div class="funil">{vsl_html}</div>
<div class="note">Taxa de ativar o som (Unmute/Play): <b>{tx_som:.0f}%</b>. O YouTube nao conta autoplay mudo; a fonte e o pixel. Ativar o som anda colado com virar lead.</div>
</section>

<section>
<div class="verdict">
<h2>Consideracoes{(' . ' + esc(veredito_titulo)) if veredito_titulo else ''}</h2>
<ul>{cons_html}</ul>
</div>
</section>

<section>
<h2>Linha do tempo</h2>
<div class="tl">{tl_html}</div>
</section>

</main>
<footer><div class="wrap">Dashboard diario Dono 14% . gerado {esc(gerado_em)} . dados Meta+VSL ao vivo, leads pelo banco . dashboard-dono14.html</div></footer>
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(doc)
print(f"OK dashboard salvo: {OUT}")
