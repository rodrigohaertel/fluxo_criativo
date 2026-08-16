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
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SUPABASE_URL = "https://sizhdcrnfylimhsdfdnf.supabase.co"
TZ_SP = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horario de verao desde 2019)
RAIZ_PROD = Path(__file__).resolve().parent.parent / "meus-produtos" / "dono-14" / "trafego"


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
FALSOS = RAIZ_PROD / "cadastros-falsos.json"
hashes_falsos = set()
if FALSOS.exists():
    try:
        hashes_falsos = {f["hash"] for f in json.loads(FALSOS.read_text(encoding="utf-8"))["falsos"]}
    except Exception as e:  # noqa: BLE001
        print(f"[AVISO] cadastros-falsos.json ilegivel ({e}); nenhum falso excluido.", file=sys.stderr)

orfaos_por_dia = defaultdict(set)      # ressubmissao: CONTA como captacao
falsos_por_dia = defaultdict(set)      # falso/spam: nao conta em lugar nenhum
for e in evs:
    ph = (e.get("email_hash_prefix") or "")[:HASH_N]
    if not ph or ph in hashes_vivos:
        continue
    k = dia_sp(e["created_at"]).strftime("%d/%m")
    (falsos_por_dia if ph in hashes_falsos else orfaos_por_dia)[k].add(e["event_id"])

# REGRA DE CONTAGEM (decisao do Rodrigo, 16/08/2026)
#   CAPTACAO   = cadastros que a midia entregou. Inclui ressubmissao (a mesma
#                pessoa preenchendo de novo: o anuncio pagou por aquilo e o
#                reengajamento tem valor real). Exclui falso/spam.
#                E o numero OFICIAL: manda no CPL, na regua e no gatilho.
#   LEAD NOVO  = pessoas unicas. Serve para projecao comercial e CAC.
# Ressubmissao viva no banco ja entra sozinha em `banco` (sao linhas separadas);
# a apagada volta pela contagem de orfaos.
def norm_tel(t):
    return re.sub(r"\D", "", t or "")[-11:]


ident_por_dia = defaultdict(set)
for s in subs:
    k = dia_sp(s["created_at"]).strftime("%d/%m")
    ident_por_dia[k].add((s.get("email") or "").strip().lower() or norm_tel(s.get("whatsapp")))

# REGRA DA ROTINA (06/08/2026): a serie de metricas termina em ONTEM. O dia de
# hoje esta em aberto (lead pode entrar a qualquer hora) e contar um parcial como
# dia normal distorce a media e o CPL.
hoje_sp = datetime.now(TZ_SP).date()
ontem_sp = hoje_sp - timedelta(days=1)
print("=" * 66)
print(f"BANCO SUPABASE (direto, sem conector) | consultado {datetime.now(TZ_SP).strftime('%d/%m %H:%M')} SP")
print("=" * 66)
print(f"SERIE (somente dias FECHADOS, termina em {ontem_sp.strftime('%d/%m')}):")
print(f"{'dia':<8}{'CAPTACAO':>10}{'lead_novo':>11}{'funil_A':>9}{'funil_B':>9}"
      f"{'eventos':>9}{'resub':>7}{'falso':>7}")
tot_cap = tot_novo = tot_resub = tot_falso = 0
for i in range(dias, 0, -1):
    d = (hoje_sp - timedelta(days=i)).strftime("%d/%m")
    v = por_dia.get(d, {"banco": 0, "a": 0, "b": 0})
    resub = len(orfaos_por_dia.get(d, set()))     # ressubmissao apagada: volta na captacao
    falso = len(falsos_por_dia.get(d, set()))     # falso: nao conta
    captacao = v["banco"] + resub
    novos = len(ident_por_dia.get(d, set()))      # pessoas unicas no dia
    tot_cap += captacao; tot_novo += novos; tot_resub += resub; tot_falso += falso
    print(f"{d:<8}{captacao:>10}{novos:>11}{v['a']:>9}{v['b']:>9}"
          f"{len(ev_por_dia.get(d, set())):>9}{(resub or '-'):>7}{(falso or '-'):>7}")
print(f"{'TOTAL':<8}{tot_cap:>10}{tot_novo:>11}")
print("\n  CAPTACAO = numero OFICIAL (CPL, regua, gatilho). Inclui ressubmissao, porque")
print("  a midia pagou por aquele cadastro, e exclui falso/spam.")
print("  lead_novo = pessoas unicas no dia, para projecao comercial e CAC.")
if tot_resub:
    print(f"  resub: {tot_resub} cadastro(s) que o Rodrigo unificou e apagou; o evento sobrou e")
    print("  por isso volta para a captacao. Nao e divergencia, nao investigar.")
if tot_falso:
    print(f"  falso: {tot_falso} evento(s) de cadastro falso (lista em cadastros-falsos.json).")

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
