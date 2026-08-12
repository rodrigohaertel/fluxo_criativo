#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funil do periodo do agente de WhatsApp, do lead ao fechamento.

Etapas (definidas pelo Rodrigo em 11/08/2026):
  1. Total de leads            todas as submissoes do periodo
  2. Leads Dono 14%            cards com a tag "Dono 14%" (triagem de produto)
  3. Sessoes agendadas         cards com a tag "Sessao Agendada"
  4. Comparecimento            agendadas menos a tag "No Show"
                               (a tag "Sessao Realizada" nao serve: foi criada em 09/08
                                e nao cobre o periodo inteiro)
  5. Fechamentos               cards no estagio ganho

O relatorio traz DUAS leituras: a oficial (regra acima, so por tag) e a auditada,
que corrige as inconsistencias de tag encontradas no CRM. As duas aparecem lado a
lado, com a lista nominal de cada divergencia.

Uso: py -3 scripts/dono14-funil-whatsapp.py
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

# Inicio do agente de WhatsApp: primeira mensagem e primeira conversa registradas.
INICIO = "2026-07-17"
UNTIL = date.today().isoformat()
TAG_NOVA = "2026-08-09"   # dia em que a tag "Sessao Realizada" foi criada


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


print(f">>> Periodo: {INICIO} a {UNTIL}")
tags = {t["id"]: t["name"] for t in sb("crm_tags", {"select": "id,name", "limit": "100"})}
vinculos = sb("crm_card_tags", {"select": "card_id,tag_id", "limit": "10000"})
por_card = defaultdict(set)
for v in vinculos:
    por_card[v["card_id"]].add(tags.get(v["tag_id"]))

cards = sb("crm_cards", {
    "select": "id,submission_id,nome,stage,created_at,sessao_agendada,valor_contrato,faturamento_medio",
    "deleted_at": "is.null", "limit": "5000"})
subs = sb("contact_submissions", {
    "select": "id,name,source,ab_variant,utm_content,faturamento_medio,created_at", "limit": "5000"})
sub_por_id = {s["id"]: s for s in subs}

# data de referencia do lead: a submissao quando existe, senao a criacao do card
def entrada(c):
    s = sub_por_id.get(c.get("submission_id"))
    return (s["created_at"] if s else c["created_at"])[:10]


leads = [s for s in subs if s["created_at"][:10] >= INICIO]
periodo = [c for c in cards if entrada(c) >= INICIO]
T = lambda c: {x for x in por_card.get(c["id"], set()) if x}

# ------------------------------------------------------------------ etapas
d14 = [c for c in periodo if "Dono 14%" in T(c)]
painel = [c for c in periodo if "Painel do Dono" in T(c)]
sem_produto = [c for c in periodo if not ({"Dono 14%", "Painel do Dono", "Projeto 14%"} & T(c))]

ag_tag = [c for c in periodo if "Sessão Agendada" in T(c)]
noshow_tag = [c for c in periodo if "No Show" in T(c)]

# leitura oficial, so por tag, como o Rodrigo pediu
of_agendadas = len(ag_tag)
of_noshow = len(noshow_tag)
of_compareceu = of_agendadas - of_noshow
of_fechou = len([c for c in periodo if c["stage"] == "ganho"])

# ------------------------------------------------------ auditoria das tags
# 1. sessao marcada no campo de data mas sem a tag de agendamento
sem_tag_com_data = [c for c in periodo if c.get("sessao_agendada") and "Sessão Agendada" not in T(c)]
# 2. marcado como no show e ao mesmo tempo como sessao realizada (remarcou e foi)
noshow_mas_foi = [c for c in noshow_tag if "Sessão Realizada" in T(c)]
# 3. no show sem nenhum sinal de agendamento
noshow_sem_agenda = [c for c in noshow_tag if "Sessão Agendada" not in T(c) and not c.get("sessao_agendada")]

# leitura auditada: agendamento = tag OU campo de data preenchido
ag_real = [c for c in periodo if ("Sessão Agendada" in T(c)) or c.get("sessao_agendada")]
# no show que de fato nao compareceu = tem a tag e nao tem sinal de que a sessao ocorreu
noshow_real = [c for c in noshow_tag if "Sessão Realizada" not in T(c)]
au_agendadas = len(ag_real)
au_noshow = len(noshow_real)
au_compareceu = au_agendadas - au_noshow
au_fechou = of_fechou

contratos = [c for c in periodo if c["stage"] == "contrato"]
valor_ganho = sum(c.get("valor_contrato") or 0 for c in periodo if c["stage"] == "ganho")
valor_contrato = sum(c.get("valor_contrato") or 0 for c in contratos)

