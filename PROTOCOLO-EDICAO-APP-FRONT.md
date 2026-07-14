# Protocolo de Edição do App-Front

Guia de trabalho para alterações no aplicativo **app-front** (Painel do Dono).
Objetivo: permitir que o Rodrigo evolua a parte visual e de conteúdo do app com segurança, sem tocar na estrutura técnica que é responsabilidade do Vitor, e sempre testando no ambiente de homologação antes de ir pra produção.

Repositório: `Do-Custo-ao-Lucro/app-front`
Stack: Next.js 15 (App Router), React 19, Material UI v7, NextAuth, recharts, TypeScript.
O front consome a API do backend do Vitor (`app-back`) pela variável `NEXT_PUBLIC_BACKEND_URL`.

---

## 1. Princípio inegociável

Neste app o Rodrigo mexe **apenas no front**: aparência, layout, textos, cores, imagens e organização visual das telas.

Qualquer alteração que possa mudar a **estrutura** ou o **comportamento de dados** do sistema (a parte do Vitor) **não é feita direto**. Ela é sinalizada, explicada e validada com o Vitor **antes** de qualquer commit. Na dúvida entre "isso é front ou é estrutura?", trata como estrutura e pergunta.

Regra de segurança extra: **todo trabalho começa na branch `dev`**. O `main` (produção) só recebe algo depois de testado em homologação e aprovado.

---

## 2. Mapa de zonas do repositório

O código está dividido em três zonas. Antes de editar qualquer arquivo, identifique em qual zona ele está.

### Zona Verde (livre para editar)

Aparência e conteúdo. Pode alterar sem pedir autorização, respeitando a Regra do Contrato (seção 3).

- `src/config/Theme.tsx` — cores da marca, tipografia, estilo dos botões (tema do Material UI).
- `src/components/**` — componentes visuais reutilizáveis (chips, cards, gráficos, diálogos visuais, campos com máscara, overlays de carregamento).
- `src/patterns/**` — blocos visuais maiores (formulários, menus, cards de produto, containers de lista, paginação). A parte de layout e texto.
- `app/**/page.tsx` e `layout.tsx` — as 45 telas do app. Layout, ordem dos elementos, textos visíveis, espaçamentos, responsividade.
- `src/dictionaries/lang/pt-BR.json` e `en.json` — todos os textos e rótulos da interface (copy do app).
- `public/**` — logos, ícones, imagens e outros assets estáticos.

### Zona Amarela (edita com cuidado, regra do contrato)

Arquivos visuais que também carregam lógica de dados. Pode mexer no visual, mas **não** pode alterar quais dados são enviados/lidos. Ver seção 3.

- Formulários dentro de `src/patterns/**` (ex.: `ProductForm`, `ComboForm`, `PurchaseHistoryForm`).
- Telas em `app/**/page.tsx` que preenchem e enviam formulários.
- `src/hooks/**` de interface (ex.: `useDialog`, `useScreenSize`, `useTheme`, `useText`). Os hooks puramente visuais são verdes; os que carregam ou salvam dados são amarelos.

### Zona Vermelha (só com validação do Vitor antes)

Estrutura, contrato de dados, autenticação, build e deploy. Não tocar sem aviso e aprovação do Vitor.

- `src/controllers/**` — as 26 classes que chamam a API do backend.
- `src/payload/**` — os DTOs (o formato exato dos dados trocados com o backend).
- `src/model/**` — os modelos de domínio.
- `src/utils/RequestLib`, `src/utils/TokenUtils`, `src/utils/Auth` e utilitários de infraestrutura.
- `src/config/Config.tsx` — URLs do backend e do app.
- `src/context/**` que guarda estado de dados (ex.: `UserContext`, `CompanyContext`, `SubscriptionContext`).
- `middleware.ts` — proteção de rotas e autenticação.
- `pages/api/**` — rotas de API do NextAuth.
- `next.config.ts`, `Dockerfile`, `.github/workflows/ci-cd.yml`, `package.json`, `package-lock.json`, variáveis de ambiente (`.env*`).

---

## 3. A Regra do Contrato de Dados

Esta é a regra fina que separa uma edição segura de uma perigosa dentro da Zona Amarela.

