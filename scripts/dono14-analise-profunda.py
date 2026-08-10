#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dono14-analise-profunda.py (v3) — ANÁLISE PROFUNDA diária do funil Dono 14%,
determinística e em NÍVEL DE CRIATIVO, com os semáforos oficiais do Rodrigo
(meus-produtos/dono-14/trafego/reguas-criativos.md) e a leitura dos 5 degraus
da skill /trafego-analise (hook, retenção, CTR, connect, CPL).

Dados ao vivo: Meta nível anúncio (funil de vídeo completo) + banco Supabase
direto. Narrativa: .contexto.json (escrita pelo assistente com julgamento).

FORMATO PADRÃO, aprovado pelo Rodrigo em 08/08/2026. Não reduzir sem combinar:

  1. Janela GLOBAL do criativo. Cada cartão cobre da primeira aparição até o dia
     fechado, nunca só os últimos 7 dias, porque o ciclo comercial é mais longo
     que uma semana. A "era" (INICIO_ERA) só define QUAIS criativos aparecem.
  2. Lupa comercial por criativo, com os leads REAIS do banco casados pelo
     utm_content: leads, CPL real, sessões agendadas, fechamentos, quantos de
     cada produto (Dono 14% e Painel do Dono), receita, CAC e ROAS. A janela
     creditável começa em 19/07/2026, quando o utm_content passou a ser gravado.
  3. Tabela com FREQ e CPM além de CTR, CPC, CPV, funil de vídeo e connect, mais
     LEADS BANCO e CPL REAL por período (o CPL da Meta fica só como contraste).
  4. Filtro "Por dia" e "Por semana" na mesma tabela, e linha de TOTAL da vida.
  5. Gráfico de evolução semanal (SVG puro): leads em barras, CTR e CPL em linha.
  6. Etapas do CRM com o nome do board (Sessão, SDR, Fechamento, Ganhos), nunca
     a chave crua do banco. Fonte: src/lib/crmStages.ts do repositório do site.
  7. Largura de 85% da janela e nenhuma célula quebrando em duas linhas.

