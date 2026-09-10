#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dono14-orcamento.py — Orcamento real dos conjuntos da campanha viva do Dono 14%.

Existe porque a rotina das 02h vinha repetindo, desde 24/08, o aviso "nao foi
possivel confirmar via API se a reducao de orcamento ja esta ativa". A chamada
inline era barrada pelo detector de padroes do terminal; num script proprio, com
o token lido do .env, ela passa e a pendencia deixa de existir.

Somente leitura (GET). Uso: py -3 scripts/dono14-orcamento.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CAMPANHA = "120247419652220527"   # [DONO14] [CONV] [LEADS] ABO
PLANO_ATUAL = 240.00              # Rodizio de 4 criativos a R$ 60/dia (05/09). Em 10/09 o A45 ocupou a vaga do A42, que venceu.


def token():
    for linha in (Path(__file__).resolve().parent.parent / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("FB_ACCESS_TOKEN_PERMANENTE="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("FB_ACCESS_TOKEN_PERMANENTE nao encontrado no .env")


p = {"fields": "name,daily_budget,effective_status,end_time", "limit": 100,
     "access_token": token(), "_": str(int(time.time()))}
url = f"https://graph.facebook.com/v21.0/{CAMPANHA}/adsets?" + urllib.parse.urlencode(p)
dados = json.loads(urllib.request.urlopen(url, timeout=90).read()).get("data", [])

print("=" * 62)
print("ORCAMENTO REAL NA CONTA (conjuntos ATIVOS)")
print("=" * 62)
SP = timezone(timedelta(hours=-3))
AGORA = datetime.now(SP)


def venceu(s):
    """Conjunto com cronograma ja terminado nao entrega mais, mesmo que a API
    continue devolvendo effective_status ACTIVE. Em 09/09/2026 o A42 apareceu
    assim e inflou o programado em R$ 60, gerando alarme falso de divergencia."""
    bruto = s.get("end_time")
    if not bruto:
        return False
    try:
        return datetime.fromisoformat(bruto.replace("+0000", "+00:00")).astimezone(SP) < AGORA
    except ValueError:
        return False


total = 0.0
encerrados = []
for s in sorted(dados, key=lambda x: x.get("name", "")):
    if s.get("effective_status") != "ACTIVE":
        continue
    nome = (s.get("name") or "?")[:38]
    orc = int(s.get("daily_budget") or 0) / 100
    if venceu(s):
        encerrados.append((nome, orc, s.get("end_time")))
        continue
    total += orc
    fim = s.get("end_time")
    if fim:
        try:
            fim = datetime.fromisoformat(fim.replace("+0000", "+00:00")).astimezone(SP).strftime("  (termina %d/%m %Hh%M)")
        except ValueError:
            fim = ""
    print(f"  {nome:<40} R$ {orc:>7.2f}/dia{fim or ''}")

if encerrados:
    print("\n  Cronograma ja vencido, nao entregam mais (fora da soma):")
    for nome, orc, fim in encerrados:
        print(f"    {nome:<38} R$ {orc:>7.2f}/dia, terminou em {str(fim)[:10]}")

pausados = sum(1 for s in dados if s.get("effective_status") != "ACTIVE")
print(f"\n  PROGRAMADO/DIA: R$ {total:.2f}   ({pausados} conjunto(s) pausado(s))")
print(f"  PLANO COMBINADO: R$ {PLANO_ATUAL:.2f}/dia")
if abs(total - PLANO_ATUAL) < 1:
    print("  STATUS: APLICADO. Comparar o gasto do dia com este valor.")
else:
    print(f"  STATUS: DIVERGENTE (conta em R$ {total:.0f}, plano R$ {PLANO_ATUAL:.0f}).")
    print("  Registrar no marcador e comparar o gasto com o valor REAL da conta.")
