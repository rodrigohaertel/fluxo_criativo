#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dono14-relatorio-criativos.py — Regenera os BLOCOS NUMERICOS do relatorio de criativos.

Existe porque o relatorio-criativos-a30-a49-*.html vinha sendo remontado a mao todo
dia: 100 KB de HTML, cinco tabelas com dezenas de celulas cada, e o risco de um numero
velho sobreviver num canto. As secoes de julgamento (1, 3 a 14) continuam escritas a
mao, porque sao analise. O que este script cuida e do que muda sozinho a cada dia:

  - o painel de KPIs do topo
  - 1a. Mes contra mes (tabela + os tres paragrafos de leitura)
  - 1b. O placar dos ultimos 7 dias, por lead que pode comprar
  - 1c. Quem se cadastrou, por faixa de faturamento
  - 2.  Tabela mestre

Usa como molde o relatorio mais recente que existir na pasta e troca so esses blocos,
ancorando em cada <h2>. Somente leitura na Meta e no Supabase.

Antes de rodar: py -3 scripts/dono14-analise-criativos.py (gera o dataset).
Uso: py -3 scripts/dono14-relatorio-criativos.py
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "meus-produtos" / "dono-14" / "trafego" / "analise"
SB = "https://sizhdcrnfylimhsdfdnf.supabase.co"
CAMPANHA = "120247419652220527"
TZ = timezone(timedelta(hours=-3))
PERFIL_MIN, PERFIL_TETO = 100_000, 1_000_000   # ver reguas-criativos.md, CPL de perfil
REFERENCIA_CPLQ = 160                          # custo por lead no perfil, media da conta


def _env(chave):
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith(chave + "="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(chave + " nao encontrado no .env")


KEY = _env("SUPABASE_SERVICE_KEY")
TOK = _env("FB_ACCESS_TOKEN_PERMANENTE")


def sb(tabela, params):
    u = SB + "/rest/v1/" + tabela + "?" + urllib.parse.urlencode(params, safe="*.,()")
    r = urllib.request.Request(u, headers={"apikey": KEY, "Authorization": "Bearer " + KEY})
    return json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))


def meta_por_ad(desde, ate):
    tr = urllib.parse.quote(json.dumps({"since": desde, "until": ate}))
    u = ("https://graph.facebook.com/v21.0/" + CAMPANHA + "/insights?level=ad"
         "&fields=ad_name,spend,impressions,inline_link_clicks,actions"
         "&time_range=" + tr + "&limit=200&access_token=" + TOK)
    g = defaultdict(lambda: defaultdict(float))
    for r in json.loads(urllib.request.urlopen(u, timeout=90).read()).get("data", []):
        k = r["ad_name"].strip()[:4]
        g[k]["sp"] += float(r["spend"])
        g[k]["im"] += int(r["impressions"])
        g[k]["cl"] += int(r.get("inline_link_clicks") or 0)
        for a in r.get("actions", []):
            if a["action_type"] == "landing_page_view":
                g[k]["lpv"] += int(a["value"])
    return g


def brl(v, dec=0):
    return ("R$ " + format(v, "," + "." + str(dec) + "f")).replace(",", "X").replace(".", ",").replace("X", ".")


def dec1(v):
    """Uma casa decimal com virgula, porque o relatorio e em pt_BR."""
    return format(v, ".1f").replace(".", ",")


def pct(a, b):
    return (str(round(a / b * 100)) + "%") if b else "0%"


def sem_cplq(v):
    """Semaforo do CPL de perfil (reguas-criativos.md, adotado pelo Rodrigo em 24/09)."""
    if not v:
        return ""
    if v > 260:
        return "\U0001F534"
    if v >= 170:
        return "\U0001F7E1"
    if v >= 120:
        return "\U0001F7E2"
    return "\U0001F49A"


# ------------------------------------------------------------------ dados
ds = json.loads((PASTA / "dataset-criativos-a30-a46.json").read_text(encoding="utf-8"))
por_cri = {c["criativo"]: c for c in ds["criativos"]}