Uso:    py -3 scripts/dono14-analise-profunda.py [--out CAMINHO]
Chaves: FB_ACCESS_TOKEN_PERMANENTE e SUPABASE_SERVICE_KEY no .env.
"""
import html
import json
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
API = "https://graph.facebook.com/v21.0"
ACC = "act_760723921231720"
SUPABASE_URL = "https://sizhdcrnfylimhsdfdnf.supabase.co"
TZ_SP = timezone(timedelta(hours=-3))
INICIO_SERIE = "2026-06-09"
INICIO_ERA = "2026-07-28"
CTX = RAIZ / "meus-produtos/dono-14/trafego/analise/diario/.contexto.json"
OUT_DIR = RAIZ / "meus-produtos/dono-14/trafego/analise"
DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


def chave(nome):
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith(nome + "="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(f"ERRO: {nome} nao encontrado no .env")


FB, SB = chave("FB_ACCESS_TOKEN_PERMANENTE"), chave("SUPABASE_SERVICE_KEY")


def meta_get(path, **params):
    params["access_token"] = FB
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    out = []
    while url:
        with urllib.request.urlopen(url, timeout=90) as r:
            d = json.loads(r.read().decode())
        if "data" in d:
            out.extend(d["data"])
            url = (d.get("paging") or {}).get("next")
        else:
            return d
    return out


def sb_get(tabela, params):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}?" + urllib.parse.urlencode(params, safe="*.,()")
    req = urllib.request.Request(url, headers={"apikey": SB, "Authorization": f"Bearer {SB}"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def act(actions, t):
    for a in actions or []:
        if a.get("action_type") == t:
            try:
                return int(float(a.get("value", 0)))
            except Exception:
                return 0
    return 0


def vids(row, key):
    v = row.get(key) or []
    return int(float(v[0].get("value", 0))) if v else 0


def num(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def dia_sp(iso):
    s = iso.replace("Z", "+00:00")
    if "." in s:
        base, resto = s.split(".", 1)
        p = max(resto.find("+"), resto.find("-"))
        frac, tz = (resto[:p], resto[p:]) if p > 0 else (resto, "+00:00")
        s = f"{base}.{frac[:6].ljust(6, '0')}{tz}"
    return datetime.fromisoformat(s).astimezone(TZ_SP)


def brl(v, dec=0):
    return ("R$ " + f"{v:,.{dec}f}").replace(",", "X").replace(".", ",").replace("X", ".")


def esc(s):
    return html.escape(str(s))


# ------------------------- semaforos oficiais (reguas-criativos.md, 05/08) ---
def sem_ctr(v):
    if v is None: return ("", "-")
    if v < 1.00: return ("dead", "🔴")
    if v < 1.25: return ("bad", "🟡")
    if v <= 1.50: return ("top", "🟢")
    return ("top", "💚")


def sem_cpc(v):
    if not v: return ("", "-")
    if v > 15: return ("dead", "🔴")
    if v >= 10: return ("bad", "🟡")
    if v >= 5: return ("top", "🟢")
    return ("top", "💚")


def sem_cpv(v):
    if not v: return ("", "-")
    if v > 23: return ("dead", "🔴")
    if v >= 15: return ("bad", "🟡")
    if v >= 8: return ("top", "🟢")
    return ("top", "💚")


def sem_cpl(v):
    if not v: return ("", "-")
    if v > 150: return ("dead", "🔴")
    if v >= 100: return ("bad", "🟡")
    if v >= 70: return ("top", "🟢")
    return ("top", "💚")


# REGRA DA ROTINA (06/08/2026): toda leitura da Meta termina em ONTEM. O dia de
# hoje esta em aberto (pacing, atribuicao e dedup ainda mudam) e um parcial
# tratado como dia normal distorce serie, acumulado e semaforos.
hoje = datetime.now(TZ_SP).date()
ontem = hoje - timedelta(days=1)
ddmm = lambda d: d.strftime("%d/%m")

# ------------------------------------------------------------------ contexto
ctx = json.loads(CTX.read_text(encoding="utf-8")) if CTX.exists() else {}
veredito = ctx.get("veredito_titulo", "")
consideracoes = ctx.get("consideracoes", [])

# ------------------------------------------------------------------ Meta
camps = meta_get(f"{ACC}/campaigns", fields="id,name,objective",
                 effective_status='["ACTIVE","PAUSED","WITH_ISSUES","ARCHIVED"]', limit=200)
IDS = {c["id"] for c in camps if c.get("objective") == "OUTCOME_LEADS"}
diario = meta_get(f"{ACC}/insights", level="campaign", time_increment=1, limit=1000,
                  time_range=json.dumps({"since": INICIO_SERIE, "until": ontem.isoformat()}),
                  fields="date_start,campaign_id,spend")
gasto_dia = defaultdict(float)
for r in diario:
    if r.get("campaign_id") in IDS:
        gasto_dia[r["date_start"]] += num(r["spend"])

FIELDS_AD = ("date_start,ad_name,campaign_id,spend,impressions,reach,frequency,inline_link_clicks,actions,"
             "video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,"
             "video_p95_watched_actions,video_avg_time_watched_actions")
# JANELA GLOBAL DO CRIATIVO (decisao do Rodrigo, 08/08/2026): o ciclo comercial
# passa de 7 dias, entao a leitura por criativo cobre a VIDA INTEIRA dele, nao a
# ultima semana. Buscamos desde o inicio da serie e o cartao mostra da primeira
# aparicao ate ontem. A "era" (28/07) segue definindo apenas QUAIS criativos
# aparecem, ou seja, os que estao vivos hoje.
ads = meta_get(f"{ACC}/insights", level="ad", time_increment=1, limit=5000,
               time_range=json.dumps({"since": INICIO_SERIE, "until": ontem.isoformat()}), fields=FIELDS_AD)
ads = [r for r in ads if r.get("campaign_id") in IDS and num(r.get("spend")) > 0.5]
vivos_na_era = {(r.get("ad_name") or "?").split(" ")[0][:4] for r in ads
                if r["date_start"] >= INICIO_ERA}

# Rotulos oficiais das etapas do CRM. Fonte unica: src/lib/crmStages.ts do repo
# Do-Custo-ao-Lucro/docustoaolucro (o board do AdminCRM e a regua). Nunca exibir
# o valor cru do banco: "sessao_estrategica" no board se chama "Sessão".
ETAPA_LABEL = {
    "entrada": "Entrada", "contato_inicial": "SDR", "sessao_estrategica": "Sessão",
    "recuperacao": "Recuperação", "contrato": "Fechamento", "ganho": "Ganhos",
    "perdido": "Perdidos",
    # chaves legadas do enum, migradas para as colunas novas
    "abordagem_passiva": "SDR", "abordagem_ativa": "SDR", "painel": "SDR",
    "no_show": "Recuperação",
}


def rotulo_etapa(stage):
    return ETAPA_LABEL.get(str(stage or ""), str(stage or "-"))


CAMPOS = ("sp", "im", "rc", "cl", "v3", "lpv", "ld", "p25", "p50", "p75", "p95")
por_ad_dia, acum, semanal = defaultdict(dict), defaultdict(lambda: defaultdict(float)), defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
for r in ads:
    nome = (r.get("ad_name") or "?").split(" ")[0][:4]
    vals = dict(sp=num(r["spend"]), im=num(r["impressions"]), rc=num(r.get("reach")),
                cl=num(r["inline_link_clicks"]),
                v3=act(r.get("actions"), "video_view"), lpv=act(r.get("actions"), "landing_page_view"),
                ld=act(r.get("actions"), "onsite_web_lead") or act(r.get("actions"), "lead"),
                p25=vids(r, "video_p25_watched_actions"), p50=vids(r, "video_p50_watched_actions"),
                p75=vids(r, "video_p75_watched_actions"), p95=vids(r, "video_p95_watched_actions"))
    vals["tm"] = vids(r, "video_avg_time_watched_actions")
    # BUG CORRIGIDO em 08/08/2026: aqui era atribuicao direta (`= vals`), o que
    # SOBRESCREVIA o dia quando o mesmo criativo aparecia em mais de uma linha
    # (mesmo nome rodando em conjuntos diferentes). O acumulado somava e a tabela
    # diaria mostrava so a ultima linha, entao os dois nunca fechavam: no A39 a
    # vida inteira dava R$ 1.228 e a soma dos dias, R$ 784.
    alvo = por_ad_dia[r["date_start"]].setdefault(nome, {k: 0.0 for k in (*CAMPOS, "tm")})
    for k in (*CAMPOS, "tm"):
        if k == "tm":
            alvo[k] = max(alvo[k], vals[k])   # tempo medio nao se soma
        else:
            alvo[k] += vals[k]
    d = date.fromisoformat(r["date_start"])
    sem_ini = d - timedelta(days=d.weekday())
    for k in CAMPOS:
        acum[nome][k] += vals[k]
        semanal[nome][sem_ini][k] += vals[k]

# ------------------------------------------------------------------ Banco
inicio_utc = datetime(2026, 6, 9, 3, tzinfo=timezone.utc).isoformat()
subs = sb_get("contact_submissions", {"select": "id,name,source,created_at",
                                      "or": "(source.ilike.mentoria*,source.ilike.sess*)",
                                      "created_at": f"gte.{inicio_utc}", "order": "created_at.asc"})
cards = sb_get("crm_cards", {"select": "stage,faturamento_medio,valor_contrato,submission_id", "deleted_at": "is.null"})
card_por_sub = {c["submission_id"]: c for c in cards if c.get("submission_id")}
leads_dia = defaultdict(int)
leads_ontem = []
for s in subs:
    d = dia_sp(s["created_at"])
    leads_dia[d.date()] += 1
    if d.date() == ontem:
        c = card_por_sub.get(s["id"], {})
        fat = c.get("faturamento_medio")
        leads_ontem.append((d.strftime("%H:%M"), s.get("name", "?"),
                            (brl(float(fat)) + "/mês") if fat else "-",
                            rotulo_etapa(c.get("stage"))))
stages = defaultdict(int)
for c in cards:
    stages[str(c.get("stage"))] += 1
vendas_qtd = stages.get("ganho", 0)
vendas_valor = sum(float(c.get("valor_contrato") or 0) for c in cards if str(c.get("stage")) == "ganho")

# ------------------------------------------------- LUPA COMERCIAL POR CRIATIVO
# O lead carrega o criativo em contact_submissions.utm_content (ex: "A40").
# ATENCAO (regra do projeto): esse campo so passou a ser gravado em 19/07/2026.
# Lead anterior a essa data NAO e creditavel a criativo nenhum, e por isso o
# gasto usado no CAC por criativo tambem comeca em 19/07.
INICIO_UTM = date(2026, 7, 19)
inicio_utm_utc = datetime(2026, 7, 19, 3, tzinfo=timezone.utc).isoformat()

subs_utm = sb_get("contact_submissions", {
    "select": "id,name,created_at,utm_content,source",
    "or": "(source.ilike.mentoria*,source.ilike.sess*)",
    "created_at": f"gte.{inicio_utm_utc}", "order": "created_at.asc"})
cards_com = sb_get("crm_cards", {
    "select": "id,stage,valor_contrato,submission_id,sessao_agendada,contrato_produto",
    "deleted_at": "is.null"})
card_por_sub_com = {c["submission_id"]: c for c in cards_com if c.get("submission_id")}

# produto de cada card: preferir a tag; contrato_produto entra como reforco
try:
    _tags = {t["id"]: (t.get("name") or "") for t in sb_get("crm_tags", {"select": "id,name"})}
    _ct = sb_get("crm_card_tags", {"select": "card_id,tag_id"})
    tags_por_card = defaultdict(list)
    for ct in _ct:
        tags_por_card[ct["card_id"]].append(_tags.get(ct["tag_id"], ""))
except Exception:  # noqa: BLE001
    tags_por_card = defaultdict(list)


def produto_do_card(c):
    """Devolve 'dono14', 'painel' ou None, olhando tags e contrato_produto."""
    texto = " ".join(tags_por_card.get(c.get("id"), [])) + " " + str(c.get("contrato_produto") or "")
    t = texto.lower()
    if "14" in t:
        return "dono14"
    if "painel" in t:
        return "painel"
    return None


CAMPOS_COM = ("leads", "sessao", "ganho", "painel", "dono14", "receita")
com_por_ad = defaultdict(lambda: defaultdict(float))   # acumulado por criativo
leads_ad_dia = defaultdict(lambda: defaultdict(int))   # [criativo][AAAA-MM-DD] = leads reais
for s in subs_utm:
    ad = (s.get("utm_content") or "").strip().split(" ")[0][:4]
    if not ad:
        continue
    d = dia_sp(s["created_at"]).date()
    if d > ontem:            # regra do dia fechado: hoje nao entra
        continue
    leads_ad_dia[ad][d.isoformat()] += 1
    com_por_ad[ad]["leads"] += 1
    c = card_por_sub_com.get(s["id"])
    if not c:
        continue
    if c.get("sessao_agendada"):
        com_por_ad[ad]["sessao"] += 1
    prod = produto_do_card(c)
    if prod:
        com_por_ad[ad][prod] += 1
    if str(c.get("stage")) == "ganho":
        com_por_ad[ad]["ganho"] += 1
        com_por_ad[ad]["receita"] += float(c.get("valor_contrato") or 0)

# gasto por criativo SO na janela creditavel (a partir de 19/07), para o CAC
gasto_ad_utm = defaultdict(float)
for dstr, ads_do_dia in por_ad_dia.items():
    if date.fromisoformat(dstr) < INICIO_UTM:
        continue
    for nome, v in ads_do_dia.items():
        gasto_ad_utm[nome] += v["sp"]

total_gasto, total_leads = sum(gasto_dia.values()), sum(leads_dia.values())
gasto_ontem = gasto_dia.get(ontem.isoformat(), 0.0)
leads_ontem_n = leads_dia.get(ontem, 0)
cpl_ontem = gasto_ontem / leads_ontem_n if leads_ontem_n else 0
semanas = defaultdict(lambda: {"sp": 0.0, "ld": 0})
for dstr, sp in gasto_dia.items():
    d = date.fromisoformat(dstr)
    semanas[d - timedelta(days=d.weekday())]["sp"] += sp
for d, n in leads_dia.items():
    semanas[d - timedelta(days=d.weekday())]["ld"] += n

# ------------------------------------------------------------------ HTML
CSS = """<style>:root{--bg:#0a1714;--bg2:#0e201b;--card:#12241f;--line:#1e3a31;--cream:#eef2ea;
--cream60:rgba(238,242,234,.62);--cream40:rgba(238,242,234,.4);--win:#37d399;--warn:#e88a5a;
--dead:#c94f4f;--gold:#e0b464;--a:#5aa9e6;--font:'Segoe UI',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}body{background:radial-gradient(ellipse 80% 55% at 70% -5%,rgba(224,180,100,.06),transparent 55%),var(--bg);color:var(--cream);font-family:var(--font);padding:32px 10px 60px;line-height:1.55}
/* 85% da largura da janela (o Rodrigo pediu em 08/08: sobrava lateral demais).
   O teto de 1800px evita linha de texto longa demais em monitor ultrawide. */
.wrap{width:85%;max-width:1800px;min-width:320px;margin:0 auto}.snap{display:inline-block;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--warn);border:1px solid rgba(232,138,90,.35);border-radius:20px;padding:4px 12px;margin-bottom:14px}
h1{font-size:1.75rem;font-weight:800}.sub{color:var(--cream60);font-size:.92rem;margin-top:6px;max-width:78ch}
.grp{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin-top:20px}
.grp h2{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:12px}
.grp h3{font-size:.95rem;color:var(--cream);margin:14px 0 6px}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
/* nowrap: nenhum dado da tabela pode quebrar em duas linhas (ex: "🟢 R$ 13,71"
   virava duas linhas e desalinhava a leitura da coluna). */
