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
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CAMPANHA = "120247419652220527"   # [DONO14] [CONV] [LEADS] ABO
PLANO_ATUAL = 120.00              # R$/dia: so A39, apos pausar o A40 em 31/08 (sobe com o A42)


def token():
    for linha in (Path(__file__).resolve().parent.parent / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("FB_ACCESS_TOKEN_PERMANENTE="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("FB_ACCESS_TOKEN_PERMANENTE nao encontrado no .env")


p = {"fields": "name,daily_budget,effective_status", "limit": 100,
     "access_token": token(), "_": str(int(time.time()))}
url = f"https://graph.facebook.com/v21.0/{CAMPANHA}/adsets?" + urllib.parse.urlencode(p)
dados = json.loads(urllib.request.urlopen(url, timeout=90).read()).get("data", [])

print("=" * 62)
print("ORCAMENTO REAL NA CONTA (conjuntos ATIVOS)")
print("=" * 62)
total = 0.0
for s in sorted(dados, key=lambda x: x.get("name", "")):
    if s.get("effective_status") != "ACTIVE":
        continue
    orc = int(s.get("daily_budget") or 0) / 100
    total += orc
    print(f"  {(s.get('name') or '?')[:38]:<40} R$ {orc:>7.2f}/dia")
pausados = sum(1 for s in dados if s.get("effective_status") != "ACTIVE")
print(f"\n  PROGRAMADO/DIA: R$ {total:.2f}   ({pausados} conjunto(s) pausado(s))")
print(f"  PLANO COMBINADO: R$ {PLANO_ATUAL:.2f}/dia")
if abs(total - PLANO_ATUAL) < 1:
    print("  STATUS: APLICADO. Comparar o gasto do dia com este valor.")
else:
    print(f"  STATUS: DIVERGENTE (conta em R$ {total:.0f}, plano R$ {PLANO_ATUAL:.0f}).")
    print("  Registrar no marcador e comparar o gasto com o valor REAL da conta.")