# O dataset devolve "(sem ficha editorial cadastrada)" para as pecas que ainda nao
# entraram no cockpit de criativos. Este mapa e o remendo, e sai daqui quando a ficha
# for cadastrada. Titulos conferidos no briefing de 12/09 e nos roteiros das pecas.
TITULO_FALLBACK = {
    "A47": "De cabeça eu não sei",
    "A48": "O seu bolso já pagou conta do restaurante",
    "A49": "Você fica com uma sensação",
}


def titulo_de(cri):
    t = (por_cri.get(cri, {}).get("titulo") or "").strip()
    if not t or "sem ficha" in t.lower():
        return TITULO_FALLBACK.get(cri, "")
    return t

reat = {r["submission_id"]: r["correto"] for r in json.loads(
    (RAIZ / "meus-produtos" / "dono-14" / "trafego" / "reatribuicoes.json"
     ).read_text(encoding="utf-8"))["reatribuicoes"]}
tags = {t["id"]: (t.get("name") or "") for t in sb("crm_tags", {"select": "id,name"})}
tags_card = defaultdict(list)
for x in sb("crm_card_tags", {"select": "card_id,tag_id"}):
    tags_card[x["card_id"]].append(tags.get(x["tag_id"], ""))
cards = sb("crm_cards", {"select": "id,stage,valor_contrato,submission_id", "deleted_at": "is.null"})
card_por_sub = {c["submission_id"]: c for c in cards if c.get("submission_id")}
subs = sb("contact_submissions", {
    "select": "id,name,created_at,utm_content,faturamento_medio",
    "or": "(source.ilike.mentoria*,source.ilike.sess*)",
    "created_at": "gte.2026-07-19T03:00:00+00:00", "order": "created_at.asc"})

HOJE = datetime.now(TZ).date()
ONTEM = HOJE - timedelta(days=1)
SETE = ONTEM - timedelta(days=6)
INICIO_UTM = datetime(2026, 7, 19).date()


def faixa_de(f):
    """Nome da faixa. O formulario mudou duas vezes (21/09 e 24/09), entao a leitura
    e por INTERVALO de valor, nunca pelo rotulo de um botao."""
    if f is None or f <= 0:
        return "nao"
    if f > PERFIL_TETO:
        return "falso"
    if f < 50_000:
        return "f49"
    if f < PERFIL_MIN:
        return "f99"
    if f < 200_000:
        return "f199"
    if f < 300_000:
        return "f299"
    return "f300"


def agrega(desde, ate):
    """Cadastros por criativo na janela, com faixa, perfil, sessao e venda."""
    ag = defaultdict(lambda: defaultdict(float))
    for s in subs:
        d = datetime.fromisoformat(
            s["created_at"].replace("Z", "+00:00").split(".")[0] + "+00:00").astimezone(TZ).date()
        if not (desde <= d <= ate):
            continue
        cri = (reat.get(s["id"]) or s.get("utm_content") or "").strip()[:4]
        if not cri:
            continue
        fx = faixa_de(float(s.get("faturamento_medio") or 0))
        a = ag[cri]
        a["n"] += 1
        a[fx] += 1
        if fx in ("f199", "f299", "f300"):
            a["q"] += 1
        c = card_por_sub.get(s["id"]) or {}
        if any("Sessão Agendada" in t for t in tags_card.get(c.get("id"), [])):
            a["sess"] += 1
        if c.get("stage") == "ganho":
            a["ganho"] += 1
            a["receita"] += float(c.get("valor_contrato") or 0)
    return ag


GANHOS_CRM = [c for c in cards if c.get("stage") == "ganho"]
VENDAS_CRM = len(GANHOS_CRM)
RECEITA_CRM = sum(float(c.get("valor_contrato") or 0) for c in GANHOS_CRM)