th,td{padding:8px 5px;text-align:right;font-size:.84rem;border-top:1px solid rgba(30,58,49,.6);white-space:nowrap}
th{font-size:.62rem;text-transform:uppercase;letter-spacing:.05em;color:var(--cream40);border:none;text-align:right}
th:first-child,td:first-child{text-align:left}td.l,th.l{text-align:left}
.top{color:var(--win)}.bad{color:var(--warn)}.dead{color:var(--dead)}
tr.hl{background:rgba(55,211,153,.07)}
.cards{display:flex;gap:14px;flex-wrap:wrap;margin-top:4px}
.c{flex:1;min-width:150px;background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.c .t{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--cream40)}
.c .v{font-size:1.2rem;font-weight:800;margin-top:4px}.c .s{font-size:.75rem;color:var(--cream40);margin-top:2px}
.criativo{border:1px solid var(--line);border-left:3px solid var(--a);border-radius:12px;padding:16px;margin-top:14px;background:var(--bg2)}
.criativo h3{margin-top:0;font-size:1.05rem}
.badges{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 4px}
.badge{border:1px solid var(--line);border-radius:8px;padding:6px 12px;font-size:.8rem;background:var(--card)}
.badge b{font-size:.95rem}
.verdict{background:rgba(196,255,94,.05);border:1px solid rgba(55,211,153,.4);border-radius:12px;padding:16px 20px;margin-top:12px}
.verdict li{margin:8px 0 8px 16px;font-size:.92rem;color:var(--cream60)}
.legenda{font-size:.78rem;color:var(--cream40);margin-top:8px}
.cinza{color:var(--cream40)}
h4.lupa{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin:16px 0 8px;padding-top:12px;border-top:1px solid var(--line)}
.filtro{display:flex;gap:8px;margin:8px 0 10px}
.fbtn{background:var(--card);color:var(--cream60);border:1px solid var(--line);border-radius:8px;
padding:6px 16px;font-size:.8rem;font-family:var(--font);cursor:pointer}
.fbtn:hover{border-color:var(--gold)}
.fbtn.on{background:rgba(224,180,100,.14);color:var(--gold);border-color:var(--gold);font-weight:700}
.oculto{display:none}
tr.tot td{border-top:2px solid var(--gold);font-weight:800;background:rgba(224,180,100,.06)}
svg.graf{width:100%;min-width:560px;height:auto}
.gtxt{fill:var(--cream40);font-size:11px;font-family:var(--font)}
.gnum{fill:var(--cream60);font-size:10px;font-family:var(--font)}
.foot{color:var(--cream40);font-size:.76rem;margin-top:22px;line-height:1.7}
div.scroll{overflow-x:auto}</style>"""


def linha_metricas(v):
    """calcula métricas derivadas de um dict de campos brutos"""
    im, cl, v3, lpv, sp = v["im"], v["cl"], v["v3"], v["lpv"], v["sp"]
    rc = v.get("rc", 0)
    return dict(
        # freq no agregado e aproximada: soma o alcance de cada dia, entao quem
        # aparece em dias diferentes conta mais de uma vez. Serve para tendencia.
        freq=im / rc if rc else None, cpm=sp / im * 1000 if im else None,
        ctr=cl / im * 100 if im else None, cpc=sp / cl if cl else None,
        cpv=sp / lpv if lpv else None, cpl=sp / v["ld"] if v["ld"] else None,
        hook=v3 / im * 100 if im else 0, p25=v["p25"] / v3 * 100 if v3 else 0,
        p50=v["p50"] / v3 * 100 if v3 else 0, p75=v["p75"] / v3 * 100 if v3 else 0,
        p95=v["p95"] / v3 * 100 if v3 else 0, conn=min(lpv / cl * 100, 100) if cl else 0)


def fmt_sem(valor, fn, prefixo="", sufixo="", dec=2):
    if valor is None:
        return "<td>-</td>"
    cls, emj = fn(valor)
    val = f"{valor:.{dec}f}".replace(".", ",")
    return f"<td class='{cls}'>{emj} {prefixo}{val}{sufixo}</td>"


# --------- cartões por criativo (a parte "nível criativo" que o Rodrigo cobra)
nomes_ativos = sorted(vivos_na_era, key=lambda n: -acum[n]["sp"])


def celulas_periodo(v, ld_banco, creditavel):
    """Colunas de metrica compartilhadas pela visao diaria e pela semanal."""
    md = linha_metricas(v)
    if creditavel:
        cel_ld = f"<td>{ld_banco}</td>"
        cel_cpl = (fmt_sem(v["sp"] / ld_banco, sem_cpl, prefixo="R$ ", dec=0)
                   if ld_banco else "<td class='cinza'>sem lead</td>")
    else:
        cel_ld = cel_cpl = "<td class='cinza'>n/d</td>"
    cel_freq = f"<td>{md['freq']:.2f}</td>".replace(".", ",") if md["freq"] else "<td>-</td>"
    cel_cpm = f"<td>{brl(md['cpm'])}</td>" if md["cpm"] else "<td>-</td>"
    return ("".join([
        f"<td>{brl(v['sp'])}</td>",
        cel_freq,
        cel_cpm,
        fmt_sem(md["ctr"], sem_ctr, sufixo="%"),
        fmt_sem(md["cpc"], sem_cpc, prefixo="R$ "),
        fmt_sem(md["cpv"], sem_cpv, prefixo="R$ "),
        f"<td>{md['hook']:.0f}%</td><td>{md['p25']:.0f}%</td><td>{md['p50']:.0f}%</td>",
        f"<td>{md['p75']:.0f}%</td><td>{md['p95']:.0f}%</td><td>{v.get('tm', 0):.0f}s</td>",
        f"<td>{md['conn']:.0f}%</td><td>{int(v['ld'])}</td>",
        cel_ld, cel_cpl,
    ]))


CABECALHO_LUPA = ("<tr><th class=l>período</th><th>gasto</th><th>freq</th><th>CPM</th><th>CTR</th>"
                  "<th>CPC</th><th>CPV</th><th>hook</th>"
                  "<th>p25</th><th>p50</th><th>p75</th><th>p95</th><th>t.méd</th><th>connect</th>"
                  "<th>leads Meta</th><th>leads banco</th><th>CPL real</th></tr>")

cartoes = ""
for idx, nome in enumerate(nomes_ativos):
    a = acum[nome]
    m = linha_metricas(a)
    dias_do_ad = sorted(d for d in por_ad_dia if nome in por_ad_dia[d])
    nasceu = date.fromisoformat(dias_do_ad[0]) if dias_do_ad else ontem

    # ---------- visao DIARIA, desde a primeira aparicao do criativo
    linhas_dia = ""
    for dstr in dias_do_ad:
        v = por_ad_dia[dstr][nome]
        d = date.fromisoformat(dstr)
        rot = f"{ddmm(d)} {DIAS_SEMANA[d.weekday()]}"
        ld_banco = leads_ad_dia.get(nome, {}).get(dstr, 0)
        linhas_dia += (f"<tr><td class=l>{rot}</td>"
                       + celulas_periodo(v, ld_banco, d >= INICIO_UTM) + "</tr>")

    # ---------- visao SEMANAL (segunda a domingo), com os dados somados da semana
    linhas_sem_lupa, serie_grafico = "", []
    for sem_ini in sorted(semanal[nome].keys()):
        sv = dict(semanal[nome][sem_ini])
        sv["tm"] = 0
        dias_da_sem = [d for d in dias_do_ad
                       if sem_ini <= date.fromisoformat(d) <= sem_ini + timedelta(days=6)]
        tms = [por_ad_dia[d][nome].get("tm", 0) for d in dias_da_sem]
        sv["tm"] = sum(tms) / len(tms) if tms else 0
        ld_banco_sem = sum(leads_ad_dia.get(nome, {}).get(d, 0) for d in dias_da_sem)
        sem_fim = min(sem_ini + timedelta(days=6), ontem)
        rot = f"{ddmm(sem_ini)} a {ddmm(sem_fim)}"
        linhas_sem_lupa += (f"<tr><td class=l>{rot}</td>"
                            + celulas_periodo(sv, ld_banco_sem, sem_fim >= INICIO_UTM) + "</tr>")
        ms = linha_metricas(sv)
        serie_grafico.append({
            "rot": ddmm(sem_ini), "ctr": ms["ctr"] or 0,
            "cpl": (sv["sp"] / ld_banco_sem) if ld_banco_sem else None,
            "leads": ld_banco_sem, "gasto": sv["sp"], "conn": ms["conn"] or 0,
        })

    # ---------- linha de TOTAL (vida inteira do criativo)
    ld_banco_total = sum(leads_ad_dia.get(nome, {}).values())
    total_row = ("<tr class='tot'><td class=l>TOTAL (vida do criativo)</td>"
                 + celulas_periodo(a, ld_banco_total, True) + "</tr>")

    # fadiga semanal (CTR por semana)
    fad = ""
    for sem_ini in sorted(semanal[nome].keys()):
        sv = semanal[nome][sem_ini]
        ctr_s = sv["cl"] / sv["im"] * 100 if sv["im"] else 0
        cls, emj = sem_ctr(ctr_s)
        fad += f"<span class='badge'>sem {ddmm(sem_ini)}: <b class='{cls}'>{emj} {ctr_s:.2f}%</b> ({brl(sv['sp'])})</span>"
    # ---- lupa comercial do criativo (leads reais -> sessao -> venda -> CAC)
    cm = com_por_ad.get(nome, {})
    ld_real = int(cm.get("leads", 0))
    n_sessao, n_ganho = int(cm.get("sessao", 0)), int(cm.get("ganho", 0))
    n_painel, n_d14 = int(cm.get("painel", 0)), int(cm.get("dono14", 0))
    receita_ad = float(cm.get("receita", 0))
    gasto_utm = gasto_ad_utm.get(nome, 0.0)
    cpl_real_ad = gasto_utm / ld_real if ld_real else None
    cac_ad = gasto_utm / n_ganho if n_ganho else None
    roas_ad = receita_ad / gasto_utm if gasto_utm else None
    tx_sessao = (n_sessao / ld_real * 100) if ld_real else 0
    tx_venda = (n_ganho / ld_real * 100) if ld_real else 0
    comercial = f"""