Uma tela ou formulário pode ser reestilizado, reordenado e reescrito à vontade. O que **não** pode mudar sem o Vitor é o **contrato**: quais campos são enviados ao controller, com quais nomes, em qual formato, e quais dados são lidos de volta.

**Pode (verde):** trocar a cor de um botão, mudar o texto de um rótulo, reorganizar a ordem dos campos na tela, ajustar espaçamento, deixar responsivo, trocar um ícone, melhorar uma mensagem.

**Não pode sem o Vitor (vermelho):** adicionar, remover ou renomear um campo enviado a um controller; mudar o tipo de um dado (texto, número, data); alterar uma chamada de API; mexer no formato de um DTO; mudar regra de validação que o backend espera.

Teste rápido: "se eu salvar isso, o app pede ou envia algum dado diferente pro backend?" Se sim, para e valida com o Vitor.

---

## 4. Fluxo de trabalho (passo a passo)

Todo ajuste segue esta sequência. Nunca pular direto pro `main`.

1. **Partir do `dev` atualizado.** Clonar o repositório e entrar na branch `dev`, sempre com a última versão.
2. **Identificar a zona.** Localizar o arquivo e confirmar se é verde, amarelo ou vermelho (seção 2). Se for vermelho, ir para a seção 5 antes de qualquer coisa.
3. **Editar só o necessário.** Alteração cirúrgica: mexer apenas no que foi pedido, sem "melhorar" o que não faz parte da tarefa.
4. **Conferir localmente.** Rodar a verificação de build e de lint pra garantir que a alteração não quebrou nada (`build` e `lint`). Erro de referência ou de tipo aparece aqui, não depois em produção.
5. **Publicar no `dev`.** Commit e push na branch `dev`. Isso dispara o deploy automático no ambiente de **homologação**.
6. **Testar em homolog.** Abrir a tela no ambiente de homologação e conferir o resultado de verdade, no navegador, inclusive no celular.
7. **Aprovar e subir pro `main`.** Só depois de validado, levar a mudança pro `main` (via merge do `dev`), o que dispara o deploy de **produção**.

Ponto importante: como o `dev` publica em homolog automaticamente, o ambiente de homolog é o nosso campo de teste seguro. Nada vai pro cliente até o merge no `main`.

---

## 5. Gate de validação com o Vitor

Sempre que uma tarefa esbarrar na Zona Vermelha (ou na dúvida da Regra do Contrato), o trabalho **para** e o Rodrigo recebe um aviso claro **antes** de qualquer commit, no seguinte formato:

```
Atenção: essa alteração encosta na estrutura do Vitor.

O que você pediu: {descrição em linguagem simples}
Por que isso é estrutura: {o que muda no contrato de dados, autenticação, build ou deploy}
Arquivo(s) afetado(s): {lista}
Risco se mexermos sozinhos: {o que pode quebrar}
Sugestão: validar com o Vitor antes. Posso preparar a alteração e deixar pronta pra ele revisar, ou aguardar o retorno dele.
```

Nada é enviado enquanto o Rodrigo não confirmar que falou com o Vitor e está liberado. Se o Rodrigo preferir, a alteração pode ser preparada numa branch separada (ex.: `feature/nome`) só para o Vitor revisar, sem tocar em `dev` nem `main`.

---

## 6. Checklist antes de publicar no dev

- [ ] A alteração é só visual/conteúdo, ou passou pelo gate do Vitor.
- [ ] Nenhum campo, DTO ou chamada de API foi alterado sem validação.
- [ ] O `build` passou sem erro.
- [ ] O `lint` passou sem erro novo.
- [ ] A mudança está na branch `dev` (nunca commit direto no `main`).
- [ ] Depois do deploy, a tela foi conferida em homolog, no desktop e no celular.

---

## 7. O que nunca fazer

- Commitar direto no `main` sem passar pelo `dev` e por homolog.
- Editar qualquer arquivo da Zona Vermelha sem aviso e validação do Vitor.
- Mudar nomes ou formatos de dados trocados com o backend.
- Mexer em `Dockerfile`, workflows, `next.config.ts` ou variáveis de ambiente por conta própria.
- Subir segredo ou token para qualquer arquivo do repositório.
