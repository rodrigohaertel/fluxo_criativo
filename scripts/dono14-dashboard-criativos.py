#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera o dashboard HTML de analise por criativo (A30 em diante) do Dono 14%.

Le o dataset consolidado (Meta nivel anuncio + banco Supabase + CRM) e monta
um HTML standalone, sem dependencia externa, no padrao visual do produto.

Uso: py -3 scripts/dono14-dashboard-criativos.py
Fonte: meus-produtos/dono-14/trafego/analise/dataset-criativos-a30-a41.json
Saida: meus-produtos/dono-14/trafego/analise/criativos-a30-a41-{data}.html
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parent.parent
BASE = RAIZ / "meus-produtos" / "dono-14" / "trafego" / "analise"
D = json.loads((BASE / "dataset-criativos-a30-a41.json").read_text(encoding="utf-8"))
C = D["criativos"]
por = {l["criativo"]: l for l in C}
LEITURA_NARRATIVA = "2026-08-29"   # data em que os vereditos em texto foram escritos
DEFASADO = D.get("gerado_em", LEITURA_NARRATIVA) > LEITURA_NARRATIVA
AVISO_DEFASAGEM = ("""<div class="fix"><p><b>Números novos, leitura antiga.</b> Os dados desta página foram coletados em """
    + D.get("gerado_em", "") + """ e estão atualizados. Já os vereditos em texto (as conclusões das seções 5 a 9) foram escritos na leitura de """
    + LEITURA_NARRATIVA + """ e não foram revisados contra estes números. Trate os textos como hipótese a confirmar, não como conclusão vigente.</p></div>""") if DEFASADO else ""


def brl(v, dec=0):
    if v is None:
        return "sem dado"
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s


def num(v, dec=1):
    if v is None:
        return "sem dado"
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calor(valor, vals, inverso=False):
    """Devolve uma classe de calor pela posicao do valor no conjunto."""
    vs = [v for v in vals if v is not None]
    if valor is None or not vs:
        return "z0"
    lo, hi = min(vs), max(vs)
    if hi == lo:
        return "z3"
    p = (valor - lo) / (hi - lo)
    if inverso:
        p = 1 - p
    return "z" + str(min(5, int(p * 5) + 1))


def barra(valor, maximo, cls=""):
    largura = 0 if not maximo else max(2, round(100 * valor / maximo))
    return f'<span class="bar {cls}"><i style="width:{largura}%"></i></span>'


# ---------------------------------------------------------------- agregados
GASTO = D["totais"]["gasto"]
RAST = [l for l in C if l["rastreado"]]
NAO_RAST = [l for l in C if not l["rastreado"]]
gasto_rast = sum(l["gasto"] for l in RAST)
leads_banco = sum(l["leads_banco"] for l in RAST)
q100 = sum(l["q100"] for l in RAST)
leads_meta_janela = sum(l["leads_meta_rast"] for l in C)

familias = {}
for l in C:
    f = familias.setdefault(l["familia"], dict(gasto=0.0, imp=0, lc=0, lpv=0, leads_meta=0, leads_banco=0,
                                               q100=0, pecas=[], hook=[], p50=[], ctr=[], conv=[]))
    f["gasto"] += l["gasto"]; f["imp"] += l["impressoes"]; f["lc"] += l["cliques_link"]; f["lpv"] += l["lpv"]
    f["leads_meta"] += l["leads_meta"]; f["leads_banco"] += l["leads_banco"]; f["q100"] += l["q100"]
    f["pecas"].append(l["criativo"]); f["hook"].append(l["hook"]); f["p50"].append(l["p50"])
    f["ctr"].append(l["ctr_link"]); f["conv"].append(l["lpv_lead_meta"])

for f in familias.values():
    f["hook_m"] = round(sum(f["hook"]) / len(f["hook"]), 1)
    f["p50_m"] = round(sum(f["p50"]) / len(f["p50"]), 1)
    f["ctr_m"] = round(100 * f["lc"] / f["imp"], 2) if f["imp"] else 0
    f["conv_m"] = round(100 * f["leads_meta"] / f["lpv"], 1) if f["lpv"] else 0
    f["cpl_m"] = round(f["gasto"] / f["leads_meta"], 2) if f["leads_meta"] else None

ORDEM_FAM = ["Prova de mercado", "Demonstração (Painel)", "Paradoxo puro", "Paradoxo numérico",
             "Inimigo comum", "Filtro / convocação", "História de origem"]
fam_ord = [f for f in ORDEM_FAM if f in familias] + [f for f in familias if f not in ORDEM_FAM]

# ---------------------------------------------------------------- financeiro
FIN = D["financeiro"]
CONTA = D["conta"]
RECEITA = FIN["receita_total"]
GASTO_CONTA = CONTA["gasto_total"]
GASTO_FUNIL = CONTA["gasto_funil_mentoria"]          # só os criativos A30 a A41
GASTO_FUNIL_TOPO = GASTO_FUNIL + CONTA["gasto_topo_funil"]  # com posts e carrosséis de topo
ROAS_FUNIL = round(RECEITA / GASTO_FUNIL, 2)
ROAS_FUNIL_TOPO = round(RECEITA / GASTO_FUNIL_TOPO, 2)
ROAS_CONTA = round(RECEITA / GASTO_CONTA, 2)
CAC_FUNIL = round(GASTO_FUNIL / FIN["vendas_total"], 2)
CAC_CONTA = round(GASTO_CONTA / FIN["vendas_total"], 2)
LEADS_PERIODO = D["totais"]["leads_banco_total_periodo"]
TX_VENDA = round(100 * FIN["vendas_total"] / LEADS_PERIODO, 1)
RECEITA_POR_LEAD = round(RECEITA / LEADS_PERIODO, 2)
CAIXA_IMEDIATO = FIN["entrada_por_venda"] * FIN["vendas_total"]
TETOS = [(1, RECEITA_POR_LEAD), (3, RECEITA_POR_LEAD / 3), (5, RECEITA_POR_LEAD / 5), (10, RECEITA_POR_LEAD / 10)]


def linha_roas(l):
    if not l["rastreado"]:
        return ""
    if l["receita"]:
        rec = f'<b class="win">{brl(l["receita"])}</b>'
        roas = f'<b class="win">{num(l["roas"],2)}x</b>'
        cac = brl(l["cac"])
    elif l["leads_banco"]:
        rec = '<em>ainda não</em>'
        roas = '<em>sem venda</em>'
        cac = '<em>sem venda</em>'
    else:
        rec = roas = cac = '<em>sem lead</em>'
    pipe = brl(l["pipeline_valor"]) if l["pipeline_valor"] else "<em>zero</em>"
    roasp = f'{num(l["roas_pipeline"],2)}x' if l["roas_pipeline"] else "<em>sem base</em>"
    return f"""<tr>
  <td class="k"><b>{l['criativo']}</b><em>{l['titulo']}</em></td>
  <td class="n">{brl(l['gasto_rast'])}</td>
  <td class="n">{l['leads_banco']}</td>
  <td class="n">{rec}</td>
  <td class="n">{roas}</td>
  <td class="n">{cac}</td>
  <td class="n dim">{pipe}</td>
  <td class="n dim">{roasp}</td>
</tr>"""


def teto_cpl():
    piores = max(t[1] for t in TETOS)
    linhas = ""
    for mult, teto in TETOS:
        rot = "empata" if mult == 1 else f"{mult}x"
        linhas += (f'<div class="lin"><span class="cd">{rot}</span>{barra(teto, piores)}'
                   f'<span class="vl">{brl(teto)}</span></div>')
    return linhas