<h4 class="lupa">Lupa comercial · leads do BANCO por utm_content (janela creditável: 19/07 em diante)</h4>
<div class="badges">
  <span class="badge">gasto na janela: <b>{brl(gasto_utm)}</b></span>
  <span class="badge">leads reais: <b>{ld_real}</b></span>
  <span class="badge">CPL real: <b class="{sem_cpl(cpl_real_ad)[0] if cpl_real_ad else ''}">
      {(sem_cpl(cpl_real_ad)[1] + ' ' + brl(cpl_real_ad)) if cpl_real_ad else '-'}</b></span>
  <span class="badge">sessões agendadas: <b>{n_sessao}</b> <span class="cinza">({tx_sessao:.0f}% dos leads)</span></span>
  <span class="badge">fechamentos: <b class="{'top' if n_ganho else ''}">{n_ganho}</b> <span class="cinza">({tx_venda:.0f}% dos leads)</span></span>
</div>
<div class="badges">
  <span class="badge">Dono 14%: <b>{n_d14}</b></span>
  <span class="badge">Painel do Dono: <b>{n_painel}</b></span>
  <span class="badge">receita: <b>{brl(receita_ad)}</b></span>
  <span class="badge">CAC do criativo: <b class="{'top' if cac_ad else ''}">{brl(cac_ad) if cac_ad else 'sem venda ainda'}</b></span>
  <span class="badge">ROAS: <b>{(f'{roas_ad:.1f}x') if roas_ad else '-'}</b></span>
