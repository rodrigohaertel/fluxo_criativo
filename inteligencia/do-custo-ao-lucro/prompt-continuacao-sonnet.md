# Prompt de Continuação — Página de Vendas do Desafio do Preço do Prato

> Cole o conteúdo abaixo no novo chat com Claude Sonnet para retomar o trabalho sem perder contexto.

---

## Contexto

Estou construindo a página de vendas do **"Desafio do Preço do Prato em 10min"** (R$ 77, low-ticket) para o projeto **Do Custo ao Lucro Restaurantes**. O trabalho está em andamento e foi pausado depois do Passo 3 (Extrator de Copy QFD) ser reexecutado formalmente.

**Quem sou**: Rodrigo Haertel — fundador do Do Custo ao Lucro Restaurantes. Ajudo donos de restaurantes a alcançarem 14% de lucro operacional através da correta precificação do cardápio. Mantra: "Lucro não é sorte, é método." Tom: parceiro estratégico, autoridade calma e direta (referências Tiago Leifert + Camila Farani). Não quero tom de guru motivacional.

**Produto**: Desafio do Preço do Prato em 10min — R$ 77 (decoy R$ 97). Checkout Hotmart: `https://pay.hotmart.com/P104019404T?off=31h5xetn&checkoutMode=10`. Método central: Método Prato Real™ (5 etapas). Big Idea Visual: "número aparecendo na tela".

---

## O que já foi feito

1. **Passo 2** (configurações) — feito
2. **Passo 3 — Extrator de Copy (QFD)** — reexecutado formalmente. JSON em `output/copy-estruturada.json` com melhorias já aprovadas por mim:
   - Premissa SEM imperativo: *"O prato que mais vende pode ser o que mais afunda o caixa."*
   - Decorado aspiracional reforçado (dormir sem conta de cabeça, ver sobra real no caixa, falar de lucro com segurança com sócio/família)
   - Desejos ampliados com 4 itens aspiracionais
   - Expert preenchido: Rodrigo Haertel, bio, credenciais, mantra, referências de tom
   - Urgência concreta: *"Preço de lançamento: R$ 77. Quando esse lote fechar, volta para R$ 97."*
3. **Passo 4 — Designer HTML** — feito. `output/design-tokens.json` tem paleta premium dark-gold validada (primary `#D4A862`, bg_dark `#0B1F18`, Fraunces + Inter).
4. **Passo 4.5 — Revisor de design** — feito. Score 7.5/10.
5. **Passo 5 — Construtores de blocos** — feito. `output/bloco1.html`, `bloco2.html`, `bloco3.html`, `bloco4.html`.
6. **Passo 6 — Concatenação** — feito. `output/pagina-de-venda.html` concatenado e copiado para `C:\Users\rodri\OneDrive\Documentos\Claude\Projects\Do Custo ao Lucro - Restaurantes\pagina-de-venda-desafio.html`.
7. **Revisão dupla** — copy 7.8/10 + design 7.5/10 = consolidado ~7.7/10.

---

## O que precisa ser feito (próximos passos)

As melhorias aprovadas estão no `copy-estruturada.json` **mas ainda não foram propagadas para os HTMLs**. Preciso que você:

### 1. Propagar copy atualizado para os blocos HTML
Ler `output/copy-estruturada.json` (fonte da verdade) e editar cada bloco:

- **bloco1.html (Hero)**: trocar premissa/headline/subheadline pelo conteúdo novo. Substituir a `.urgency-bar` vaga atual pela versão concreta de preço ("Preço de lançamento: R$ 77. Quando esse lote fechar, volta para R$ 97.").
- **bloco1.html — ADICIONAR seção VSL**: incluir um `.video-wrapper` com placeholder (responsive 16:9) entre os bullet points e o CTA. Deixar comentário HTML marcando onde inserir o `<iframe>` ou `<video>` depois.
- **bloco3.html (seção 10 — Autoridade)**: refazer em 2 colunas. Esquerda: foto do Rodrigo (`rodrigo-haertel.jpg`) + nome "Rodrigo Haertel" + especialidade "Ajudar donos de restaurantes a alcançarem 14% de lucro operacional através da correta precificação do cardápio" + mantra em destaque "Lucro não é sorte, é método." Direita: manter emblema "482 donos pesquisados — apenas 9% sabiam o custo real" + credenciais (Criador do Método Prato Real™, Fundador Do Custo ao Lucro, Autor do Guia do Dono de Restaurante).
- **bloco4.html (seção 15 — Desejos)**: adicionar os 4 novos desejos aspiracionais (já estão no JSON).

### 2. Salvar foto do Rodrigo
Ainda preciso anexar a foto (retrato de estúdio, fundo preto, camisa marinho). Vou enviar no chat. Salve em `C:\Users\rodri\OneDrive\Documentos\Claude\Projects\Do Custo ao Lucro - Restaurantes\rodrigo-haertel.jpg`.

### 3. Referenciar o ebook
Antes de finalizar a seção Autoridade, leia `C:\Users\rodri\OneDrive\Documentos\Claude\Projects\Do Custo ao Lucro - Restaurantes\pagina-de-venda-guia.html` para garantir que o tom da bio e as credenciais estão coerentes com o que já uso no ebook.

### 4. Reconcatenar e entregar
Concatenar os 4 blocos em `output/pagina-de-venda.html` e copiar para `C:\Users\rodri\OneDrive\Documentos\Claude\Projects\Do Custo ao Lucro - Restaurantes\pagina-de-venda-desafio.html`.

---

## Minhas preferências

- **Copy**: sem imperativo forçado em premissa/headline (imperativo só no CTA). Linguagem de parceiro estratégico, não de guru.
- **Design**: mais elementos visuais (mockups, screenshots do software, ícones grandes, gráficos antes/depois). Evitar parede de texto. A paleta dark-gold está aprovada — não mexer.
- **Entrega**: fazer o trabalho avançar. Se tem dado no contexto, já entrega o material pronto. Só perguntar se faltar dado crítico.
- **Urgência**: só se for real e verificável. Nada de texto vago.
- **Coerência**: todo material novo deve herdar tom do ecossistema (ebook, site).

---

## Artefatos para ler primeiro

1. `output/copy-estruturada.json` — copy final aprovado (fonte da verdade)
2. `output/design-tokens.json` — paleta e tipografia
3. `output/bloco1.html`, `bloco2.html`, `bloco3.html`, `bloco4.html` — HTML atual (a ser editado)
4. `C:\Users\rodri\OneDrive\Documentos\Claude\Projects\Do Custo ao Lucro - Restaurantes\pagina-de-venda-guia.html` — referência de tom do ebook

---

## Comandos úteis

- Reexecutar revisão: `/revisor-copy` e `/revisor-design`
- Reconstruir blocos específicos: `/construtor-bloco1`, `/construtor-bloco3`, `/construtor-bloco4`
- Gerar página inteira do zero: `/criar-pagina`

**Começa pela propagação do copy atualizado para os blocos HTML. Não reescreva o copy do zero — apenas migre do JSON para o HTML, preservando o que já está bom.**
