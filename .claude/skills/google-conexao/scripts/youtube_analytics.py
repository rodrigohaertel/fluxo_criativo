#!/usr/bin/env python3
"""Leitura do YouTube Analytics e do YouTube Data do próprio canal.

Usa a autorização gravada por autorizar.py (GOOGLE_OAUTH_REFRESH_TOKEN no .env).
Só leitura. Nenhum valor sensível é exibido. Só usa a biblioteca padrão do Python.

Uso:
  youtube_analytics.py testar
  youtube_analytics.py lista   [--max 200]
  youtube_analytics.py videos  [--dias 28] [--max 50]
  youtube_analytics.py origens [--dias 28] [--video ID]
  youtube_analytics.py canal   [--dias 28]

Cada comando imprime um resumo e salva o JSON completo em
meus-produtos/{ativo}/entregas/youtube-analytics/.
"""
import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
DATA = "https://www.googleapis.com/youtube/v3"

ORIGENS_PT = {
    "ADVERTISING": "Anúncio (pago)",
    "SHORTS": "Feed de Shorts",
    "YT_SEARCH": "Busca do YouTube",
    "RELATED_VIDEO": "Vídeos sugeridos",
    "SUBSCRIBER": "Inscritos e página inicial",
    "YT_CHANNEL": "Página do canal",
    "YT_OTHER_PAGE": "Outras páginas do YouTube",
    "EXT_URL": "Sites externos",
    "NO_LINK_OTHER": "Acesso direto ou desconhecido",
    "NO_LINK_EMBEDDED": "Incorporado em outro site",
    "PLAYLIST": "Playlists",
    "NOTIFICATION": "Notificações",
    "END_SCREEN": "Tela final",
    "HASHTAGS": "Hashtags",
    "SOUND_PAGE": "Página de som",
}


def raiz_projeto() -> Path:
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        if (cur / ".env").exists():
            return cur
        cur = cur.parent
    raise SystemExit("Arquivo .env não encontrado na raiz do projeto.")