</div>
<div class="legenda">Vida do criativo: {ddmm(nasceu)} a {ddmm(ontem)} · gasto total {brl(a['sp'])}.
CPL real, CAC e ROAS usam a janela creditável (19/07 em diante), porque antes disso o lead não guardava o criativo.</div>"""

    # ---------- grafico de evolucao semanal (SVG puro, sem biblioteca)
    grafico = ""
    if len(serie_grafico) >= 2:
        W, H, PADL, PADB, PADT = 640, 190, 44, 26, 14
        n = len(serie_grafico)
        larg = (W - PADL - 12) / max(n - 1, 1)
        max_ctr = max([s["ctr"] for s in serie_grafico] + [1]) * 1.25
        cpls = [s["cpl"] for s in serie_grafico if s["cpl"]]
        max_cpl = (max(cpls) * 1.25) if cpls else 1
        max_ld = max([s["leads"] for s in serie_grafico] + [1])
        yb = H - PADB

        def px(i):
            return PADL + i * larg

        def py(val, teto):
            return PADT + (yb - PADT) * (1 - (val / teto if teto else 0))

        barras = "".join(
            f'<rect x="{px(i) - 9:.0f}" y="{py(s["leads"], max_ld * 1.6):.0f}" width="18" '
            f'height="{max(yb - py(s["leads"], max_ld * 1.6), 0):.0f}" fill="rgba(90,169,230,.28)" rx="3"/>'
            f'<text x="{px(i):.0f}" y="{py(s["leads"], max_ld * 1.6) - 4:.0f}" class="gnum" text-anchor="middle">{s["leads"]}</text>'
            for i, s in enumerate(serie_grafico))
        lin_ctr = " ".join(f'{px(i):.0f},{py(s["ctr"], max_ctr):.0f}' for i, s in enumerate(serie_grafico))
        pts_cpl = [(i, s["cpl"]) for i, s in enumerate(serie_grafico) if s["cpl"]]
        lin_cpl = " ".join(f'{px(i):.0f},{py(v, max_cpl):.0f}' for i, v in pts_cpl)
        rotulos = "".join(
            f'<text x="{px(i):.0f}" y="{H - 8}" class="gtxt" text-anchor="middle">{s["rot"]}</text>'
            for i, s in enumerate(serie_grafico))
        marc_ctr = "".join(f'<circle cx="{px(i):.0f}" cy="{py(s["ctr"], max_ctr):.0f}" r="3" fill="#37d399"/>'
                           for i, s in enumerate(serie_grafico))
        marc_cpl = "".join(f'<circle cx="{px(i):.0f}" cy="{py(v, max_cpl):.0f}" r="3" fill="#e0b464"/>'
                           for i, v in pts_cpl)
        grafico = f"""