def resumo_regua():
    """Conta como os criativos com CPL medido se distribuem contra o teto."""
    vals = [(x["criativo"], x["cpl_banco"] or x["cpl_meta"]) for x in C if (x["cpl_banco"] or x["cpl_meta"])]
    a5 = [c for c, v in vals if v <= RECEITA_POR_LEAD / 5]
    a3 = [c for c, v in vals if RECEITA_POR_LEAD / 5 < v <= RECEITA_POR_LEAD / 3]
    a1 = [c for c, v in vals if RECEITA_POR_LEAD / 3 < v <= RECEITA_POR_LEAD]
    fora = [c for c, v in vals if v > RECEITA_POR_LEAD]
    sem = [x["criativo"] for x in C if not (x["cpl_banco"] or x["cpl_meta"])]
    return vals, a5, a3, a1, fora, sem


REGUA, ACIMA5, ENTRE35, ENTRE13, FORA, SEM_CPL = resumo_regua()


def conc(cs, sing, plur):
    """Concordancia simples pelo tamanho da lista."""
    return sing if len(cs) == 1 else plur


def lista(cs):
    if not cs:
        return "nenhum"
    if len(cs) == 1:
        return cs[0]
    return ", ".join(cs[:-1]) + " e " + cs[-1]


def cpl_vs_teto():
    alvo3 = RECEITA_POR_LEAD / 3
    alvo5 = RECEITA_POR_LEAD / 5
    linhas = ""
    elegiveis = [(x, x["cpl_banco"] or x["cpl_meta"]) for x in C if (x["cpl_banco"] or x["cpl_meta"])]
    for l, cpl in sorted(elegiveis, key=lambda t: t[1]):
        fonte = "banco" if l["cpl_banco"] else "Meta"
        if cpl <= alvo5:
            cls, sel = "vencedor", "acima de 5x"
        elif cpl <= alvo3:
            cls, sel = "", "entre 3x e 5x"
        elif cpl <= RECEITA_POR_LEAD:
            cls, sel = "", "entre 1x e 3x"
        else:
            cls, sel = "vazio", "abaixo do empate"
        linhas += (f'<div class="lin {cls}"><span class="cd">{l["criativo"]}</span>{barra(cpl, RECEITA_POR_LEAD)}'
                   f'<span class="vl">{brl(cpl)}</span><span class="sel">{sel} · {fonte}</span></div>')
    return linhas


# ---------------------------------------------------------------- colunas de calor
col = lambda k: [l[k] for l in C]

# ---------------------------------------------------------------- HTML
def linha_mestre(l):
    cls = "novo" if l["rastreado"] else ""
    if l.get("correcao"):
        cls += " corrigido"
        leads = '<span class="tag art">artefato</span>'
        cpl = '<em>não gerou</em>'
        marca = '<em class="art">zerado, ver correção acima</em>'
    else:
        leads = str(l["leads_meta"])
        cpl = brl(l["cpl_meta"])
        marca = ""
    return f"""<tr class="{cls}">
  <td class="k"><b>{l['criativo']}</b><em>{l['titulo']}</em>{marca}</td>
  <td class="{calor(l['gasto'], col('gasto'))} n">{brl(l['gasto'])}</td>
  <td class="n">{num(l['freq'],2)}</td>
  <td class="{calor(l['ctr'], col('ctr'))} n">{num(l['ctr'],2)}%</td>
  <td class="{calor(l['cpc'], col('cpc'), True)} n">{brl(l['cpc'],2)}</td>
  <td class="{calor(l['cpm'], col('cpm'), True)} n">{brl(l['cpm'],2)}</td>
  <td class="{calor(l['hook'], col('hook'))} n">{num(l['hook'])}%</td>
  <td class="{calor(l['p25'], col('p25'))} n">{num(l['p25'])}%</td>
  <td class="{calor(l['p50'], col('p50'))} n">{num(l['p50'])}%</td>
  <td class="{calor(l['p75'], col('p75'))} n">{num(l['p75'])}%</td>
  <td class="{calor(l['p95'], col('p95'))} n">{num(l['p95'])}%</td>
  <td class="{calor(l['connect'], col('connect'))} n">{num(l['connect'])}%</td>
  <td class="n">{leads}</td>
  <td class="n">{cpl}</td>
</tr>"""


def linha_banco(l):
    if l["rastreado"]:
        selo = '<span class="tag ok">rastreado</span>'
        gasto = brl(l["gasto_rast"])
        lmeta = str(l["leads_meta_rast"])
        lb = str(l["leads_banco"])
        cpl = brl(l["cpl_banco"]) if l["leads_banco"] else "<em>não gerou</em>"
        qq = f"{l['q100']} <em>({num(l['taxa_q'],0)}%)</em>" if l["leads_banco"] else "<em>zero</em>"
        cplq = brl(l["cpl_q"]) if l["q100"] else "<em>não gerou</em>"
        funil = (f"<span class='pill g'>{l['ganhos']} ganho</span>" if l["ganhos"] else "") + \
                (f"<span class='pill c'>{l['contratos']} contrato</span>" if l["contratos"] else "") + \
                (f"<span class='pill s'>{l['sessoes']} sessão</span>" if l["sessoes"] else "") + \
                (f"<span class='pill v'>{l['pipeline']} em aberto</span>" if l["pipeline"] else "") + \
                (f"<span class='pill p'>{l['perdidos']} perdido</span>" if l["perdidos"] else "") or "<em>sem lead</em>"
        custo = brl(l["custo_avanco"]) if l["avancos"] else "<em>sem avanço</em>"
    else:
        selo = '<span class="tag off">sem rastreio</span>'
        gasto = brl(l["gasto"])
        lmeta = str(l["leads_meta"])
        lb = cpl = qq = cplq = custo = "<em>não medível</em>"
        funil = "<em>lead sem origem no banco</em>"
    obs = f'<div class="obs">{l["correcao"]}</div>' if l.get("correcao") else ""
    return f"""<tr class="{'novo' if l['rastreado'] else 'apagado'}">
  <td class="k"><b>{l['criativo']}</b><em>{l['titulo']}</em>{obs}</td>
  <td class="n">{selo}</td>
  <td class="n">{gasto}</td>
  <td class="n dim">{lmeta}</td>
  <td class="n forte">{lb}</td>
  <td class="n forte">{cpl}</td>
  <td class="n">{qq}</td>
  <td class="n forte">{cplq}</td>
  <td class="fun">{funil}</td>
  <td class="n">{custo}</td>
</tr>"""


# escada de metricas: barras comparativas
def escada(titulo, chave, sufixo="%", inverso=False, nota=""):
    vals = [(l["criativo"], l[chave]) for l in C]
    validos = [(c, v) for c, v in vals if v]
    mx = max(v for _, v in validos) or 1
    top = sorted(validos, key=lambda x: x[1], reverse=not inverso)[0][0]
    linhas = ""
    for c, v in vals:
        d = "vencedor" if c == top else ""
        if not v:
            linhas += (f'<div class="lin vazio"><span class="cd">{c}</span>'
                       f'{barra(0, mx)}<span class="vl">sem lead</span></div>')
            continue
        rot = brl(v) if chave.startswith("cpl") else f"{num(v)}{sufixo}"
        linhas += (f'<div class="lin {d}"><span class="cd">{c}</span>'
                   f'{barra(v, mx)}<span class="vl">{rot}</span></div>')
    return f'<div class="degrau"><h4>{titulo}</h4><p class="hint">{nota}</p>{linhas}</div>'


