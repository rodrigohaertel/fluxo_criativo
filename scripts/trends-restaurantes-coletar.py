# -*- coding: utf-8 -*-
"""Coleta diária de trends do mercado de bares e restaurantes (Linha Editorial).

Roda às 07h pelo Agendador do Windows (scripts/trends-restaurantes-autorun.cmd),
antes da curadoria do Claude, que escolhe os 3 tópicos do dia.

O que busca (fontes em meus-produtos/linha-editorial/trends/fontes.json):
  1. Instagram dos criadores e da mídia do setor, pelo Apify: os últimos posts de
     cada perfil, com comentários, curtidas, views e os comentários mais recentes.
  2. Hashtags do setor, pelo Apify.
  3. Google Notícias (RSS) das últimas 48 horas.

Grava meus-produtos/linha-editorial/trends/coleta/AAAA-MM-DD.json e mantém
historico-posts.json, que dá a mediana de comentários de cada perfil. A "força"
de um post é comentários ÷ mediana do perfil: 3,0 quer dizer três vezes mais
conversa que o normal daquele perfil, que é o sinal de assunto em debate.

Somente leitura. O token do Apify vem do .env e nunca é impresso.
"""
import json
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from statistics import median

import requests

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "meus-produtos" / "linha-editorial" / "trends"
FONTES = PASTA / "fontes.json"
HISTORICO = PASTA / "historico-posts.json"
APIFY = "https://api.apify.com/v2"
ATOR = "apify~instagram-scraper"
DIAS_HISTORICO = 45


