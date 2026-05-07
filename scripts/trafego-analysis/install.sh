#!/usr/bin/env bash
set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║    trafego — Instalador (Mac/Linux)                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Prefere Python 3.12; fallback para python3 genérico
if command -v python3.12 &> /dev/null; then
    PY_BIN=python3.12
elif command -v python3 &> /dev/null; then
    PY_BIN=python3
else
    echo "❌ Python 3 não encontrado."
    echo "   Instale em: https://www.python.org/downloads/ (recomendado 3.12)"
    exit 1
fi

PY_VERSION=$($PY_BIN -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
PY_MAJOR=$($PY_BIN -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$($PY_BIN -c 'import sys; print(sys.version_info[1])')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    echo "❌ Python 3.11+ necessário (encontrado: $PY_VERSION)"
    echo "   Recomendado: 3.12"
    exit 1
fi

if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 14 ]; then
    echo "⚠ Python $PY_VERSION detectado. Algumas dependências podem não ter wheels."
    echo "  Recomendamos Python 3.12. Para continuar mesmo assim, pressione ENTER."
    read -r
fi

echo "✓ Python $PY_VERSION ($PY_BIN)"

# Cria venv se não existir
if [ ! -d ".venv" ]; then
    echo "→ Criando virtualenv em .venv/"
    $PY_BIN -m venv .venv
fi

# Ativa
source .venv/bin/activate
echo "✓ Virtualenv ativado"

# Atualiza pip
python -m pip install --upgrade pip --quiet

# Instala skill
echo "→ Instalando dependências (pode levar 1-2 min)..."
python -m pip install -e ".[web]" --quiet

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ Instalação concluída!                                ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  Próximos passos:                                        ║"
echo "║                                                          ║"
echo "║  1) Ative o ambiente (sempre antes de usar):             ║"
echo "║     source .venv/bin/activate                            ║"
echo "║                                                          ║"
echo "║  2) Configure sua conta:                                 ║"
echo "║     trafego setup                                        ║"
echo "║                                                          ║"
echo "║  3) Primeira análise:                                    ║"
echo "║     trafego                                              ║"
echo "║                                                          ║"
echo "║  4) Ou abra a UI Web:                                    ║"
echo "║     trafego web                                          ║"
echo "║                                                          ║"
echo "║  Docs: docs/PRIMEIRO_USO.md                              ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
