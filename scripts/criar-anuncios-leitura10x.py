# -*- coding: utf-8 -*-
import sys, io, os, json, requests
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

# IDs ja criados
CAMPAIGN_ID = "120246576536940613"
ADSET_ID    = "120246576537170613"
IMAGE_HASH  = "3d0bff4e49533352201408680108d3eb"
DESTINATION_URL = "https://vendatodosantodia.com.br/pv0622/"

COPIES = [
    {
        "nome": "AD - Argumento com Dado - Imagem",
        "headline": "3 livros por mes cabem em 15 minutos por dia",
        "body": (
            "Um livro de nao ficcao tem em media 220 paginas. Lendo no ritmo medio de adulto, "
            "voce termina em 147 minutos. Tres livros por mes exigem 441 minutos no total, "
            "menos de 15 minutos por dia.\n\n"
            "A barreira e metodo, nao tempo.\n\n"
            "A maioria das pessoas que diz nao ter tempo para ler gasta esse tempo de outra forma. "
            "Nao tem a ver com disciplina: tem a ver com nao ter uma estrutura que encaixe a leitura "
            "nos minutos que ja existem na rotina.\n\n"
            "O Metodo 30x10 resolve isso com 30 videos de 10 minutos, um por dia, com aplicacao "
            "imediata no livro que voce ja esta lendo. No 30. dia, tres livros concluidos com o "
            "mesmo tempo de antes.\n\nR$97. Acesso imediato."
        ),
    },
    {
        "nome": "AD - Contraste - Imagem",
        "headline": "O capitulo 3 e onde a maioria dos habitos de leitura termina",
        "body": (
            "A maioria tenta criar habito de leitura da mesma forma: reserva um bloco de 1 hora "
            "por dia, compra livros novos, comeca empolgado. Na semana 2, o bloco some da agenda "
            "e o livro fica parado no capitulo 3.\n\n"
            "O motivo e estrutural. A rotina de quem trabalha 8 horas por dia raramente tem um "
            "bloco de 1 hora disponivel de forma consistente.\n\n"
            "55% dos leitores brasileiros apontam falta de tempo como principal motivo para nao "
            "ler mais. O sistema que funciona parte do contrario: 10 minutos por dia, uma tecnica "
            "aplicada imediatamente, sem depender de bloco reservado na agenda.\n\n"
            "O Metodo 30x10 entrega 30 videos curtos com tecnicas de leitura para aplicar direto "
            "no livro que voce ja esta lendo. Tres livros por mes com o tempo que ja existe na rotina."
            "\n\nR$97. Acesso imediato."
        ),
    },
    {
        "nome": "AD - Especificidade e Prova - Imagem",
        "headline": "Um sistema para terminar 3 livros por mes",
        "body": (
            "A logica e verificavel antes de comprar. Um livro de nao ficcao tem em media 220 paginas. "
            "Com a tecnica certa, voce termina em menos de 3 horas de leitura total. Tres livros no "
            "mes exigem menos de 15 minutos por dia.\n\n"
            "O Metodo 30x10 estrutura esse processo em 30 videos de 10 minutos, um por dia, cada um "
            "com uma tecnica para aplicar imediatamente no livro que voce esta lendo. No 30. dia, "
            "velocidade e absorcao aumentam a ponto de concluir 3 livros com o mesmo tempo que voce ja tem.\n\n"
            "O metodo entrega consistencia de rotina, nao promessa de velocidade extrema. A meta de "
            "3 livros por mes tem respaldo matematico, nao depende de esforco adicional e cabe na "
            "agenda de quem trabalha 8 horas por dia.\n\nR$97. Acesso imediato."
        ),
    },
]

def api_post(endpoint, payload):
    payload["access_token"] = TOKEN
    resp = requests.post(f"{BASE_URL}/{endpoint}", json=payload)
    return resp.json()

results = {"anuncios": [], "erros": []}

print("Criando criativos e anuncios...")
for i, copy in enumerate(COPIES, start=1):
    print(f"  Anuncio {i}/3: {copy['nome']}...")

    creative_resp = api_post(
        f"{ACT}/adcreatives",
        {
            "name": f"Criativo - {copy['nome']}",
            "object_story_spec": {
                "page_id": PAGE_ID,
                "link_data": {
                    "image_hash": IMAGE_HASH,
                    "link": DESTINATION_URL,
                    "message": copy["body"],
                    "name": copy["headline"],
                    "call_to_action": {
                        "type": "LEARN_MORE",
                        "value": {"link": DESTINATION_URL},
                    },
                },
            },
        },
    )

    if "id" not in creative_resp:
        results["erros"].append({"etapa": f"criativo_{i}", "resposta": creative_resp})
        print(f"  ERRO criativo {i}: {creative_resp.get('error', {}).get('message', str(creative_resp))}")
        continue

    creative_id = creative_resp["id"]

    ad_resp = api_post(
        f"{ACT}/ads",
        {
            "name": copy["nome"],
            "adset_id": ADSET_ID,
            "creative": {"creative_id": creative_id},
            "status": "PAUSED",
        },
    )

    if "id" in ad_resp:
        results["anuncios"].append({"nome": copy["nome"], "ad_id": ad_resp["id"], "creative_id": creative_id})
        print(f"  OK Ad ID: {ad_resp['id']}")
    else:
        results["erros"].append({"etapa": f"ad_{i}", "resposta": ad_resp})
        print(f"  ERRO ad {i}: {ad_resp.get('error', {}).get('message', str(ad_resp))}")

output_path = Path(__file__).parent.parent / "meus-produtos" / "leitura-10x" / "entregas" / "criativos" / "campanha-criada-2026-05-05.json"
full_result = {
    "campanha": {"id": CAMPAIGN_ID},
    "conjunto": {"id": ADSET_ID},
    "imagem": {"hash": IMAGE_HASH},
    "anuncios": results["anuncios"],
    "erros": results["erros"],
}
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(full_result, f, indent=2, ensure_ascii=False)

ads_ok = len(results["anuncios"])
print(f"\n{'='*50}")
print(f"STATUS: {'criado_com_sucesso' if not results['erros'] else 'criado_parcialmente'}")
print(f"Campanha  : {CAMPAIGN_ID}")
print(f"Conjunto  : {ADSET_ID}")
print(f"Anuncios  : {ads_ok}/3 criados")
if results["erros"]:
    for e in results["erros"]:
        print(f"  Erro: {e['etapa']} - {e.get('resposta',{}).get('error',{}).get('message','')}")
print(f"{'='*50}")