<h4 class="lupa">Evolução semanal</h4>
<div class="badges">
  <span class="badge"><b style="color:#5aa9e6">barras</b> leads reais</span>
  <span class="badge"><b style="color:#37d399">linha verde</b> CTR link (teto {max_ctr:.2f}%)</span>
  <span class="badge"><b style="color:#e0b464">linha ouro</b> CPL real (teto {brl(max_cpl)})</span>
</div>
<div class="scroll"><svg viewBox="0 0 {W} {H}" class="graf" role="img">
  <line x1="{PADL - 20}" y1="{yb}" x2="{W - 6}" y2="{yb}" stroke="#1e3a31"/>
  {barras}
  <polyline points="{lin_ctr}" fill="none" stroke="#37d399" stroke-width="2"/>
  {marc_ctr}
  {f'<polyline points="{lin_cpl}" fill="none" stroke="#e0b464" stroke-width="2" stroke-dasharray="5 3"/>' if len(pts_cpl) > 1 else ''}
  {marc_cpl}
  {rotulos}
</svg></div>"""
    cartoes += f"""
<div class="criativo"><h3>{esc(nome)} · acumulado da era ({brl(a['sp'])})</h3>
<div class="badges">
  {"".join(f"<span class='badge'>{lbl}: <b class='{fn(val)[0] if val is not None else ''}'>{fn(val)[1] if val is not None else '-'} {txt}</b></span>" for lbl, val, fn, txt in [
      ("CTR link", m["ctr"], sem_ctr, (f"{m['ctr']:.2f}%".replace('.', ',')) if m["ctr"] is not None else "-"),
      ("CPC link", m["cpc"], sem_cpc, brl(m["cpc"], 2) if m["cpc"] else "-"),
      ("CPV (visita)", m["cpv"], sem_cpv, brl(m["cpv"], 2) if m["cpv"] else "-"),
      ("CPL Meta", m["cpl"], sem_cpl, brl(m["cpl"]) if m["cpl"] else "sem lead"),
  ])}
  <span class="badge">connect: <b>{m['conn']:.0f}%</b></span>
  <span class="badge">leads Meta: <b>{int(a['ld'])}</b></span>
