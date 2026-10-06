#!/usr/bin/env python3
"""Compara o tamanho dos públicos de VV 3s (o do Rodrigo x os de teste criados em 05/10/2026)
com as views de 3s dos anúncios no mesmo período. Só leitura na Meta.

Uso: py -3 scripts/vv-comparar-publicos.py
Saída: imprime o relatório e salva em
meus-produtos/dono-14/trafego/analise/publicos-vv/AAAA-MM-DD.md
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLICOS = [
    ("Quente - VV 03s - 180D (o seu)", "120237198955150527", 180),
    ("Teste - VV 03s - 180D (200 vídeos mais vistos)", "120249475201450527", 180),
    ("Teste - VV 03s - 2026 (200 vídeos mais vistos)", "120249475201000527", 278),
]


def ler_env() -> dict:
    env = {}
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = ler_env()
TOKEN = ENV["FB_ACCESS_TOKEN_PERMANENTE"]
CONTA = "act_" + ENV["FB_AD_ACCOUNT_ID"].replace("act_", "")


def get(caminho: str, **params) -> dict:
    params["access_token"] = TOKEN
    url = f"https://graph.facebook.com/v25.0/{caminho}?" + urllib.parse.urlencode(params)
    try:
        return json.loads(urllib.request.urlopen(url, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read()).get("error", {})}


def anuncios(desde: date, ate: date) -> dict:
    r = get(f"{CONTA}/insights", time_range=json.dumps({"since": str(desde), "until": str(ate)}),
            fields="reach,impressions,frequency,actions")
    linha = (r.get("data") or [{}])[0]
    views = next((int(a["value"]) for a in linha.get("actions", []) if a["action_type"] == "video_view"), 0)
    freq = float(linha.get("frequency") or 0)
    return {"alcance": int(linha.get("reach") or 0), "views3s": views, "freq": freq,
            "pessoas_est": round(views / freq) if freq else 0}


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".") if n not in (None, "") else "sem dado"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    ref = {180: anuncios(hoje - timedelta(days=180), ontem), 278: anuncios(date(2026, 1, 1), ontem)}

    linhas = [f"# Públicos de VV 3s: conferência de {hoje.strftime('%d/%m/%Y')}", "",
              "| Público | Janela | Tamanho na Meta | Situação | Atualizado em |", "|---|---|---|---|---|"]
    tamanhos = {}
    for nome, pid, dias in PUBLICOS:
        r = get(pid, fields="approximate_count_lower_bound,approximate_count_upper_bound,operation_status,time_updated")
        if "error" in r:
            linhas.append(f"| {nome} | {dias} dias | erro: {r['error'].get('message')} | | |")
            continue
        lo, hi = r.get("approximate_count_lower_bound"), r.get("approximate_count_upper_bound")
        st = r.get("operation_status") or {}
        pronto = "pronto" if st.get("code") == 200 else f"ainda preenchendo (código {st.get('code')})"
        atual = datetime.fromtimestamp(r.get("time_updated", 0)).strftime("%d/%m %H:%M")
        tamanhos[nome] = (lo, hi, st.get("code"))
        linhas.append(f"| {nome} | {dias} dias | {fmt(lo)} a {fmt(hi)} | {pronto} | {atual} |")

    linhas += ["", "## Referência: anúncios no mesmo período", "",
               "| Janela | Alcance (pessoas) | Views de 3s | Frequência | Pessoas com 3s (estimativa: views ÷ frequência) |",
               "|---|---|---|---|---|"]
    for dias, a in ref.items():
        linhas.append(f"| {dias} dias | {fmt(a['alcance'])} | {fmt(a['views3s'])} | "
                      f"{str(round(a['freq'], 2)).replace('.', ',')} | {fmt(a['pessoas_est'])} |")

    linhas += ["", "## Como ler", "",
               "- Compare **Quente - VV 03s - 180D** com **Teste - VV 03s - 180D**: mesma janela, mesmo evento.",
               "- Se o Teste ficar bem acima do Quente, o público do Rodrigo está com vídeos faltando.",
               "- Se os dois ficarem parecidos, o público do Rodrigo está certo e a diferença para as views é repetição.",
               "- Público com situação \"ainda preenchendo\" não tem tamanho confiável: repetir a leitura mais tarde.",
               "- Os públicos de teste não incluem views orgânicas do Instagram nem vídeos sem página."]

    relatorio = "\n".join(linhas) + "\n"
    pasta = RAIZ / "meus-produtos" / "dono-14" / "trafego" / "analise" / "publicos-vv"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{hoje}.md"
    destino.write_text(relatorio, encoding="utf-8")
    print(relatorio)
    print(f"Salvo em: {destino}")


if __name__ == "__main__":
    main()
