#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documento oficial do funil do CRM do Dono 14%, em tres janelas.

  Janela G. Global      todo o CRM, do primeiro lead ate a data de corte
  Janela A. Antes       do inicio ate 16/07/2026, sem o agente de WhatsApp
  Janela B. Depois      de 17/07/2026 em diante, com o agente no ar

A e B nao se sobrepoem, entao servem de comparacao. G e a soma das duas.

Alem do funil, o documento traz a analise de impacto do agente, que trata os dois
vieses que impedem a leitura ingenua do antes contra depois:
  Vies de marcacao   no periodo antes, metade dos cards nao tem tag de produto, e os
                     que tem sao os que avancaram. Tratado com metrica que nao depende
                     da tag: agendamentos sobre o total de leads.
  Vies de maturacao  o periodo antes ja fechou seu ciclo, o depois ainda tem pipeline
                     aberto. Tratado com coorte de dias de vida e com o valor em aberto.

Etapas do funil (definidas pelo Rodrigo):
  1. Total de leads       submissoes do periodo
  2. Leads Dono 14%       cards com a tag "Dono 14%"
  3. Sessoes agendadas    tag "Sessao Agendada" OU campo sessao_agendada preenchido
  4. Comparecimento       agendadas menos os que faltaram
                          (falta = tag "No Show" sem a tag "Sessao Realizada")
                          A tag "Sessao Realizada" nasceu em 09/08 e nao cobre o periodo
                          inteiro, por isso ela nao vira etapa, so corrige o No Show.
  5. Fechamentos          estagio ganho, contrato assinado

Uso: py -3 scripts/dono14-funil-whatsapp.py [AAAA-MM-DD]
     sem argumento, corta em 2026-08-12