def bloco_kpis():
    fin, tot = ds["financeiro"], ds["totais"]
    visitas = sum((c.get("lpv") or 0) for c in ds["criativos"])
    sess = sum((c.get("sess_agendadas") or 0) for c in ds["criativos"])
    mes = ds["fechamento_mensal"].get(ONTEM.strftime("%Y-%m")) or {}
    cpl_mes = mes.get("cpl") or 0
    cplq_mes = (mes.get("gasto") / mes.get("q100")) if mes.get("q100") else 0
    teto = (fin["receita_rastreada"] / tot["leads_banco"]) if tot["leads_banco"] else 0
    cls_q = "bad" if cplq_mes > REFERENCIA_CPLQ else "win"
    return ('<div class="kpis">\n'
            '  <div class="kpi"><b>' + brl(tot["gasto"]) + '</b><span>investido em '
            + str(len(ds["criativos"])) + ' peças</span></div>\n'
            '  <div class="kpi"><b>' + str(visitas) + '</b><span>visitas na página</span></div>\n'
            '  <div class="kpi"><b>' + str(tot["leads_banco"]) + '</b><span>leads rastreados</span></div>\n'
            '  <div class="kpi"><b>' + str(sess) + '</b><span>sessões agendadas</span></div>\n'
            '  <div class="kpi win"><b>' + str(fin["vendas_rastreadas"]) + ' de ' + str(VENDAS_CRM)
            + '</b><span>vendas rastreáveis</span></div>\n'
            '  <div class="kpi win"><b>' + brl(fin["receita_rastreada"]) + '</b><span>receita rastreável</span></div>\n'
            '  <div class="kpi"><b>' + brl(teto) + '</b><span>teto de CPL</span></div>\n'
            '  <div class="kpi"><b>' + brl(cpl_mes) + '</b><span>CPL do mês corrente</span></div>\n'
            '  <div class="kpi ' + cls_q + '"><b>' + (brl(cplq_mes) if cplq_mes else "sem perfil")
            + '</b><span>CPL de perfil do mês</span></div>\n'
            '</div>')


MESES = {"06": "Junho", "07": "Julho", "08": "Agosto", "09": "Setembro",
         "10": "Outubro", "11": "Novembro", "12": "Dezembro"}


def bloco_1a():
    linhas = ""
    dados = []
    for ym in sorted(ds["fechamento_mensal"]):
        v = ds["fechamento_mensal"][ym]
        if not (v.get("leads") or v.get("gasto")):
            continue
        nome = MESES.get(ym[5:7], ym)
        corrente = ym == ONTEM.strftime("%Y-%m")
        if corrente:
            nome = nome + " (1 a " + str(ONTEM.day) + ")"
        dados.append((nome, v))
        cplq = (v["gasto"] / v["q100"]) if v["q100"] else 0
        linhas += ('<tr class="' + ("novo" if corrente else "") + '"><td class="k">' + nome + '</td>'
                   '<td class="n">' + brl(v["gasto"]) + '</td>'
                   '<td class="n">' + str(v["leads"]) + '</td>'
                   '<td class="n">' + str(v["q100"]) + ' <em class="dim">'
                   + str(round(v["taxa_q"])) + '%</em></td>'
                   '<td class="n">' + brl(v["cpl"]) + '</td>'
                   '<td class="n forte">' + ((sem_cplq(cplq) + " " + brl(cplq)) if cplq else "sem perfil") + '</td>'
                   '<td class="n forte">' + str(v["vendas"]) + '</td>'
                   '<td class="n forte">' + brl(v["receita"]) + '</td>'
                   '<td class="n">' + dec1(v["roas"]) + 'x</td></tr>')
    leitura = ""
    if len(dados) >= 2:
        na, va = dados[-2]
        nb, vb = dados[-1]
        cplq_a = (va["gasto"] / va["q100"]) if va["q100"] else 0
        cplq_b = (vb["gasto"] / vb["q100"]) if vb["q100"] else 0
        dq = vb["taxa_q"] - va["taxa_q"]
        leitura = (
            '<p><b>' + na + ' e ' + nb + ' custaram ' + brl(va["gasto"]) + ' e ' + brl(vb["gasto"])
            + ' em mídia de conversão.</b> ' + na + ' fechou ' + brl(va["receita"]) + ' com '
            + str(va["vendas"]) + ' venda(s), ROAS de ' + dec1(va["roas"]) + 'x. '
            + nb + ' fechou ' + brl(vb["receita"]) + ' com ' + str(vb["vendas"]) + ' venda(s), ROAS de '
            + dec1(vb["roas"]) + 'x.</p>'
            '<p><b>O degrau que mais mexeu foi a taxa de perfil:</b> de ' + str(round(va["taxa_q"]))
            + '% em ' + na.split(" (")[0].lower() + ' para ' + str(round(vb["taxa_q"])) + '% em '
            + nb.split(" (")[0].lower() + ', uma variação de ' + format(dq, "+.0f") + ' pontos. '
            'O custo por lead no perfil foi de ' + brl(cplq_a) + ' para ' + brl(cplq_b)
            + ', contra a referência de ' + brl(REFERENCIA_CPLQ) + ' da conta.</p>'
            '<p>O CPL simples saiu de ' + brl(va["cpl"]) + ' para ' + brl(vb["cpl"]) + '. '
            '<b>Comparar os dois CPL lado a lado é o ponto:</b> o simples pode cair enquanto o de perfil sobe, '
            'e é exatamente isso que as peças novas fizeram. A régua do CPL de perfil está em '
            '<code>reguas-criativos.md</code>.</p>')
    return ('<h2>1a. Mês contra mês, degrau por degrau</h2>\n'
            '<p class="sub">Mídia vem da Graph API. Cadastro, perfil, sessão e venda vêm do banco e do CRM, '
            'conferidos em ' + ONTEM.strftime("%d/%m/%Y") + '. A receita é contada pela data em que o cartão '
            'entrou em "ganho", e não pela data em que o lead entrou.</p>\n'
            '<div class="tbox"><table>\n'
            '<thead><tr><th>Mês</th><th>Mídia de conversão</th><th>Cadastros</th><th>No perfil</th><th>CPL</th>'
            '<th>CPL de perfil</th><th>Vendas</th><th>Receita</th><th>ROAS</th></tr></thead>\n'
            '<tbody>' + linhas + '</tbody></table></div>\n'
            '<div class="aviso">' + leitura + '</div>')