def _token():
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("APIFY_API_TOKEN="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("APIFY_API_TOKEN não encontrado no .env")


TOKEN = _token()
erros = []


def iniciar_execucao(urls, limite):
    payload = {"directUrls": urls, "resultsType": "posts", "resultsLimit": limite, "addParentData": False}
    r = requests.post(f"{APIFY}/acts/{ATOR}/runs", params={"token": TOKEN}, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["data"]["id"]


def esperar_execucao(run_id, limite_s=900):
    inicio = time.time()
    while time.time() - inicio < limite_s:
        r = requests.get(f"{APIFY}/actor-runs/{run_id}", params={"token": TOKEN, "waitForFinish": 60}, timeout=90)
        d = r.json()["data"]
        if d["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            itens = []
            if d["status"] == "SUCCEEDED":
                it = requests.get(f"{APIFY}/datasets/{d['defaultDatasetId']}/items",
                                  params={"token": TOKEN, "clean": "true", "format": "json"}, timeout=120)
                itens = it.json()
            else:
                erros.append(f"Apify terminou com status {d['status']}")
            return itens, d.get("usageTotalUsd")
    erros.append("Apify passou de 15 minutos e foi deixado para trás")
    return [], None


def data_post(p):
    t = p.get("timestamp")
    if not t:
        return None
    return datetime.fromisoformat(t.replace("Z", "+00:00"))


def resumir(p, mediana):
    com = p.get("commentsCount") or 0
    views = p.get("videoPlayCount") or p.get("videoViewCount")
    forca = round(com / mediana, 1) if mediana else None
    comentarios = [
        {"de": c.get("ownerUsername"), "texto": (c.get("text") or "")[:220], "curtidas": c.get("likesCount")}
        for c in (p.get("latestComments") or [])[:6]
    ]
    dt = data_post(p)
    return {
        "perfil": p.get("ownerUsername"),
        "formato": "Reel" if p.get("productType") == "clips" else {"Sidecar": "Carrossel", "Image": "Imagem", "Video": "Vídeo"}.get(p.get("type"), p.get("type")),
        "publicado": dt.astimezone().strftime("%d/%m %H:%M") if dt else None,
        "horas_no_ar": round((datetime.now(timezone.utc) - dt).total_seconds() / 3600) if dt else None,
        "comentarios": com,
        "curtidas": p.get("likesCount"),
        "views": views,
        "mediana_comentarios_do_perfil": mediana,
        "forca": forca,
        "legenda": (p.get("caption") or "")[:700],
        "comentarios_recentes": comentarios,
        "link": p.get("url"),
    }


def coletar_instagram(fontes):
    perfis = fontes["criadores"] + fontes["midia"]
    urls_perfis = [f"https://www.instagram.com/{u}/" for u in perfis]
    urls_tags = [f"https://www.instagram.com/explore/tags/{h}/" for h in fontes.get("hashtags", [])]

    ids = {}
    try:
        ids["perfis"] = iniciar_execucao(urls_perfis, fontes.get("posts_por_perfil", 6))
    except Exception as e:
        erros.append(f"Apify (perfis) não iniciou: {str(e)[:150]}")
    if urls_tags:
        try:
            ids["tags"] = iniciar_execucao(urls_tags, fontes.get("posts_por_hashtag", 10))
        except Exception as e:
            erros.append(f"Apify (hashtags) não iniciou: {str(e)[:150]}")

    res, custo = {}, 0.0
    for chave, rid in ids.items():
        itens, usd = esperar_execucao(rid)
        res[chave] = [i for i in itens if isinstance(i, dict) and not i.get("error")]
        custo += usd or 0
    return res.get("perfis", []), res.get("tags", []), round(custo, 3), perfis


def atualizar_historico(posts):
    hist = json.loads(HISTORICO.read_text(encoding="utf-8")) if HISTORICO.exists() else {}
    corte = (date.today() - timedelta(days=DIAS_HISTORICO)).isoformat()
    for p in posts:
        u, sc, dt = p.get("ownerUsername"), p.get("shortCode"), data_post(p)
        if not (u and sc and dt):
            continue
        hist.setdefault(u, {})[sc] = {"data": dt.date().isoformat(), "comentarios": p.get("commentsCount") or 0}
    for u in list(hist):
        hist[u] = {k: v for k, v in hist[u].items() if v["data"] >= corte}
    HISTORICO.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    medianas = {}
    for u, posts_u in hist.items():
        vals = [v["comentarios"] for v in posts_u.values()]
        medianas[u] = median(vals) if len(vals) >= 3 else None
    return medianas


def coletar_noticias(consultas, janela_h):
    vistos, saida = set(), []
    limite = datetime.now(timezone.utc) - timedelta(hours=janela_h)
    for q in consultas:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": f"{q} when:2d", "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"})
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            raiz = ET.fromstring(r.content)
        except Exception as e:
            erros.append(f"Google Notícias ({q}): {str(e)[:120]}")
            continue
        for item in raiz.iter("item"):
            titulo = (item.findtext("title") or "").strip()
            chave = titulo.lower()[:90]
            if not titulo or chave in vistos:
                continue
            try:
                dt = parsedate_to_datetime(item.findtext("pubDate"))
            except Exception:
                dt = None
            if dt and dt < limite:
                continue
            vistos.add(chave)
            saida.append({
                "busca": q,
                "titulo": titulo,
                "fonte": item.findtext("source"),
                "publicado": dt.astimezone().strftime("%d/%m %H:%M") if dt else None,
                "link": item.findtext("link"),
            })
    return saida


def main():
    fontes = json.loads(FONTES.read_text(encoding="utf-8"))
    janela = fontes.get("janela_horas", 48)
    hoje = date.today().isoformat()
    (PASTA / "coleta").mkdir(parents=True, exist_ok=True)

    posts, tags, custo, perfis = coletar_instagram(fontes)
    medianas = atualizar_historico(posts)

    recentes, sem_post = [], []
    for u in perfis:
        dos_perfil = [p for p in posts if p.get("ownerUsername") == u]
        novos = [p for p in dos_perfil if (data_post(p) or datetime.min.replace(tzinfo=timezone.utc))
                 >= datetime.now(timezone.utc) - timedelta(hours=janela)]
        if not novos:
            sem_post.append(u)
        recentes += [dict(resumir(p, medianas.get(u)), grupo="mídia" if u in fontes["midia"] else "criador") for p in novos]
    recentes.sort(key=lambda x: (x["forca"] or 0, x["comentarios"]), reverse=True)

    tags_ok = [resumir(p, None) for p in tags
               if (data_post(p) or datetime.min.replace(tzinfo=timezone.utc)) >= datetime.now(timezone.utc) - timedelta(hours=janela)]
    tags_ok.sort(key=lambda x: x["comentarios"], reverse=True)

    noticias = coletar_noticias(fontes.get("noticias", []), janela)

    saida = {
        "data": hoje,
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "janela_horas": janela,
        "custo_apify_usd": custo,
        "perfis_lidos": len(perfis),
        "posts_lidos": len(posts),
        "instagram_recentes": recentes,
        "perfis_sem_post_na_janela": sem_post,
        "hashtags_recentes": tags_ok[:20],
        "noticias": noticias,
        "erros": erros,
    }
    destino = PASTA / "coleta" / f"{hoje}.json"
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Coleta salva em {destino}")
    print(f"Instagram: {len(posts)} posts lidos, {len(recentes)} nas últimas {janela}h, "
          f"{len(tags_ok)} de hashtag. Notícias: {len(noticias)}. Custo Apify: US$ {custo}.")
    for e in erros:
        print("ALERTA:", e)
    return 0 if (posts or noticias) else 1


if __name__ == "__main__":
    sys.exit(main())
