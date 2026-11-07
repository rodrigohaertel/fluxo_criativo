---
name: workshop-marketing:revisor-anuncio
description: Revisar um anúncio pronto (roteiro de vídeo, anúncio estático, legenda da Meta, headline, capa) pela metodologia VTSD antes de gravar ou publicar. Dá nota pela régua do produto ou pela régua padrão de 10 critérios, corrige os vícios do Manual da Copy sozinho e devolve o resto como decisão do aluno, com a correção já escrita. Use quando o aluno pedir "revisa esse anúncio", "passa o revisor no A54", "avalia esse criativo", "dá nota nesse roteiro", "o que falta nesse anúncio".
---

# Revisor de Anúncio (VTSD)

Julga um anúncio que já existe. Não gera peça nova.

**A skill completa está em `.claude/skills/revisor-anuncio/SKILL.md`.** Leia o arquivo inteiro antes do Passo 0 e siga cada bloco dele à risca. Este command é o roteiro com o aluno: o que receber, o que anunciar, o que mostrar e onde salvar.

## Usage

```
/revisor-anuncio
/revisor-anuncio A54
/revisor-anuncio "caminho/do/roteiro.html"
```

---

## Passo 0. Contexto

1. Leia `meus-produtos/.ativo` e `meus-produtos/{ativo}/resumo-produto.md` (se não existir, gere conforme "Contexto Persistente do Negócio" no CLAUDE.md).
2. Carregue tudo o que o Passo 0 da skill pede: Manual da Copy, Mandala, regras da `/copy-anuncio`, checklist Light Copy, réguas e `regras-do-revisor.md` do produto, cabeçalhos das peças anteriores.
3. Sem produto ativo: pergunte nicho, público, Quadro e oferta de topo, uma coisa por vez, e siga sem salvar nada.

## Passo 1. Receber a peça

- Se o aluno passou um código (ex.: `A54`), procure o roteiro em `meus-produtos/{ativo}/entregas/criativos/` (pasta ou arquivo que comece com o código) e leia a versão mais recente.
- Se passou um caminho, leia o arquivo.
- Se colou o texto, use o texto.
- Se faltar o tipo da Mandala ou a fase do funil, pergunte, **uma coisa por vez**:

```
Qual é a fase do funil deste anúncio?

1. Descoberta
2. Relacionamento
3. Conversão
4. Remarketing

Digite o número:
```

## Passo 2. Anunciar e revisar

```
🔍 Próximo passo: revisar o anúncio {código} pelo VTSD (6 blocos). Tempo estimado: cerca de 90 segundos.
```

Rode os seis blocos da skill (A a F), a nota (régua do produto ou régua padrão) e monte a saída no formato fixo do Passo 4 da skill. Conte as palavras com Python antes de citar qualquer número.

## Passo 3. Mostrar e aprovar

Mostre a saída completa e termine com:

```
1. Aprovar e salvar
2. Quero ajustar algo
```

- **Aprovou e a peça veio de arquivo:** aplique as correções aprovadas no arquivo, rode `scripts/verificar-acentuacao.py` nele e devolva o caminho absoluto completo.
- **Aprovou e a peça veio colada:** devolva o texto final e sugira onde salvar.
- **Reprovou alguma sugestão:** registre a lição em `meus-produtos/{ativo}/entregas/criativos/regras-do-revisor.md` no mesmo turno (formato da skill, com a data) e refaça só o item reprovado.

## Passo 4. Próximo passo

Depois da aprovação, sugira o que vem em seguida conforme a peça: gravar (`/peca` ou `/reels-editar`), subir o teste (`/trafego-testes` ou `/trafego-criar-campanha`) ou gerar o estático (`/criativo-estatico`).
