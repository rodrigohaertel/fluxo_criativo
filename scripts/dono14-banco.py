#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dono14-banco.py — Reconciliação de leads direto no banco Supabase (produção),
sem depender do conector MCP (que não carrega em sessões automáticas).

Saída: leads por dia (banco x eventos dedup), nomes dos leads de ontem e hoje,
e resumo dos stages do CRM. Somente leitura (GET).

Chaves lidas do .env (nunca ficam neste arquivo):
  SUPABASE_SERVICE_KEY=...   (chave service_role ou sb_secret do projeto sizhdcrnfylimhsdfdnf)

Uso: py -3 scripts/dono14-banco.py [dias]   (padrão: 10 dias)
"""
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SUPABASE_URL = "https://sizhdcrnfylimhsdfdnf.supabase.co"
TZ_SP = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horario de verao desde 2019)


def carregar_chave():
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        env = cur / ".env"
        if env.exists():
            for linha in env.read_text(encoding="utf-8").splitlines():
                if linha.startswith("SUPABASE_SERVICE_KEY="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
        cur = cur.parent
    sys.exit("ERRO: SUPABASE_SERVICE_KEY nao encontrada no .env. "
             "Pegue em Supabase Dashboard > projeto sizhdcrnfylimhsdfdnf > Settings > API keys "
             "e adicione a linha SUPABASE_SERVICE_KEY=... no .env.")


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


def dia_sp(iso):
    """Converte timestamp ISO (UTC) para data e hora de Sao Paulo."""
    s = iso.replace("Z", "+00:00")
    # PostgREST pode devolver fracao de segundo com mais de 6 digitos; normaliza
    if "." in s:
        base, resto = s.split(".", 1)
        tzpos = max(resto.find("+"), resto.find("-"))
        frac, tz = (resto[:tzpos], resto[tzpos:]) if tzpos > 0 else (resto, "+00:00")
        s = f"{base}.{frac[:6].ljust(6, '0')}{tz}"
    dt = datetime.fromisoformat(s).astimezone(TZ_SP)
    return dt


dias = int(sys.argv[1]) if len(sys.argv) > 1 else 10
inicio_utc = (datetime.now(TZ_SP) - timedelta(days=dias)).astimezone(timezone.utc)
inicio_iso = inicio_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00")

# ---------------- 1. contact_submissions (a verdade dos leads)
subs = get("contact_submissions", {
    "select": "name,whatsapp,email,source,created_at",
    "or": "(source.ilike.mentoria*,source.ilike.sess*)",
    "created_at": f"gte.{inicio_iso}",
    "order": "created_at.asc",
})

# ---------------- 2. lead_events (dedup por event_id)
evs = get("lead_events", {
    "select": "event_id,created_at,email_hash_prefix",
    "event_name": "eq.Lead",
    "created_at": f"gte.{inicio_iso}",
})

# ---------------- 3. crm_cards (stages)
cards = get("crm_cards", {
    "select": "stage,faturamento_medio,submission_id",
    "deleted_at": "is.null",
})

# ---------------- agregacoes
por_dia = defaultdict(lambda: {"banco": 0, "a": 0, "b": 0})
for s in subs:
    d = dia_sp(s["created_at"])
    k = d.strftime("%d/%m")
    por_dia[k]["banco"] += 1
    if (s.get("source") or "").lower().startswith("sess"):
        por_dia[k]["b"] += 1
    else:
        por_dia[k]["a"] += 1

ev_por_dia = defaultdict(set)
for e in evs:
    ev_por_dia[dia_sp(e["created_at"]).strftime("%d/%m")].add(e["event_id"])

# ---------------- eventos ORFAOS (explicam a diferenca evento x lead)
# Quando o Rodrigo unifica dois cadastros do mesmo lead e apaga o duplicado, ou
# apaga um cadastro falso, a linha some de contact_submissions mas o evento fica
# gravado em lead_events. Sem isso, a rotina reportava "divergencia" e pedia
# investigacao todo dia (aconteceu em 10/08, lead falso, e 15/08, unificacao).
# O casamento e por prefixo de hash do e-mail, unico vinculo que a tabela guarda.
HASH_N = 16  # tamanho gravado em lead_events.email_hash_prefix
hashes_vivos = {
    hashlib.sha256((s["email"] or "").strip().lower().encode()).hexdigest()[:HASH_N]
    for s in subs if s.get("email")
}
orfaos_por_dia = defaultdict(set)
for e in evs:
    ph = (e.get("email_hash_prefix") or "")[:HASH_N]
    if ph and ph not in hashes_vivos:
        orfaos_por_dia[dia_sp(e["created_at"]).strftime("%d/%m")].add(e["event_id"])

# REGRA DA ROTINA (06/08/2026): a serie de metricas termina em ONTEM. O dia de
# hoje esta em aberto (lead pode entrar a qualquer hora) e contar um parcial como
# dia normal distorce a media e o CPL.
hoje_sp = datetime.now(TZ_SP).date()
ontem_sp = hoje_sp - timedelta(days=1)
print("=" * 66)
print(f"BANCO SUPABASE (direto, sem conector) | consultado {datetime.now(TZ_SP).strftime('%d/%m %H:%M')} SP")
print("=" * 66)
print(f"SERIE (somente dias FECHADOS, termina em {ontem_sp.strftime('%d/%m')}):")
print(f"{'dia':<8}{'leads_banco':>12}{'funil_A':>9}{'funil_B':>9}{'eventos_dedup':>15}{'orfaos':>8}")
total_orfaos = 0
for i in range(dias, 0, -1):
    d = (hoje_sp - timedelta(days=i)).strftime("%d/%m")
    v = por_dia.get(d, {"banco": 0, "a": 0, "b": 0})
    orf = len(orfaos_por_dia.get(d, set()))
    total_orfaos += orf
    print(f"{d:<8}{v['banco']:>12}{v['a']:>9}{v['b']:>9}"
          f"{len(ev_por_dia.get(d, set())):>15}{(orf or '-'):>8}")
if total_orfaos:
    print(f"\n  ORFAOS: {total_orfaos} evento(s) sem lead correspondente no banco. NAO e divergencia")
    print("  nem lead perdido: e cadastro que o Rodrigo apagou (falso) ou unificou (duplicado),")
    print("  cujo evento continua gravado em lead_events. O numero oficial e SEMPRE leads_banco.")

print("-" * 66)
print(f"LEADS DO DIA FECHADO ({ontem_sp.strftime('%d/%m')}) (nome, hora SP, funil):")
algum = False
for s in subs:
    d = dia_sp(s["created_at"])
    if d.date() == ontem_sp:
        funil = "B" if (s.get("source") or "").lower().startswith("sess") else "A"
        print(f"  {d.strftime('%d/%m %H:%M')}  [{funil}]  {s.get('name','?')}")
        algum = True
if not algum:
    print("  (nenhum)")

print("-" * 66)
stages = defaultdict(int)
for c in cards:
    stages[str(c.get("stage"))] += 1
print("CRM (stages, cards nao deletados):", dict(sorted(stages.items(), key=lambda kv: -kv[1])))
print("=" * 66)
print("Lembretes: leads reais = contact_submissions; eventos com count DISTINCT")
print("de event_id (o funil /mentoria emite 2 linhas por lead, e dedup normal).")
