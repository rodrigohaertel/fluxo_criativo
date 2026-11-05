# -*- coding: utf-8 -*-
"""Leitura diária do perfil @rodrigohaertel (somente leitura na Graph API).

Roda às 03h pelo Agendador do Windows (scripts/instagram-perfil-autorun.cmd).
Grava o relatório do dia em meus-produtos/linha-editorial/trafego/analise/perfil-diario/AAAA-MM-DD.md
e guarda a contagem de seguidores das 03h em historico.json, na mesma pasta.

Regra do dia fechado: as séries terminam em ontem. A Meta só fecha os seguidores
que entraram e saíram de um dia cerca de 30 horas depois; enquanto isso, o saldo
do dia sai da diferença entre duas contagens das 03h.

O token vem do .env e nunca é impresso.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "meus-produtos" / "linha-editorial" / "trafego" / "analise" / "perfil-diario"
IG = "17841401560243113"
CONTA = "act_760723921231720"
META_SEGUIDORES, META_DATA = 10000, date(2026, 11, 30)
DIAS = 14


def _token():
    tk = os.environ.get("FB_ACCESS_TOKEN_PERMANENTE")
    if tk:
        return tk
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("FB_ACCESS_TOKEN_PERMANENTE="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("FB_ACCESS_TOKEN_PERMANENTE não encontrado no .env")


TOKEN = _token()


def get(caminho, **p):
    p["access_token"] = TOKEN
    url = f"https://graph.facebook.com/v25.0/{caminho}?" + urllib.parse.urlencode(p)
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"erro": e.read().decode("utf-8", "replace")[:200]}
    except Exception as e:  # rede fora do ar às 03h, por exemplo
        return {"erro": str(e)[:200]}


def total(metrica, a, b, **x):
    r = get(f"{IG}/insights", metric=metrica, period="day", metric_type="total_value", since=a, until=b, **x)
    if "erro" in r:
        return None
    t = (r.get("data") or [{}])[0].get("total_value", {})
    if x.get("breakdown"):
        try:
            return {y["dimension_values"][0]: y["value"] for y in t["breakdowns"][0]["results"]}
        except Exception:
            return None
    return t.get("value")


def dia(d):
    a, b = d.isoformat(), (d + timedelta(days=1)).isoformat()
    return a, {
        "visitas": total("profile_views", a, b),
        "engajadas": total("accounts_engaged", a, b),
        "segue": total("follows_and_unfollows", a, b, breakdown="follow_type"),
        "tipo": total("reach", a, b, breakdown="media_product_type"),
        "comentarios": total("comments", a, b),
        "salvamentos": total("saves", a, b),
        "compartilhamentos": total("shares", a, b),
    }


def gasto(inicio, fim):
    linhas, depois = [], None
    while True:
        p = dict(level="campaign", time_increment=1, fields="campaign_name,spend,date_start", limit=500,
                 time_range=json.dumps({"since": inicio.isoformat(), "until": fim.isoformat()}))
        if depois:
            p["after"] = depois
        r = get(f"{CONTA}/insights", **p)
        linhas += r.get("data", [])
        depois = r.get("paging", {}).get("cursors", {}).get("after") if r.get("paging", {}).get("next") else None
        if not depois:
            return [g for g in linhas if "DONO14" not in g["campaign_name"].upper()]


def posts(desde):
    md = get(f"{IG}/media", fields="id,caption,timestamp,media_product_type,media_type", limit=25).get("data", [])
    md = [m for m in md if m["timestamp"][:10] >= desde.isoformat()]

    def ins(m):
        r = get(f"{m['id']}/insights", metric="reach,views,saved,shares,comments,likes")
        m["ins"] = {x["name"]: x["values"][0]["value"] for x in r.get("data", [])}
        return m

    with ThreadPoolExecutor(8) as ex:
        return list(ex.map(ins, md))


def brl(v):
    return ("R$ %.2f" % v).replace(".", ",")


def num(v):
    return "n/d" if v is None else f"{v:,}".replace(",", ".")


def main():
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    PASTA.mkdir(parents=True, exist_ok=True)

    conta = get(IG, fields="followers_count,media_count")
    if "erro" in conta:
        raise SystemExit("Graph API sem resposta: " + conta["erro"])
    seguidores = conta["followers_count"]

    hist_arq = PASTA / "historico.json"
    hist = json.loads(hist_arq.read_text(encoding="utf-8")) if hist_arq.exists() else {}
    hist[hoje.isoformat()] = {"hora": datetime.now().strftime("%H:%M"), "seguidores": seguidores}
    hist_arq.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    anterior = hist.get(ontem.isoformat())

    datas = [ontem - timedelta(days=i) for i in range(DIAS - 1, -1, -1)]
    with ThreadPoolExecutor(12) as ex:
        dados = dict(ex.map(dia, datas))

    g = gasto(datas[0], ontem)
    turb, outro = {}, {}
    for linha in g:
        alvo = turb if linha["campaign_name"].startswith("Post do Instagram") else outro
        alvo[linha["date_start"]] = alvo.get(linha["date_start"], 0) + float(linha["spend"])

    # Saldo de cada dia: o fechado da Meta, ou a diferença entre as contagens das 03h.
    for d in datas:
        k = d.isoformat()
        s = dados[k]["segue"] or {}
        if "FOLLOWER" in s:
            dados[k]["saldo"], dados[k]["origem"] = s.get("FOLLOWER", 0) - s.get("NON_FOLLOWER", 0), "fechado"
        else:
            a, b = hist.get(k), hist.get((d + timedelta(days=1)).isoformat())
            dados[k]["saldo"], dados[k]["origem"] = (b["seguidores"] - a["seguidores"], "contagem das 03h") if a and b else (None, "")

    L = [f"# Perfil @rodrigohaertel · leitura de {hoje.strftime('%d/%m/%Y')}, {hist[hoje.isoformat()]['hora']}", ""]
    linha_seg = f"**Seguidores agora: {num(seguidores)}**"
    if anterior:
        linha_seg += f" ({seguidores - anterior['seguidores']:+d} desde {ontem.strftime('%d/%m')} às {anterior['hora']})"
    L += [linha_seg, ""]

    L += ["## Últimos 7 dias fechados", "",
          "| Dia | Saldo de seguidores | Visitas | Contas engajadas | Story | Carrossel | Reel sem anúncio | Turbinados | Custo por seguidor |",
          "|---|---|---|---|---|---|---|---|---|"]
    for d in datas[-7:]:
        k, x = d.isoformat(), dados[d.isoformat()]
        t = x["tipo"] or {}
        saldo = "n/d" if x["saldo"] is None else f"{x['saldo']:+d}" + ("" if x["origem"] == "fechado" else " (contagem das 03h)")
        custo = brl(turb.get(k, 0) / x["saldo"]) if x["saldo"] else "n/d"
        L.append(f"| {d.strftime('%d/%m')} | {saldo} | {num(x['visitas'])} | {num(x['engajadas'])} | {num(t.get('STORY'))} | "
                 f"{num(t.get('CAROUSEL_CONTAINER'))} | {num(t.get('REEL'))} | {brl(turb.get(k, 0))} | {custo} |")

    def soma(janela):
        ks = [d.isoformat() for d in janela if dados[d.isoformat()]["saldo"] is not None]
        s = sum(dados[k]["saldo"] for k in ks)
        v = sum(turb.get(k, 0) for k in ks)
        return len(ks), s, v

    n7, s7, v7 = soma(datas[-7:])
    n14, s14, v14 = soma(datas[:7])
    L += [""]
    if n7:
        L.append(f"- **Ritmo dos últimos {n7} dias:** {s7 / n7:.0f} seguidores líquidos por dia, a {brl(v7 / s7) if s7 else 'n/d'} cada nos turbinados."
                 + (f" Semana anterior: {s14 / n14:.0f} por dia, a {brl(v14 / s14) if s14 else 'n/d'}." if n14 else ""))
    for k, rotulo in (("comentarios", "Comentários"), ("salvamentos", "Salvamentos"), ("compartilhamentos", "Compartilhamentos")):
        a = sum(dados[d.isoformat()][k] or 0 for d in datas[-7:])
        b = sum(dados[d.isoformat()][k] or 0 for d in datas[:7])
        L.append(f"- **{rotulo} na semana:** {a} (semana anterior: {b}).")
    L.append(f"- **Outras campanhas da Linha Editorial (aula no Gerenciador):** {brl(sum(outro.get(d.isoformat(), 0) for d in datas[-7:]))} na semana.")

    faltam, dias_meta = META_SEGUIDORES - seguidores, (META_DATA - hoje).days + 1
    if faltam > 0 and dias_meta > 0:
        L.append(f"- **Meta de {num(META_SEGUIDORES)} em {META_DATA.strftime('%d/%m')}:** faltam {num(faltam)} em {dias_meta} dias, "
                 f"{faltam / dias_meta:.0f} por dia." + (f" No ritmo atual, chega em {(hoje + timedelta(days=round(faltam / (s7 / n7)))).strftime('%d/%m')}." if n7 and s7 > 0 else ""))
    elif faltam <= 0:
        L.append(f"- **Meta de {num(META_SEGUIDORES)} batida.**")

    L += ["", f"## Turbinados de ontem ({ontem.strftime('%d/%m')})", "", "| Campanha | Gasto |", "|---|---|"]
    for linha in sorted((x for x in g if x["date_start"] == ontem.isoformat()), key=lambda x: -float(x["spend"])):
        L.append(f"| {linha['campaign_name'][:70]} | {brl(float(linha['spend']))} |")

    L += ["", "## Publicações dos últimos 14 dias (alcance sem anúncio)", "",
          "| Data | Tipo | Começo da legenda | Pessoas | Visualizações | Salvamentos | Compartilhamentos | Comentários |",
          "|---|---|---|---|---|---|---|---|"]
    for m in posts(hoje - timedelta(days=14)):
        i = m["ins"]
        tipo = "Carrossel" if m["media_type"] == "CAROUSEL_ALBUM" else ("Reel" if m["media_product_type"] == "REELS" else m["media_type"].title())
        leg = (m.get("caption") or "").replace("\n", " ").replace("|", "/")[:55]
        L.append(f"| {m['timestamp'][8:10]}/{m['timestamp'][5:7]} | {tipo} | {leg} | {num(i.get('reach'))} | {num(i.get('views'))} | "
                 f"{num(i.get('saved'))} | {num(i.get('shares'))} | {num(i.get('comments'))} |")

    L += ["", "Fonte: Graph API, dias fechados até ontem. O custo por seguidor de cada Reel (régua oficial) depende da tela de insights do post e fica para a leitura com o Rodrigo.", ""]
    arq = PASTA / f"{hoje.isoformat()}.md"
    arq.write_text("\n".join(L), encoding="utf-8")
    print("Relatório salvo:", arq)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
