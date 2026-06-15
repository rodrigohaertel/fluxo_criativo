# Contribuindo com o trafego

Obrigado por considerar contribuir. Este projeto é MIT e qualquer contribuição é bem-vinda.

---

## Tipos de contribuição

- **Bug reports** — abra issue usando o template "Bug report"
- **Feature requests** — template "Feature request"
- **Perguntas / dúvidas** — template "Pergunta"
- **Pull Requests** — contribuições de código (ver abaixo)

---

## Como contribuir com código

### 1. Fork + clone

```bash
git clone git@github.com:SEU_USUARIO/skill-analise.git
cd skill-analise
git remote add upstream git@github.com:trafegopaid/skill-analise.git
```

### 2. Instale em modo editable com deps de dev

```bash
python -m venv .venv
source .venv/bin/activate       # Mac/Linux
# .venv\Scripts\activate.bat    # Windows

pip install --upgrade pip
pip install -e ".[web,dev]"
```

### 3. Crie uma branch

```bash
git checkout -b feat/nome-da-feature
# ou
git checkout -b fix/bug-que-estou-resolvendo
```

### 4. Código

**Estilo:**
- Python 3.11+
- Formatação com `ruff` (já configurado no pyproject.toml)
- Tipagem com type hints onde fizer sentido — não é obrigatório 100%
- Docstrings em PT-BR ou EN (seja consistente dentro do módulo)

**Princípios:**
- Módulos curtos e focados
- Sem dependências novas a menos que absolutamente necessário — cada dep adicionada é um custo de manutenção
- Mensagens de erro pensadas para o USUÁRIO FINAL, não para o dev (quem vê é traffic manager, não engenheiro)

### 5. Testes

Todo código novo precisa de teste. Veja `tests/` para referência.

```bash
# Rodar todos os testes
pytest

# Rodar um arquivo específico
pytest tests/test_metrics.py

# Com coverage
pytest --cov=trafego_analysis
```

**Todos os testes precisam passar** antes de abrir PR.

### 6. Commit

Convenção: mensagens no presente, começando com tipo:

```
feat: adicionar análise de campanhas por idade
fix: corrigir cálculo de hook rate quando impressions é zero
docs: melhorar guia de setup do token
refactor: extrair cálculo de CPA para metrics.py
test: adicionar cobertura para fadiga em ads de RMK
chore: atualizar dependência do pandas
```

Commits pequenos e focados. Evite commits tipo "várias mudanças".

### 7. Push + Pull Request

```bash
git push origin feat/nome-da-feature
```

Abra PR contra `main` do upstream. No corpo do PR, explique:

- **O que** muda
- **Por quê** (problema que resolve)
- **Como testar** (passos manuais, além dos testes automáticos)
- **Screenshots** se for mudança visual (UI Web, galeria HTML)

---

## Prioridades do roadmap

Antes de trabalhar em features grandes, verifique se está no roadmap ([CHANGELOG.md](CHANGELOG.md) → "Conhecido / não implementado"). Features priorizadas pela maintainer têm mais chance de serem aceitas.

Ideias novas: abra issue de **Feature request** antes de codar — economiza retrabalho.

---

## Code of Conduct

Este projeto adota o [Contributor Covenant](CODE_OF_CONDUCT.md). Respeito mútuo é obrigatório.

---

## Licença

Ao contribuir, você concorda que seu código será licenciado sob **MIT** (mesma do projeto).