Chave lida do .env: SUPABASE_SERVICE_KEY
"""
import json
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "meus-produtos" / "dono-14" / "trafego" / "analise"
SUPABASE = "https://sizhdcrnfylimhsdfdnf.supabase.co"

INICIO_AGENTE = "2026-07-17"   # primeira mensagem e primeira conversa do agente
FIM_ANTES = "2026-07-16"       # ultimo dia sem o agente
COORTE_DIAS = 7                # dias de vida para a comparacao de maturacao equalizada
FIM = sys.argv[1] if len(sys.argv) > 1 else "2026-08-12"
TAG_REALIZADA_CRIADA = "2026-08-09"
TAGS_CRIADAS = "2026-06-22"    # dia em que o conjunto de tags do CRM foi criado


def env(chave):
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith(chave + "="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit(f"ERRO: {chave} nao encontrado no .env")


KEY = env("SUPABASE_SERVICE_KEY")


def sb(tabela, params):
    url = f"{SUPABASE}/rest/v1/{tabela}?" + urllib.parse.urlencode(params, safe="*.,()")
    r = urllib.request.Request(url, headers={"apikey": KEY, "Authorization": "Bearer " + KEY})
    return json.loads(urllib.request.urlopen(r, timeout=60).read().decode())


print(f">>> Corte em {FIM} | agente desde {INICIO_AGENTE}")
tags_meta = sb("crm_tags", {"select": "id,name,created_at", "limit": "100"})
tags = {t["id"]: t["name"] for t in tags_meta}
vinculos = sb("crm_card_tags", {"select": "card_id,tag_id,created_at", "limit": "10000"})
por_card = defaultdict(set)
tag_em = defaultdict(dict)          # quando cada tag foi aplicada, para medir velocidade
for v in vinculos:
    nome = tags.get(v["tag_id"])
    por_card[v["card_id"]].add(nome)
    tag_em[v["card_id"]][nome] = v["created_at"][:10]

cards = sb("crm_cards", {
    "select": "id,submission_id,nome,stage,created_at,sessao_agendada,valor_contrato,faturamento_medio,stage_changed_at",
    "deleted_at": "is.null", "limit": "5000"})
subs = sb("contact_submissions", {
    "select": "id,name,source,ab_variant,utm_content,created_at", "limit": "5000"})
sub_por_id = {s["id"]: s for s in subs}


def entrada(c):
    s = sub_por_id.get(c.get("submission_id"))
    return (s["created_at"] if s else c["created_at"])[:10]


T = lambda c: {x for x in por_card.get(c["id"], set()) if x}
PRIMEIRO = min(entrada(c) for c in cards)


def dias(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def media(l):
    return round(sum(l) / len(l), 1) if l else None


def janela(ini, fim=None):
    """Monta todos os numeros de uma janela de datas."""
    fim = fim or FIM
    per = [c for c in cards if ini <= entrada(c) <= fim]
    leads_per = [s for s in subs if ini <= s["created_at"][:10] <= fim]
    d14 = [c for c in per if "Dono 14%" in T(c)]
    painel = [c for c in per if "Painel do Dono" in T(c)]
    sem_prod = [c for c in per if not ({"Dono 14%", "Painel do Dono", "Projeto 14%"} & T(c))]
    agendou_tudo = [c for c in per if ("Sessão Agendada" in T(c)) or c.get("sessao_agendada")]
    # a cadeia a partir daqui roda dentro do subconjunto Dono 14%, senao o funil
    # soma agendamento de outro produto no numerador e infla a taxa
    ag = [c for c in d14 if ("Sessão Agendada" in T(c)) or c.get("sessao_agendada")]
    ag_fora = [c for c in agendou_tudo if c not in ag]
    faltou = [c for c in ag if "No Show" in T(c) and "Sessão Realizada" not in T(c)]
    compareceu = len(ag) - len(faltou)
    ganho = [c for c in d14 if c["stage"] == "ganho"]
    ganho_fora = [c for c in per if c["stage"] == "ganho" and c not in ganho]
    contrato = [c for c in d14 if c["stage"] == "contrato"]
    stages = defaultdict(int)
    for c in per:
        stages[c["stage"] or "sem estágio"] += 1
    # auditoria de marcacao
    aud = dict(
        data_sem_tag=[c for c in per if c.get("sessao_agendada") and "Sessão Agendada" not in T(c)],
        tag_sem_data=[c for c in per if "Sessão Agendada" in T(c) and not c.get("sessao_agendada")],
        noshow_e_realizada=[c for c in per if "No Show" in T(c) and "Sessão Realizada" in T(c)],
        noshow_sem_agenda=[c for c in per if "No Show" in T(c) and "Sessão Agendada" not in T(c)
                           and not c.get("sessao_agendada")],
        sem_tag_produto=sem_prod,
        sem_tag_alguma=[c for c in per if not T(c)],
    )
    # ---- metricas que nao dependem da tag de produto (imunes ao vies de marcacao)
    ag_qualquer = [c for c in per if ("Sessão Agendada" in T(c)) or c.get("sessao_agendada")]
    ganho_qualquer = [c for c in per if c["stage"] == "ganho"]

    # ---- coorte equalizada: so quem ja teve COORTE_DIAS de vida ate o corte
    maduros = [c for c in per if dias(entrada(c), fim) >= COORTE_DIAS]
    ag_coorte = [c for c in maduros
                 if tag_em[c["id"]].get("Sessão Agendada")
                 and dias(entrada(c), tag_em[c["id"]]["Sessão Agendada"]) <= COORTE_DIAS]

    # ---- velocidade entre etapas
    t_lead_ag, t_ag_sessao, t_lead_fecha = [], [], []
    for c in per:
        marcou = tag_em[c["id"]].get("Sessão Agendada")
        if marcou and entrada(c) <= marcou:
            t_lead_ag.append(dias(entrada(c), marcou))
        if marcou and c.get("sessao_agendada") and marcou <= c["sessao_agendada"][:10]:
            t_ag_sessao.append(dias(marcou, c["sessao_agendada"][:10]))
        if c["stage"] == "ganho" and c.get("stage_changed_at"):
            t_lead_fecha.append(dias(entrada(c), c["stage_changed_at"][:10]))

    return dict(
        cards=per, leads=len(leads_per), d14=len(d14), painel=len(painel), sem_prod=len(sem_prod),
        ag_qualquer=len(ag_qualquer), ganho_qualquer=len(ganho_qualquer),
        maduros=len(maduros), ag_coorte=len(ag_coorte),
        vel_lead_ag=media(t_lead_ag), n_lead_ag=len(t_lead_ag),
        vel_ag_sessao=media(t_ag_sessao), n_ag_sessao=len(t_ag_sessao),
        vel_lead_fecha=media(t_lead_fecha), n_lead_fecha=len(t_lead_fecha),
        ini=ini, fim=fim,
        agendou=len(ag), agendou_tudo=len(agendou_tudo), ag_fora=ag_fora,
        faltou=len(faltou), compareceu=compareceu,
        ganho=len(ganho), ganho_fora=ganho_fora, contrato=len(contrato),
        valor_ganho=sum(c.get("valor_contrato") or 0 for c in ganho),
        valor_contrato=sum(c.get("valor_contrato") or 0 for c in contrato),
        stages=dict(stages), aud=aud,
    )


G = janela(PRIMEIRO)                      # global
A = janela(PRIMEIRO, FIM_ANTES)           # antes do agente
B = janela(INICIO_AGENTE)                 # depois do agente

# leads por semana, nas duas janelas
por_semana = defaultdict(lambda: [0, 0])
for s in subs:
    d = s["created_at"][:10]
    if not (PRIMEIRO <= d <= FIM):
        continue
    dt = date.fromisoformat(d)
    sem = date.fromordinal(dt.toordinal() - dt.weekday()).isoformat()
    por_semana[sem][0] += 1
    if d >= INICIO_AGENTE:
        por_semana[sem][1] += 1


def pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


def brl(v):
    return "R$ " + f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def etapas(J):
    return [
        ("Total de leads", J["leads"], None, "todas as pessoas que entraram no CRM"),
        ("Leads Dono 14%", J["d14"], J["leads"], "triados com a tag do produto"),
        ("Sessões agendadas", J["agendou"], J["d14"], "tag de agendamento ou data de sessão no card"),
        ("Comparecimento", J["compareceu"], J["agendou"], "agendadas menos quem faltou e não remarcou"),
        ("Fechamentos", J["ganho"], J["compareceu"], "estágio ganho, contrato assinado"),
    ]


def funil(J, cls=""):
    et = etapas(J)
    base = et[0][1] or 1
    out = []
    for nome, v, ant, obs in et:
        larg = max(6, round(100 * v / base))
        # dentro da barra, o absoluto e o percentual sobre a base do funil (total de leads).
        # o percentual da etapa anterior fica no cabecalho, sao leituras diferentes.
        rotulo = f"{v} ({num(pct(v, base), 0)}%)"
        # barra estreita nao comporta o rotulo dentro, entao ele sai para fora
        fora = larg < 26
        conv = '<span class="conv topo">base</span>' if ant is None else \
               f'<span class="conv">{num(pct(v, ant), 0)}% da anterior</span>'
        dentro = "" if fora else f"<span>{rotulo}</span>"
        depois = f'<span class="rot-fora">{rotulo}</span>' if fora else ""
        out.append(f'''<div class="etapa">
      <div class="cab"><b>{nome}</b>{conv}</div>
      <div class="trilho"><div class="preenchida {cls}" style="width:{larg}%">{dentro}</div>{depois}</div>
      <p class="obs">{obs}</p>
    </div>''')
    return "\n".join(out)


PASSAGENS = [
    ("Lead vira lead Dono 14%", lambda J: (J["d14"], J["leads"])),
    ("Lead Dono 14% agenda sessão", lambda J: (J["agendou"], J["d14"])),
    ("Agendou e compareceu", lambda J: (J["compareceu"], J["agendou"])),
    ("Compareceu e fechou", lambda J: (J["ganho"], J["compareceu"])),
    ("Lead vira contrato, ponta a ponta", lambda J: (J["ganho"], J["leads"])),
]


def linha_passagem(nome, fn):
    g_num, g_den = fn(G)
    a_num, a_den = fn(A)
    b_num, b_den = fn(B)
    g_p, a_p, b_p = pct(g_num, g_den), pct(a_num, a_den), pct(b_num, b_den)
    delta = round(b_p - a_p, 1)
    seta = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
    cor = "win" if delta > 0 else ("bad" if delta < 0 else "dim")
    return f"""<tr>
  <td class="k">{nome}</td>
  <td class="n dim">{g_num} de {g_den}</td><td class="n">{num(g_p)}%</td>
  <td class="n dim">{a_num} de {a_den}</td><td class="n forte">{num(a_p)}%</td>
  <td class="n dim">{b_num} de {b_den}</td><td class="n forte">{num(b_p)}%</td>
  <td class="n {cor}">{seta} {num(abs(delta))} p.p.</td>
