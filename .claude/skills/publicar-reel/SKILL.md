---
name: publicar-reel
description: Programa a publicação de um Reel da Linha Editorial no YouTube (API, agendamento nativo), no Instagram e no Facebook (Planner do Meta Business Suite pelo Claude in Chrome). Lê a pasta do Reel (vídeo, capa, HTML com legenda, título e descrição), aplica os padrões do Rodrigo e mostra uma ficha de confirmação antes de agendar. Use quando o usuário pedir "publicar o R018", "programar o Reel", "agendar o vídeo no YouTube e no Instagram", "/publicar-reel R018 quinta 10h".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, ToolSearch, mcp__claude-in-chrome__*
---

# /publicar-reel

Programa um Reel nos três canais: **YouTube** (vídeo normal ou Short), **Instagram** (Reel) e **Facebook** (Reel na página Rodrigo Haertel).

Caminho validado em 29/09/2026 com o R017:
- **YouTube:** pela API, com agendamento nativo. Não precisa de clique do Rodrigo nem de computador ligado na hora.
- **Instagram + Facebook:** pelo **Planner** do Business Suite, operado no Claude in Chrome. A API do Instagram não agenda, e a API de Reels do Facebook só aceita até 90 s. O Rodrigo decidiu manter o Planner para ver tudo no calendário. **As ações dele são escolher o arquivo do vídeo e a capa no Planner.** O vídeo passa do limite de 10 MB do envio pelo Chrome, e a capa anexada pelo Chrome não é gravada pela Meta.

---

## Anúncio inicial

```
🔍 Próximo passo: programar o {código} no YouTube, no Instagram e no Facebook (5 passos). Tempo estimado: 6 a 10 minutos.
```

Sub-passos com `⏳ Passo X/5:`.

---

## Passo 1. Entender o pedido

Extraia da mensagem:
- **Código do Reel** (ex.: R018). Se faltar, liste as pastas `R### - Nome` que ainda não estão em `Publicados/` e pergunte qual é (opções numeradas).
- **Data e hora** (sempre horário de Brasília). Se faltar, leia o campo "Publicação:" no topo do HTML do Reel e **proponha** esse horário. Nunca assuma sem mostrar na ficha.

Datas relativas ("amanhã", "quinta") viram data absoluta com `date`.

## Passo 2. Ler a pasta

```bash
py -3 .claude/skills/publicar-reel/scripts/extrair.py R018
```

Devolve JSON com vídeo, capa, duração, formato do YouTube (short até 3 min, normal acima), legenda, título e descrição do YouTube **já no padrão** (cabeçalho da Sessão + rodapé de redes, ver memória `youtube-descricao-padrao`) e `alertas`.

Se faltar vídeo, capa ou HTML, pare e diga ao Rodrigo o que falta na pasta. Não publique sem capa sem perguntar.

## Passo 3. Ficha de confirmação (obrigatória, uma vez só)

Mostre a ficha abaixo e **aguarde "sim"**. Ela vale como o gate de escrita na Meta do CLAUDE.md, para os três canais de uma vez. Sem "sim", nada é enviado.

```
🛡️ Confirmação antes de programar o {código}

📹 Vídeo: {nome do arquivo} · {duração} · {MB} MB
🖼️ Capa: {nome do arquivo da capa}
🗓️ Quando: {dia da semana}, {dd/mm/aaaa} às {hh:mm} (Brasília), nos três canais

YouTube · {Short | vídeo normal (passa de 3 min)}
  Título: {título}
  Descrição: cabeçalho da Sessão (docustoaolucro.com/yt) ✅ · rodapé de redes ✅ · {N} caracteres
  Primeiras linhas do texto: "{primeiros ~150 caracteres do texto, depois do cabeçalho}"

Instagram + Facebook · Reel pelo Planner
  Legenda: "{primeiros ~125 caracteres, o que aparece antes do 'mais'}"
  Tamanho: {N} caracteres · {N} hashtags
  Configurações: legendas ocultas DESLIGADAS · remix e áudio "Não permitir"
                 · proteção de conteúdo ligada · compartilhar no Story do Facebook ligado

⚠️ Alertas: {lista de alertas do extrair.py e do Passo 1, ou "nenhum"}

O que você vai precisar fazer: escolher o vídeo e a capa no Planner quando eu pedir.
Reversível: sim, até o horário marcado (YouTube Studio e Planner).

Pode programar? Responda "sim" pra confirmar ou diga o que ajustar.
```

Se o Rodrigo quiser ver a legenda ou a descrição inteira, mostre o texto completo. Se ele pedir ajuste de texto, ajuste **só o que foi pedido** (edição cirúrgica) e mostre a ficha de novo.

## Passo 4. YouTube (em segundo plano)

Depois do "sim":

```bash
py -3 .claude/skills/publicar-reel/scripts/youtube_publicar.py R018 "2026-10-02 10:00" --enviar
```

Rode com `run_in_background: true`. Sem `--enviar`, o script só mostra a prévia. Ao terminar, guarde `VIDEO_ID` e o link. Se a descrição tiver sido ajustada no Passo 3, edite o texto no HTML do Reel antes de rodar (o script lê do HTML).