# scatter gancho x fecho
def scatter():
    pts = [l for l in C if l["lpv"] > 0]
    xs = [l["ctr_link"] for l in pts]; ys = [l["lpv_lead_meta"] for l in pts]
    xmin, xmax = 0.8, max(xs) * 1.1
    ymin, ymax = 0, max(ys) * 1.15
    W, H, P = 760, 420, 52
    def px(x): return P + (x - xmin) / (xmax - xmin) * (W - P - 24)
    def py(y): return H - P - (y - ymin) / (ymax - ymin) * (H - P - 28)
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    s = [f'<svg viewBox="0 0 {W} {H}" class="scatter" role="img" aria-label="Matriz de clique contra conversão">']
    s.append(f'<rect x="{px(mx):.0f}" y="{py(ymax):.0f}" width="{W-24-px(mx):.0f}" height="{py(my)-py(ymax):.0f}" class="quad-bom"/>')
    s.append(f'<line x1="{px(mx):.0f}" y1="{py(ymax):.0f}" x2="{px(mx):.0f}" y2="{H-P:.0f}" class="eixo-med"/>')
    s.append(f'<line x1="{P}" y1="{py(my):.0f}" x2="{W-24}" y2="{py(my):.0f}" class="eixo-med"/>')
    s.append(f'<line x1="{P}" y1="{H-P}" x2="{W-24}" y2="{H-P}" class="eixo"/>')
    s.append(f'<line x1="{P}" y1="{P-28}" x2="{P}" y2="{H-P}" class="eixo"/>')
    s.append(f'<text x="{W-24}" y="{H-P+30}" class="lbl fim">CTR de link (parou e clicou)</text>')
    s.append(f'<text x="{P-8}" y="{P-34}" class="lbl">visita para lead (%)</text>')
    s.append(f'<text x="{px(mx)+8:.0f}" y="{py(ymax)+16:.0f}" class="lbl bom">zona alvo: clica e cadastra</text>')
    gmax = max(l["gasto"] for l in pts)
    for l in pts:
        r = 7 + 15 * (l["gasto"] / gmax) ** 0.6
        cls = "pt novo" if l["rastreado"] else "pt"
        s.append(f'<circle cx="{px(l["ctr_link"]):.1f}" cy="{py(l["lpv_lead_meta"]):.1f}" r="{r:.1f}" class="{cls}"/>')
        s.append(f'<text x="{px(l["ctr_link"]):.1f}" y="{py(l["lpv_lead_meta"])+4:.1f}" class="pl">{l["criativo"]}</text>')
    for v in [1.0, 1.2, 1.4, 1.6, 1.8]:
        if xmin < v < xmax:
            s.append(f'<text x="{px(v):.0f}" y="{H-P+18}" class="tick">{num(v,1)}%</text>')
    for v in [4, 8, 12, 16]:
        if v < ymax:
            s.append(f'<text x="{P-10}" y="{py(v)+4:.0f}" class="tick fim">{v}%</text>')
    s.append("</svg>")
    return "".join(s)


def card_familia(nome):
    f = familias[nome]
    veredito, texto = VEREDITOS.get(nome, ("meio", ""))
    pecas = " ".join(f'<span class="chip">{p}</span>' for p in f["pecas"])
    return f"""<div class="fam">
  <h4>{nome}</h4>
  <div class="chips">{pecas}</div>
  <div class="fgrid">
    <div><b>{brl(f['gasto'])}</b><span>investido</span></div>
    <div><b>{num(f['hook_m'])}%</b><span>hook médio</span></div>
    <div><b>{num(f['p50_m'])}%</b><span>P50 médio</span></div>
    <div><b>{num(f['ctr_m'],2)}%</b><span>CTR de link</span></div>
    <div><b>{num(f['conv_m'])}%</b><span>visita para lead</span></div>
    <div><b>{brl(f['cpl_m']) if f['cpl_m'] else 'sem lead'}</b><span>CPL agregado</span></div>
  </div>
  <div class="ver {veredito}">{texto}</div>
</div>"""


VEREDITOS = {
 "Prova de mercado": ("bom", "A família que sustenta CPL em escala e a única que já virou venda. Autoridade externa faz o que o rosto sozinho não faz."),
 "Demonstração (Painel)": ("bom", "A família que qualifica. Traz o dono grande e faz quem chega preencher. Ponto fraco: gera pouco clique."),
 "Paradoxo puro": ("meio", "Melhor gancho e melhor clique da conta. Fecho fraco: em escala o CPL saltou de R$ 45 para R$ 244."),
 "Paradoxo numérico": ("meio", "Didático e correto, mas longo demais. Retenção paga o preço da segunda metade."),
 "Inimigo comum": ("ruim", "Prende como nenhuma outra e não converte. A38 tem a melhor retenção e o pior CPL da conta."),
 "Filtro / convocação": ("ruim", "Pior família das sete. O A41 não trouxe nenhum lead dentro do filtro, apesar do filtro mais explícito de todos."),
 "História de origem": ("ruim", "R$ 275, zero lead, a pior retenção da série. 94 segundos de rosto puro."),
}