</div>
<div class="badges"><span class="badge">funil de vídeo: hook <b>{m['hook']:.0f}%</b> · p25 <b>{m['p25']:.0f}%</b> · p50 <b>{m['p50']:.0f}%</b> · p75 <b>{m['p75']:.0f}%</b> · p95 <b>{m['p95']:.0f}%</b></span></div>
<div class="badges">{fad}</div>
{comercial}
{grafico}
<h4 class="lupa">Histórico completo · da primeira aparição ({ddmm(nasceu)}) até {ddmm(ontem)}</h4>
<div class="filtro">
  <button class="fbtn on" onclick="verLupa(this,{idx},'dia')">Por dia</button>
  <button class="fbtn" onclick="verLupa(this,{idx},'sem')">Por semana</button>
</div>
<div class="scroll" id="lupa-dia-{idx}"><table>
{CABECALHO_LUPA}
{linhas_dia}
{total_row}</table></div>
<div class="scroll oculto" id="lupa-sem-{idx}"><table>
{CABECALHO_LUPA}
{linhas_sem_lupa}
{total_row}</table></div>
<div class="legenda">CPL real = gasto do período ÷ leads do BANCO atribuídos a este criativo pelo utm_content.
"n/d" antes de 19/07 porque o campo ainda não era gravado. "leads Meta" é a atribuição da plataforma, mantida só como contraste.
Na visão por semana, cada linha soma a semana inteira (segunda a domingo) e o tempo médio é a média dos dias com entrega.</div></div>"""

# --------- placar do dia fechado
placar = ""
v_ontem = por_ad_dia.get(ontem.isoformat(), {})
for nome in nomes_ativos:
    v = v_ontem.get(nome)
    if not v:
        continue
    md = linha_metricas(v)
    placar += (f"<tr><td class=l><b>{esc(nome)}</b></td><td>{brl(v['sp'])}</td>"
               + fmt_sem(md["ctr"], sem_ctr, sufixo="%") + fmt_sem(md["cpc"], sem_cpc, prefixo="R$ ")
               + fmt_sem(md["cpv"], sem_cpv, prefixo="R$ ")
               + f"<td>{md['hook']:.0f}%</td><td>{md['p25']:.0f}%</td><td>{md['conn']:.0f}%</td><td>{int(v['ld'])}</td></tr>")

# --------- connect série (vigília)
conn_serie = ""
for dstr in sorted(por_ad_dia.keys())[-7:]:
    d = date.fromisoformat(dstr)
    tot_cl = sum(v["cl"] for v in por_ad_dia[dstr].values())
    tot_lpv = sum(v["lpv"] for v in por_ad_dia[dstr].values())
    conn = min(tot_lpv / tot_cl * 100, 100) if tot_cl else 0
    cls = "top" if conn >= 75 else ("bad" if conn >= 60 else "dead")
    detalhe = " · ".join(f"{n} {min(v['lpv']/v['cl']*100,100) if v['cl'] else 0:.0f}%" for n, v in sorted(por_ad_dia[dstr].items()))
    conn_serie += (f"<tr><td class=l>{ddmm(d)} {DIAS_SEMANA[d.weekday()]}</td><td class='{cls}'>{conn:.0f}%</td>"
                   f"<td>{int(tot_cl)}</td><td>{int(tot_lpv)}</td><td class=l>{esc(detalhe)}</td></tr>")

# --------- 5 degraus (skill /trafego-analise)
deg = []
tot = defaultdict(float)
for n in nomes_ativos:
    for k in CAMPOS:
        tot[k] += acum[n][k]
m_tot = linha_metricas(dict(tot, tm=0))
deg_rows = [
    ("1. Parou o scroll?", "Hook (3s ÷ impressões)", f"{m_tot['hook']:.0f}%", "Urgência Oculta"),
    ("2. Ficou até o fim?", "Retenção p25 / p50 / p95", f"{m_tot['p25']:.0f}% / {m_tot['p50']:.0f}% / {m_tot['p95']:.0f}%", "Decorados + Furadeira"),
    ("3. Clicou?", "CTR de link", f"{m_tot['ctr']:.2f}%".replace(".", ",") if m_tot['ctr'] else "-", "Identidade do Produto"),
    ("4. Chegou na página?", "Connect (LPV ÷ cliques)", f"{m_tot['conn']:.0f}%", "Quadro na Parede"),
    ("5. Cadastrou?", "CPL real (banco)", brl(cpl_ontem) if cpl_ontem else "sem lead ontem", "Oferta + Id. do Consumidor"),
]
degraus = "".join(f"<tr><td class=l><b>{a}</b></td><td class=l>{b}</td><td>{c}</td><td class=l>{d}</td></tr>" for a, b, c, d in deg_rows)

# --------- restantes
linhas_leads = "".join(f"<tr><td class=l>{esc(h)}</td><td class=l>{esc(n)}</td><td>{esc(f)}</td><td class=l>{esc(s)}</td></tr>"
                       for h, n, f, s in leads_ontem) or "<tr><td class=l colspan=4>Nenhum lead no dia fechado.</td></tr>"
linhas_sem = ""
for ini in sorted(semanas.keys())[-8:]:
    s = semanas[ini]
    cplsem = s["sp"] / s["ld"] if s["ld"] else None
    linhas_sem += (f"<tr><td class=l>{ddmm(ini)} a {ddmm(ini + timedelta(days=6))}</td><td>{brl(s['sp'])}</td>"
                   f"<td><b>{s['ld']}</b></td>" + fmt_sem(cplsem, sem_cpl, prefixo="R$ ", dec=0) + "</tr>")
linhas_cons = "".join(f"<li>{esc(c)}</li>" for c in consideracoes)
cls_o, emj_o = sem_cpl(cpl_ontem) if cpl_ontem else ("", "")

doc = f"""<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análise Profunda · Nível Criativo · {ddmm(hoje)} · Dono 14%</title>{CSS}
<div class="wrap">
<span class="snap">Snapshot · gerado em {hoje.strftime('%d/%m/%Y')} por script determinístico v2 · dia fechado: {ddmm(ontem)} · série somente com dias fechados (o dia em aberto não entra) · réguas oficiais de 05/08 · substitui a versão anterior</span>
<h1>Análise Profunda · Nível Criativo · Dono 14%</h1>
<div class="sub">{esc(veredito)}</div>
<div class="cards" style="margin-top:18px">
  <div class="c"><div class="t">Dia fechado ({ddmm(ontem)})</div><div class="v">{leads_ontem_n} leads (banco)</div><div class="s">gasto {brl(gasto_ontem)}</div></div>
  <div class="c"><div class="t">CPL real do dia</div><div class="v {cls_o}">{emj_o} {brl(cpl_ontem) if cpl_ontem else '-'}</div><div class="s">régua: 💚&lt;70 · 🟢70-100 · 🟡100-150 · 🔴&gt;150</div></div>
  <div class="c"><div class="t">Série (desde 09/06)</div><div class="v">{total_leads} leads</div><div class="s">{brl(total_gasto)} · CPL médio {brl(total_gasto/total_leads) if total_leads else '-'}</div></div>
  <div class="c"><div class="t">Etapa "Sessão"</div><div class="v top">{stages.get('sessao_estrategica', 0)}</div><div class="s">no board do CRM, ao vivo</div></div>
  <div class="c"><div class="t">Etapa "Ganhos"</div><div class="v top">{vendas_qtd} · {brl(vendas_valor)}</div><div class="s">CAC {brl(total_gasto/vendas_qtd) if vendas_qtd else '-'} · "Fechamento" ({stages.get('contrato', 0)}) é pipeline, não receita</div></div>
