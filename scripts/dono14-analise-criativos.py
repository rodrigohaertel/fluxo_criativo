#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de dados da analise por criativo do Dono 14% (A30 em diante).

Faz, em uma passada:
  1. Meta Graph API, nivel anuncio, do inicio do periodo ate hoje (acumulado e mensal)
  2. Meta Graph API, nivel anuncio, so da janela com rastreamento (a partir de 19/07/2026)
  3. Meta Graph API, nivel conta, para o gasto total do periodo
  4. Composicao do gasto da conta por tipo de anuncio (calculada, nao hardcoded)
  5. Supabase: contact_submissions (leads reais) e crm_cards (estagio e valores)
  6. Monta o dataset consolidado usado pelo dashboard

Saida: meus-produtos/dono-14/trafego/analise/dataset-criativos-a30-a41.json
Depois deste script, rodar scripts/dono14-dashboard-criativos.py para gerar o HTML.

Uso: py -3 scripts/dono14-analise-criativos.py
Chaves lidas do .env (nunca ficam neste arquivo):
  FB_ACCESS_TOKEN_PERMANENTE, FB_AD_ACCOUNT_ID, SUPABASE_SERVICE_KEY
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "meus-produtos" / "dono-14" / "trafego" / "analise"
CACHE = DESTINO / "diario"
API = "https://graph.facebook.com/v21.0"
SUPABASE = "https://sizhdcrnfylimhsdfdnf.supabase.co"

SINCE = "2026-04-01"                 # inicio da serie historica da analise
INICIO_RASTREIO = "2026-07-19"       # dia em que o utm_content passou a gravar o criativo
PRIMEIRO_CRIATIVO = 30               # A30 em diante entram na analise
MATURACAO_DIAS = 7                   # dias que um lead precisa ter para entrar na coorte madura
UNTIL = date.today().isoformat()

# Correcao manual (Rodrigo, 07 e 10/08/2026): o A35 nao gerou lead nenhum.
# Os 8 leads que a Meta atribui a ele sao artefato de atribuicao e contam como ZERO
# em toda a analise: tabela mestre, medias por familia e regua de custo por lead.
LEADS_ARTEFATO = {"A35"}
CORRECOES = {"A35": "Zerado por decisão do Rodrigo: os 8 leads que a Meta atribui ao A35 são artefato de atribuição. A peça não gerou nenhum lead, e o CPL de R$ 52 do gerenciador é falso."}