**Capa de Short (obrigatório quando o formato é `short`):** a API só preenche a miniatura horizontal. A miniatura vertical do Short só entra pelo Studio. Depois do envio, abra no Chrome `https://studio.youtube.com/video/{VIDEO_ID}/edit`, use `find` para achar o campo de arquivo da seção Miniatura, envie a capa em PNG com `file_upload`, clique em **Salvar** e confirme o aviso "Alterações salvas". **Só envie a capa depois que o YouTube terminar de processar** (API: `processingStatus = succeeded`; no Studio, a miniatura deixa de mostrar "…"). Enviada antes disso, a capa não fica gravada (R019, 02/10/2026). Para confirmar, **recarregue a página** e veja a capa na seção Miniatura; se voltar o "…" ou um quadro do vídeo, reenvie. Faça isso em uma aba separada, para não mexer na aba do Planner. Em vídeo normal (acima de 3 min) a capa da API basta.

Se o YouTube devolver o vídeo como "bloqueado/privado" por app não verificado, avise o Rodrigo. No teste do R017 isso **não** aconteceu.

## Passo 5. Instagram + Facebook pelo Planner

Carregue as ferramentas do Chrome em uma chamada ToolSearch (`tabs_context_mcp, tabs_create_mcp, navigate, computer, find, read_page, file_upload, javascript_tool, get_page_text, browser_batch`).

1. Abra `https://business.facebook.com/latest/content_calendar`.
2. Clique na **seta ao lado de "Criar post"** (canto superior direito) → **"Criar reel"**. Confira que "Postar em" mostra **Rodrigo Haertel e rodrigohaertel**.
3. Clique no campo **Texto** e digite a legenda completa (a do JSON).
4. Peça ao Rodrigo, em uma mensagem só, com os dois caminhos completos:
   *"No Planner: (1) clique em Adicionar vídeo e escolha {caminho do vídeo}; (2) quando carregar, em Miniatura → Carregar imagem, escolha {caminho da capa}. Não clique em Avançar. Me avise com 'pronto'."* Espere.
5. **Capa: quem escolhe é o Rodrigo, sempre.** Nunca anexe a capa pelo Chrome (interceptar o campo de arquivo com JavaScript). Em 29/09 (R017) e 02/10 (R018) a capa anexada assim apareceu na tela como aplicada, mas a Meta não gravou, e o post do Instagram programado **não deixa editar a capa depois**: foi preciso refazer. Depois do "pronto", confira no screenshot que a **prévia grande à direita mostra a capa** (e não um quadro do vídeo). Se mostrar quadro do vídeo, peça para ele escolher a capa de novo antes de avançar.
6. Espere o aviso **"Seu vídeo está seguro para ser publicado"** e clique em **Avançar**.
7. Em **Legendas ocultas**, deixe **desmarcado** (vem ligado por padrão, confira com `javascript_tool`). Em **Remix e uso de áudio original**, marque **"Não permitir"**. Essas duas opções só existem quando o Facebook está marcado.
8. Em **Opções de programação**, clique em **Programar**. Para Facebook e Instagram: clique na data e escolha o dia no calendário, depois use `find` ("hour and minute spinbutton") e digite hora e minuto em cada spinbutton. Confira com `zoom` que os dois mostram a data e a hora certas.
9. Confira com `javascript_tool` que: horas = hora combinada nos dois canais, remix "Não permitir" marcado e legendas ocultas desmarcadas. **Não clique em "Compartilhar"**, que publica na hora.
10. Clique em **Programar** (o botão azul no rodapé). A ficha do Passo 3 já foi aprovada, então não pergunte de novo, **a menos que algo tenha mudado** (data, capa ou configuração diferente da ficha).
11. Volte ao Planner e confirme que aparecem **dois cards** no dia e na hora combinados (ícone do Facebook e do Instagram). A miniatura do card é um quadro do vídeo, não a capa, e isso é normal. **Não clique em espaço vazio do calendário**, porque isso abre um post novo em branco.

## Encerramento

```
✅ Concluído: {código} programado para {dia}, {dd/mm} às {hh:mm}.
- YouTube: {link} ({Short | vídeo normal}), capa aplicada
- Instagram e Facebook: Reel no Planner
```

Sugira: *"Depois que sair, confira a capa no grid do Instagram. Quando quiser, eu movo a pasta do {código} para Publicados/."* (Mover só com o ok dele.)

---

## Se precisar refazer só um canal

Post programado do Instagram não aceita edição de capa. Para refazer: crie um Reel novo com **"Postar em" só no canal a refazer** (desmarque o outro), programe, confirme no Planner e só então exclua o antigo, com o ok do Rodrigo. Nunca exclua antes de o novo estar programado.

---

## Regras

- Na janela "Detalhes do post" do Planner existe o botão **"Publicar agora"**. Nunca clique nele.

- Horário sempre de Brasília (America/Sao_Paulo).
- Texto que vai ao ar é o do HTML do Reel. Nada de reescrever legenda por conta própria. Se notar algo fora das regras de linguagem da memória (ex.: "te paga"), **aponte na ficha como alerta** e deixe o Rodrigo decidir.
- Nunca exibir token. O `.env` é lido pelos scripts.
- Ficar de olho em novidades: se a Meta liberar agendamento do Instagram pela API, ou Reels acima de 90 s no Facebook, avise e proponha migrar o Passo 5 para a API (memória `meta-reels-configuracao-padrao`).