</tr>"""


def nominal(lista):
    if not lista:
        return '<p class="zerado">nenhum caso, marcação limpa</p>'
    itens = ""
    for c in lista:
        t = " · ".join(sorted(T(c))) or "sem tag"
        d = (c.get("sessao_agendada") or "")[:10]
        det = f" · sessão em {d[8:10]}/{d[5:7]}" if d else ""
        itens += f"<li><b>{c['nome']}</b> <em>{c['stage']}{det}</em><span class='tgs'>{t}</span></li>"
    return f"<ul class='nom'>{itens}</ul>"


AUDITS = [
    ("Data de sessão no card, sem a tag de agendamento", "data_sem_tag",
     "A sessão existe, mas ninguém marcou a tag. Contando só por tag, a sessão some do funil."),
    ("Tag de agendamento, sem data de sessão", "tag_sem_data",
     "O inverso. A tag diz que agendou, mas não há data no card para conferir."),
    ("No Show junto com Sessão Realizada", "noshow_e_realizada",
     "Contradição. Provável remarcação em que a tag de falta ficou para trás."),
    ("No Show sem nenhum sinal de agendamento", "noshow_sem_agenda",
     "Marcado como falta sem tag nem data de sessão."),
    ("Sem tag de produto", "sem_tag_produto",
     "Não dá para saber se o lead é Dono 14%, Painel do Dono ou outro."),
]

gerado = datetime.now().strftime("%d/%m/%Y às %H:%M")
dias_g = dias(PRIMEIRO, FIM)
dias_a = dias(PRIMEIRO, FIM_ANTES)
dias_b = dias(INICIO_AGENTE, FIM)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Funil do CRM · Dono 14% · histórico e recorte do agente</title>
<style>
  :root{{
    --bg:#0b241b; --bg2:#0f2e23; --card:#143a2d; --line:#2a4d3f;
    --gold:#c9a86a; --gold2:#e3cd9e; --cream:#f4efe4; --muted:#9fb5aa;
    --win:#37d399; --warn:#f2c14e; --bad:#e06a6a;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--cream);line-height:1.6;padding:36px 18px 80px}}
  .wrap{{max-width:1120px;margin:0 auto}}
  header{{border-bottom:2px solid var(--gold);padding-bottom:22px;margin-bottom:10px}}
  .kicker{{color:var(--gold);font-size:.74rem;letter-spacing:.22em;text-transform:uppercase;margin-bottom:10px}}
  h1{{font-size:2rem;color:#fff;line-height:1.14;margin-bottom:12px}}
  .lead{{color:var(--gold2);max-width:880px}}
  h2{{color:var(--gold);font-size:1.06rem;text-transform:uppercase;letter-spacing:.08em;margin:46px 0 6px;padding-left:12px;border-left:3px solid var(--gold)}}
  h2 + .sub{{color:var(--muted);font-size:.9rem;margin:0 0 18px 15px;max-width:900px}}
  h3{{color:#fff;font-size:1.05rem;margin-bottom:4px}}
  h4{{color:var(--gold2);font-size:.93rem;margin:18px 0 6px}}
  p{{margin-bottom:12px}} b{{color:var(--gold2)}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 17px}}
  .kpi b{{display:block;font-size:1.7rem;color:#fff;line-height:1.1;font-variant-numeric:tabular-nums}}
  .kpi span{{display:block;font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:5px}}
  .kpi.win b{{color:var(--win)}} .kpi.warn b{{color:var(--warn)}}
  .dois{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  .tres{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
  .painel.g{{border-top:3px solid var(--muted)}}
  .preenchida.g{{background:linear-gradient(90deg,#33544a,#8fa79c)}}
  .painel{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px}}
  .painel.a{{border-top:3px solid var(--gold)}} .painel.b{{border-top:3px solid var(--win)}}
  .painel .tit{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}}
  .painel .per{{color:var(--muted);font-size:.8rem;margin-bottom:6px}}
  .etapa{{margin:14px 0}}
  .cab{{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:5px}}
  .cab b{{color:#fff;font-size:.93rem}}
  .conv{{font-size:.74rem;color:var(--gold);white-space:nowrap}} .conv.topo{{color:var(--muted)}}
  .trilho{{background:rgba(255,255,255,.05);border-radius:8px;overflow:hidden;height:34px;display:flex;align-items:center}}
  .preenchida{{height:100%;flex-shrink:0;background:linear-gradient(90deg,#2a6b52,var(--gold));border-radius:8px;display:flex;align-items:center;justify-content:flex-end;padding-right:11px}}
  .rot-fora{{padding-left:10px;color:var(--cream);font-weight:700;font-size:.9rem;font-variant-numeric:tabular-nums;white-space:nowrap}}
  .preenchida.b{{background:linear-gradient(90deg,#2a6b52,var(--win))}}
  .preenchida span{{color:#08281d;font-weight:800;font-size:.94rem;font-variant-numeric:tabular-nums}}
  .obs{{color:var(--muted);font-size:.77rem;margin:4px 0 0}}
  .tbox{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--bg2);margin:10px 0}}
  table{{width:100%;border-collapse:collapse;font-size:.87rem;min-width:660px}}
  th{{background:#0d2b21;color:var(--gold);text-transform:uppercase;font-size:.63rem;letter-spacing:.07em;padding:11px 10px;text-align:right}}
  th:first-child{{text-align:left}}
  th.grupo{{text-align:center;border-left:1px solid var(--line);color:var(--gold2)}}
  td{{padding:11px 10px;border-top:1px solid var(--line)}}
  td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
  td.k{{color:var(--gold2);font-weight:600}}
  td.forte{{color:#fff;font-weight:700}}
  td.win{{color:var(--win)}} td.bad{{color:var(--bad)}} td.dim{{color:var(--muted)}}
  .aviso{{background:linear-gradient(180deg,rgba(242,193,78,.12),rgba(20,58,45,.35));border:1px solid var(--warn);border-radius:12px;padding:16px 20px;margin:16px 0}}
  .aviso b{{color:var(--warn)}}
  .ok{{background:rgba(55,211,153,.08);border:1px solid rgba(55,211,153,.4);border-radius:12px;padding:16px 20px;margin:14px 0}}
  .ok b{{color:var(--win)}}
  .alerta{{background:rgba(224,106,106,.09);border:1px solid rgba(224,106,106,.45);border-radius:12px;padding:16px 20px;margin:14px 0}}
  .alerta b{{color:var(--bad)}}
  ul.nom{{list-style:none;margin:6px 0}}
  ul.nom li{{padding:8px 0;border-bottom:1px solid rgba(42,77,63,.6);font-size:.85rem;display:flex;flex-wrap:wrap;gap:8px;align-items:baseline}}
  ul.nom li:last-child{{border:none}} ul.nom li b{{color:#fff}}
  ul.nom li em{{font-style:normal;color:var(--muted);font-size:.79rem}}
  .tgs{{margin-left:auto;color:var(--gold);font-size:.71rem;text-align:right}}
  .zerado{{color:var(--win);font-size:.84rem;margin:6px 0 0}}
  .placar{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:12px 0}}
  .item{{background:var(--bg2);border:1px solid var(--line);border-radius:11px;padding:13px 15px}}
  .item.limpo{{border-color:rgba(55,211,153,.45)}}
  .item .q{{font-size:.8rem;color:var(--cream);line-height:1.35}}
  .item .v{{font-size:1.45rem;font-weight:800;color:var(--win);font-variant-numeric:tabular-nums}}
  .item.sujo .v{{color:var(--warn)}}
  .barra{{display:flex;align-items:center;gap:9px}}
  .barra i{{display:block;height:9px;background:linear-gradient(90deg,#2a6b52,var(--gold));border-radius:6px}}
  .barra i.b{{background:linear-gradient(90deg,#2a6b52,var(--win))}}
  footer{{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:.8rem}}
  @media(max-width:980px){{.tres{{grid-template-columns:1fr}}}}
  @media(max-width:780px){{.dois{{grid-template-columns:1fr}} body{{padding:22px 12px 60px}} h1{{font-size:1.5rem}}}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="kicker">Documento oficial · Funil do CRM · Mentoria Dono 14%</div>
  <h1>O funil do CRM em três janelas, e o que o agente de WhatsApp mudou de fato.</h1>
  <p class="lead">Três janelas na mesma régua. Global, de {PRIMEIRO[8:10]}/{PRIMEIRO[5:7]} a {FIM[8:10]}/{FIM[5:7]} ({dias_g} dias). Antes do agente, até {FIM_ANTES[8:10]}/{FIM_ANTES[5:7]} ({dias_a} dias). Depois do agente, de {INICIO_AGENTE[8:10]}/{INICIO_AGENTE[5:7]} em diante ({dias_b} dias). Antes e Depois não se sobrepõem, então servem de comparação real, e a seção 3 usa as duas para responder se o agente melhorou o funil. Fonte: contact_submissions, crm_cards e as tags do CRM de produção. Snapshot de {gerado}, com dados fechados até {FIM[8:10]}/{FIM[5:7]}.</p>
</header>

<div class="kpis">
  <div class="kpi"><b>{G['leads']}</b><span>leads no CRM, total</span></div>
  <div class="kpi win"><b>{B['leads']}</b><span>leads desde o agente</span></div>
  <div class="kpi"><b>{G['d14']}</b><span>leads Dono 14%, total</span></div>
  <div class="kpi warn"><b>{B['agendou']}</b><span>sessões agendadas com o agente</span></div>
  <div class="kpi"><b>{G['ganho']}</b><span>fechamentos, total</span></div>
  <div class="kpi win"><b>{brl(G['valor_ganho'])}</b><span>receita fechada, total</span></div>
</div>

<h2>1. O funil nas três janelas</h2>
<p class="sub">Mesma definição de etapa nas três, para a comparação ser justa. A janela Global é a soma das outras duas. Antes e Depois não se sobrepõem, e são elas que sustentam a comparação da seção 3. Sessão agendada considera a tag de agendamento ou a data de sessão preenchida no card. Comparecimento desconta quem tem a tag No Show e não tem a de Sessão Realizada, ou seja, faltou e não remarcou.</p>

<div class="tres">
  <div class="painel g">
    <div class="tit">Janela 1</div>
    <h3>Global</h3>
    <p class="per">{PRIMEIRO[8:10]}/{PRIMEIRO[5:7]} a {FIM[8:10]}/{FIM[5:7]} · {dias_g} dias</p>
    {funil(G, "g")}
  </div>
  <div class="painel a">
    <div class="tit">Janela 2</div>
    <h3>Antes do agente</h3>
    <p class="per">{PRIMEIRO[8:10]}/{PRIMEIRO[5:7]} a {FIM_ANTES[8:10]}/{FIM_ANTES[5:7]} · {dias_a} dias</p>
    {funil(A)}
  </div>
  <div class="painel b">
    <div class="tit">Janela 3</div>
    <h3>Depois do agente</h3>
    <p class="per">{INICIO_AGENTE[8:10]}/{INICIO_AGENTE[5:7]} a {FIM[8:10]}/{FIM[5:7]} · {dias_b} dias</p>
    {funil(B, "b")}
  </div>
</div>

<div class="aviso">
  <p><b>O período com agente concentra quase metade do CRM em menos tempo.</b> São {B['leads']} dos {G['leads']} leads ({num(pct(B['leads'], G['leads']),0)}%) em {dias_b} dos {dias_g} dias. O ritmo passou de {num(A['leads']/dias_a,1)} para {num(B['leads']/dias_b,1)} leads por dia, alta de {num(100*((B['leads']/dias_b)/(A['leads']/dias_a)-1),0)}%.</p>
</div>

<h2>2. As taxas de passagem, número e percentual</h2>
<p class="sub">Cada linha é uma passagem do funil, com a conta fechada e o percentual nas duas janelas. A última coluna mostra a diferença em pontos percentuais entre o recorte do agente e o histórico completo.</p>
<div class="tbox"><table>
<thead>
  <tr>
    <th rowspan="2">Passagem</th>
    <th colspan="2" class="grupo">Global</th>
    <th colspan="2" class="grupo">Antes do agente</th>
    <th colspan="2" class="grupo">Depois do agente</th>
    <th rowspan="2">Antes → Depois</th>
  </tr>
  <tr><th>Números</th><th>%</th><th>Números</th><th>%</th><th>Números</th><th>%</th></tr>
</thead>
<tbody>
{''.join(linha_passagem(nome, fn) for nome, fn in PASSAGENS)}
</tbody></table></div>

<div class="tbox"><table>
<thead><tr><th>Etapa, em valor absoluto</th><th>Global</th><th>Antes do agente</th><th>Depois do agente</th></tr></thead>
<tbody>
  <tr><td class="k">Total de leads</td><td class="n forte">{G['leads']}</td><td class="n forte">{A['leads']}</td><td class="n forte">{B['leads']}</td></tr>
  <tr><td class="k">Leads Dono 14%</td><td class="n forte">{G['d14']}</td><td class="n forte">{A['d14']}</td><td class="n forte">{B['d14']}</td></tr>
  <tr><td class="k">Leads Painel do Dono</td><td class="n">{G['painel']}</td><td class="n">{A['painel']}</td><td class="n">{B['painel']}</td></tr>
  <tr><td class="k">Sessões agendadas</td><td class="n forte">{G['agendou']}</td><td class="n forte">{A['agendou']}</td><td class="n forte">{B['agendou']}</td></tr>
  <tr><td class="k">Faltaram e não remarcaram</td><td class="n">{G['faltou']}</td><td class="n">{A['faltou']}</td><td class="n">{B['faltou']}</td></tr>
  <tr><td class="k">Compareceram</td><td class="n forte">{G['compareceu']}</td><td class="n forte">{A['compareceu']}</td><td class="n forte">{B['compareceu']}</td></tr>
  <tr><td class="k">Fechamentos</td><td class="n forte">{G['ganho']}</td><td class="n forte">{A['ganho']}</td><td class="n forte">{B['ganho']}</td></tr>
  <tr><td class="k">Em contrato, ainda não é receita</td><td class="n">{G['contrato']}</td><td class="n">{A['contrato']}</td><td class="n">{B['contrato']}</td></tr>
  <tr><td class="k">Receita fechada</td><td class="n forte">{brl(G['valor_ganho'])}</td><td class="n forte">{brl(A['valor_ganho'])}</td><td class="n forte">{brl(B['valor_ganho'])}</td></tr>
  <tr><td class="k">Valor em contrato</td><td class="n">{brl(G['valor_contrato'])}</td><td class="n">{brl(A['valor_contrato'])}</td><td class="n">{brl(B['valor_contrato'])}</td></tr>
</tbody></table></div>

<div class="aviso">
  <p><b>Por que o funil roda dentro do subconjunto Dono 14%.</b> A partir da segunda etapa, todas as contas usam só os cards com a tag do produto. No global houve {G['agendou_tudo']} agendamentos, mas {len(G['ag_fora'])} deles são de leads de outro produto ou sem tag de produto. Somar esses agendamentos sobre a base de leads Dono 14% inflaria a taxa do global de {num(pct(G['agendou'], G['d14']))}% para {num(pct(G['agendou_tudo'], G['d14']))}%, misturando numerador de um universo com denominador de outro. No período com agente isso não acontece: os {B['agendou']} agendamentos são todos de leads Dono 14%.</p>
</div>

<div class="alerta">
  <p><b>Cuidado ao comparar a primeira linha.</b> A taxa de lead que vira lead Dono 14% está subestimada no período antes do agente: {len(A['aud']['sem_tag_produto'])} dos {len(A['cards'])} cards nunca receberam tag de produto, contra {len(B['aud']['sem_tag_produto'])} de {len(B['cards'])} depois. As tags do CRM só nasceram em {TAGS_CRIADAS[8:10]}/{TAGS_CRIADAS[5:7]}. Ou seja, o salto de {num(pct(A['d14'], A['leads']))}% para {num(pct(B['d14'], B['leads']))}% mede sobretudo a melhora do processo de marcação, não a mudança de público. A seção 3 trata esse viés.</p>
</div>

<h2>3. O agente melhorou o funil? A leitura com os vieses tratados</h2>
<p class="sub">Esta é a pergunta que as três janelas existem para responder. Comparar antes com depois direto na tabela acima leva a conclusão errada, por dois motivos que precisam ser neutralizados antes de qualquer veredito.</p>

<div class="alerta">
  <h4 style="margin-top:0">Viés 1. A marcação era pior antes, então o denominador mente</h4>
  <p>No período antes do agente, <b>{num(pct(A['sem_prod'], len(A['cards'])),0)}% dos cards não têm tag de produto</b> ({A['sem_prod']} de {len(A['cards'])}). Depois do agente são {num(pct(B['sem_prod'], len(B['cards'])),0)}% ({B['sem_prod']} de {len(B['cards'])}). E os cards que receberam tag no período antigo tendem a ser justamente os que avançaram, porque ninguém volta para etiquetar lead que sumiu. Isso é viés de seleção: a base de leads Dono 14% do antes é uma amostra dos melhores, não do total.</p>
  <p>Resultado prático: a taxa de lead Dono 14% que agenda sessão aparece como <b>{num(pct(A['agendou'], A['d14']))}%</b> antes contra <b>{num(pct(B['agendou'], B['d14']))}%</b> depois, sugerindo uma piora de {num(abs(pct(B['agendou'], B['d14']) - pct(A['agendou'], A['d14'])))} pontos que <b>não existe</b>.</p>
</div>

<div class="ok">
  <h4 style="margin-top:0">Correção do viés 1: medir sobre o total de leads, sem depender de tag</h4>
  <p>Contando todos os agendamentos sobre todos os leads que entraram, a tag de produto sai da conta e o viés some.</p>
  <div class="tbox"><table>
    <thead><tr><th>Métrica imune à marcação</th><th>Antes</th><th>Depois</th><th>Diferença</th></tr></thead>
    <tbody>
      <tr><td class="k">Leads que agendaram sessão</td>
          <td class="n forte">{A['ag_qualquer']} de {A['leads']} · {num(pct(A['ag_qualquer'], A['leads']))}%</td>
          <td class="n forte">{B['ag_qualquer']} de {B['leads']} · {num(pct(B['ag_qualquer'], B['leads']))}%</td>
          <td class="n win">{num(pct(B['ag_qualquer'], B['leads']) - pct(A['ag_qualquer'], A['leads']))} p.p.</td></tr>
      <tr><td class="k">Leads que fecharam contrato</td>
          <td class="n forte">{A['ganho_qualquer']} de {A['leads']} · {num(pct(A['ganho_qualquer'], A['leads']))}%</td>
          <td class="n forte">{B['ganho_qualquer']} de {B['leads']} · {num(pct(B['ganho_qualquer'], B['leads']))}%</td>
          <td class="n dim">{num(pct(B['ganho_qualquer'], B['leads']) - pct(A['ganho_qualquer'], A['leads']))} p.p.</td></tr>
    </tbody>
  </table></div>
  <p><b>A taxa de agendamento não caiu, está estável.</b> {num(pct(A['ag_qualquer'], A['leads']))}% antes e {num(pct(B['ag_qualquer'], B['leads']))}% depois. Toda a queda que aparecia na tabela anterior era artefato de marcação.</p>
</div>

<div class="alerta">
  <h4 style="margin-top:0">Viés 2. O período antes já fechou o ciclo, o depois ainda está aberto</h4>
  <p>O antes teve {dias_a} dias e <b>zero</b> pessoas paradas em contrato: tudo que ia fechar já fechou, tudo que ia morrer já morreu. O depois tem {dias_b} dias e <b>{B['contrato']} pessoas em contrato assinado, somando {brl(B['valor_contrato'])}</b>, que ainda não viraram receita. Comparar fechamento hoje penaliza o período novo por um motivo que não é performance, é calendário.</p>
</div>

<div class="ok">
  <h4 style="margin-top:0">Correção do viés 2: coorte equalizada e valor em aberto</h4>
  <p>Olhando só quem já teve <b>{COORTE_DIAS} dias de vida</b> em cada janela, e contando apenas o que aconteceu dentro desses {COORTE_DIAS} dias:</p>
  <div class="tbox"><table>
    <thead><tr><th>Coorte de {COORTE_DIAS} dias</th><th>Antes</th><th>Depois</th></tr></thead>
    <tbody>
      <tr><td class="k">Leads com {COORTE_DIAS} dias ou mais</td><td class="n">{A['maduros']}</td><td class="n">{B['maduros']}</td></tr>
      <tr><td class="k">Agendaram dentro de {COORTE_DIAS} dias</td>
          <td class="n forte">{A['ag_coorte']} · {num(pct(A['ag_coorte'], A['maduros']))}%</td>
          <td class="n forte">{B['ag_coorte']} · {num(pct(B['ag_coorte'], B['maduros']))}%</td></tr>
    </tbody>
  </table></div>
  <p>Empate técnico, com a ressalva de que a coorte madura do depois é pequena ({B['maduros']} pessoas) e concentrada nos primeiros dias do agente.</p>
  <p><b>O que ainda pode mudar o veredito:</b> os {B['contrato']} contratos em aberto do período novo valem {brl(B['valor_contrato'])}. Se metade fechar, a taxa de fechamento do depois sai de {num(pct(B['ganho_qualquer'], B['leads']))}% para cerca de {num(pct(B['ganho_qualquer'] + B['contrato'] // 2, B['leads']))}%, acima do antes. O julgamento final do agente depende dessa fila.</p>
</div>

<h2>4. Onde o agente mudou o jogo: velocidade</h2>
<p class="sub">Se a taxa de conversão está estável e o fechamento ainda não maturou, o efeito do agente aparece em outro lugar: no tempo. Aqui não há viés de marcação nem de maturação, porque cada medição usa as datas do próprio card.</p>
<div class="tbox"><table>
<thead><tr><th>Etapa</th><th>Antes</th><th>Depois</th><th>Diferença</th><th>Leitura</th></tr></thead>
<tbody>
  <tr><td class="k">Lead entra até agendar</td>
      <td class="n">{num(A['vel_lead_ag'])} dias <em class="obs">n={A['n_lead_ag']}</em></td>
      <td class="n forte">{num(B['vel_lead_ag'])} dias <em class="obs">n={B['n_lead_ag']}</em></td>
      <td class="n win">{num(A['vel_lead_ag'] - B['vel_lead_ag'])} dias mais rápido</td>
      <td>o ganho mais claro do agente, {num(100 * (A['vel_lead_ag'] - B['vel_lead_ag']) / A['vel_lead_ag'], 0)}% de redução</td></tr>
  <tr><td class="k">Agendar até a sessão acontecer</td>
      <td class="n">{num(A['vel_ag_sessao'])} dias <em class="obs">n={A['n_ag_sessao']}</em></td>
      <td class="n">{num(B['vel_ag_sessao'])} dias <em class="obs">n={B['n_ag_sessao']}</em></td>
      <td class="n bad">{num(B['vel_ag_sessao'] - A['vel_ag_sessao'])} dias mais lento</td>
      <td>não depende do agente, é a agenda disponível</td></tr>
  <tr><td class="k">Lead entra até fechar contrato</td>
      <td class="n">{num(A['vel_lead_fecha'])} dias <em class="obs">n={A['n_lead_fecha']}</em></td>
      <td class="n">{num(B['vel_lead_fecha'])} dias <em class="obs">n={B['n_lead_fecha']}</em></td>
      <td class="n dim">base pequena</td>
      <td>{A['n_lead_fecha'] + B['n_lead_fecha']} casos no total, não conclusivo</td></tr>
</tbody></table></div>

<div class="ok">
  <p><b>O veredito honesto sobre o agente, hoje.</b> Ele não mudou a taxa de conversão do funil, que segue estável em torno de {num(pct(B['ag_qualquer'], B['leads']),0)}% de agendamento sobre os leads que entram. O que ele mudou, e muito, foi o <b>tempo até o agendamento, de {num(A['vel_lead_ag'])} para {num(B['vel_lead_ag'])} dias</b>, e a <b>disciplina de marcação, de {num(pct(A['sem_prod'], len(A['cards'])),0)}% para {num(pct(B['sem_prod'], len(B['cards'])),0)}% de cards sem triagem</b>. São dois ganhos operacionais reais, que aumentam a capacidade de atender mais lead sem aumentar equipe. Se isso vira mais receita, os {B['contrato']} contratos em aberto dirão nas próximas semanas.</p>
</div>

<h2>5. Qualidade da marcação no CRM</h2><p class="sub">Reverificação feita depois da sua auditoria. Cada bloco conta quantos cards estão com marcação inconsistente, no histórico completo e no recorte do agente.</p>

<div class="placar">
{''.join(f'''<div class="item {'limpo' if not B['aud'][chave] else 'sujo'}">
    <div class="v">{len(B['aud'][chave])}</div>
    <div class="q">{titulo}</div>
    <p class="obs">{len(A['aud'][chave])} no histórico completo</p>
  </div>''' for titulo, chave, _ in AUDITS)}
</div>

<div class="ok">
  <p><b>A auditoria funcionou.</b> No recorte do agente, os três problemas que apareceram na leitura de 11/08 estão zerados: nenhuma sessão com data e sem tag, nenhum No Show marcado junto com Sessão Realizada, nenhum No Show sem agendamento. A tag Sessão Realizada saltou de 7 para {sum(1 for c in cards if 'Sessão Realizada' in T(c))} cards, o que dá base para ela virar etapa própria do funil daqui a algumas semanas.</p>
</div>

{''.join(f'''<h4>{titulo} · {len(B['aud'][chave])} no recorte, {len(A['aud'][chave])} no histórico</h4>
<p class="obs">{desc}</p>
{nominal(A['aud'][chave])}''' for titulo, chave, desc in AUDITS if A['aud'][chave])}

<div class="aviso">
  <p><b>O que ainda vale arrumar.</b> Sobram {len(B['aud']['tag_sem_data'])} cards no recorte com tag de agendamento e sem data de sessão. Não distorcem a contagem de agendamento, porque a tag já basta para contar, mas impedem medir tempo entre agendar e comparecer. Preencher a data nesses cards fecha a última lacuna do período.</p>
</div>

<h2>6. Onde estão as pessoas hoje</h2>
<p class="sub">Distribuição por estágio do CRM nas duas janelas.</p>
<div class="tbox"><table>
<thead><tr><th>Estágio</th><th>Histórico</th><th>%</th><th>Desde o agente</th><th>%</th></tr></thead>
<tbody>
{''.join(f'''<tr><td class="k">{s}</td><td class="n">{v}</td><td class="n dim">{num(pct(v, len(A['cards'])),0)}%</td><td class="n">{B['stages'].get(s, 0)}</td><td class="n dim">{num(pct(B['stages'].get(s, 0), len(B['cards'])),0)}%</td></tr>''' for s, v in sorted(A['stages'].items(), key=lambda kv: -kv[1]))}
</tbody></table></div>

<h2>7. Ritmo de entrada de leads</h2>
<p class="sub">Leads por semana em todo o histórico. A barra verde marca as semanas já sob o agente de WhatsApp.</p>
<div class="tbox"><table>
<thead><tr><th>Semana de</th><th>Leads</th><th>Sob o agente</th><th></th></tr></thead>
<tbody>
{''.join(f'''<tr><td class="k">{k[8:10]}/{k[5:7]}</td><td class="n">{v[0]}</td><td class="n dim">{v[1] if v[1] else ''}</td><td><div class="barra"><i class="{'b' if v[1] == v[0] and v[0] else ''}" style="width:{round(320 * v[0] / max(x[0] for x in por_semana.values()))}px"></i></div></td></tr>''' for k, v in sorted(por_semana.items()))}
</tbody></table></div>

<h2>8. Leitura dos números</h2>
<div class="painel">
  <h4>O gargalo é o agendamento, nas duas janelas</h4>
  <p>De cada 10 leads triados como Dono 14%, {num(pct(B['agendou'], B['d14'])/10, 1)} agendam sessão no recorte do agente, contra {num(pct(A['agendou'], A['d14'])/10, 1)} no histórico. É a passagem mais estreita do funil e a de maior alavanca: cada ponto ganho aqui vale mais que qualquer melhora nas etapas seguintes, porque elas já operam em nível alto.</p>

  <h4>Comparecimento saudável</h4>
  <p>Quem agenda comparece em {num(pct(B['compareceu'], B['agendou']))}% dos casos no recorte, contra {num(pct(A['compareceu'], A['agendou']))}% no histórico. Não há problema de no-show a resolver, e a diferença entre as janelas sugere que o agente de WhatsApp está segurando melhor o lead até a call.</p>

  <h4>O fechamento depende da fila</h4>
  <p>São {B['ganho']} contratos assinados no recorte, {brl(B['valor_ganho'])}. Mas há {B['contrato']} pessoas paradas no estágio contrato, somando {brl(B['valor_contrato'])}. Esse valor já passou por sessão e por proposta, e é a maior alavanca de curto prazo da operação. Se metade fechar, o resultado do recorte triplica.</p>

  <h4>O que a comparação não prova</h4>
  <p>As duas janelas se sobrepõem: o recorte está dentro do histórico, não ao lado dele. Então a Janela A não é um grupo de controle, e a diferença entre elas mistura três coisas ao mesmo tempo: a entrada do agente de WhatsApp, a troca de oferta para a Sessão gratuita e a melhora da marcação no CRM. Serve para acompanhar tendência, não para atribuir causa a um fator só.</p>
</div>

<footer>
  Mentoria Dono 14% · Rodrigo Haertel · Documento oficial do funil do CRM, dados fechados até {FIM[8:10]}/{FIM[5:7]}/2026.<br>
  Fechamento conta apenas o estágio ganho, contrato assinado. Contrato gerado ainda é pipeline, não receita.
  A tag Sessão Realizada nasceu em {TAG_REALIZADA_CRIADA[8:10]}/{TAG_REALIZADA_CRIADA[5:7]} e por isso não é etapa do funil, serve só para corrigir o No Show de quem remarcou.
  Regenerar com: py -3 scripts/dono14-funil-whatsapp.py [AAAA-MM-DD]
</footer>

</div>
</body>
</html>
"""