def env(chave):
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith(chave + "="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(f"ERRO: {chave} nao encontrado no .env")


TOKEN = env("FB_ACCESS_TOKEN_PERMANENTE")
ACCOUNT = env("FB_AD_ACCOUNT_ID").replace("act_", "")
SB_KEY = env("SUPABASE_SERVICE_KEY")


# ----------------------------------------------------------------- Meta
def meta_get(url=None, path=None, params=None):
    if url is None:
        params = dict(params or {})
        params["access_token"] = TOKEN
        url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    for _ in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", "ignore")
            if "limit" in corpo.lower():
                print("    rate limit, aguardando 30s", file=sys.stderr)
                time.sleep(30)
                continue
            print(f"[ERRO HTTP] {corpo[:300]}", file=sys.stderr)
            return {"data": []}
        except Exception as e:
            print(f"[ERRO REDE] {e}", file=sys.stderr)
            time.sleep(5)
    return {"data": []}


def meta_paginado(path, params):
    saida = []
    d = meta_get(path=path, params=params)
    saida.extend(d.get("data", []))
    while d.get("paging", {}).get("next"):
        d = meta_get(url=d["paging"]["next"])
        saida.extend(d.get("data", []))
    return saida


CAMPOS = ",".join([
    "campaign_name", "campaign_id", "adset_name", "ad_name", "ad_id",
    "spend", "impressions", "reach", "frequency", "clicks", "ctr", "cpc", "cpm",
    "inline_link_clicks", "inline_link_click_ctr", "actions",
    "video_play_actions", "video_p25_watched_actions", "video_p50_watched_actions",
    "video_p75_watched_actions", "video_p95_watched_actions", "video_p100_watched_actions",
    "video_thruplay_watched_actions", "video_avg_time_watched_actions",
    "date_start", "date_stop",
])


def n(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def act(lista, tipo):
    for i in (lista or []):
        if i.get("action_type") == tipo:
            return n(i.get("value"))
    return 0.0


LEAD_ACT = ["offsite_conversion.fb_pixel_lead", "lead",
            "onsite_conversion.lead_grouped", "complete_registration"]


def cod(*valores):
    """Extrai o codigo do criativo (A##) do primeiro valor que casar."""
    for v in valores:
        m = re.search(r"A\d{2}", (v or "").upper())
        if m:
            return m.group(0)
    return None


def da_analise(codigo):
    return bool(codigo) and int(codigo[1:]) >= PRIMEIRO_CRIATIVO


print(f">>> Conta act_{ACCOUNT} | periodo {SINCE} a {UNTIL}")
print(">>> [1/6] Meta, nivel anuncio, acumulado do periodo")
acumulado = meta_paginado(f"act_{ACCOUNT}/insights", {
    "level": "ad", "time_range": json.dumps({"since": SINCE, "until": UNTIL}),
    "fields": CAMPOS, "limit": 200})
print(f"    {len(acumulado)} linhas")

print(">>> [2/6] Meta, nivel anuncio, mes a mes")
mensal = meta_paginado(f"act_{ACCOUNT}/insights", {
    "level": "ad", "time_range": json.dumps({"since": SINCE, "until": UNTIL}),
    "time_increment": "monthly", "fields": CAMPOS, "limit": 400})
print(f"    {len(mensal)} linhas")

print(f">>> [3/6] Meta, nivel anuncio, janela com rastreamento (desde {INICIO_RASTREIO})")
pos = meta_paginado(f"act_{ACCOUNT}/insights", {
    "level": "ad", "time_range": json.dumps({"since": INICIO_RASTREIO, "until": UNTIL}),
    "fields": "ad_name,spend,impressions,inline_link_clicks,actions", "limit": 300})
print(f"    {len(pos)} linhas")

print(">>> [4/6] Meta, nivel conta, gasto total e por mes")
conta_total = meta_get(path=f"act_{ACCOUNT}/insights", params={
    "level": "account", "time_range": json.dumps({"since": SINCE, "until": UNTIL}),
    "fields": "spend,impressions"}).get("data", [])
conta_janela = meta_get(path=f"act_{ACCOUNT}/insights", params={
    "level": "account", "time_range": json.dumps({"since": INICIO_RASTREIO, "until": UNTIL}),
    "fields": "spend"}).get("data", [])
conta_mes = meta_get(path=f"act_{ACCOUNT}/insights", params={
    "level": "account", "time_range": json.dumps({"since": SINCE, "until": UNTIL}),
    "time_increment": "monthly", "fields": "spend"}).get("data", [])

GASTO_CONTA = n(conta_total[0]["spend"]) if conta_total else 0.0
GASTO_CONTA_JANELA = n(conta_janela[0]["spend"]) if conta_janela else 0.0

CACHE.mkdir(parents=True, exist_ok=True)
(CACHE / ".adlevel-a30-a41-bruto.json").write_text(
    json.dumps({"gerado_em": UNTIL, "since": SINCE, "acumulado": acumulado, "mensal": mensal},
               ensure_ascii=False, indent=1), encoding="utf-8")


# ------------------------------------------------- agregacao Meta por criativo
def agregar(linhas):
    agg = {}
    for r in linhas:
        c = cod(r.get("ad_name"))
        if not da_analise(c):
            continue
        d = agg.setdefault(c, defaultdict(float))
        a = r.get("actions") or []
        d["spend"] += n(r.get("spend")); d["imp"] += n(r.get("impressions"))
        d["reach"] += n(r.get("reach")); d["clicks"] += n(r.get("clicks"))
        d["lc"] += n(r.get("inline_link_clicks")); d["lpv"] += act(a, "landing_page_view")
        d["v3"] += act(a, "video_view")
        for k, campo in [("p25", "video_p25_watched_actions"), ("p50", "video_p50_watched_actions"),
                         ("p75", "video_p75_watched_actions"), ("p95", "video_p95_watched_actions")]:
            d[k] += act(r.get(campo), "video_view")
        d["tp"] += act(r.get("video_thruplay_watched_actions"), "video_view")
        d["leads_meta"] += max([act(a, t) for t in LEAD_ACT] + [0])
    for c in LEADS_ARTEFATO:
        if c in agg:
            agg[c]["leads_meta"] = 0.0
    return agg


meta_agg = agregar(acumulado)
pos_agg = agregar(pos)

janela_meses = defaultdict(list)
for r in mensal:
    c = cod(r.get("ad_name"))
    if da_analise(c) and n(r.get("spend")) > 0:
        janela_meses[c].append(r["date_start"][:7])

# composicao do gasto da conta, por tipo de anuncio (calculada)
grupos = defaultdict(float)
for r in acumulado:
    nome = r.get("ad_name") or ""
    campanha = r.get("campaign_name") or ""
    c = cod(nome)
    if da_analise(c):
        chave = f"Criativos A{PRIMEIRO_CRIATIVO} em diante (funil da mentoria)"
    elif c:
        chave = "Criativos anteriores (outro produto e outro objetivo)"
    elif nome.upper().startswith("CAR-"):
        chave = "Carrosséis de reconhecimento"
    else:
        chave = "Posts impulsionados do Instagram"
    grupos[chave] += n(r.get("spend"))

OBS_GRUPO = {
    f"Criativos A{PRIMEIRO_CRIATIVO} em diante (funil da mentoria)": "captação de lead para a Sessão",
    "Criativos anteriores (outro produto e outro objetivo)": "campanhas de outro produto, fora do funil da mentoria",
    "Carrosséis de reconhecimento": "topo de funil da linha editorial",
    "Posts impulsionados do Instagram": "topo de funil da linha editorial",
}
GASTO_FUNIL = grupos.get(f"Criativos A{PRIMEIRO_CRIATIVO} em diante (funil da mentoria)", 0.0)
GASTO_TOPO = grupos.get("Carrosséis de reconhecimento", 0.0) + grupos.get("Posts impulsionados do Instagram", 0.0)
GASTO_OUTRO = grupos.get("Criativos anteriores (outro produto e outro objetivo)", 0.0)


# ----------------------------------------------------------------- Supabase
def sb(tabela, params):
    url = f"{SUPABASE}/rest/v1/{tabela}?" + urllib.parse.urlencode(params, safe="*.,()")
    r = urllib.request.Request(url, headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY})
    return json.loads(urllib.request.urlopen(r, timeout=60).read().decode())


print(">>> [5/6] Supabase, leads reais e cartoes do CRM")
subs = sb("contact_submissions", {
    "select": "id,name,source,ab_variant,utm_content,utm_term,landing_url,faturamento_medio,created_at",
    "created_at": f"gte.{SINCE}", "order": "created_at.asc", "limit": "5000"})
cards = sb("crm_cards", {
    "select": "submission_id,stage,motivo_perda,valor_contrato,sessao_agendada,faturamento_medio,created_at,deleted_at",
    "deleted_at": "is.null", "limit": "5000"})
print(f"    {len(subs)} leads, {len(cards)} cartoes")

card_por_sub = {c["submission_id"]: c for c in cards if c.get("submission_id")}


def zero():
    return {"leads": 0, "q100": 0, "q200": 0, "stages": defaultdict(int),
            "sessoes": 0, "contratos": 0, "ganhos": 0, "perdidos": 0,
            "receita": 0.0, "pipeline_valor": 0.0, "vendas": 0,
            # funil de sessao: agendada, ja realizada (data no passado) e convertida
            "sess_agendadas": 0, "sess_realizadas": 0, "sess_convertidas": 0,
            # coorte com 7 dias ou mais de maturacao
            "maduros": 0, "maduros_avancaram": 0}


banco = defaultdict(zero)
sem_utm = {"leads": 0, "q100": 0, "stages": defaultdict(int),
           "receita": 0.0, "pipeline_valor": 0.0, "vendas": 0}

for s in subs:
    c = cod(s.get("utm_content"), s.get("utm_term"))
    card = card_por_sub.get(s["id"]) or {}
    st = str(card.get("stage") or "sem_card")
    fat = s.get("faturamento_medio") or 0
    valor = n(card.get("valor_contrato"))
    alvo = banco[c] if da_analise(c) else sem_utm
    alvo["leads"] += 1
    alvo["stages"][st] += 1
    if fat >= 100000:
        alvo["q100"] += 1
    if da_analise(c) and fat >= 200000:
        alvo["q200"] += 1
    if st == "ganho":
        alvo["receita"] += valor
        alvo["vendas"] += 1
    elif st == "contrato":
        alvo["pipeline_valor"] += valor
    if da_analise(c):
        for chave, estagio in [("sessoes", "sessao_estrategica"), ("contratos", "contrato"),
                               ("ganhos", "ganho"), ("perdidos", "perdido")]:
            if st == estagio:
                alvo[chave] += 1
        avancou = st in ("sessao_estrategica", "contrato", "ganho")
        fechou = st in ("contrato", "ganho")
        agendada = (card.get("sessao_agendada") or "")[:10]
        if agendada:
            alvo["sess_agendadas"] += 1
            if agendada <= UNTIL:
                alvo["sess_realizadas"] += 1
                if fechou:
                    alvo["sess_convertidas"] += 1
        if (date.fromisoformat(UNTIL) - date.fromisoformat(s["created_at"][:10])).days >= MATURACAO_DIAS:
            alvo["maduros"] += 1
            if avancou:
                alvo["maduros_avancaram"] += 1

for c in CORRECOES:
    if c in banco:
        banco[c] = zero()


# ------------------------------------------------- ficha editorial dos criativos
FICHA = {
 "A30": dict(titulo="O prato que sangra sua margem", mandala="Problema-Solução", familia="Filtro / convocação",
             textura="Rosto puro", dur=63, nota=8.7, lote="Base (mai/26)", conceito="o prato que sangra"),
 "A31": dict(titulo="Fatura 200 mil, tira só 6 mil", mandala="Certo vs Errado + Tutorial 3 passos", familia="Paradoxo numérico",
             textura="Rosto puro", dur=82, nota=8.4, lote="Base (mai/26)", conceito="muito prato, pouco resultado"),
 "A32": dict(titulo="7 em cada 10 restaurantes não lucram", mandala="Dado de mercado (ABRASEL)", familia="Prova de mercado",
             textura="Rosto puro", dur=71, nota=9.3, lote="Base (mai/26)", conceito="o clube dos 33%"),
 "A33": dict(titulo="O cartão pessoal pagava o fornecedor", mandala="Autoridade com fragilidade", familia="História de origem",
             textura="Rosto + b-roll", dur=94, nota=8.6, lote="Base (mai/26)", conceito="o carro-chefe que afundava"),
 "A34": dict(titulo="Faturar mais não tira do vermelho", mandala="Conta na mesa / decomposição", familia="Paradoxo puro",
             textura="Rosto puro", dur=65, nota=9.4, lote="Base (mai/26)", conceito="os 72% que saem antes"),
 "A35": dict(titulo="A culpa não é da seleção", mandala="Quebra de objeção / confronto", familia="Inimigo comum",
             textura="Rosto puro (sazonal)", dur=67, nota=8.9, lote="Base (mai/26)", conceito="a culpa terceirizada"),
 "A36": dict(titulo="A margem que some sem você ver", mandala="Problema-Agravamento", familia="Demonstração (Painel)",
             textura="Tela do Painel", dur=55, nota=9.5, lote="Refresh (jun/26)", conceito="o lucro imaginado"),
 "A37": dict(titulo="Apenas 36% dos restaurantes dão lucro", mandala="Caso / prova (ABRASEL)", familia="Prova de mercado",
             textura="Reportagem b-roll", dur=45, nota=9.5, lote="Refresh (jun/26)", conceito="os 36% que lucram"),
 "A38": dict(titulo="O culpado não é o iFood", mandala="Inimigo comum", familia="Inimigo comum",
             textura="Rosto cru, uma tomada", dur=50, nota=9.6, lote="Refresh (jun/26)", conceito="o ralo invisível"),
 "A39": dict(titulo="Salão cheio não é lucro (react ABRASEL)", mandala="Prova / dado de mercado", familia="Prova de mercado",
             textura="Tela de notícia", dur=77, nota=9.5, lote="Rodada nova (jul/26)", conceito="o lucro que o movimento esconde"),
 "A40": dict(titulo="Você jura que tem 15% de lucro", mandala="Mito vs Verdade + Demonstração", familia="Demonstração (Painel)",
             textura="Tela dividida (Painel)", dur=86, nota=9.6, lote="Rodada nova (jul/26)", conceito="o lucro imaginado"),
 "A41": dict(titulo="Procura-se dono de restaurante", mandala="Convocação / convite direto", familia="Filtro / convocação",
             textura="Rosto puro", dur=44, nota=9.4, lote="Rodada nova (jul/26)", conceito="o vazamento"),
}
FICHA_PADRAO = dict(titulo="(sem ficha editorial cadastrada)", mandala="a definir", familia="a definir",
                    textura="a definir", dur=0, nota=0, lote="novo", conceito="a definir")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


linhas = []
for c in sorted(meta_agg, key=lambda x: int(x[1:])):
    m = meta_agg[c]
    b = banco.get(c) or zero()
    p = pos_agg.get(c) or defaultdict(float)
    gasto_rast = round(p["spend"], 2)
    st = dict(b["stages"])
    pipeline = st.get("contato_inicial", 0) + st.get("recuperacao", 0)
    avancos = b["sessoes"] + b["contratos"] + b["ganhos"]
    ficha = FICHA.get(c, FICHA_PADRAO)
    linhas.append(dict(
        criativo=c, **ficha,
        meses=sorted(set(janela_meses.get(c, []))),
        gasto=round(m["spend"], 2), impressoes=int(m["imp"]), alcance=int(m["reach"]),
        freq=round(m["imp"] / m["reach"], 2) if m["reach"] else 0,
        ctr=pct(m["clicks"], m["imp"]), ctr_link=pct(m["lc"], m["imp"]),
        cpc=round(m["spend"] / m["clicks"], 2) if m["clicks"] else 0,
        cpc_link=round(m["spend"] / m["lc"], 2) if m["lc"] else 0,
        cpm=round(1000 * m["spend"] / m["imp"], 2) if m["imp"] else 0,
        hook=pct(m["v3"], m["imp"]),
        p25=pct(m["p25"], m["v3"]), p50=pct(m["p50"], m["v3"]),
        p75=pct(m["p75"], m["v3"]), p95=pct(m["p95"], m["v3"]),
        cliques_link=int(m["lc"]), lpv=int(m["lpv"]),
        connect=pct(m["lpv"], m["lc"]),
        leads_meta=int(m["leads_meta"]),
        cpl_meta=round(m["spend"] / m["leads_meta"], 2) if m["leads_meta"] else None,
        rastreado=gasto_rast > 0,
        gasto_rast=gasto_rast, imp_rast=int(p["imp"]), lpv_rast=int(p["lpv"]),
        leads_meta_rast=int(p["leads_meta"]),
        leads_banco=b["leads"],
        cpl_banco=round(gasto_rast / b["leads"], 2) if b["leads"] else None,
        q100=b["q100"], q200=b["q200"],
        cpl_q=round(gasto_rast / b["q100"], 2) if b["q100"] else None,
        taxa_q=pct(b["q100"], b["leads"]),
        sessoes=b["sessoes"], contratos=b["contratos"], ganhos=b["ganhos"], perdidos=b["perdidos"],
        pipeline=pipeline, avancos=avancos,
        custo_avanco=round(gasto_rast / avancos, 2) if avancos else None,
        stages=st,
        sess_agendadas=b["sess_agendadas"], sess_realizadas=b["sess_realizadas"],
        sess_convertidas=b["sess_convertidas"],
        taxa_sessao=pct(b["sess_convertidas"], b["sess_realizadas"]),
        maduros=b["maduros"], maduros_avancaram=b["maduros_avancaram"],
        taxa_coorte=pct(b["maduros_avancaram"], b["maduros"]),
        receita=round(b["receita"], 2), vendas=b["vendas"],
        pipeline_valor=round(b["pipeline_valor"], 2),
        roas=round(b["receita"] / gasto_rast, 2) if gasto_rast and b["receita"] else None,
        roas_pipeline=round((b["receita"] + b["pipeline_valor"]) / gasto_rast, 2) if gasto_rast and (b["receita"] + b["pipeline_valor"]) else None,
        cac=round(gasto_rast / b["vendas"], 2) if b["vendas"] else None,
        lpv_lead=pct(b["leads"], p["lpv"]) if b["leads"] else 0.0,
        lpv_lead_meta=pct(m["leads_meta"], m["lpv"]),
        correcao=CORRECOES.get(c),
    ))

print(">>> [6/6] Montando o dataset consolidado")
saida = dict(
    gerado_em=UNTIL,
    periodo=f"{SINCE} a {UNTIL}",
    criativos=linhas,
    sem_utm=dict(leads=sem_utm["leads"], q100=sem_utm["q100"], stages=dict(sem_utm["stages"])),
    totais=dict(
        gasto=round(sum(l["gasto"] for l in linhas), 2),
        gasto_rastreado=round(sum(l["gasto_rast"] for l in linhas), 2),
        leads_meta=sum(l["leads_meta"] for l in linhas),
        leads_banco=sum(l["leads_banco"] for l in linhas),
        leads_banco_total_periodo=len(subs),
    ),
    conta=dict(
        gasto_total=round(GASTO_CONTA, 2),
        gasto_janela=round(GASTO_CONTA_JANELA, 2),
        composicao=[(nome, round(v, 2), OBS_GRUPO.get(nome, "")) for nome, v in
                    sorted(grupos.items(), key=lambda kv: -kv[1]) if v > 0],
        gasto_funil_mentoria=round(GASTO_FUNIL, 2),
        gasto_topo_funil=round(GASTO_TOPO, 2),
        gasto_outro_produto=round(GASTO_OUTRO, 2),
        gasto_por_mes={r["date_start"][:7]: round(n(r["spend"]), 2) for r in conta_mes},
    ),
    financeiro=dict(
        receita_total=round(sum(l["receita"] for l in linhas) + sem_utm["receita"], 2),
        receita_rastreada=round(sum(l["receita"] for l in linhas), 2),
        receita_sem_utm=round(sem_utm["receita"], 2),
        vendas_total=sum(l["vendas"] for l in linhas) + sem_utm["vendas"],
        vendas_rastreadas=sum(l["vendas"] for l in linhas),
        pipeline_total=round(sum(l["pipeline_valor"] for l in linhas) + sem_utm["pipeline_valor"], 2),
        ticket_medio=15000.0,
        ticket_avista=12000.0,
        entrada_por_venda=500.0,
        parcelas="R$ 500 de sinal, R$ 1.000 na primeira parcela e 9 de R$ 1.500",
    ),
    correcoes=CORRECOES,
    inicio_rastreio=INICIO_RASTREIO,
    maturacao_dias=MATURACAO_DIAS,
)

destino = DESTINO / "dataset-criativos-a30-a41.json"
destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
print(f">>> dataset salvo: {destino}")
print()
print(f"{'cri':<5}{'gasto':>8}{'ldMeta':>7}{'ldBanco':>8}{'CPLbanco':>10}{'q100':>6}{'sess':>5}{'ctr':>5}{'ganho':>6}{'receita':>10}")
for l in linhas:
    print(f"{l['criativo']:<5}{l['gasto']:>8.0f}{l['leads_meta']:>7}{l['leads_banco']:>8}"
          f"{(l['cpl_banco'] or 0):>10.0f}{l['q100']:>6}{l['sessoes']:>5}{l['contratos']:>5}"
          f"{l['ganhos']:>6}{l['receita']:>10.0f}")
print()
print("conta:", saida["conta"]["gasto_total"], "| funil:", saida["conta"]["gasto_funil_mentoria"],
      "| receita:", saida["financeiro"]["receita_total"], "| vendas:", saida["financeiro"]["vendas_total"])