def bloco_1b():
    g = meta_por_ad(SETE.isoformat(), ONTEM.isoformat())
    ag = agrega(SETE, ONTEM)
    linhas = ""
    tg = tn = tq = 0.0
    for cri in sorted(g, key=lambda k: -g[k]["sp"]):
        if g[cri]["sp"] < 1:
            continue
        a = ag.get(cri, {})
        n = int(a.get("n", 0))
        q = int(a.get("q", 0))
        sp = g[cri]["sp"]
        tg += sp
        tn += n
        tq += q
        cplq = sp / q if q else 0
        linhas += ('<tr>\n <td class="k"><b>' + cri + '</b><em>'
                   + titulo_de(cri)[:46] + '</em></td>'
                   '<td class="n">' + brl(sp) + '</td>'
                   '<td class="n">' + str(int(g[cri]["lpv"])) + '</td>'
                   '<td class="n">' + str(n) + '</td>'
                   '<td class="n">' + (brl(sp / n) if n else "-") + '</td>'
                   '<td class="n forte">' + str(q) + '</td>'
                   '<td class="n forte">' + ((sem_cplq(cplq) + " " + brl(cplq)) if cplq else "nenhum") + '</td>'
                   '<td class="n">' + str(int(a.get("sess", 0))) + '</td></tr>')
    resumo = ('<p><b>Na janela toda:</b> ' + brl(tg) + ' gastos, ' + str(int(tn)) + ' cadastros, '
              + str(int(tq)) + ' no perfil (' + pct(tq, tn) + '), CPL simples de '
              + (brl(tg / tn) if tn else "-") + ' e <b>custo por lead no perfil de '
              + (brl(tg / tq) if tq else "nenhum lead no perfil") + '</b>, contra a referência de '
              + brl(REFERENCIA_CPLQ) + ' da conta.</p>')
    return ('<h2>1b. O placar dos últimos 7 dias, por lead que pode comprar</h2>\n'
            '<p class="sub">Janela de ' + SETE.strftime("%d/%m") + ' a ' + ONTEM.strftime("%d/%m")
            + ', só as peças que gastaram. A coluna que decide é a destacada: <b>quanto custou cada lead '
            'dentro do perfil de R$ 100 mil</b>. Faturamento declarado acima de R$ 1 milhão é descartado '
            'como preenchimento falso. Régua: 💚 abaixo de R$ 120 · 🟢 até R$ 170 · 🟡 até R$ 260 · '
            '🔴 acima disso.</p>\n'
            '<div class="tbox"><table>\n'
            '<thead><tr><th>Peça</th><th>Gasto na janela</th><th>Visitas</th><th>Leads</th><th>CPL</th>'
            '<th>No perfil</th><th>Custo por lead no perfil</th><th>Sessões</th></tr></thead>\n'
            '<tbody>' + linhas + '</tbody></table></div>\n'
            '<div class="fix">' + resumo + '</div>')


