# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

"""
Script de criacao de campanha Meta Ads - Leitura 10x
Executa upload de imagem + criação de campanha, conjunto e 3 anúncios.
Todos os itens criados com status PAUSED.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Carregar .env
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
INSTAGRAM_USER_ID = env.get("FB_INSTAGRAM_USER_ID", "")
PIXEL_ID = env.get("META_PIXEL_ID", "")
BASE_URL = "https://graph.facebook.com/v22.0"
ACT = f"act_{AD_ACCOUNT_ID}"

IMAGE_PATH = Path(__file__).parent.parent / "meus-produtos" / "leitura-10x" / "entregas" / "criativos" / "ChatGPT Image 5 de mai. de 2026, 17_08_25.png"
DESTINATION_URL = "https://vendatodosantodia.com.br/pv0622/"

COPIES = [
    {
        "nome": "AD - Argumento com Dado - Imagem",
        "headline": "3 livros por mês cabem em 15 minutos por dia",
        "body": (
            "Um livro de não ficção tem em média 220 páginas. Lendo no ritmo médio de adulto, "
            "você termina em 147 minutos. Três livros por mês exigem 441 minutos no total, "
            "menos de 15 minutos por dia.\n\n"
            "A barreira é método, não tempo.\n\n"
            "A maioria das pessoas que diz não ter tempo para ler gasta esse tempo de outra forma. "
            "Não tem a ver com disciplina: tem a ver com não ter uma estrutura que encaixe a leitura "
            "nos minutos que já existem na rotina.\n\n"
            "O Método 30×10 resolve isso com 30 vídeos de 10 minutos, um por dia, com aplicação "
            "imediata no livro que você já está lendo. No 30.° dia, três livros concluídos com o "
            "mesmo tempo de antes.\n\nR$97. Acesso imediato."
        ),
    },
    {
        "nome": "AD - Contraste - Imagem",
        "headline": "O capítulo 3 é onde a maioria dos hábitos de leitura termina",
        "body": (
            "A maioria tenta criar hábito de leitura da mesma forma: reserva um bloco de 1 hora "
            "por dia, compra livros novos, começa empolgado. Na semana 2, o bloco some da agenda "
            "e o livro fica parado no capítulo 3.\n\n"
            "O motivo é estrutural. A rotina de quem trabalha 8 horas por dia raramente tem um "
            "bloco de 1 hora disponível de forma consistente.\n\n"
            "55% dos leitores brasileiros apontam falta de tempo como principal motivo para não "
            "ler mais. O sistema que funciona parte do contrário: 10 minutos por dia, uma técnica "
            "aplicada imediatamente, sem depender de bloco reservado na agenda.\n\n"
            "O Método 30×10 entrega 30 vídeos curtos com técnicas de leitura para aplicar direto "
            "no livro que você já está lendo. Três livros por mês com o tempo que já existe na rotina."
            "\n\nR$97. Acesso imediato."
        ),
    },
    {
        "nome": "AD - Especificidade e Prova - Imagem",
        "headline": "Um sistema para terminar 3 livros por mês",
        "body": (
            "A lógica é verificável antes de comprar. Um livro de não ficção tem em média 220 páginas. "
            "Com a técnica certa, você termina em menos de 3 horas de leitura total. Três livros no "
            "mês exigem menos de 15 minutos por dia.\n\n"
            "O Método 30×10 estrutura esse processo em 30 vídeos de 10 minutos, um por dia, cada um "
            "com uma técnica para aplicar imediatamente no livro que você está lendo. No 30.° dia, "
            "velocidade e absorção aumentam a ponto de concluir 3 livros com o mesmo tempo que você já tem.\n\n"
            "O método entrega consistência de rotina, não promessa de velocidade extrema. A meta de "
            "3 livros por mês tem respaldo matemático, não depende de esforço adicional e cabe na "
            "agenda de quem trabalha 8 horas por dia.\n\nR$97. Acesso imediato."
        ),
    },
]

results = {
    "imagem": {},
    "campanha": {},
    "conjunto": {},
    "anuncios": [],
    "erros": [],
}


def api_post(endpoint, payload):
    payload["access_token"] = TOKEN
    resp = requests.post(f"{BASE_URL}/{endpoint}", json=payload)
    return resp.json()


def api_post_files(endpoint, data, files):
    data["access_token"] = TOKEN
    resp = requests.post(f"{BASE_URL}/{endpoint}", data=data, files=files)
    return resp.json()


# ─── 1. Upload da imagem ────────────────────────────────────────────────────
print("⏳ Passo 1/5: upload da imagem criativa...")
with open(IMAGE_PATH, "rb") as img_file:
    resp = api_post_files(
        f"{ACT}/adimages",
        data={},
        files={"filename": ("criativo-leitura10x.png", img_file, "image/png")},
    )

if "images" in resp:
    image_hash = list(resp["images"].values())[0]["hash"]
    results["imagem"] = {"hash": image_hash, "status": "ok"}
    print(f"   ✅ Imagem enviada. Hash: {image_hash}")
else:
    results["erros"].append({"etapa": "upload_imagem", "resposta": resp})
    print(f"   ❌ Erro no upload: {resp}")
    print(json.dumps(results, indent=2))
    exit(1)

# ─── 2. Criar campanha ──────────────────────────────────────────────────────
print("⏳ Passo 2/5: criando campanha...")
camp_resp = api_post(
    f"{ACT}/campaigns",
    {
        "name": "Perpétuo - Leitura 10x - 1-1-3 - 2026-05-05",
        "objective": "OUTCOME_SALES",
        "status": "PAUSED",
        "special_ad_categories": [],
        "buying_type": "AUCTION",
        "daily_budget": 5000,  # R$50,00 em centavos
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    },
)

if "id" in camp_resp:
    campaign_id = camp_resp["id"]
    results["campanha"] = {"id": campaign_id, "status": "ok"}
    print(f"   ✅ Campanha criada. ID: {campaign_id}")
else:
    results["erros"].append({"etapa": "criar_campanha", "resposta": camp_resp})
    print(f"   ❌ Erro ao criar campanha: {camp_resp}")
    print(json.dumps(results, indent=2))
    exit(1)

# ─── 3. Criar conjunto ──────────────────────────────────────────────────────
print("⏳ Passo 3/5: criando conjunto de anúncios...")
start_time = (datetime.now(timezone(timedelta(hours=-3))) + timedelta(hours=1)).replace(
    minute=0, second=0, microsecond=0
)
start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S-03:00")

adset_resp = api_post(
    f"{ACT}/adsets",
    {
        "name": "AS - Advantage+ - Brasil",
        "campaign_id": campaign_id,
        "status": "PAUSED",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "billing_event": "IMPRESSIONS",
        "promoted_object": {
            "pixel_id": PIXEL_ID,
            "custom_event_type": "PURCHASE",
        },
        "targeting": {
            "geo_locations": {"countries": ["BR"]},
            "age_min": 18,
            "age_max": 65,
        },
        "attribution_spec": [{"event_type": "CLICK_THROUGH", "window_days": 7}],
        "destination_type": "WEBSITE",
        "start_time": start_time_str,
    },
)

if "id" in adset_resp:
    adset_id = adset_resp["id"]
    results["conjunto"] = {"id": adset_id, "status": "ok"}
    print(f"   ✅ Conjunto criado. ID: {adset_id}")
else:
    results["erros"].append({"etapa": "criar_conjunto", "resposta": adset_resp})
    print(f"   ❌ Erro ao criar conjunto: {adset_resp}")
    # reverter campanha
    requests.delete(
        f"{BASE_URL}/{campaign_id}",
        params={"access_token": TOKEN},
    )
    print("   Campanha revertida.")
    print(json.dumps(results, indent=2))
    exit(1)

# ─── 4+5. Criar criativos e anúncios ────────────────────────────────────────
print("⏳ Passo 4/5: criando criativos e anúncios...")
for i, copy in enumerate(COPIES, start=1):
    print(f"   Anúncio {i}/3: {copy['nome']}...")

    # Criar ad creative
    creative_resp = api_post(
        f"{ACT}/adcreatives",
        {
            "name": f"Criativo - {copy['nome']}",
            "object_story_spec": {
                "page_id": PAGE_ID,
                "link_data": {
                    "image_hash": image_hash,
                    "link": DESTINATION_URL,
                    "message": copy["body"],
                    "name": copy["headline"],
                    "call_to_action": {
                        "type": "LEARN_MORE",
                        "value": {"link": DESTINATION_URL},
                    },
                },
            },
            "instagram_actor_id": INSTAGRAM_USER_ID,
        },
    )

    if "id" not in creative_resp:
        results["erros"].append(
            {"etapa": f"criar_criativo_{i}", "nome": copy["nome"], "resposta": creative_resp}
        )
        print(f"   ❌ Erro no criativo {i}: {creative_resp}")
        continue

    creative_id = creative_resp["id"]

    # Criar ad
    ad_resp = api_post(
        f"{ACT}/ads",
        {
            "name": copy["nome"],
            "adset_id": adset_id,
            "creative": {"creative_id": creative_id},
            "status": "PAUSED",
        },
    )

    if "id" in ad_resp:
        results["anuncios"].append(
            {
                "nome": copy["nome"],
                "ad_id": ad_resp["id"],
                "creative_id": creative_id,
                "status": "ok",
            }
        )
        print(f"   ✅ Anúncio criado. ID: {ad_resp['id']}")
    else:
        results["erros"].append(
            {"etapa": f"criar_ad_{i}", "nome": copy["nome"], "resposta": ad_resp}
        )
        print(f"   ❌ Erro no anúncio {i}: {ad_resp}")

# ─── Resultado final ─────────────────────────────────────────────────────────
print("\n⏳ Passo 5/5: consolidando resultado...")
output_path = Path(__file__).parent.parent / "meus-produtos" / "leitura-10x" / "entregas" / "criativos" / "campanha-criada-2026-05-05.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

ads_ok = len([a for a in results["anuncios"] if a["status"] == "ok"])
print(f"\n{'=' * 60}")
print(f"STATUS: {'criado_com_sucesso' if not results['erros'] else 'criado_parcialmente'}")
print(f"Campanha ID : {results['campanha'].get('id', 'N/A')}")
print(f"Conjunto ID : {results['conjunto'].get('id', 'N/A')}")
print(f"Anúncios OK : {ads_ok}/3")
if results["erros"]:
    print(f"Erros       : {len(results['erros'])}")
    for e in results["erros"]:
        print(f"  - {e['etapa']}: {e.get('resposta', {}).get('error', {}).get('message', str(e))}")
print(f"Resultado   : {output_path}")
print(f"{'=' * 60}")
