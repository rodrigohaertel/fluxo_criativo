---
name: publicar-reel
description: Programa a publicação de um Reel da Linha Editorial no YouTube (API, agendamento nativo), no Instagram e no Facebook (Planner do Meta Business Suite pelo Claude in Chrome). Lê a pasta do Reel (vídeo, capa, HTML com legenda, título e descrição), aplica os padrões do Rodrigo e mostra uma ficha de confirmação antes de agendar. Use quando o usuário pedir "publicar o R018", "programar o Reel", "agendar o vídeo no YouTube e no Instagram", "/publicar-reel R018 quinta 10h".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, ToolSearch, mcp__claude-in-chrome__*
---

# /publicar-reel

Programa um Reel nos três canais: **YouTube** (vídeo normal ou Short), **Instagram** (Reel) e **Facebook** (Reel na página Rodrigo Haertel).

Caminho validado em 29/09/2026 com o R017:
- **YouTube:** pela API, com agendamento nativo. Não precisa de clique do Rodrigo nem de computador ligado na hora.
- **Instagram + Facebook:** pelo **Planner** do Business Suite, operado no Claude in Chrome. A API do Instagram não agenda, e a API de Reels do Facebook só aceita até 90 s. O Rodrigo decidiu manter o Planner para ver tudo no calendário. **A única ação dele é escolher o arquivo do vídeo**, porque o envio de arquivo pelo Chrome tem limite de 10 MB.

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

O que você vai precisar fazer: escolher o arquivo do vídeo no Planner quando eu pedir.
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

Se o YouTube devolver o vídeo como "bloqueado/privado" por app não verificado, avise o Rodrigo. No teste do R017 isso **não** aconteceu.

## Passo 5. Instagram + Facebook pelo Planner

Carregue as ferramentas do Chrome em uma chamada ToolSearch (`tabs_context_mcp, tabs_create_mcp, navigate, computer, find, read_page, file_upload, javascript_tool, get_page_text, browser_batch`).

1. Abra `https://business.facebook.com/latest/content_calendar`.
2. Clique na **seta ao lado de "Criar post"** (canto superior direito) → **"Criar reel"**. Confira que "Postar em" mostra **Rodrigo Haertel e rodrigohaertel**.
3. Clique no campo **Texto** e digite a legenda completa (a do JSON).
4. Peça ao Rodrigo: *"Clique em Adicionar vídeo e escolha: {caminho completo do vídeo}. Me avise com 'subiu'."* Espere.
5. **Capa:** em Miniatura → aba **"Carregar imagem"**. O campo de arquivo não existe até o clique, então intercepte-o com `javascript_tool`:
   ```js
   const orig = HTMLInputElement.prototype.click;
   HTMLInputElement.prototype.click = function(){ if(this.type==='file'){ this.setAttribute('aria-label','capa-upload'); this.style.cssText='display:block;position:fixed;top:5px;left:5px;z-index:99999'; if(!this.isConnected) document.body.appendChild(this); window.__capaInput=this; HTMLInputElement.prototype.click=orig; return;} return orig.call(this); };
   const link=[...document.querySelectorAll('a')].find(e=>e.textContent.trim()==='Carregar imagem'); link && link.click(); !!window.__capaInput
   ```
   Depois use `find` com "file input labeled capa-upload", `file_upload` com o caminho da capa e esconda o campo (`window.__capaInput.style.display='none'`). Se a capa passar de 10 MB, converta antes para JPG com ffmpeg no scratchpad.
6. Espere o aviso **"Seu vídeo está seguro para ser publicado"** e clique em **Avançar**.
7. Em **Legendas ocultas**, deixe **desmarcado**. Em **Remix e uso de áudio original**, marque **"Não permitir"**.
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

## Regras

- Horário sempre de Brasília (America/Sao_Paulo).
- Texto que vai ao ar é o do HTML do Reel. Nada de reescrever legenda por conta própria. Se notar algo fora das regras de linguagem da memória (ex.: "te paga"), **aponte na ficha como alerta** e deixe o Rodrigo decidir.
- Nunca exibir token. O `.env` é lido pelos scripts.
- Ficar de olho em novidades: se a Meta liberar agendamento do Instagram pela API, ou Reels acima de 90 s no Facebook, avise e proponha migrar o Passo 5 para a API (memória `meta-reels-configuracao-padrao`).