alvo = por["A40"]
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cockpit de Criativos · A30 a A41 · Dono 14%</title>
<style>
  :root{{
    --bg:#0b241b; --bg2:#0f2e23; --card:#143a2d; --line:#2a4d3f;
    --gold:#c9a86a; --gold2:#e3cd9e; --cream:#f4efe4; --muted:#9fb5aa;
    --win:#37d399; --warn:#f2c14e; --bad:#e06a6a;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--cream);line-height:1.55;padding:32px 18px 80px}}
  .wrap{{max-width:1240px;margin:0 auto}}
  header{{border-bottom:2px solid var(--gold);padding-bottom:22px;margin-bottom:26px}}
  .kicker{{color:var(--gold);font-size:.72rem;letter-spacing:.24em;text-transform:uppercase;margin-bottom:10px}}
  h1{{font-size:2rem;color:#fff;line-height:1.12;margin-bottom:10px}}
  .lead{{color:var(--gold2);max-width:900px}}
  h2{{color:var(--gold);font-size:1.05rem;text-transform:uppercase;letter-spacing:.09em;margin:44px 0 6px;padding-left:12px;border-left:3px solid var(--gold)}}
  h2 + .sub{{color:var(--muted);font-size:.9rem;margin:0 0 16px 15px;max-width:920px}}
  h4{{color:var(--gold2);font-size:.95rem;margin-bottom:8px}}

  .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:12px;margin-bottom:8px}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
  .kpi b{{display:block;font-size:1.8rem;color:#fff;line-height:1.1;font-variant-numeric:tabular-nums}}
  .kpi span{{display:block;font-size:.76rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:5px}}
  .kpi.win b{{color:var(--win)}} .kpi.bad b{{color:var(--bad)}} .kpi.warn b{{color:var(--warn)}}

  .aviso{{background:linear-gradient(180deg,rgba(242,193,78,.12),rgba(20,58,45,.35));border:1px solid var(--warn);border-radius:12px;padding:16px 20px;margin:18px 0}}
  .aviso b{{color:var(--warn)}}
  .fix{{background:rgba(224,106,106,.1);border:1px solid rgba(224,106,106,.45);border-radius:12px;padding:14px 18px;margin:12px 0;font-size:.92rem}}
  .fix b{{color:var(--bad)}}

  .tbox{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--bg2)}}
  table{{width:100%;border-collapse:collapse;font-size:.84rem;min-width:940px}}
  th{{background:#0d2b21;color:var(--gold);text-transform:uppercase;font-size:.63rem;letter-spacing:.07em;padding:11px 8px;text-align:right;position:sticky;top:0;white-space:nowrap}}
  th:first-child{{text-align:left}}
  td{{padding:10px 8px;border-top:1px solid var(--line);vertical-align:middle}}
  td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
  td.k{{min-width:210px}}
  td.k b{{color:var(--gold2);font-size:.95rem}}
  td.k em{{display:block;font-style:normal;color:var(--muted);font-size:.78rem;line-height:1.3}}
  tr.novo td.k b{{color:#fff}}
  tr.novo{{background:rgba(55,211,153,.05)}}
  tr.apagado td{{opacity:.62}}
  td.dim{{color:var(--muted)}}
  td.forte{{color:#fff;font-weight:700}}
  .obs{{color:var(--bad);font-size:.72rem;margin-top:5px;line-height:1.35}}

  .z0{{color:var(--muted)}}
  .z1{{background:rgba(224,106,106,.20)}} .z2{{background:rgba(224,106,106,.10)}}
  .z3{{background:rgba(159,181,170,.07)}}
  .z4{{background:rgba(55,211,153,.11)}} .z5{{background:rgba(55,211,153,.22);color:#fff;font-weight:600}}

  .tag{{font-size:.66rem;padding:3px 8px;border-radius:20px;letter-spacing:.04em;white-space:nowrap}}
  .tag.ok{{color:var(--win);border:1px solid rgba(55,211,153,.45);background:rgba(55,211,153,.1)}}
  .tag.off{{color:var(--muted);border:1px solid var(--line)}}
  .tag.art{{color:var(--bad);border:1px solid rgba(224,106,106,.5);background:rgba(224,106,106,.1)}}
  tr.corrigido{{background:rgba(224,106,106,.06)}}
  td.k em.art{{color:var(--bad);font-size:.72rem;margin-top:4px}}
  .pill{{display:inline-block;font-size:.68rem;padding:2px 8px;border-radius:20px;margin:2px 3px 2px 0;white-space:nowrap}}
  .pill.s{{background:rgba(242,193,78,.16);color:var(--warn)}}
  .pill.c{{background:rgba(201,168,106,.18);color:var(--gold2)}}
  .pill.g{{background:rgba(55,211,153,.2);color:var(--win)}}
  .pill.p{{background:rgba(224,106,106,.14);color:var(--bad)}}
  .pill.v{{background:rgba(159,181,170,.14);color:var(--muted)}}
  td.fun{{min-width:180px}} td.fun em{{color:var(--muted);font-style:normal;font-size:.78rem}}

  .degraus{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px}}
  .degrau{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
  .hint{{color:var(--muted);font-size:.76rem;margin-bottom:10px;line-height:1.35}}
  .lin{{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:.78rem}}
  .cd{{width:34px;color:var(--muted);font-variant-numeric:tabular-nums}}
  .lin.vencedor .cd{{color:var(--win);font-weight:700}}
  .bar{{flex:1;height:9px;background:rgba(255,255,255,.06);border-radius:6px;overflow:hidden}}
  .bar i{{display:block;height:100%;background:linear-gradient(90deg,#2a6b52,var(--gold));border-radius:6px}}
  .lin.vencedor .bar i{{background:linear-gradient(90deg,#2a6b52,var(--win))}}
  .vl{{width:50px;text-align:right;color:var(--cream);font-variant-numeric:tabular-nums}}

  .scatter{{width:100%;height:auto;background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:8px}}
  .scatter .eixo{{stroke:var(--line);stroke-width:1.5}}
  .scatter .eixo-med{{stroke:rgba(201,168,106,.35);stroke-width:1;stroke-dasharray:5 5}}
  .scatter .quad-bom{{fill:rgba(55,211,153,.07)}}
  .scatter .pt{{fill:rgba(201,168,106,.35);stroke:var(--gold);stroke-width:1.5}}
  .scatter .pt.novo{{fill:rgba(55,211,153,.3);stroke:var(--win);stroke-width:2}}
  .scatter .pl{{fill:#fff;font-size:11px;font-weight:700;text-anchor:middle;font-family:inherit}}
  .scatter .lbl{{fill:var(--muted);font-size:12px;font-family:inherit}}
  .scatter .lbl.fim{{text-anchor:end}}
  .scatter .lbl.bom{{fill:var(--win)}}
  .scatter .tick{{fill:var(--muted);font-size:10px;text-anchor:middle;font-family:inherit}}
  .scatter .tick.fim{{text-anchor:end}}

  .fams{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}}
  .fam{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
  .chips{{margin-bottom:10px}}
  .chip{{display:inline-block;font-size:.7rem;padding:2px 8px;border:1px solid var(--line);border-radius:20px;margin:0 4px 4px 0;color:var(--gold2)}}
  .fgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px 8px;margin:10px 0 12px}}
  .fgrid b{{display:block;color:#fff;font-size:1rem;font-variant-numeric:tabular-nums}}
  .fgrid span{{display:block;color:var(--muted);font-size:.68rem;text-transform:uppercase;letter-spacing:.04em}}
  .ver{{font-size:.84rem;padding:10px 12px;border-radius:9px;line-height:1.45}}
  .ver.bom{{background:rgba(55,211,153,.1);border-left:3px solid var(--win)}}
  .ver.meio{{background:rgba(242,193,78,.1);border-left:3px solid var(--warn)}}
  .ver.ruim{{background:rgba(224,106,106,.09);border-left:3px solid var(--bad)}}

  .alvo{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:12px 0}}
  .alvo .col{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
  .alvo .col.win{{border-color:rgba(55,211,153,.5);background:linear-gradient(180deg,rgba(55,211,153,.09),var(--card))}}
  .alvo h5{{color:var(--gold);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}}
  .alvo .row{{display:flex;justify-content:space-between;font-size:.82rem;padding:4px 0;border-bottom:1px solid rgba(42,77,63,.6)}}
  .alvo .row:last-child{{border:none}}
  .alvo .row b{{color:#fff;font-variant-numeric:tabular-nums}}
  .alvo .row b.win{{color:var(--win)}}

  .plano{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
  .p{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;border-top:3px solid var(--gold)}}
  .p .cod{{color:var(--gold);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase}}
  .p h4{{font-size:1.1rem;color:#fff;margin:4px 0 10px}}
  .p p{{font-size:.87rem;margin-bottom:10px}}
  .p .meta{{font-size:.78rem;color:var(--muted);border-top:1px solid var(--line);padding-top:9px;margin-top:4px}}
  .p .meta b{{color:var(--gold2)}}
  .p.gate{{border-top-color:var(--warn)}}
  .p.gate .cod{{color:var(--warn)}}

  ul.nao{{list-style:none;margin-top:8px}}
  ul.nao li{{background:rgba(224,106,106,.07);border-left:3px solid var(--bad);border-radius:8px;padding:11px 14px;margin-bottom:8px;font-size:.88rem}}
  ul.nao li b{{color:var(--bad)}}
  footer{{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:.8rem}}
  @media(max-width:640px){{
    body{{padding:20px 12px 60px}} h1{{font-size:1.45rem}}
    .fgrid{{grid-template-columns:repeat(2,1fr)}}
  }}
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="kicker">Cockpit de criativos · Mentoria Dono 14% · {D['periodo'].replace('2026-04-01 a 2026-08-07','1º de abril a 7 de agosto de 2026')}</div>
  <h1>A30 a A41 lado a lado: o que parou o scroll, o que fez clicar e o que trouxe o dono certo.</h1>
  <p class="lead">Doze criativos, {brl(GASTO)} investidos, três fontes cruzadas: métricas de anúncio da Meta, leads reais do banco e estágio no CRM. Snapshot gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}. Não é dado ao vivo.</p>
</header>

<div class="kpis">
  <div class="kpi"><b>{brl(GASTO)}</b><span>investido nos 12</span></div>
  <div class="kpi warn"><b>{D['totais']['leads_meta']}</b><span>leads atribuídos pela Meta no período todo</span></div>
  <div class="kpi win"><b>{leads_banco}</b><span>leads com criativo identificado (Meta também aponta {leads_meta_janela})</span></div>
  <div class="kpi"><b>{q100}</b><span>leads dentro do filtro</span></div>
  <div class="kpi"><b>{brl(D['totais']['gasto_rastreado'])}</b><span>investido com criativo identificado (de 19/07 em diante)</span></div>
  <div class="kpi win"><b>{brl(por['A40']['cpl_q'])}</b><span>melhor CPL qualificado (A40)</span></div>
  <div class="kpi win"><b>{brl(RECEITA)}</b><span>receita fechada no período</span></div>
  <div class="kpi win"><b>{num(ROAS_FUNIL,2)}x</b><span>ROAS do funil da mentoria</span></div>
</div>

<div class="fix">
  <p><b>Entrou venda, e a maior da série.</b> {brl(18000)} fechados em 28/08, atribuídos ao A39. A receita subiu para <b>{brl(RECEITA)}</b> em {FIN['vendas_total']} vendas, e o ROAS do funil voltou para <b>{num(ROAS_FUNIL,2)}x</b>. O pipeline vivo está em {brl(FIN['pipeline_total'])}, com dois contratos do A39 e um do A40.</p>
  <p><b>A fuga do fim do funil continua.</b> Já são {FIN['contrato_perdido_total']} contratos com valor fechado que foram para perdido, somando {brl(FIN['contrato_perdido_valor'])}. Para cada real que virou receita, quase um e meio caiu depois da assinatura. É o degrau mais caro da operação e nenhum criativo alcança ele.</p>
</div>

<div class="aviso">
  <p><b>Leia isto antes de qualquer número.</b> O código do criativo só passou a ser gravado no banco em <b>{D['inicio_rastreio'][8:10]}/{D['inicio_rastreio'][5:7]}/2026</b>. Só o A39, o A40 e o A41 têm lead real rastreável de ponta a ponta. Para o A30 até o A38 existe apenas a atribuição da Meta, que já provou ser fantasma nesta conta. Os {D['sem_utm']['leads']} leads de junho e da primeira metade de julho entraram sem origem de criativo e por isso não podem ser creditados a ninguém.</p>
  <p><b>Os dois números de lead do topo não se contradizem, medem janelas diferentes.</b> Os {D['totais']['leads_meta']} da Meta somam abril a agosto inteiro, quando a maior parte do investimento rodou sem rastreamento. Os {leads_banco} são só de 19/07 em diante. <b>Dentro dessa mesma janela a Meta aponta {leads_meta_janela} e o banco tem {leads_banco}</b>, ou seja, para os criativos novos a atribuição da Meta virou confiável. O problema de atribuição continua valendo apenas para A30 a A38, que rodaram antes.</p>
  <p>Dos {brl(GASTO)} investidos no período, só {brl(D['totais']['gasto_rastreado'])} rodaram com o criativo identificado no banco. Toda conclusão de CPL real desta página vale para essa fatia, e é por isso que a tabela 2 usa o gasto da janela, não o gasto histórico da peça.</p>
</div>

{AVISO_DEFASAGEM}

<div class="fix">
  <p><b>Correção aplicada.</b> {D['correcoes'].get('A35','')} O A35 entra com <b>zero lead</b> em toda esta página, inclusive na tabela mestre, nas médias por família de ângulo e na régua de custo por lead. O número de 8 leads que aparece no gerenciador da Meta não é usado em nenhum cálculo aqui.</p>
</div>

<h2>1. Tabela mestre</h2>
<p class="sub">As colunas do gerenciador, com todos os anúncios da conta no período. P25 a P95 são calculados sobre quem passou dos 3 segundos, ou seja, retenção de quem parou o scroll. Verde é bom, vermelho é ruim, dentro de cada coluna. As linhas destacadas são os três criativos com rastreamento completo.</p>
<div class="tbox"><table>
<thead><tr>
  <th>Criativo</th><th>Gasto</th><th>Freq</th><th>CTR</th><th>CPC</th><th>CPM</th>
  <th>Hook</th><th>P25</th><th>P50</th><th>P75</th><th>P95</th><th>Connect</th>
  <th>Leads Meta</th><th>CPL Meta</th>
</tr></thead>
<tbody>
{''.join(linha_mestre(l) for l in C)}
</tbody></table></div>

<h2>2. A tabela que decide: banco e CRM</h2>
<p class="sub">Lead da Meta contra lead que existe no banco, com faturamento declarado e estágio real no CRM. Qualificado é o lead que declarou faturar R$ 100 mil ou mais. <b>Nas linhas rastreadas, o gasto considerado é só o da janela em que o código do criativo já era gravado</b> (de 19/07 em diante), senão o A34 apareceria com um CPL de banco inflado pelo dinheiro que gastou antes do rastreamento existir. Custo por avanço considera sessão agendada, contrato e venda.</p>
<div class="tbox"><table>
<thead><tr>
  <th>Criativo</th><th>Status</th><th>Gasto na janela</th><th>Leads Meta</th><th>Leads banco</th>
  <th>CPL banco</th><th>Qualificados</th><th>CPL qualificado</th>
  <th>Funil no CRM</th><th>Custo por avanço</th>
</tr></thead>
<tbody>
{''.join(linha_banco(l) for l in C)}
</tbody></table></div>

<h2>3. ROAS e faturamento</h2>
<p class="sub">A régua da casa: venda só conta quando o card chega no estágio ganho. Contrato ainda é pipeline, não receita. O ROAS de referência usa como denominador só o investimento no funil da mentoria, que são os doze criativos desta análise. O quadro abaixo mostra as outras duas leituras possíveis e por que elas não servem para decidir criativo.</p>

<div class="kpis">
  <div class="kpi win"><b>{brl(RECEITA)}</b><span>receita fechada</span></div>
  <div class="kpi"><b>{FIN['vendas_total']}</b><span>vendas assinadas</span></div>
  <div class="kpi"><b>{brl(GASTO_FUNIL)}</b><span>investido no funil da mentoria</span></div>
  <div class="kpi win"><b>{num(ROAS_FUNIL,2)}x</b><span>ROAS do funil da mentoria</span></div>
  <div class="kpi"><b>{brl(FIN['ticket_medio'])}</b><span>ticket médio do contrato</span></div>
  <div class="kpi"><b>{brl(CAC_FUNIL)}</b><span>custo por venda</span></div>
  <div class="kpi"><b>{num(TX_VENDA)}%</b><span>lead que vira venda</span></div>
  <div class="kpi warn"><b>{brl(FIN['pipeline_total'])}</b><span>em contrato, ainda não é receita</span></div>
</div>

<div class="grana">
  <div class="caixa destaque">
    <h4>Qual denominador entra no ROAS</h4>
    <p class="hint">A conta gastou {brl(GASTO_CONTA)} no período, mas nem tudo é funil da mentoria. Por isso existem três leituras, e a que vale para decidir criativo é a primeira.</p>
    <table style="min-width:0;font-size:.82rem">
      <tr><td class="k"><b class="win">{num(ROAS_FUNIL,2)}x</b><em>funil da mentoria</em></td><td class="n">{brl(RECEITA)} sobre {brl(GASTO_FUNIL)}</td></tr>
      <tr><td class="k"><b>{num(ROAS_FUNIL_TOPO,2)}x</b><em>com o topo de funil junto</em></td><td class="n">{brl(RECEITA)} sobre {brl(GASTO_FUNIL_TOPO)}</td></tr>
      <tr><td class="k"><b>{num(ROAS_CONTA,2)}x</b><em>conta inteira</em></td><td class="n">{brl(RECEITA)} sobre {brl(GASTO_CONTA)}</td></tr>
    </table>
  </div>
  <div class="caixa">
    <h4>Onde foi cada real da conta</h4>
    <p class="hint">Quebra do investimento total de {brl(GASTO_CONTA)}, por tipo de anúncio.</p>
    {''.join(f'<div class="lin"><span class="cd" style="width:auto;flex:1;color:var(--cream)">{nome}</span>{barra(v, GASTO_CONTA)}<span class="vl">{brl(v)}</span></div><p class="hint" style="margin:0 0 8px 0">{obs}</p>' for nome, v, obs in CONTA['composicao'])}
  </div>
</div>

<div class="aviso">
  <p><b>Por que o ROAS de referência exclui os R$ {num(CONTA['gasto_outro_produto'],0)}.</b> Esse dinheiro foi para as campanhas <b>[D10] [CONVERSÃO] [COMPRA]</b>, com os criativos A12 a A29, que rodaram só em abril, vendem outro produto e têm objetivo de compra, não de captação de lead. Somar esse gasto ao denominador afunda o ROAS da mentoria sem motivo. Já os {brl(CONTA['gasto_topo_funil'])} de posts impulsionados e carrosséis são topo de funil da linha editorial: ajudam a formar audiência, mas não captam lead direto, então aparecem só na leitura do meio.</p>
</div>

<div class="aviso">
  <p><b>O que esses R$ 60 mil são e o que não são.</b> São quatro contratos assinados de mentoria, ticket de {brl(FIN['ticket_medio'])} cada no parcelado ({brl(FIN['ticket_avista'])} à vista). O recebimento é diluído: {FIN['parcelas']}. Ou seja, o caixa de entrada imediato desses quatro contratos é de {brl(CAIXA_IMEDIATO)}, e o restante entra ao longo de onze meses. O ROAS de {num(ROAS_FUNIL,2)}x é sobre valor de contrato fechado, não sobre dinheiro já na conta.</p>
  <p><b>Só uma das quatro vendas é rastreável a um criativo.</b> As outras três entraram em junho e no começo de julho, antes de o código do criativo ser gravado, no período em que o A32, o A34 e o A36 concentravam o investimento. A receita histórica veio da fase sem rastreio, e por isso não dá para coroar nenhuma peça antiga como a que vendeu.</p>
</div>

<div class="tbox"><table>
<thead><tr>
  <th>Criativo</th><th>Gasto na janela</th><th>Leads</th><th>Receita fechada</th><th>ROAS</th>
  <th>Custo por venda</th><th>Pipeline em contrato</th><th>ROAS se o pipeline fechar</th>
</tr></thead>
<tbody>
{''.join(linha_roas(l) for l in C)}
<tr class="apagado"><td class="k"><b>Sem rastreio</b><em>criativos A30 a A38 antes de 19/07</em></td>
  <td class="n">{brl(GASTO_FUNIL - D['totais']['gasto_rastreado'])}</td><td class="n">{D['sem_utm']['leads']}</td>
  <td class="n">{brl(FIN['receita_sem_utm'])}</td>
  <td class="n">{num(FIN['receita_sem_utm']/(GASTO_FUNIL - D['totais']['gasto_rastreado']),2)}x</td>
  <td class="n">{brl((GASTO_FUNIL - D['totais']['gasto_rastreado'])/3)}</td>
  <td class="n dim">zero</td><td class="n dim">sem base</td></tr>
</tbody></table></div>

<div class="grana">
  <div class="caixa destaque">
    <h4>Quanto vale um lead, e até onde o CPL pode subir</h4>
    <p class="hint">Cada lead que entrou no período vale, na média histórica, <b>{brl(RECEITA_POR_LEAD)}</b> de contrato fechado ({brl(RECEITA)} divididos por {LEADS_PERIODO} leads). Isso define o teto de CPL para cada nível de retorno.</p>
    {teto_cpl()}
    <p class="hint" style="margin-top:10px">Leia assim: pagando até {brl(RECEITA_POR_LEAD/3)} por lead, a operação entrega 3x. Acima de {brl(RECEITA_POR_LEAD)}, o lead custa mais do que devolve.</p>
  </div>
  <div class="caixa">
    <h4>Onde cada criativo cai nessa régua</h4>
    <p class="hint">CPL do banco quando existe, CPL da Meta quando não existe. A barra cheia é o ponto de empate.</p>
    {cpl_vs_teto()}
  </div>
</div>

<div class="aviso">
  <p><b>A conclusão que mais muda a operação.</b> Dos {len(REGUA)} criativos com CPL medido, <b>{len(ACIMA5)} entregam acima de 5x</b> ({lista(ACIMA5)}) e {len(ENTRE35)} {conc(ENTRE35,'fica','ficam')} entre 3x e 5x ({lista(ENTRE35)}). Abaixo de 3x {conc(ENTRE13+FORA,'fica','ficam')} {len(ENTRE13) + len(FORA)} ({lista(ENTRE13 + FORA)}), e o {lista(FORA)} {conc(FORA,'passou','passaram')} do ponto de empate de {brl(RECEITA_POR_LEAD)}. Outros {len(SEM_CPL)} não geraram lead nenhum e por isso não entram na régua ({lista(SEM_CPL)}). <b>O gargalo desta conta não é o preço do lead, é o volume e a qualificação</b>. Cortar criativo por CPL de R$ 100 ou R$ 150 é otimizar a variável errada. O que decide o resultado é quantos leads dentro do filtro de R$ 100 mil a peça consegue trazer, e é exatamente aí que o A40 se separa dos outros.</p>
  <p><b>Ressalva de base.</b> Quatro vendas em {LEADS_PERIODO} leads é amostra pequena para uma taxa estável. A taxa de {num(TX_VENDA)}% e o valor de {brl(RECEITA_POR_LEAD)} por lead são a melhor estimativa disponível hoje, não uma constante. Reavaliar a cada cinco vendas novas.</p>
</div>

<h2>4. O degrau que separa os líderes: a sessão</h2>
<p class="sub">Trazer lead barato e qualificado é meio caminho. O que fecha contrato é a sessão converter. Aqui estão só os criativos que já levaram alguém até a call, com coorte de {D.get('maturacao_dias',7)} dias para a comparação ser justa.</p>
<div class="tbox"><table>
<thead><tr><th>Criativo</th><th>Leads</th><th>Coorte madura</th><th>Avançaram</th><th>Sessões agendadas</th><th>Sessões realizadas</th><th>Viraram contrato ou venda</th><th>Taxa da sessão</th></tr></thead>
<tbody>
{''.join(f"""<tr class="{'novo' if l['rastreado'] else ''}">
  <td class="k"><b>{l['criativo']}</b><em>{l['titulo']}</em></td>
  <td class="n">{l['leads_banco']}</td>
  <td class="n">{l['maduros']}</td>
  <td class="n">{l['maduros_avancaram']} <em>({num(l['taxa_coorte'],0)}%)</em></td>
  <td class="n">{l['sess_agendadas']}</td>
  <td class="n">{l['sess_realizadas']}</td>
  <td class="n forte">{l['sess_convertidas']}</td>
  <td class="n {'z5' if l['taxa_sessao'] >= 50 else ('z1' if l['sess_realizadas'] else '')}">{num(l['taxa_sessao'],0)}%{'' if l['sess_realizadas'] else ' <em>sem base</em>'}</td>
</tr>""" for l in C if l['sess_agendadas'] or l['maduros'])}
</tbody></table></div>
<div class="aviso">
  <p><b>Este é o achado que decide a próxima leva.</b> O A39 levou {por['A39']['sess_realizadas']} pessoas à sessão e fechou {por['A39']['sess_convertidas']} ({num(por['A39']['taxa_sessao'],0)}%). O A40 levou {por['A40']['sess_realizadas']} e fechou {por['A40']['sess_convertidas']}. Os dois trazem lead barato e qualificado, o A40 até melhor nos dois quesitos, mas só um deles traz gente que compra depois de conversar.</p>
  <p><b>A hipótese, e ela é hipótese.</b> O A39 abre com o problema de mercado, então atrai quem quer resolver um problema. O A40 abre mostrando a ferramenta funcionando, então atrai quem quer conhecer a ferramenta. Intenção diferente na entrada, resultado diferente na saída.</p>
  <p><b>O que ainda não está decidido.</b> O A40 tem {por['A40']['sess_agendadas'] - por['A40']['sess_realizadas']} sessões agendadas que ainda não aconteceram. Se elas fecharem, a leitura muda. Enquanto não acontecerem, três sessões sem conversão é sinal, não sentença.</p>
</div>

<h2>5. A escada de métricas</h2>
<p class="sub">Cada degrau responde uma pergunta diferente e culpa um elemento diferente do método. Um criativo não se julga por um número, se julga pela escada inteira.</p>
<div class="degraus">
{escada('Parou o scroll (hook rate)', 'hook', nota='Culpa do gancho e da Urgência Oculta. Faixa apertada nesta conta: o hook não separa vencedor de perdedor.')}
{escada('Ficou até a metade (P50)', 'p50', nota='Culpa do meio do vídeo e dos Decorados. Aqui a separação é brutal e a demonstração ganha.')}
{escada('Clicou (CTR de link)', 'ctr_link', nota='Culpa da promessa e do CTA. O paradoxo lidera, a demonstração patina.')}
{escada('Chegou na página (connect rate)', 'connect', nota='Métrica da página, não do criativo. O salto de junho para agosto é a LP nova, não mérito da peça.')}
{escada('Cadastrou (visita para lead)', 'lpv_lead_meta', nota='Culpa da oferta e da página, com o criativo definindo a intenção de quem chega.')}
{escada('Custou quanto por lead', 'cpl_meta', '', inverso=True, nota='Leitura pela atribuição da Meta. Só serve para comparar entre criativos do mesmo período.')}
</div>

<h2>6. O alvo: gancho que faz clicar com fecho que faz cadastrar</h2>
<p class="sub">Cada bolha é um criativo. Quanto mais à direita, mais gente clicou. Quanto mais acima, mais gente cadastrou depois de chegar. O tamanho é o quanto foi investido. O canto superior direito é onde o dinheiro rende.</p>
{scatter()}

<div class="alvo">
  <div class="col"><h5>A34 · o melhor gancho</h5>
    <div class="row"><span>Hook</span><b>{num(por['A34']['hook'])}%</b></div>
    <div class="row"><span>CTR de link</span><b class="win">{num(por['A34']['ctr_link'],2)}%</b></div>
    <div class="row"><span>P50</span><b>{num(por['A34']['p50'])}%</b></div>
    <div class="row"><span>Vendeu</span><b>não</b></div>
  </div>
  <div class="col"><h5>A40 · o melhor lead</h5>
    <div class="row"><span>P50</span><b class="win">{num(por['A40']['p50'])}%</b></div>
    <div class="row"><span>CPL de banco</span><b class="win">{brl(por['A40']['cpl_banco'])}</b></div>
    <div class="row"><span>Dentro do filtro</span><b class="win">{num(por['A40']['taxa_q'],0)}%</b></div>
    <div class="row"><span>Vendeu</span><b>ainda não</b></div>
  </div>
  <div class="col win"><h5>A39 · o que vende</h5>
    <div class="row"><span>Leads</span><b>{por['A39']['leads_banco']}</b></div>
    <div class="row"><span>Coorte madura</span><b class="win">{num(por['A39']['taxa_coorte'],0)}%</b></div>
    <div class="row"><span>Taxa da sessão</span><b class="win">{num(por['A39']['taxa_sessao'],0)}%</b></div>
    <div class="row"><span>Vendas fechadas</span><b class="win">{por['A39']['vendas']}</b></div>
  </div>
  <div class="col win"><h5>A39 · o retorno</h5>
    <div class="row"><span>Investido</span><b>{brl(por['A39']['gasto_rast'])}</b></div>
    <div class="row"><span>Receita fechada</span><b class="win">{brl(por['A39']['receita'])}</b></div>
    <div class="row"><span>ROAS</span><b class="win">{num(por['A39']['roas'],2)}x</b></div>
    <div class="row"><span>Em contrato</span><b>{brl(por['A39']['pipeline_valor'])}</b></div>
  </div>
</div>
<div class="aviso">
  <p><b>Agora a comparação está pareada, e ela é dura.</b> As duas peças chegaram ao mesmo número de sessões realizadas: {por['A39']['sess_realizadas']} cada. O A39 converteu {por['A39']['sess_convertidas']} delas, o A40 converteu {por['A40']['sess_convertidas']}. Mesma quantidade de conversas, quatro vezes mais contrato. É a evidência mais limpa que a conta produziu até aqui, porque não depende de volume nem de maturação.</p>
  <p><b>O A40 segue imbatível no topo.</b> {por['A40']['leads_banco']} leads a {brl(por['A40']['cpl_banco'])}, contra {por['A39']['leads_banco']} a {brl(por['A39']['cpl_banco'])}. CPM de {brl(por['A40']['cpm'],2)} contra {brl(por['A39']['cpm'],2)}, P50 de {num(por['A40']['p50'])}% contra {num(por['A39']['p50'])}%, e taxa de lead dentro do filtro praticamente empatada ({num(por['A40']['taxa_q'],0)}% contra {num(por['A39']['taxa_q'],0)}%). Ele custa metade e entrega o dobro de gente.</p>
  <p><b>E o dinheiro vem todo do outro.</b> O A39 tem {por['A39']['vendas']} vendas e {brl(por['A39']['receita'])}, com ROAS de {num(por['A39']['roas'],2)}x. O A40 tem zero, com {por['A40']['leads_banco']} leads e {brl(por['A40']['gasto_rast'])} investidos. A hipótese que sustenta os dois fatos é a mesma desde o começo: o A39 abre pelo problema e traz quem quer resolver, o A40 abre pela ferramenta e traz quem quer conhecer a ferramenta.</p>
  <p><b>O teto de CPL voltou a subir</b> com a venda nova, para {brl(RECEITA_POR_LEAD)} por lead. O limite para 3x é {brl(RECEITA_POR_LEAD/3)}, e as duas peças cabem com folga: {brl(por['A39']['cpl_banco'])} e {brl(por['A40']['cpl_banco'])}.</p>
  <p><b>A frequência das duas passou de 2</b> ({num(por['A39']['freq'],2)} e {num(por['A40']['freq'],2)}). Público novo segue sendo a pendência mais antiga desta análise.</p>
</div>

<h2>7. O DNA por família de ângulo</h2>
<p class="sub">Os doze criativos agrupados pelo ângulo da Mandala, com o número de cada família. É aqui que a decisão de roteiro se sustenta.</p>
<div class="fams">
{''.join(card_familia(f) for f in fam_ord)}
</div>

<h2>8. A direção da leva A42, A43 e A44</h2>
<p class="sub">Tudo acima aponta para o mesmo lugar: partir do A39, que é o único que vende, e corrigir onde ele é fraco.</p>
<div class="plano">
  <div class="p">
    <div class="cod">A42 · aposta principal</div>
    <h4>Dilema, ancorado no dado que já vendeu</h4>
    <p>Ângulo inédito na conta, com a prova de mercado que faz o A39 converter. A estrutura de dilema é a que mais segura no meio, porque a pessoa fica para descobrir a saída, e é exatamente o meio que o A39 perde hoje.</p>
    <div class="meta">Meta: manter a taxa de sessão de <b>{num(por['A39']['taxa_sessao'],0)}%</b> e subir o P50 de <b>{num(por['A39']['p50'])}%</b> para <b>20%</b>. Duração alvo: 60 a 75s.</div>
  </div>
  <div class="p">
    <div class="cod">A43 · o alvo literal</div>
    <h4>A conta dos 72% montada na tela</h4>
    <p>Pega a conta empilhada que deu ao A34 o melhor clique da conta e monta ela linha a linha no Painel, em vez de contar de boca. Junta o melhor gancho com o payoff visual que o A40 provou reter.</p>
    <div class="meta">Rosto no gancho e no CTA, tela no miolo. Meta: hook acima de <b>28%</b>, CTR de link acima de <b>1,7%</b> e P50 acima de <b>20%</b>.</div>
  </div>
  <div class="p gate">
    <div class="cod">A44 · travado pela prova</div>
    <h4>Antes e depois no Painel</h4>
    <p>Só sai quando houver número de saída verificável de um mentorado, com print conferido. Sem a prova real, não sobe. Substituto, se o número não vier: uma segunda demonstração com outro Painel e outro porte de restaurante.</p>
    <div class="meta">A família de demonstração é a que qualifica melhor e ainda tem só <b>duas peças</b>. Ampliar essa família vale mais que abrir uma família nova.</div>
  </div>
</div>

<div class="aviso">
  <p><b>Duas ações valem mais que criativo novo, e são para agora.</b> Primeira: a frequência do A39 está em {num(por['A39']['freq'],2)} e a do A40 em {num(por['A40']['freq'],2)}, as duas subindo. As peças estão provadas, o público é que acabou. Ampliar segmentação ou lookalike antes que o CPM suba mais. Segunda: há {brl(FIN['pipeline_total'])} parados em contrato assinado que ainda não viraram receita. Destravar isso rende mais que qualquer ponto de CPL.</p>
</div>

<h2>9. O que não repetir</h2>
<ul class="nao">
  <li><b>Convocação e "procura-se", com ressalva.</b> Teste encerrado: o A41 gastou {brl(por['A41']['gasto_rast'])} e trouxe {por['A41']['leads_banco']} leads, sendo {por['A41']['q100']} dentro do filtro, a {brl(por['A41']['cpl_q'])} o lead qualificado. É de longe o pior da leva nova (o A40 faz o mesmo por {brl(por['A40']['cpl_q'])}), e o único lead que prestou entrou no último dia, com sessão ainda por acontecer. A mesma família do A30, que custou {brl(por['A30']['cpl_meta'])} por lead. Não repetir o formato, mas esperar a sessão desse lead antes de enterrar o ângulo de vez.</li>
  <li><b>História de origem longa em rosto puro.</b> O A33 gastou {brl(por['A33']['gasto'])}, não gerou lead nenhum e tem a pior retenção da série, com 94 segundos.</li>
  <li><b>Perseguir hook e retenção como critério de vitória.</b> O A38 tem a melhor retenção da conta (P95 de {num(por['A38']['p95'])}%) e o melhor connect ({num(por['A38']['connect'])}%), com o pior CPL ({brl(por['A38']['cpl_meta'])}) e a pior taxa de cadastro. Métrica de vaidade confirmada com dado novo.</li>
  <li><b>Subir criativo novo no CBO junto com os antigos.</b> O A32 consumiu {brl(1933)} do CBO enquanto o A34 e o A38 ficaram na migalha. Conjunto isolado, como está sendo feito hoje no ABO de teste, e está funcionando.</li>
  <li><b>Coroar ou enterrar peça pela atribuição da Meta.</b> O A35 mostrava {por['A35']['leads_meta']} leads no gerenciador e {por['A35']['leads_banco']} lead real. Veredito só com o banco e o CRM na mão.</li>
</ul>

<h2>10. Ressalvas de leitura</h2>
<div class="aviso">
  <p><b>A comparação entre lotes não é limpa.</b> Entre o A38 e o A39 mudou a oferta (de mentoria para sessão gratuita), mudou a página e mudou a estrutura de campanha. Só a família do ângulo é comparável, não o CPL absoluto.</p>
  <p><b>O A40 ainda não está julgado.</b> Ele tem {por['A40']['sess_agendadas'] - por['A40']['sess_realizadas']} sessões marcadas que não aconteceram. Três sessões sem conversão é sinal forte, mas a amostra é pequena e a peça é mais nova que o A39. O veredito real sai quando essas sessões acontecerem.</p>
  <p><b>Faturamento declarado não é qualificação.</b> O A40 trouxe declarações de R$ 8 milhões, R$ 1,5 milhão e R$ 1,2 milhão por mês. As duas primeiras foram perdidas. Declaração fora da curva merece desconfiança, não comemoração.</p>
  <p><b>A base ainda é pequena.</b> {FIN['vendas_total']} vendas em {D['totais']['leads_banco_total_periodo']} leads sustentam uma taxa de {num(TX_VENDA)}% e um valor de {brl(RECEITA_POR_LEAD)} por lead. É a melhor estimativa disponível, não uma constante. Reavaliar a cada cinco vendas novas.</p>
  <p><b>A atribuição da Meta continua imprestável para os criativos antigos.</b> Para os novos ela já bate com o banco. O A35 segue como o exemplo do erro: 8 leads no gerenciador, zero na realidade, e por isso ele entra com zero em toda esta página.</p>
</div>

<footer>
  Mentoria Dono 14% · Rodrigo Haertel, o engenheiro do cardápio · Snapshot de {datetime.now().strftime('%d/%m/%Y %H:%M')}, não é dado ao vivo.<br>
  Fontes: Meta Graph API nível anúncio (conta inteira, {D['periodo']}), tabela contact_submissions e crm_cards do banco de produção.
  Lead real conta pelo banco e pelo CRM, nunca pela atribuição da Meta. Rastreamento por criativo disponível a partir de 19/07/2026.
</footer>

</div>
</body>
</html>
"""

saida = BASE / f"criativos-a30-a41-{datetime.now().strftime('%Y-%m-%d-%H%M')}.html"
saida.write_text(html, encoding="utf-8")

# copia de nome fixo, sempre a versao mais recente (link estavel para abrir)
atual = BASE / "criativos-a30-a41-ATUAL.html"
atual.write_text(html, encoding="utf-8")

print("dashboard:", saida)
print("atalho fixo:", atual)