</div>

<div class="grp"><h2>Placar do dia fechado ({ddmm(ontem)}) · por criativo, com semáforos</h2>
<div class="scroll"><table>
<tr><th>criativo</th><th>gasto</th><th>CTR link</th><th>CPC link</th><th>CPV (visita)</th><th>hook</th><th>p25</th><th>connect</th><th>leads Meta</th></tr>
{placar}</table></div>
<div class="legenda">Semáforos oficiais (05/08): CTR 🔴&lt;1% 🟡1-1,25% 🟢1,25-1,5% 💚&gt;1,5% · CPC 🔴&gt;15 🟡10-15 🟢5-10 💚&lt;5 · CPV 🔴&gt;23 🟡15-23 🟢8-15 💚&lt;8 · CPL 🔴&gt;150 🟡100-150 🟢70-100 💚&lt;70</div></div>

<div class="grp"><h2>🔬 Lupa por criativo · vida inteira, lupa comercial e fadiga</h2>{cartoes}</div>
<script>
function verLupa(btn, idx, modo) {{
  document.getElementById('lupa-dia-' + idx).classList.toggle('oculto', modo !== 'dia');
  document.getElementById('lupa-sem-' + idx).classList.toggle('oculto', modo !== 'sem');
  btn.parentNode.querySelectorAll('.fbtn').forEach(function (b) {{ b.classList.remove('on'); }});
  btn.classList.add('on');
}}
</script>

<div class="grp"><h2>Vigília do connect rate · série diária (combinado e por criativo)</h2>
<div class="scroll"><table><tr><th>dia</th><th>connect combinado</th><th>cliques</th><th>visitas (LPV)</th><th>por criativo</th></tr>{conn_serie}</table></div>
<div class="legenda">Referência: saudável ≥ 75-80%. Amostras diárias pequenas (4-15 cliques por conjunto) oscilam ±20 pontos com 1 clique; ler tendência de 3 dias, não o dia isolado.</div></div>

<div class="grp"><h2>Os 5 degraus do funil (leitura VTSD, acumulado da era)</h2>
<div class="scroll"><table><tr><th>degrau</th><th>métrica</th><th>valor</th><th>termômetro de</th></tr>{degraus}</table></div></div>

<div class="grp"><h2>Leads do dia fechado ({ddmm(ontem)}) · banco + CRM</h2>
<div class="scroll"><table><tr><th class=l>hora</th><th class=l>nome</th><th>faturamento</th><th class=l>etapa no CRM</th></tr>{linhas_leads}</table></div>
<div class="legenda">Etapas com os nomes do board (fonte única: src/lib/crmStages.ts). Entrada · SDR · Sessão · Recuperação · Fechamento · Ganhos · Perdidos.</div></div>

<div class="grp"><h2>Régua semanal (leads = banco, CPL com semáforo)</h2>
<div class="scroll"><table><tr><th>semana</th><th>gasto</th><th>leads</th><th>CPL real</th></tr>{linhas_sem}</table></div></div>

<div class="grp"><h2>Considerações e plano vigente (julgamento do assistente)</h2>
<div class="verdict"><ul>{linhas_cons}</ul></div></div>

<div class="foot">Fontes: Meta Marketing API (nível anúncio, funil de vídeo completo, por conjunto e por dia), banco Supabase via consulta direta (contact_submissions, crm_cards), contexto do dia. Réguas oficiais: meus-produtos/dono-14/trafego/reguas-criativos.md (Rodrigo, 05/08). Atribuição por criativo é da Meta; leads reais sempre pelo banco. Gerado por scripts/dono14-analise-profunda.py v2. Snapshot estático.</div>
</div>"""

out = OUT_DIR / f"analise-profunda-leads-{hoje.isoformat()}.html"
if "--out" in sys.argv:
    out = Path(sys.argv[sys.argv.index("--out") + 1])
out.write_text(doc, encoding="utf-8")
print(f"OK analise profunda v3 (formato padrao de 08/08) salva: {out}")