COLS = [("f49", "Até R$ 49 mil", ""), ("f99", "R$ 50 a 99 mil", ""),
        ("f199", "R$ 100 a 199 mil", "forte"), ("f299", "R$ 200 a 299 mil", "forte"),
        ("f300", "R$ 300 mil ou mais", "forte"), ("falso", "Falso", ""),
        ("nao", "Não informado", "")]


def bloco_1c():
    ag = agrega(INICIO_UTM, ONTEM)
    linhas = ""
    for cri in sorted(ag):
        a = ag[cri]
        n = int(a["n"])
        if not n:
            continue
        gasto = por_cri.get(cri, {}).get("gasto_rast") or 0
        cel = ""
        for chave, _, cls in COLS:
            v = int(a.get(chave, 0))
            cel += ('<td class="n ' + (cls if v else "dim") + '">' + (str(v) if v else "·")
                    + '<em class="dim"> ' + pct(v, n) + '</em></td>')
        q = int(a["q"])
        cplq = gasto / q if q else 0
        linhas += ('<tr><td class="k"><b>' + cri + '</b> '
                   + titulo_de(cri)[:40] + '</td>'
                   '<td class="n">' + str(n) + '</td>' + cel
                   + '<td class="n forte">' + str(q) + ' <em class="dim">' + pct(q, n) + '</em></td>'
                   '<td class="n forte">' + ((sem_cplq(cplq) + " " + brl(cplq)) if cplq else "nenhum")
                   + '</td></tr>')
    th = "".join("<th>" + nome + "</th>" for _, nome, _ in COLS)
    return ('<h2>1c. Quem se cadastrou, por faixa de faturamento</h2>\n'
            '<p class="sub">O que decide nesta conta não é o volume de cadastro, é quantos deles estão no '
            '<b>perfil Dono 14%</b>, que começa em R$ 100 mil de faturamento. Abaixo disso a triagem manda '
            'para o Painel do Dono e a peça não alimenta a Sessão Estratégica. O formulário mudou de faixas '
            'duas vezes (21/09 e 24/09), então a leitura é por intervalo de valor, nunca pelo rótulo de um '
            'botão. As três colunas em destaque são o perfil.</p>\n'
            '<div class="tbox"><table>\n'
            '<thead><tr><th>Peça</th><th>Leads</th>' + th
            + '<th>No perfil Dono 14%</th><th>Custo por lead no perfil</th></tr></thead>\n'
            '<tbody>' + linhas + '</tbody></table></div>')


