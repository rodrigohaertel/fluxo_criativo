#!/usr/bin/env python3
"""Autorização única da conta Google (YouTube Analytics, YouTube Data e Google Ads).

Lê GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET do .env, abre o navegador
para o dono da conta autorizar e grava GOOGLE_OAUTH_REFRESH_TOKEN no .env.
Nenhum valor sensível é exibido no terminal. Só usa a biblioteca padrão do Python.
"""
import http.server
import json
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

PORTA = 8765
REDIRECT_URI = f"http://127.0.0.1:{PORTA}/"
ESCOPOS = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/adwords",
]


def caminho_env() -> Path:
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        candidato = cur / ".env"
        if candidato.exists():
            return candidato
        cur = cur.parent
    raise SystemExit("Arquivo .env não encontrado na raiz do projeto.")


def ler_env(path: Path) -> dict:
    dados = {}
    for linha in path.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            chave, valor = linha.split("=", 1)
            dados[chave.strip()] = valor.strip().strip('"').strip("'")
    return dados


def gravar_env(path: Path, chave: str, valor: str) -> None:
    linhas = path.read_text(encoding="utf-8").splitlines()
    nova = f"{chave}={valor}"
    for i, linha in enumerate(linhas):
        if linha.startswith(f"{chave}="):
            linhas[i] = nova
            break
    else:
        linhas.append(nova)
    path.write_text("\n".join(linhas) + "\n", encoding="utf-8")


class Receptor(http.server.BaseHTTPRequestHandler):
    resultado = {}

    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params or "error" in params:
            Receptor.resultado = {k: v[0] for k, v in params.items()}
            corpo = "<h2>Autorização recebida. Pode fechar esta aba e voltar ao Severino.</h2>"
        else:
            corpo = "<h2>Aguardando a autorização.</h2>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo.encode("utf-8"))

    def log_message(self, *args):
        pass


def importar_json(env_path: Path, arquivo: Path) -> None:
    """Copia o ID e a chave secreta do JSON baixado do Google Cloud para o .env e apaga o JSON."""
    if not arquivo.exists():
        raise SystemExit(f"Arquivo não encontrado: {arquivo}")
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    bloco = dados.get("installed") or dados.get("web") or {}
    if not bloco.get("client_id") or not bloco.get("client_secret"):
        raise SystemExit("O arquivo não parece ser a credencial OAuth baixada do Google Cloud.")
    gravar_env(env_path, "GOOGLE_OAUTH_CLIENT_ID", bloco["client_id"])
    gravar_env(env_path, "GOOGLE_OAUTH_CLIENT_SECRET", bloco["client_secret"])
    arquivo.unlink()
    print("GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET salvos no .env (valores mascarados).")
    print("O arquivo JSON baixado foi apagado.")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    env_path = caminho_env()
    if len(sys.argv) == 3 and sys.argv[1] == "--importar":
        importar_json(env_path, Path(sys.argv[2]))
    env = ler_env(env_path)
    client_id = env.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = env.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit(
            "Faltam GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET no .env. "
            "Rode /google-conexao para o passo a passo."
        )

    estado = secrets.token_urlsafe(24)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(ESCOPOS),
        "access_type": "offline",
        "prompt": "consent",
        "state": estado,
    })

    servidor = http.server.HTTPServer(("127.0.0.1", PORTA), Receptor)
    servidor.timeout = 300
    print("Abrindo o navegador para você autorizar a conta Google do canal.")
    print("Se o canal for de uma conta de marca, escolha a conta de marca na tela do Google.")
    webbrowser.open(url)

    # O navegador pode pedir outros caminhos (favicon) antes do retorno com o código
    limite = time.time() + 300
    servidor.timeout = 5
    while not Receptor.resultado and time.time() < limite:
        servidor.handle_request()
    servidor.server_close()

    res = Receptor.resultado
    if not res:
        raise SystemExit("Tempo esgotado sem autorização. Rode o script de novo.")
    if "error" in res:
        raise SystemExit(f"Autorização negada pelo Google: {res['error']}")
    if res.get("state") != estado:
        raise SystemExit("Resposta inválida (estado não confere). Rode o script de novo.")

    corpo = urllib.parse.urlencode({
        "code": res["code"],
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=corpo)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tokens = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"O Google recusou a troca do código (HTTP {e.code}). Confira o client ID e o secret no .env.")

    refresh = tokens.get("refresh_token")
    if not refresh:
        raise SystemExit("O Google não devolveu a autorização permanente. Rode o script de novo.")

    gravar_env(env_path, "GOOGLE_OAUTH_REFRESH_TOKEN", refresh)
    print("Autorização concluída. GOOGLE_OAUTH_REFRESH_TOKEN salvo no .env (valor mascarado).")


if __name__ == "__main__":
    main()
