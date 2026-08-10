#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dono14-comercial.py — Funil comercial do CRM (crm_cards + tags) direto do Supabase.

Somente leitura (GET). Chave lida do .env (SUPABASE_SERVICE_KEY).

Uso: py -3 scripts/dono14-comercial.py
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SUPABASE_URL = "https://sizhdcrnfylimhsdfdnf.supabase.co"


def carregar_chave():
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        env = cur / ".env"
        if env.exists():
            for linha in env.read_text(encoding="utf-8").splitlines():
                if linha.startswith("SUPABASE_SERVICE_KEY="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
        cur = cur.parent
    sys.exit("ERRO: SUPABASE_SERVICE_KEY nao encontrada no .env.")


KEY = carregar_chave()


def get(tabela, params):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}?" + urllib.parse.urlencode(params, safe="*.,()")
    req = urllib.request.Request(url, headers={
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


cards = get("crm_cards", {
    "select": "id,stage,valor_contrato,faturamento_medio,uf,motivo_perda,submission_id",
    "deleted_at": "is.null",
})
subs = get("contact_submissions", {"select": "id,name"})
subs_by_id = {s["id"]: s.get("name") for s in subs}
tags = get("crm_tags", {"select": "id,name"})
tags_by_id = {t["id"]: t.get("name") for t in tags}
card_tags = get("crm_card_tags", {"select": "card_id,tag_id"})

tags_por_card = {}
for ct in card_tags:
    tags_por_card.setdefault(ct["card_id"], []).append(tags_by_id.get(ct["tag_id"], "?"))

print("=" * 70)
print("CRM COMERCIAL (crm_cards + tags) — direto do banco")
print("=" * 70)
print(f"Total de cards ativos: {len(cards)}")

total_receita = 0.0
vendas_dono14 = 0
vendas_painel = 0
for c in cards:
    t = tags_por_card.get(c["id"], [])
    if any("dono 14" in x.lower() for x in t):
        vendas_dono14 += 1
        total_receita += float(c.get("valor_contrato") or 0)
    if any("painel do dono" in x.lower() for x in t):
        vendas_painel += 1

print(f"Vendas com tag 'Dono 14%': {vendas_dono14} | receita somada: R$ {total_receita:.2f}")
print(f"Vendas com tag 'Painel do Dono': {vendas_painel}")
print("-" * 70)
print("Cards ordenados por valor de contrato (maior primeiro):")
for c in sorted(cards, key=lambda x: -(x.get("valor_contrato") or 0)):
    if not c.get("valor_contrato"):
        continue
    nome = subs_by_id.get(c.get("submission_id"), "?")
    t = ", ".join(tags_por_card.get(c["id"], []))
    print(f"  {nome:<30} stage={c['stage']:<20} valor=R$ {c['valor_contrato']:.2f}  tags=[{t}]")
print("-" * 70)
print("Motivos de perda (stage=perdido, com motivo preenchido):")
motivos = {}
for c in cards:
    if c.get("stage") == "perdido" and c.get("motivo_perda"):
        motivos[c["motivo_perda"]] = motivos.get(c["motivo_perda"], 0) + 1
for m, n in sorted(motivos.items(), key=lambda kv: -kv[1]):
    print(f"  {n:>3}x  {m}")
print("=" * 70)