def bloco_2():
    linhas = ""
    for c in ds["criativos"]:
        cri = c["criativo"]
        ld = int(c.get("leads_banco") or 0)
        rast = bool(c.get("rastreado")) or ld > 0
        lpv = int(c.get("lpv") or 0)
        cpl = c.get("cpl_banco") or 0
        cplq = c.get("cpl_q") or 0
        linhas += ('<tr class="' + ("" if rast else "apagado") + '">\n'
                   ' <td class="k"><b>' + cri + '</b><em>' + titulo_de(cri)[:46] + '</em></td>'
                   '<td class="dim">' + str(c.get("lote") or "-") + '</td>'
                   '<td class="dim">' + str(c.get("familia") or "-") + '</td>'
                   '<td class="dim">' + str(c.get("textura") or "-") + '</td>'
                   '<td class="n">' + str(c.get("dur") or "-") + '</td>'
                   '<td class="n">' + brl(c.get("gasto") or 0) + '</td>'
                   '<td class="n">' + brl(c.get("cpm") or 0) + '</td>'
                   '<td class="n">' + format((c.get("hook") or 0) * 100, ".1f") + '%</td>'
                   '<td class="n">' + format((c.get("p50") or 0) * 100, ".1f") + '%</td>'
                   '<td class="n">' + format(c.get("ctr_link") or 0, ".2f") + '%</td>'
                   '<td class="n">' + str(lpv) + '</td>'
                   '<td class="n forte">' + (str(ld) if rast else '<em class="dim">sem rastreio</em>') + '</td>'
                   '<td class="n">' + (brl(cpl) if cpl else "-") + '</td>'
                   '<td class="n">' + (pct(ld, lpv) if (rast and lpv) else "-") + '</td>'
                   '<td class="n forte">' + (str(int(c.get("q100") or 0)) if rast else "-") + '</td>'
                   '<td class="n forte">' + ((sem_cplq(cplq) + " " + brl(cplq)) if cplq else "-") + '</td>'
                   '<td class="n">' + (str(int(c.get("sess_agendadas") or 0)) if rast else "-") + '</td>'
                   '<td class="n forte">' + (str(int(c.get("ganhos") or 0)) if rast else "-") + '</td>'
                   '<td class="n forte">' + (brl(c.get("receita") or 0) if c.get("receita") else "-")
                   + '</td></tr>')
    return ('<h2>2. Tabela mestre: as ' + str(len(ds["criativos"])) + ' peças lado a lado</h2>\n'
            '<p class="sub">Vida inteira de cada peça. Lead, qualificação, sessão e venda vêm do banco e do '
            'CRM. Para A30 a A38 não existe lead rastreável, porque o código do criativo só passou a ser '
            'gravado em 19/07/2026. A coluna <b>CPL de perfil</b> é a régua adotada em 24/09. Atenção: aqui '
            'ela vem do dataset, que não aplica o teto de R$ 1 milhão; a seção 1c aplica.</p>\n'
            '<div class="tbox"><table>\n'
            '<thead><tr><th>Peça</th><th>Lote</th><th>Família</th><th>Textura</th><th>Dur</th><th>Gasto</th>'
            '<th>CPM</th><th>Hook</th><th>P50</th><th>CTR link</th><th>Visitas</th><th>Leads</th><th>CPL</th>'
            '<th>Visita→lead</th><th>Qualif</th><th>CPL de perfil</th><th>Sessões</th><th>Vendas</th>'
            '<th>Receita</th></tr></thead>\n'
            '<tbody>' + linhas + '</tbody></table></div>')


# ------------------------------------------------------------------ montagem
moldes = sorted(PASTA.glob("relatorio-criativos-a30-a49-2026-*.html"))
if not moldes:
    sys.exit("ERRO: nenhum relatorio anterior para usar de molde.")
html = moldes[-1].read_text(encoding="utf-8")
print(">>> molde: " + moldes[-1].name)


def troca_h2(texto, prefixo, novo):
    """Troca o bloco que vai do <h2> indicado ate o proximo <h2>."""
    m = re.search(r"<h2>" + re.escape(prefixo) + r".*?</h2>", texto, re.S)
    if not m:
        print("    AVISO: secao '" + prefixo + "' nao encontrada, mantida como estava")
        return texto
    prox = texto.find("<h2>", m.end())
    fim = prox if prox > 0 else len(texto)
    return texto[:m.start()] + novo + "\n\n" + texto[fim:]


novo_kpi = bloco_kpis()
if re.search(r'<div class="kpis">.*?</div>\s*(?=<h2>)', html, re.S):
    html = re.sub(r'<div class="kpis">.*?</div>\s*(?=<h2>)', lambda _: novo_kpi + "\n\n", html,
                  count=1, flags=re.S)
    print("    KPIs regerados")
else:
    print("    AVISO: painel de KPIs nao encontrado")

for prefixo, fn in (("1a.", bloco_1a), ("1b.", bloco_1b), ("1c.", bloco_1c), ("2.", bloco_2)):
    html = troca_h2(html, prefixo, fn())
    print("    secao " + prefixo + " regerada")

html = re.sub(r"(conferidos? em )\d{2}/\d{2}/\d{4}", "\\g<1>" + ONTEM.strftime("%d/%m/%Y"), html)

destino = PASTA / ("relatorio-criativos-a30-a49-" + HOJE.isoformat() + ".html")
destino.write_text(html, encoding="utf-8")
(PASTA / "relatorio-criativos-ATUAL.html").write_text(html, encoding="utf-8")
print(">>> salvo:       " + str(destino))
print(">>> atalho fixo: " + str(PASTA / "relatorio-criativos-ATUAL.html"))
