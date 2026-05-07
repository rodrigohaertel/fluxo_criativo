# -*- coding: utf-8 -*-
import sys, io, json, requests
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

env_path = Path(__file__).parent.parent / ".env"
env = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

TOKEN = env.get("FB_ACCESS_TOKEN_PERMANENTE", "")
AD_ACCOUNT_ID = env.get("FB_AD_ACCOUNT_ID", "")
PAGE_ID = env.get("FB_PAGE_ID", "")
BASE_URL = "https://graph.facebook.com/v22.0"
ACT = f"act_{AD_ACCOUNT_ID}"

IMAGE_HASH = "3d0bff4e49533352201408680108d3eb"
BASE_URL_DEST = "https://vendatodosantodia.com.br/pv0622/"
UTM_PARAMS = "utm_source=meta-ads&utm_campaign={{campaign.name}}|{{campaign.id}}&utm_medium={{adset.name}}|{{adset.id}}&utm_content={{ad.name}}|{{ad.id}}&utm_term={{placement}}"
FULL_URL = BASE_URL_DEST + ("?" if "?" not in BASE_URL_DEST else "&") + UTM_PARAMS

ADS = [
    {"ad_id": "120246576556320613", "nome": "AD - Argumento com Dado - Imagem",
     "headline": "3 livros por mes cabem em 15 minutos por dia",
     "body": ("Um livro de nao ficcao tem em media 220 paginas. Lendo no ritmo medio de adulto, "
              "voce termina em 147 minutos. Tres livros por mes exigem 441 minutos no total, "
              "menos de 15 minutos por dia.\n\nA barreira e metodo, nao tempo.\n\n"
              "A maioria das pessoas que diz nao ter tempo para ler gasta esse tempo de outra forma. "
              "Nao tem a ver com disciplina: tem a ver com nao ter uma estrutura que encaixe a leitura "
              "nos minutos que ja existem na rotina.\n\nO Metodo 30x10 resolve isso com 30 videos de "
              "10 minutos, um por dia, com aplicacao imediata no livro que voce ja esta lendo. No 30. dia, "
              "tres livros concluidos com o mesmo tempo de antes.\n\nR$97. Acesso imediato.")},
    {"ad_id": "120246576557170613", "nome": "AD - Contraste - Imagem",
     "headline": "O capitulo 3 e onde a maioria dos habitos de leitura termina",
     "body": ("A maioria tenta criar habito de leitura da mesma forma: reserva um bloco de 1 hora "
              "por dia, compra livros novos, comeca empolgado. Na semana 2, o bloco some da agenda "
              "e o livro fica parado no capitulo 3.\n\nO motivo e estrutural. A rotina de quem trabalha "
              "8 horas por dia raramente tem um bloco de 1 hora disponivel de forma consistente.\n\n"
              "55% dos leitores brasileiros apontam falta de tempo como principal motivo para nao ler mais. "
              "O sistema que funciona parte do contrario: 10 minutos por dia, uma tecnica aplicada "
              "imediatamente, sem depender de bloco reservado na agenda.\n\nO Metodo 30x10 entrega 30 "
              "videos curtos com tecnicas de leitura para aplicar direto no livro que voce ja esta lendo. "
              "Tres livros por mes com o tempo que ja existe na rotina.\n\nR$97. Acesso imediato.")},
    {"ad_id": "120246576557680613", "nome": "AD - Especificidade e Prova - Imagem",
     "headline": "Um sistema para terminar 3 livros por mes",
     "body": ("A logica e verificavel antes de comprar. Um livro de nao ficcao tem em media 220 paginas. "
              "Com a tecnica certa, voce termina em menos de 3 horas de leitura total. Tres livros no mes "
              "exigem menos de 15 minutos por dia.\n\nO Metodo 30x10 estrutura esse processo em 30 videos "
              "de 10 minutos, um por dia, cada um com uma tecnica para aplicar imediatamente no livro que "
              "voce esta lendo. No 30. dia, velocidade e absorcao aumentam a ponto de concluir 3 livros "
              "com o mesmo tempo que voce ja tem.\n\nO metodo entrega consistencia de rotina, nao promessa "
              "de velocidade extrema. A meta de 3 livros por mes tem respaldo matematico, nao depende de "
              "esforco adicional e cabe na agenda de quem trabalha 8 horas por dia.\n\nR$97. Acesso imediato.")},
]

def api_post(endpoint, payload):
    payload["access_token"] = TOKEN
    resp = requests.post(f"{BASE_URL}/{endpoint}", json=payload)
    return resp.json()

print(f"URL final com UTMs:\n{FULL_URL}\n")

for ad in ADS:
    print(f"Atualizando: {ad['nome']}...")

    creative_resp = api_post(f"{ACT}/adcreatives", {
        "name": f"Criativo UTM - {ad['nome']}",
        "object_story_spec": {
            "page_id": PAGE_ID,
            "link_data": {
                "image_hash": IMAGE_HASH,
                "link": FULL_URL,
                "message": ad["body"],
                "name": ad["headline"],
                "call_to_action": {"type": "LEARN_MORE", "value": {"link": FULL_URL}},
            },
        },
    })

    if "id" not in creative_resp:
        print(f"  ERRO criativo: {creative_resp.get('error', {}).get('message', str(creative_resp))}")
        continue

    new_creative_id = creative_resp["id"]

    ad_update = requests.post(
        f"{BASE_URL}/{ad['ad_id']}",
        json={"creative": {"creative_id": new_creative_id}, "access_token": TOKEN},
    ).json()

    if "success" in ad_update or "id" in ad_update:
        print(f"  OK — criativo {new_creative_id} vinculado ao ad {ad['ad_id']}")
    else:
        print(f"  ERRO update ad: {ad_update.get('error', {}).get('message', str(ad_update))}")

print("\nConcluido.")
