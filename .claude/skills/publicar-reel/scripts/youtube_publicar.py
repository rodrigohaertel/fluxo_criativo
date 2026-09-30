#!/usr/bin/env python3
"""Envia um Reel ao YouTube com agendamento nativo, capa, título e descrição no padrão.

Uso: py -3 youtube_publicar.py R017 "2026-09-30 10:00"            (só mostra o que vai enviar)
     py -3 youtube_publicar.py R017 "2026-09-30 10:00" --enviar   (envia de verdade)

Horário sempre de Brasília. Lê GOOGLE_OAUTH_* do .env. Nenhum valor sensível é exibido.
"""
import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
BRT = timezone(timedelta(hours=-3))


def ler_env() -> dict:
    env = {}
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def token_google(env: dict) -> str:
    corpo = urllib.parse.urlencode({
        "client_id": env["GOOGLE_OAUTH_CLIENT_ID"], "client_secret": env["GOOGLE_OAUTH_CLIENT_SECRET"],
        "refresh_token": env["GOOGLE_OAUTH_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    try:
        return json.loads(urllib.request.urlopen("https://oauth2.googleapis.com/token", data=corpo).read())["access_token"]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Autorização do Google recusada (HTTP {e.code}). Rode /google-conexao.")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        raise SystemExit('Uso: youtube_publicar.py R017 "2026-09-30 10:00" [--enviar]')
    enviar = "--enviar" in sys.argv
    quando = datetime.strptime(sys.argv[2], "%Y-%m-%d %H:%M").replace(tzinfo=BRT)
    if quando <= datetime.now(BRT) + timedelta(minutes=15):
        raise SystemExit("O horário precisa estar pelo menos 15 minutos no futuro.")

    r = subprocess.run([sys.executable, str(AQUI / "extrair.py"), sys.argv[1]],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    d = json.loads(r.stdout)
    video, capa = Path(d["video"]), Path(d["capa"]) if d["capa"] else None

    meta = {
        "snippet": {"title": d["youtube_titulo"], "description": d["youtube_descricao"], "categoryId": "27",
                    "defaultLanguage": "pt-BR", "defaultAudioLanguage": "pt-BR"},
        "status": {"privacyStatus": "private",
                   "publishAt": quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "selfDeclaredMadeForKids": False, "embeddable": True},
    }
    if not enviar:
        print(json.dumps({"previa": True, "formato": d["formato_youtube"], "video": video.name,
                          "capa": capa.name if capa else None, "agendado_brasilia": sys.argv[2], **meta},
                         ensure_ascii=False, indent=2))
        return

    at = token_google(ler_env())
    tamanho = video.stat().st_size
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(tamanho)})
    url_envio = urllib.request.urlopen(req).headers["Location"]
    print(f"Enviando {tamanho / 1e6:.0f} MB para o YouTube...", flush=True)

    class Leitor:
        def __init__(self, f):
            self.f, self.lido, self.marca = f, 0, 0

        def read(self, n=-1):
            b = self.f.read(8 * 1024 * 1024 if n == -1 else n)
            self.lido += len(b)
            if self.lido * 4 // tamanho > self.marca:
                self.marca = self.lido * 4 // tamanho
                print(f"  {self.marca * 25}%", flush=True)
            return b

    with open(video, "rb") as f:
        req = urllib.request.Request(url_envio, data=Leitor(f), method="PUT",
                                     headers={"Authorization": f"Bearer {at}", "Content-Type": "video/mp4",
                                              "Content-Length": str(tamanho)})
        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=3600).read())
        except urllib.error.HTTPError as e:
            raise SystemExit(f"Erro no envio: HTTP {e.code} {e.read().decode()[:600]}")
    vid = resp["id"]
    print(f"VIDEO_ID {vid}")
    print(f"LINK https://youtu.be/{vid}")
    print(f"STATUS {resp['status'].get('privacyStatus')} publishAt={resp['status'].get('publishAt')}")

    if capa:
        arquivo, tipo = capa, "image/png" if capa.suffix.lower() == ".png" else "image/jpeg"
        if capa.stat().st_size > 2_000_000:
            arquivo = Path(tempfile.gettempdir()) / f"capa_{d['codigo']}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(capa), "-q:v", "3", str(arquivo)], check=True)
            tipo = "image/jpeg"
        req = urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
            data=arquivo.read_bytes(), method="POST",
            headers={"Authorization": f"Bearer {at}", "Content-Type": tipo})
        try:
            urllib.request.urlopen(req)
            print("CAPA ok")
        except urllib.error.HTTPError as e:
            print(f"CAPA falhou: HTTP {e.code} {e.read().decode()[:300]}")


if __name__ == "__main__":
    main()
