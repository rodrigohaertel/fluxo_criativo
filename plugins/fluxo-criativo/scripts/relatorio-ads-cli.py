#!/usr/bin/env python3
"""Relatório de Meta Ads via CLI oficial (meta-ads).

Uso:
  python relatorio-ads-cli.py [periodo] [inicio] [fim]

  periodo: 1=ontem (padrão), 2=últimos 7 dias, 3=últimos 30 dias, 4=personalizado
  inicio/fim: DD/MM/AAAA (apenas para periodo=4)

Exemplos:
  python relatorio-ads-cli.py 1
  python relatorio-ads-cli.py 2
  python relatorio-ads-cli.py 4 01/04/2026 30/04/2026
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.parse


# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------

def carregar_env():
    raiz = Path(__file__).parent.parent
    env_path = raiz / ".env"
    config = {}
    if not env_path.exists():
        return config
    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        config[chave.strip()] = valor.strip().strip('"').strip("'")
    return config


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------

def fmt_brl(v):
    try:
        n = float(v)
        inteiro = int(n)
        decimal = round((n - inteiro) * 100)
        inteiro_fmt = f"{inteiro:,}".replace(",", ".")
        return f"R$ {inteiro_fmt},{decimal:02d}"
    except Exception:
        return f"R$ {v}"


def fmt_num(v):
    try:
        return f"{int(float(v)):,}".replace(",", ".")
    except Exception:
        return str(v)


# ---------------------------------------------------------------------------
# Período
# ---------------------------------------------------------------------------

def calcular_periodo(escolha, inicio_custom=None, fim_custom=None):
    hoje = datetime.today()
    if escolha == "1":
        d = hoje - timedelta(days=1)
        iso = d.strftime("%Y-%m-%d")
        return iso, iso, d.strftime("%d/%m/%Y"), "yesterday"
    elif escolha == "2":
        inicio = hoje - timedelta(days=7)
        fim = hoje - timedelta(days=1)
        return inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"), "Últimos 7 dias", "last_7d"
    elif escolha == "3":
        inicio = hoje - timedelta(days=30)
        fim = hoje - timedelta(days=1)
        return inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"), "Últimos 30 dias", "last_30d"
    elif escolha == "4":
        inicio = datetime.strptime(inicio_custom, "%d/%m/%Y")
        fim = datetime.strptime(fim_custom, "%d/%m/%Y")
        label = f"{inicio_custom} a {fim_custom}"
        return inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"), label, None
    else:
        d = hoje - timedelta(days=1)
        iso = d.strftime("%Y-%m-%d")
        return iso, iso, d.strftime("%d/%m/%Y"), "yesterday"


# ---------------------------------------------------------------------------
# Busca de insights via meta-ads CLI
# ---------------------------------------------------------------------------

FIELDS = "spend,impressions,reach,clicks,ctr,cpm,cpc,actions,cost_per_action_type"


def buscar_insights_cli(access_token, account_id_num, inicio_iso, fim_iso, preset=None):
    """Tenta usar o CLI 'meta ads insights get'. Retorna dict com 'data'.

    O CLI espera AD_ACCOUNT_ID no formato act_XXXX.
    Tenta primeiro com --fields; se falhar por flag desconhecida, tenta sem.
    """
    # CLI espera prefixo act_
    account_id_full = f"act_{account_id_num}"
    env = {**os.environ, "ACCESS_TOKEN": access_token, "AD_ACCOUNT_ID": account_id_full}

    if preset:
        args_periodo = ["--date-preset", preset]
    else:
        args_periodo = ["--since", inicio_iso, "--until", fim_iso]

    args_formato = ["--format", "json", "--no-input"]

    def _tentar(cmd_base, args_extras):
        try:
            r = subprocess.run(
                cmd_base + args_periodo + args_extras + args_formato,
                env=env, capture_output=True, text=True, timeout=30
            )
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
            if r.returncode == 3:
                raise RuntimeError(
                    "Token inválido ou sem permissão (código 3). "
                    "Verifique ACCESS_TOKEN no .env e regenere o token."
                )
            if r.returncode == 4:
                raise RuntimeError(f"Erro da API Meta (código 4): {r.stderr.strip()}")
            return None
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None

    # Candidatos de comando em ordem de prioridade
    bases = [
        ["meta", "ads", "insights", "get"],
        ["meta-ads", "insights", "get"],
    ]

    for base in bases:
        # Primeira tentativa: com --fields
        resultado = _tentar(base, ["--fields", FIELDS])
        if resultado is not None:
            return resultado
        # Segunda tentativa: sem --fields (CLI com campos predefinidos)
        resultado = _tentar(base, [])
        if resultado is not None:
            return resultado

    # Fallback: módulo Python
    for mod in ["meta.ads", "meta_ads"]:
        for args_extras in [["--fields", FIELDS], []]:
            try:
                r = subprocess.run(
                    [sys.executable, "-m", mod, "insights", "get"]
                    + args_periodo + args_extras + args_formato,
                    env=env, capture_output=True, text=True, timeout=30
                )
                if r.returncode == 0 and r.stdout.strip():
                    return json.loads(r.stdout)
            except (FileNotFoundError, json.JSONDecodeError):
                continue

    raise RuntimeError(
        "Não foi possível executar o CLI 'meta ads'. "
        "Verifique se 'pip install meta-ads' foi concluído e que Python 3.12+ está no PATH."
    )


def buscar_insights_api_direta(access_token, ad_account_id, inicio_iso, fim_iso):
    """Fallback: chama a Marketing API diretamente, sem o CLI."""
    time_range = json.dumps({"since": inicio_iso, "until": fim_iso})
    params = urllib.parse.urlencode({
        "time_range": time_range,
        "fields": FIELDS,
        "level": "account",
    })
    url = f"https://graph.facebook.com/v20.0/act_{ad_account_id}/insights?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def buscar_insights(access_token, ad_account_id, inicio_iso, fim_iso, preset=None):
    """Tenta CLI primeiro; cai na API direta se CLI não estiver disponível."""
    try:
        return buscar_insights_cli(access_token, ad_account_id, inicio_iso, fim_iso, preset)
    except RuntimeError as e:
        if "pip install" in str(e) or "PATH" in str(e):
            print(f"CLI indisponível ({e}). Usando API direta como fallback.")
            return buscar_insights_api_direta(access_token, ad_account_id, inicio_iso, fim_iso)
        raise


# ---------------------------------------------------------------------------
# Montar mensagem
# ---------------------------------------------------------------------------

def montar_mensagem(dados, label_periodo, nivel="2"):
    if not dados or not dados.get("data"):
        return (f"*Relatório Meta Ads - {label_periodo}*\n\n"
                "Sem dados para o período. Verifique se há campanhas ativas.")

    d = dados["data"][0]
    linhas = [f"*Relatório Meta Ads - {label_periodo}*", ""]

    linhas += [
        "*Investimento e Alcance*",
        f"Gasto: {fmt_brl(d.get('spend', 0))}",
        f"Alcance: {fmt_num(d.get('reach', 0))}",
        f"Impressões: {fmt_num(d.get('impressions', 0))}",
    ]

    if nivel in ("2", "3", "4"):
        ctr = str(d.get("ctr", "0")).replace(".", ",")
        linhas += [
            "",
            "*Engajamento*",
            f"Cliques: {fmt_num(d.get('clicks', 0))}",
            f"CTR: {ctr}%",
            f"CPM: {fmt_brl(d.get('cpm', 0))}",
            f"CPC: {fmt_brl(d.get('cpc', 0))}",
        ]

    if nivel in ("3", "4"):
        actions = d.get("actions") or []
        conv = next((a for a in actions if a.get("action_type") in ("purchase", "lead")), None)
        if conv:
            cpa_list = d.get("cost_per_action_type") or []
            cpa = next(
                (c.get("value", 0) for c in cpa_list if c.get("action_type") == conv["action_type"]),
                0,
            )
            linhas += [
                "",
                "*Conversões*",
                f"Resultados: {fmt_num(conv.get('value', 0))}",
                f"Custo por resultado: {fmt_brl(cpa)}",
            ]

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Envio
# ---------------------------------------------------------------------------

def enviar_telegram(mensagem, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown",
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def enviar_whatsapp(mensagem, instance_id, token, client_token, numero):
    url = f"https://api.z-api.io/instances/{instance_id}/token/{token}/send-text"
    payload = json.dumps({"phone": numero, "message": mensagem}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Client-Token": client_token},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    config = carregar_env()

    # Token: prioriza ACCESS_TOKEN (CLI), depois FB_ACCESS_TOKEN_PERMANENTE, depois temporário
    access_token = (
        config.get("ACCESS_TOKEN")
        or config.get("FB_ACCESS_TOKEN_PERMANENTE")
        or config.get("FB_ACCESS_TOKEN_TEMPORARIO")
    )
    if not access_token:
        print("ERRO: Nenhum token encontrado no .env. "
              "Configure ACCESS_TOKEN ou FB_ACCESS_TOKEN_PERMANENTE.")
        sys.exit(1)

    # ID da conta: prioriza AD_ACCOUNT_ID (CLI), depois FB_AD_ACCOUNT_ID
    ad_account_id = config.get("AD_ACCOUNT_ID") or config.get("FB_AD_ACCOUNT_ID", "")
    if not ad_account_id:
        print("ERRO: AD_ACCOUNT_ID não encontrado no .env.")
        sys.exit(1)

    # Remove prefixo act_ para a API direta; o CLI lida internamente
    ad_account_id_num = ad_account_id.replace("act_", "")

    canal = config.get("RELATORIO_CANAL", "TELEGRAM").upper()
    nivel = config.get("RELATORIO_METRICAS", "2")

    # Período via argumento
    escolha = sys.argv[1] if len(sys.argv) > 1 else "1"
    inicio_custom = sys.argv[2] if len(sys.argv) > 3 else None
    fim_custom = sys.argv[3] if len(sys.argv) > 3 else None

    inicio_iso, fim_iso, label, preset = calcular_periodo(escolha, inicio_custom, fim_custom)

    print(f"Buscando insights: {label}...")

    try:
        dados = buscar_insights(access_token, ad_account_id_num, inicio_iso, fim_iso, preset)
    except Exception as e:
        print(f"ERRO ao buscar insights: {e}")
        sys.exit(1)

    mensagem = montar_mensagem(dados, label, nivel)
    print("Mensagem montada.")

    if canal == "TELEGRAM":
        bot_token = config.get("TELEGRAM_BOT_TOKEN")
        chat_id = config.get("TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            print("ERRO: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não encontrados no .env.")
            sys.exit(1)
        try:
            enviar_telegram(mensagem, bot_token, chat_id)
            print("Relatório enviado via Telegram.")
        except Exception as e:
            print(f"ERRO ao enviar Telegram: {e}")
            sys.exit(1)
    else:
        instance_id = config.get("ZAPI_INSTANCE_ID")
        token = config.get("ZAPI_TOKEN")
        client_token = config.get("ZAPI_CLIENT_TOKEN")
        numero = config.get("RELATORIO_WHATSAPP_NUMERO")
        if not all([instance_id, token, client_token, numero]):
            print("ERRO: Credenciais Z-API incompletas no .env "
                  "(ZAPI_INSTANCE_ID, ZAPI_TOKEN, ZAPI_CLIENT_TOKEN, RELATORIO_WHATSAPP_NUMERO).")
            sys.exit(1)
        try:
            enviar_whatsapp(mensagem, instance_id, token, client_token, numero)
            num_mascarado = numero[:4] + "****" + numero[-4:]
            print(f"Relatório enviado via WhatsApp para {num_mascarado}.")
        except Exception as e:
            print(f"ERRO ao enviar WhatsApp: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