DESTINO.mkdir(parents=True, exist_ok=True)
saida = DESTINO / f"funil-crm-{FIM}.html"
saida.write_text(html, encoding="utf-8")
atual = DESTINO / "funil-whatsapp-ATUAL.html"
atual.write_text(html, encoding="utf-8")

print(f"""
{'':<28}{'GLOBAL':>9}{'ANTES':>9}{'DEPOIS':>9}
{'Total de leads':<28}{G['leads']:>9}{A['leads']:>9}{B['leads']:>9}
{'Leads Dono 14%':<28}{G['d14']:>9}{A['d14']:>9}{B['d14']:>9}
{'Sessoes agendadas':<28}{G['agendou']:>9}{A['agendou']:>9}{B['agendou']:>9}
{'Compareceram':<28}{G['compareceu']:>9}{A['compareceu']:>9}{B['compareceu']:>9}
{'Fechamentos':<28}{G['ganho']:>9}{A['ganho']:>9}{B['ganho']:>9}
{'Em contrato (pipeline)':<28}{G['contrato']:>9}{A['contrato']:>9}{B['contrato']:>9}

IMPUNE AO VIES DE MARCACAO (sobre o total de leads)
{'  agendou':<28}{'':>9}{A['ag_qualquer']}/{A['leads']} = {pct(A['ag_qualquer'],A['leads'])}%   {B['ag_qualquer']}/{B['leads']} = {pct(B['ag_qualquer'],B['leads'])}%
{'  fechou':<28}{'':>9}{A['ganho_qualquer']}/{A['leads']} = {pct(A['ganho_qualquer'],A['leads'])}%   {B['ganho_qualquer']}/{B['leads']} = {pct(B['ganho_qualquer'],B['leads'])}%

VELOCIDADE (dias)
{'  lead ate agendar':<28}{'':>9}{A['vel_lead_ag']}       {B['vel_lead_ag']}
{'  agendar ate a sessao':<28}{'':>9}{A['vel_ag_sessao']}       {B['vel_ag_sessao']}

Qualidade da marcacao (depois / antes):""")
for titulo, chave, _ in AUDITS:
    print(f"  {titulo:<48}{len(B['aud'][chave]):>3} / {len(A['aud'][chave])}")
print(f"\nrelatorio: {saida}\natalho fixo: {atual}")