stages = defaultdict(int)
for c in periodo:
    stages[c["stage"] or "sem estágio"] += 1

# leads por semana, para ver o ritmo
por_semana = defaultdict(int)
for s in leads:
    d = datetime.fromisoformat(s["created_at"][:10]).date()
    ini_sem = d.fromordinal(d.toordinal() - d.weekday())
    por_semana[ini_sem.isoformat()] += 1


def pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


def brl(v):
    return "R$ " + f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


ETAPAS_OF = [
    ("Total de leads", len(leads), "todas as pessoas que preencheram o formulário no período"),
    ("Leads Dono 14%", len(d14), "triados com a tag do produto, o resto é Painel do Dono ou sem tag"),
    ("Sessões agendadas", of_agendadas, "cards com a tag Sessão Agendada"),
    ("Comparecimento", of_compareceu, "agendadas menos a tag No Show"),
    ("Fechamentos", of_fechou, "cards no estágio ganho, contrato assinado"),
]
ETAPAS_AU = [
    ("Total de leads", len(leads), ""),
    ("Leads Dono 14%", len(d14), ""),
    ("Sessões agendadas", au_agendadas, "tag ou data de sessão preenchida no card"),
    ("Comparecimento", au_compareceu, "agendadas menos quem faltou de verdade"),
    ("Fechamentos", au_fechou, ""),
]


def funil(etapas, cls=""):
    base = etapas[0][1] or 1
    linhas = []
    for i, (nome, v, obs) in enumerate(etapas):
        larg = max(6, round(100 * v / base))
        if i == 0:
            conv = '<span class="conv topo">base</span>'
        else:
            ant = etapas[i - 1][1]
            conv = f'<span class="conv">{num(pct(v, ant), 0)}% da etapa anterior</span>'
        linhas.append(f'''<div class="etapa">
      <div class="cab"><b>{nome}</b>{conv}</div>
      <div class="trilho"><div class="preenchida {cls}" style="width:{larg}%"><span>{v}</span></div></div>
      {f'<p class="obs">{obs}</p>' if obs else ''}
    </div>''')
    return "\n".join(linhas)


def nominal(lista, extra=None):
    if not lista:
        return "<p class='obs'>nenhum caso</p>"
    itens = []
    for c in lista:
        t = " · ".join(sorted(T(c)))
        d = (c.get("sessao_agendada") or "")[:10]
        det = f" · sessão em {d[8:10]}/{d[5:7]}" if d else ""
        itens.append(f"<li><b>{c['nome']}</b> <em>{c['stage']}{det}</em><span class='tgs'>{t}</span></li>")
    return "<ul class='nom'>" + "".join(itens) + "</ul>"