def ler_env(raiz: Path) -> dict:
    dados = {}
    for linha in (raiz / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            chave, valor = linha.split("=", 1)
            dados[chave.strip()] = valor.strip().strip('"').strip("'")
    return dados


def token_de_acesso(env: dict) -> str:
    faltando = [k for k in ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET", "GOOGLE_OAUTH_REFRESH_TOKEN") if not env.get(k)]
    if faltando:
        raise SystemExit("Conexão Google incompleta no .env. Rode /google-conexao. Faltando: " + ", ".join(faltando))
    corpo = urllib.parse.urlencode({
        "client_id": env["GOOGLE_OAUTH_CLIENT_ID"],
        "client_secret": env["GOOGLE_OAUTH_CLIENT_SECRET"],
        "refresh_token": env["GOOGLE_OAUTH_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=corpo), timeout=30) as r:
            return json.loads(r.read())["access_token"]
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"O Google recusou a autorização salva (HTTP {e.code}). "
            "Ela pode ter expirado ou sido revogada. Rode autorizar.py de novo."
        )


def get(url: str, params: dict, token: str) -> dict:
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detalhe = ""
        try:
            detalhe = json.loads(e.read()).get("error", {}).get("message", "")
        except Exception:
            pass
        raise SystemExit(f"Erro HTTP {e.code} na leitura do Google. {detalhe}")


def periodo(dias: int):
    fim = dt.date.today()
    return (fim - dt.timedelta(days=dias)).isoformat(), fim.isoformat()


def duracao_seg(iso: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def detalhes_videos(ids: list, token: str) -> dict:
    saida = {}
    for i in range(0, len(ids), 50):
        r = get(f"{DATA}/videos", {"part": "snippet,contentDetails,statistics,status", "id": ",".join(ids[i:i + 50])}, token)
        for item in r.get("items", []):
            seg = duracao_seg(item["contentDetails"].get("duration"))
            saida[item["id"]] = {
                "titulo": item["snippet"]["title"],
                "publicado_em": item["snippet"]["publishedAt"][:10],
                "duracao_seg": seg,
                # Aproximação: até 3 minutos pode ser Short, mas só o YouTube Studio confirma o formato
                "possivel_short": seg <= 180,
                "views_total": int(item.get("statistics", {}).get("viewCount", 0)),
                "privacidade": {"public": "público", "unlisted": "não listado", "private": "privado"}.get(item.get("status", {}).get("privacyStatus"), "?"),
            }
    return saida


def salvar(raiz: Path, nome: str, dados) -> Path:
    ativo = (raiz / "meus-produtos" / ".ativo").read_text(encoding="utf-8").strip()
    pasta = raiz / "meus-produtos" / ativo / "entregas" / "youtube-analytics"
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / f"{nome}-{dt.date.today().isoformat()}.json"
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return arq


def cmd_testar(args, token, raiz):
    r = get(f"{DATA}/channels", {"part": "snippet,statistics", "mine": "true"}, token)
    itens = r.get("items", [])
    if not itens:
        raise SystemExit("A conta autorizada não tem canal. Refaça a autorização escolhendo a conta do canal.")
    c = itens[0]
    print(f"Conexão ok. Canal: {c['snippet']['title']} | inscritos: {c['statistics'].get('subscriberCount')} | vídeos: {c['statistics'].get('videoCount')}")


def cmd_lista(args, token, raiz):
    canal = get(f"{DATA}/channels", {"part": "contentDetails", "mine": "true"}, token)["items"][0]
    uploads = canal["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, pagina = [], None
    while len(ids) < args.max:
        params = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50}
        if pagina:
            params["pageToken"] = pagina
        r = get(f"{DATA}/playlistItems", params, token)
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        pagina = r.get("nextPageToken")
        if not pagina:
            break
    ids = ids[:args.max]
    det = detalhes_videos(ids, token)
    linhas = sorted(({"id": i, **det[i]} for i in ids if i in det), key=lambda x: x["publicado_em"], reverse=True)
    arq = salvar(raiz, "lista-videos", linhas)
    print(f"{len(linhas)} vídeos. Mais recentes primeiro:")
    for v in linhas[:40]:
        marca = "short?" if v["possivel_short"] else "longo "
        print(f"  {v['publicado_em']} | {marca} | {v['privacidade']:<11} | {v['duracao_seg']:>5}s | {v['views_total']:>7} views | {v['id']} | {v['titulo'][:60]}")
    print(f"JSON completo: {arq}")


def cmd_videos(args, token, raiz):
    ini, fim = periodo(args.dias)
    r = get(ANALYTICS, {
        "ids": "channel==MINE", "startDate": ini, "endDate": fim,
        "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares",
        "dimensions": "video", "sort": "-views", "maxResults": args.max,
    }, token)
    cols = [c["name"] for c in r.get("columnHeaders", [])]
    linhas = [dict(zip(cols, row)) for row in r.get("rows", [])]
    det = detalhes_videos([l["video"] for l in linhas], token)
    for l in linhas:
        l.update(det.get(l["video"], {}))
    arq = salvar(raiz, f"videos-{args.dias}d", {"periodo": [ini, fim], "videos": linhas})
    print(f"Período {ini} a {fim}. Top {len(linhas)} vídeos por visualização:")
    for l in linhas:
        print(f"  {l['views']:>6} views | {l['averageViewPercentage']:>5.1f}% assistido | +{l['subscribersGained']} inscritos | {l.get('duracao_seg', 0):>5}s | {l.get('titulo', l['video'])[:60]}")
    print(f"JSON completo: {arq}")


def cmd_origens(args, token, raiz):
    ini, fim = periodo(args.dias)
    params = {
        "ids": "channel==MINE", "startDate": ini, "endDate": fim,
        "metrics": "views,estimatedMinutesWatched", "dimensions": "insightTrafficSourceType", "sort": "-views",
    }
    if args.video:
        params["filters"] = f"video=={args.video}"
    r = get(ANALYTICS, params, token)
    linhas = [{"origem": o, "origem_pt": ORIGENS_PT.get(o, o), "views": v, "minutos": m} for o, v, m in r.get("rows", [])]
    total = sum(l["views"] for l in linhas) or 1
    arq = salvar(raiz, f"origens-{args.dias}d" + (f"-{args.video}" if args.video else ""), {"periodo": [ini, fim], "origens": linhas})
    print(f"Período {ini} a {fim}. De onde vêm as visualizações:")
    for l in linhas:
        print(f"  {l['views']:>7} ({l['views'] / total * 100:>5.1f}%) | {l['minutos']:>7} min | {l['origem_pt']}")
    print(f"JSON completo: {arq}")


def cmd_canal(args, token, raiz):
    ini, fim = periodo(args.dias)
    r = get(ANALYTICS, {
        "ids": "channel==MINE", "startDate": ini, "endDate": fim,
        "metrics": "views,estimatedMinutesWatched,subscribersGained,subscribersLost",
        "dimensions": "day", "sort": "day",
    }, token)
    cols = [c["name"] for c in r.get("columnHeaders", [])]
    linhas = [dict(zip(cols, row)) for row in r.get("rows", [])]
    arq = salvar(raiz, f"canal-{args.dias}d", {"periodo": [ini, fim], "dias": linhas})
    print(f"Período {ini} a {fim}:")
    print(f"  Visualizações: {sum(l['views'] for l in linhas)}")
    print(f"  Minutos assistidos: {sum(l['estimatedMinutesWatched'] for l in linhas)}")
    print(f"  Inscritos ganhos: {sum(l['subscribersGained'] for l in linhas)} | perdidos: {sum(l['subscribersLost'] for l in linhas)}")
    print(f"JSON completo: {arq}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Leitura do YouTube Analytics do próprio canal")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("testar")
    s = sub.add_parser("lista"); s.add_argument("--max", type=int, default=200)
    s = sub.add_parser("videos"); s.add_argument("--dias", type=int, default=28); s.add_argument("--max", type=int, default=50)
    s = sub.add_parser("origens"); s.add_argument("--dias", type=int, default=28); s.add_argument("--video")
    s = sub.add_parser("canal"); s.add_argument("--dias", type=int, default=28)
    args = p.parse_args()

    raiz = raiz_projeto()
    token = token_de_acesso(ler_env(raiz))
    {"testar": cmd_testar, "lista": cmd_lista, "videos": cmd_videos, "origens": cmd_origens, "canal": cmd_canal}[args.cmd](args, token, raiz)


if __name__ == "__main__":
    main()