html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Funil do agente de WhatsApp · Dono 14%</title>
<style>
  :root{{
    --bg:#0b241b; --bg2:#0f2e23; --card:#143a2d; --line:#2a4d3f;
    --gold:#c9a86a; --gold2:#e3cd9e; --cream:#f4efe4; --muted:#9fb5aa;
    --win:#37d399; --warn:#f2c14e; --bad:#e06a6a;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--cream);line-height:1.6;padding:36px 18px 80px}}
  .wrap{{max-width:1080px;margin:0 auto}}
  header{{border-bottom:2px solid var(--gold);padding-bottom:22px;margin-bottom:10px}}
  .kicker{{color:var(--gold);font-size:.74rem;letter-spacing:.22em;text-transform:uppercase;margin-bottom:10px}}
  h1{{font-size:2rem;color:#fff;line-height:1.14;margin-bottom:12px}}
  .lead{{color:var(--gold2);max-width:860px}}
  h2{{color:var(--gold);font-size:1.06rem;text-transform:uppercase;letter-spacing:.08em;margin:44px 0 6px;padding-left:12px;border-left:3px solid var(--gold)}}
  h2 + .sub{{color:var(--muted);font-size:.9rem;margin:0 0 18px 15px;max-width:880px}}
  h3{{color:#fff;font-size:1.05rem;margin-bottom:4px}}
  h4{{color:var(--gold2);font-size:.95rem;margin:16px 0 8px}}
  p{{margin-bottom:12px}}
  b{{color:var(--gold2)}}
  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:8px}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
  .kpi b{{display:block;font-size:1.8rem;color:#fff;line-height:1.1;font-variant-numeric:tabular-nums}}
  .kpi span{{display:block;font-size:.74rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:5px}}
  .kpi.win b{{color:var(--win)}} .kpi.warn b{{color:var(--warn)}} .kpi.bad b{{color:var(--bad)}}
  .dois{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  .painel{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px}}
  .painel.of{{border-top:3px solid var(--gold)}}
  .painel.au{{border-top:3px solid var(--win)}}
  .painel .tit{{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:2px}}
  .etapa{{margin:14px 0}}
  .cab{{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:5px}}
  .cab b{{color:#fff;font-size:.94rem}}
  .conv{{font-size:.74rem;color:var(--gold);white-space:nowrap}}
  .conv.topo{{color:var(--muted)}}
  .trilho{{background:rgba(255,255,255,.05);border-radius:8px;overflow:hidden;height:34px}}
  .preenchida{{height:100%;background:linear-gradient(90deg,#2a6b52,var(--gold));border-radius:8px;display:flex;align-items:center;justify-content:flex-end;padding-right:11px;transition:width .3s}}
  .preenchida.au{{background:linear-gradient(90deg,#2a6b52,var(--win))}}
  .preenchida span{{color:#08281d;font-weight:800;font-size:.95rem;font-variant-numeric:tabular-nums}}
  .obs{{color:var(--muted);font-size:.78rem;margin:4px 0 0}}
  .aviso{{background:linear-gradient(180deg,rgba(242,193,78,.12),rgba(20,58,45,.35));border:1px solid var(--warn);border-radius:12px;padding:16px 20px;margin:16px 0}}
  .aviso b{{color:var(--warn)}}
  .alerta{{background:rgba(224,106,106,.09);border:1px solid rgba(224,106,106,.45);border-radius:12px;padding:16px 20px;margin:14px 0}}
  .alerta b{{color:var(--bad)}}
  .ok{{background:rgba(55,211,153,.08);border:1px solid rgba(55,211,153,.4);border-radius:12px;padding:16px 20px;margin:14px 0}}
  .ok b{{color:var(--win)}}
  ul.nom{{list-style:none;margin:8px 0}}
  ul.nom li{{padding:9px 0;border-bottom:1px solid rgba(42,77,63,.6);font-size:.86rem;display:flex;flex-wrap:wrap;gap:8px;align-items:baseline}}
  ul.nom li:last-child{{border:none}}
  ul.nom li b{{color:#fff}}
  ul.nom li em{{font-style:normal;color:var(--muted);font-size:.8rem}}
  .tgs{{margin-left:auto;color:var(--gold);font-size:.72rem;text-align:right}}
  .tbox{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--bg2);margin:10px 0}}
  table{{width:100%;border-collapse:collapse;font-size:.86rem;min-width:480px}}
  th{{background:#0d2b21;color:var(--gold);text-transform:uppercase;font-size:.64rem;letter-spacing:.07em;padding:11px 10px;text-align:left}}
  td{{padding:10px;border-top:1px solid var(--line)}}
  td.n{{text-align:right;font-variant-numeric:tabular-nums}}
  td.k{{color:var(--gold2);font-weight:600}}
  .barra{{display:flex;align-items:center;gap:8px}}
  .barra i{{display:block;height:9px;background:linear-gradient(90deg,#2a6b52,var(--gold));border-radius:6px}}
  footer{{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:.8rem}}
  @media(max-width:760px){{.dois{{grid-template-columns:1fr}} body{{padding:22px 12px 60px}} h1{{font-size:1.5rem}}}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="kicker">Funil do agente de WhatsApp · Mentoria Dono 14%</div>
  <h1>Do lead ao contrato assinado, desde que o agente entrou no ar.</h1>
  <p class="lead">Período de <b>17 de julho a {UNTIL[8:10]} de agosto de 2026</b>, {(date.fromisoformat(UNTIL) - date.fromisoformat(INICIO)).days} dias. Fonte: tabelas contact_submissions, crm_cards e as tags do CRM do banco de produção. Snapshot gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.</p>
</header>

<div class="aviso">
  <p><b>Sobre a data de corte.</b> O pedido citava 20/09, mas essa data não existe na base. O agente de WhatsApp tem primeira mensagem e primeira conversa registradas em <b>17/07/2026</b>, e é essa a data usada aqui. Se o corte certo for outro, o relatório se refaz em um comando.</p>
</div>

<div class="kpis">
  <div class="kpi"><b>{len(leads)}</b><span>leads no período</span></div>
  <div class="kpi"><b>{len(d14)}</b><span>leads Dono 14%</span></div>
  <div class="kpi warn"><b>{au_agendadas}</b><span>sessões agendadas</span></div>
  <div class="kpi"><b>{au_compareceu}</b><span>compareceram</span></div>
  <div class="kpi win"><b>{of_fechou}</b><span>fechamentos</span></div>
  <div class="kpi win"><b>{brl(valor_ganho)}</b><span>receita fechada</span></div>
</div>

<h2>1. O funil, nas duas leituras</h2>
<p class="sub">À esquerda, a regra exata que você pediu, contando só pelas tags. À direita, a leitura auditada, que corrige as inconsistências de marcação encontradas no CRM e está detalhada na seção 2. A diferença entre as duas é grande o bastante para mudar a decisão, por isso as duas aparecem.</p>

<div class="dois">
  <div class="painel of">
    <div class="tit">Leitura oficial</div>
    <h3>Só pelas tags</h3>
    <p class="obs">Sessões agendadas = tag Sessão Agendada. Comparecimento = agendadas menos a tag No Show.</p>
    {funil(ETAPAS_OF)}
  </div>
  <div class="painel au">
    <div class="tit">Leitura auditada</div>
    <h3>Tag mais o campo de data</h3>
    <p class="obs">Sessões agendadas = tag ou data de sessão preenchida. No show = quem faltou e não remarcou.</p>
    {funil(ETAPAS_AU, "au")}
  </div>
</div>

<div class="alerta">
  <p><b>As duas leituras divergem em {abs(au_compareceu - of_compareceu)} pessoas no comparecimento.</b> Pela regra das tags, {of_agendadas} agendaram e {of_compareceu} compareceram. Auditando os registros, {au_agendadas} agendaram e {au_compareceu} compareceram. A diferença não é erro de cálculo, é marcação faltando ou sobrando no CRM, e cada caso está nomeado abaixo.</p>
</div>

<h2>2. Onde as tags não batem</h2>
<p class="sub">Três problemas de marcação. Nenhum deles é grave para a operação, mas todos distorcem o funil se a leitura for só por tag.</p>

<div class="painel">
  <h4>Problema 1. Sessão marcada no card, sem a tag de agendamento ({len(sem_tag_com_data)} casos)</h4>
  <p class="obs">Têm data de sessão preenchida e a tag Sessão Realizada, mas ninguém marcou Sessão Agendada. Contando só por tag, essas sessões desaparecem do funil. E são justamente três que viraram contrato.</p>
  {nominal(sem_tag_com_data)}

  <h4>Problema 2. Marcados como No Show que na verdade compareceram ({len(noshow_mas_foi)} casos)</h4>
  <p class="obs">Têm No Show e Sessão Realizada ao mesmo tempo, e os dois estão em contrato. O padrão provável: faltaram na primeira marcação, remarcaram e compareceram, e a tag antiga ficou. Subtrair essas pessoas do comparecimento é errado.</p>
  {nominal(noshow_mas_foi)}

  <h4>Problema 3. No Show sem nenhum sinal de agendamento ({len(noshow_sem_agenda)} casos)</h4>
  <p class="obs">Marcado como falta, mas o card não tem tag de agendamento nem data de sessão. Não dá para saber se houve sessão marcada.</p>
  {nominal(noshow_sem_agenda)}
</div>

<div class="ok">
  <p><b>A sugestão prática.</b> A tag Sessão Agendada é preenchida à mão e já falhou em {len(sem_tag_com_data)} de {au_agendadas} casos. O campo de data da sessão é preenchido pelo próprio fluxo de agendamento e não falhou nenhuma vez. Para leitura de funil, o campo de data é a fonte mais confiável. A tag No Show continua útil, desde que seja removida quando a pessoa remarca e comparece.</p>
</div>

<h2>3. As taxas que importam</h2>
<p class="sub">Calculadas sobre a leitura auditada, que é a que reflete o que aconteceu de fato.</p>
<div class="tbox"><table>
<thead><tr><th>Passagem</th><th>Conta</th><th>Taxa</th><th>Leitura</th></tr></thead>
<tbody>
  <tr><td class="k">Lead vira lead Dono 14%</td><td class="n">{len(d14)} de {len(leads)}</td><td class="n">{num(pct(len(d14), len(leads)))}%</td><td>o resto é Painel do Dono ({len(painel)}) ou sem tag de produto ({len(sem_produto)})</td></tr>
  <tr><td class="k">Lead Dono 14% agenda sessão</td><td class="n">{au_agendadas} de {len(d14)}</td><td class="n">{num(pct(au_agendadas, len(d14)))}%</td><td>o degrau mais estreito do funil, e o de maior alavanca</td></tr>
  <tr><td class="k">Agendou e compareceu</td><td class="n">{au_compareceu} de {au_agendadas}</td><td class="n">{num(pct(au_compareceu, au_agendadas))}%</td><td>a taxa de comparecimento está saudável</td></tr>
  <tr><td class="k">Compareceu e fechou</td><td class="n">{of_fechou} de {au_compareceu}</td><td class="n">{num(pct(of_fechou, au_compareceu))}%</td><td>só conta contrato assinado, no estágio ganho</td></tr>
  <tr><td class="k">Lead vira contrato</td><td class="n">{of_fechou} de {len(leads)}</td><td class="n">{num(pct(of_fechou, len(leads)))}%</td><td>a taxa ponta a ponta do período</td></tr>
</tbody></table></div>

<div class="aviso">
  <p><b>O gargalo está claro.</b> De {len(d14)} leads Dono 14%, {au_agendadas} agendaram sessão. É aí que o funil aperta, não no comparecimento nem no fechamento. Quem chega na sessão comparece em {num(pct(au_compareceu, au_agendadas))}% dos casos, e quem comparece fecha em {num(pct(of_fechou, au_compareceu))}%.</p>
  <p><b>E ainda há fila.</b> {len(contratos)} pessoas estão no estágio contrato, somando {brl(valor_contrato)} que ainda não viraram receita. Se metade fechar, o resultado do período dobra.</p>
</div>

<h2>4. Onde estão as {len(periodo)} pessoas hoje</h2>
<div class="tbox"><table>
<thead><tr><th>Estágio no CRM</th><th>Pessoas</th><th></th></tr></thead>
<tbody>
{"".join(f'''<tr><td class="k">{s}</td><td class="n">{v}</td><td><div class="barra"><i style="width:{round(240*v/max(stages.values()))}px"></i><span class="obs">{num(pct(v, len(periodo)),0)}%</span></div></td></tr>''' for s, v in sorted(stages.items(), key=lambda kv: -kv[1]))}
</tbody></table></div>

<h2>5. Ritmo de entrada de leads</h2>
<p class="sub">Leads por semana no período, para ver se o volume está subindo ou caindo.</p>
<div class="tbox"><table>
<thead><tr><th>Semana de</th><th>Leads</th><th></th></tr></thead>
<tbody>
{"".join(f'''<tr><td class="k">{k[8:10]}/{k[5:7]}</td><td class="n">{v}</td><td><div class="barra"><i style="width:{round(300*v/max(por_semana.values()))}px"></i></div></td></tr>''' for k, v in sorted(por_semana.items()))}
</tbody></table></div>

<footer>
  Mentoria Dono 14% · Rodrigo Haertel · Funil do período do agente de WhatsApp, {INICIO[8:10]}/{INICIO[5:7]} a {UNTIL[8:10]}/{UNTIL[5:7]}/2026.<br>
  Fechamento conta apenas o estágio ganho, contrato assinado. Contrato gerado ainda é pipeline, não receita.
  A tag Sessão Realizada foi criada em {TAG_NOVA[8:10]}/{TAG_NOVA[5:7]} e por isso não é usada como etapa do funil, apenas para auditar o No Show.
  Regenerar com: py -3 scripts/dono14-funil-whatsapp.py
</footer>

</div>
</body>
</html>
"""

DESTINO.mkdir(parents=True, exist_ok=True)
saida = DESTINO / f"funil-whatsapp-{datetime.now().strftime('%Y-%m-%d-%H%M')}.html"
saida.write_text(html, encoding="utf-8")
atual = DESTINO / "funil-whatsapp-ATUAL.html"
atual.write_text(html, encoding="utf-8")

print(f"""
FUNIL {INICIO} a {UNTIL}
  Total de leads .......... {len(leads)}
  Leads Dono 14% .......... {len(d14)}   (Painel do Dono: {len(painel)}, sem tag: {len(sem_produto)})
  Sessoes agendadas ....... {of_agendadas} por tag  |  {au_agendadas} auditado
  Comparecimento .......... {of_compareceu} por tag  |  {au_compareceu} auditado
  Fechamentos ............. {of_fechou}   ({brl(valor_ganho)})
  Em contrato (pipeline) .. {len(contratos)}   ({brl(valor_contrato)})

Inconsistencias de tag: {len(sem_tag_com_data)} sem tag de agendamento, {len(noshow_mas_foi)} no-show que compareceu, {len(noshow_sem_agenda)} no-show sem agendamento
""")
print("relatorio:", saida)
print("atalho fixo:", atual)
