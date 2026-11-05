---
name: peca
description: Uma conversa por criativo. Conduz uma peça da Linha Editorial (Reel R###, carrossel C###) ou um anúncio do Dono 14% (A##) do brief da sessão de planejamento até a publicação, em fases: brief, debate do ângulo, roteiro em HTML com nota, capa e telas, pausa para a gravação, edição pela /reels-editar e publicação pela /publicar-reel. Guarda o estado em _peca_R0XX.json na pasta da peça e retoma de onde parou, mesmo dias depois ou em outra sessão. Três trilhas completas: Reel, carrossel (sem gravação: fundos do Gemini pelo Chrome, lâminas do HTML, Planner sem o Rodrigo escolher arquivo) e anúncio em vídeo do Dono 14% (roteiro no padrão do A52 com nota, edição com motion pela /reels-editar e anúncio criado na conta Meta com o gate 🛡️ do CLAUDE.md). Use quando o usuário disser "/peca R035", "/peca C012", "/peca A58", "vamos fazer o R035", "abre a peça do C012", "gravei o A58", "publica o R035", "próximo Reel", "próximo carrossel", "próximo anúncio".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, WebSearch, WebFetch, ToolSearch, SendUserFile, mcp__claude-in-chrome__*
---

# /peca

Uma conversa por criativo. A peça entra pelo código (`/peca R035`) e sai publicada, passando por sete fases. O que já existe como skill (edição e publicação) é chamado por dentro, como sub-skill. O que não existia (brief, debate, roteiro com nota, capa, telas, estado e fechamento) vive aqui.

Regras de conversa (CLAUDE.md): pt-BR com acentuação, **uma pergunta por vez**, opções numeradas, **nenhum código, JSON ou comando mostrado ao Rodrigo**. Ele vê o roteiro, a nota, a ficha e o vídeo, nunca o arquivo por dentro. Todo texto de venda ou de post (roteiro, legenda, título, descrição) passa pelo Manual da Copy e pela `revisora` antes de aparecer, sem dizer que passou.

Caminhos usados abaixo:
- `{SKILL}` = `.claude/skills/peca`
- `{PY}` = o Python que roda os scripts (`py -3` no Windows do Rodrigo; conferir com `py -3 --version` na primeira vez da sessão, senão `python3`)
- `{REELS}` = `meus-produtos/linha-editorial/entregas/reels`
- `{PASTA}` = a pasta da peça, `{REELS}/R0XX - Nome/`
- `{ESTADO}` = `{PASTA}/_peca_R0XX.json`

Antes de qualquer fase, carregar as referências desta skill: `references/regras-da-linha.md` (o que vale para toda peça) e a anatomia da trilha (`references/roteiro-reel.md` para Reel, `references/roteiro-carrossel.md` para carrossel, `references/roteiro-anuncio.md` mais `references/regras-do-anuncio.md` para anúncio). Só na primeira peça da sessão, as réguas: `{REELS}/REGUA-NOTA-REELS.md`, `{REELS}/REGUA-TEXTO-NA-TELA.md`, `{REELS}/REGUA-CAPAS-E-GRADE.md`; para carrossel, `{CARROSSEIS}/REGUA-NOTA-CARROSSEIS.md`; para anúncio, `{CRIATIVOS}/REGUA-NOTA-ANUNCIOS.md`.

Caminhos da trilha C:
- `{CARROSSEIS}` = `meus-produtos/linha-editorial/entregas/carrosseis`
- `{PASTA}` = `{CARROSSEIS}/Carrossel_###_Nome/` e `{ESTADO}` = `{PASTA}/_peca_C###.json`

Caminhos da trilha A:
- `{CRIATIVOS}` = `meus-produtos/dono-14/entregas/criativos`
- `{PASTA}` = `{CRIATIVOS}/A## - Mentoria - 9x16/` e `{ESTADO}` = `{PASTA}/_peca_A##.json`

**Bases do método (Venda Todo Santo Dia).** O roteiro é escrito por esta skill, sem passar pela entrevista das skills `/copy-anuncio`, `/copy-roteiro` ou `/carrossel`: o brief e as regras já respondem o que elas perguntariam. O que elas carregam de método entra como referência, lida na fase do roteiro: `.claude/skills/mandala-de-anuncios/SKILL.md` (os 18 tipos e os 3 extras, com os nomes oficiais; obrigatória no anúncio e na diferenciação do Reel e do carrossel), `.claude/skills/anuncios-video/SKILL.md` (estrutura, tempos e direção do anúncio em vídeo), `.claude/skills/conteudo/SKILL.md` (formatos de Reels e carrosséis, ganchos que funcionam e os que são clichê), `.claude/skills/elementos-literarios/SKILL.md` (1 a 3 elementos por peça, nunca mais), `.claude/rules/copy/checklist-light-copy.md` (os 12 itens, frase por frase) e a `revisora` com o Manual da Copy, sempre, antes de mostrar. O `resumo-produto.md` do produto ativo traz Quadro, Furadeira, Decorados e Urgências Ocultas: o gancho e o Decorado em dinheiro saem de lá.

---

## Passo 0. Código, pasta e estado

1. **Código.** Vem da mensagem (R035, C012, A58). Sem código: rodar `{PY} {SKILL}/scripts/peca.py proximo` e perguntar, com opções numeradas, se é o próximo Reel, o próximo carrossel ou o próximo anúncio (mostrando o código que cada um receberia).
2. **Trilha pela letra.** R = Reel, C = carrossel e A = anúncio em vídeo do Dono 14% (as três trilhas estão abaixo). Letra desconhecida: perguntar.
3. **Produto ativo.** R e C pedem `linha-editorial`; A pede `dono-14`. Se `meus-produtos/.ativo` estiver em outro, trocar com `/produto-trocar` antes de seguir (avisar em uma linha).
4. **Estado.** Rodar `{PY} {SKILL}/scripts/peca.py estado R035`. Ele devolve a pasta (se existir), o que há dentro (roteiro, capa, telas, bruto, editado, publicado) e o `_peca_R035.json` (se existir), mais a fase que os arquivos sugerem. Decidir onde entrar:

| O que o estado mostra | Onde entrar |
|---|---|
| Sem pasta e sem estado | Fase 1 (peça nova) |
| Roteiro em andamento ou aprovado, sem bruto | Fase 2 ou 3, no ponto que o estado registra; se já aprovado, Fase 4 (lembrar o que falta gravar) |
| Bruto na pasta, sem editado | Fase 5 |
| Editado na pasta, sem publicação registrada | Fase 6 |
| Carrossel com HTML e sem lâminas em PNG (`roteiro`) | Trilha C, Fase 3 ou 4, no ponto que o estado registra |
| Carrossel com as lâminas em PNG (`produzida`), sem publicação registrada | Trilha C, Fase 5 |
| Anúncio: as mesmas leituras do Reel (roteiro, gravado, editado, programado), nas fases da trilha A | Trilha A, Fases 3 a 7 |
| Publicação registrada, pasta ainda fora de `Publicados/` | Fase 7 |
| Pasta em `Publicados/` | Dizer que a peça já saiu e perguntar o que ele quer (reler números, reeditar, nada) |

Se os arquivos e o estado discordarem (ex.: estado diz "roteiro" e há um bruto), os arquivos mandam: avisar em uma linha e seguir pela fase dos arquivos.

5. **Retomada.** Ao entrar em fase posterior à primeira, abrir com um resumo de três linhas: o que a peça é (gancho em uma frase), em que fase está e o que vem agora. Sem repetir perguntas já respondidas.
6. **Nome da conversa.** A conversa se chama `{código} - {dd/mm}`, com a data em que a peça precisa ser publicada (ex.: `R035 - 11/11`; no anúncio, o primeiro dia do teste). Assim que a data for conhecida (vem do brief na Fase 1, ou do estado numa retomada), renomear com `mcp__ccd_session_mgmt__set_session_title` (`session_id` `self`). **Sem data** (peça fora das Diretrizes, anúncio sem briefing, teste sem dia marcado): perguntar ao Rodrigo a data, em uma pergunta, antes de renomear; se ele ainda não souber, nomear `{código} - data a definir` e renomear quando a data entrar. Fora do app do Claude (CLI, Codex), onde a ferramenta não existe, pular sem avisar. Guardar a data no estado (`--set publicacao.data=...`).

---

## Trilha R. Reel

### Fase 1. Brief (`🔍 Próximo passo: ler o brief do R0XX e os últimos Reels publicados (1 passo). Tempo estimado: cerca de 20 segundos.`)

1. Rodar `{PY} {SKILL}/scripts/peca.py brief R035`. Ele procura a peça no arquivo de Diretrizes do mês (`entregas/conteudo-social/Diretrizes_Editoracao_*.html`, o mais recente) e devolve: dia e hora, formato (descoberta, aula, notícia), título, gancho, detalhe, fonte e tipo de capa, mais as peças vizinhas no calendário (para a regra da grade) e os Reels já publicados nos últimos dois meses, com a cor da legenda de cada um.
2. Se a peça não estiver nas Diretrizes (código fora do mês, peça extra), perguntar em uma mensagem: qual é o papel dela (descoberta de segunda ou sexta, aula de quarta, notícia) e qual a data. O resto o debate resolve.
3. Ler, da base de conhecimento, só o que o brief aponta: `meus-produtos/linha-editorial/base-conhecimento/ganchos-consolidados.md` (a seção do gancho citado) e, quando a fonte for a Sessão, `perguntas-da-sessao.md`. Não ler a base inteira.
4. Mostrar o brief em até oito linhas (papel do dia, gancho, de onde vem, capa prevista, data e hora) e seguir direto para a Fase 2. Não pedir confirmação do brief: ele já foi aprovado na sessão de planejamento. Se algo nele contrariar `regras-da-linha.md` (tema fora do domínio, "13" solto, caso de cliente sem autorização), apontar antes de propor ângulos.

Criar a pasta da peça e gravar o estado de uma vez: `{PY} {SKILL}/scripts/peca.py estado R035 --nome NomeEmCamelCase --fase brief --brief`. O nome provisório sai do título do brief, em CamelCase sem espaços (ex.: `QuantoValeOClienteQueVolta`); se o ângulo escolhido mudar o nome, renomear na Fase 3 com `--renomear NovoNome` (o estado e o roteiro ficam dentro da pasta, nada se perde). O brief fica gravado dentro do estado.

### Fase 2. Debate do ângulo (`🔍 Próximo passo: propor os ângulos do R0XX (1 passo). Tempo estimado: cerca de 60 segundos.`)

1. Propor **três ângulos**, cada um em quatro linhas: a primeira frase falada (com o filtro de copy dentro dela), a virada, o que vale salvar e o que o Rodrigo precisa ter (foto, objeto, número conferido). Cada ângulo nasce de uma fala real da base (com o código S, A, M ou W) ou de uma notícia com fonte primária. Nenhum caso inventado.
2. Conferir cada ângulo contra os publicados que o brief trouxe: forma de filtro diferente do Reel anterior, tema e gancho que a linha não usou nos últimos dois meses, capa que obedece à grade.
3. Recomendar um e dizer por quê em uma frase. Perguntar qual ele quer (opções numeradas, mais "misturar" e "outro caminho").
4. Iterar o que ele pedir. Quando ele escolher, gravar o estado: fase `angulo`, com o ângulo e as decisões.

Pergunta de apoio, só se o brief não responder: a peça tem conta para conferir na tela, tem print de notícia, ou é só rosto? A resposta decide se a Fase 3 gera telas.

### Fase 3. Roteiro, nota, capa e telas (`🔍 Próximo passo: escrever o roteiro do R0XX com nota, legenda, capa e textos do YouTube (4 passos). Tempo estimado: 3 a 5 minutos.`)

**Passo 1/4, o roteiro.** A pasta `{PASTA}` existe desde a Fase 1 (se o nome mudou com o ângulo, renomear antes com `peca.py estado R0XX --renomear NovoNome`). Escrever nela `Reels_0XX_NomeEmCamelCase.html` pela anatomia de `references/roteiro-reel.md`: copiar a estrutura do gabarito (R019 em `Publicados/`) e os blocos de gravação e edição do último Reel publicado, nunca inventar layout. O roteiro traz: cabeçalho `.meta` (formato, tipo, duração estimada em palavras e segundos, publicação, objetivo, pilar, CTA, de onde vem), bloco `.nota` com a tabela dos sete critérios, seção 1 com a tabela Tempo / Fala / Câmera / Texto na tela (texto na tela só nos quatro casos da régua, ancorado na palavra falada), bloco de gravação, bloco de plano de edição (nos campos que a `/reels-editar` usa), seção 2 teleprompter, seção 3 legenda, seção 4 capa, seção 5 YouTube, seção 6 pendências.

**Passo 2/4, a revisão.** Manual da Copy e `revisora` sobre fala, legenda, título e descrição. Corrigir direto. Conferir as travas de `regras-da-linha.md` uma a uma (filtro na primeira frase, "para" e "em um", nada de "te paga", "sobra" só no negativo, margem só com custo variável, 13 nunca solto, número exato na tela, fonte conferida). Dar a nota com honestidade pela régua: o que perde ponto fica escrito na coluna "por quê".

**Passo 3/4, capa e telas.**
- Capa: `_CAPA_R0XX_Nome.html` no padrão do R032 (artboard 1080 x 1920, tag a y 330, texto entre y 330 e 1248, zonas seguras ligáveis, botão que baixa o PNG). Tipo pela grade (rosto ou número) conferida com as vizinhas do brief; fundo diferente da capa anterior; headline com sujeito ou frase literal da fala; número que está no vídeo. Capa de rosto fica com um espaço reservado para a foto real, que entra na Fase 5. Capa de número já sai pronta: exportar `CAPA_R0XX_Nome.png` na pasta.
- Aula de quarta: também `_CAPA_R0XX_Nome_YouTube.html` em 1920 x 1080 (painel de texto de um lado, a mesma foto de gesto do outro) e, se a aula tem conta, `_TELA_R0XX_Nome.html` com a seção 1.1 frase por frase (fala, cena, clique), que o `telas.py` da edição lê.
- Reel com cartão animado (contador, preço que cai, conta que monta, grade, régua, veredito): descrever no plano de edição o efeito, a palavra em que entra e o número exato. Efeito inédito é construído e provado em vídeo de teste antes da gravação, pela `/reels-editar`.

**Passo 4/4, mostrar.** Entregar o roteiro com `SendUserFile` (o HTML abre no navegador) e, no chat: a nota com o veredito da régua, os três pontos mais fracos da tabela e o teleprompter inteiro em texto corrido. Perguntar:

```
1. Aprovar o roteiro
2. Quero ajustar algo
```

Ajuste pedido é cirúrgico: muda só o trecho, refaz a nota, mostra o que mudou. Abaixo de 8,0 a skill reescreve antes de mostrar; de 8,0 a 8,9 mostra e aponta o que ajustaria; 9,0 ou mais grava como está.

Com a aprovação, gravar o estado: fase `roteiro_aprovado`, com nota, duração estimada, cor da legenda, tipo de capa e a lista do que falta (bruto, foto da capa, print).

### Fase 4. Pausa para a gravação

Uma mensagem só, e esperar:

- O que gravar: orientação (vertical; aula também na horizontal), enquadramento (espaço acima da cabeça para o título dos 3 segundos; de mais longe se houver veredito em tela cheia), e a regra de erro (respira e repete a frase inteira; fica a última tentativa completa).
- O que mandar além do vídeo: a foto da capa de rosto (mesma luz e fundo da foto do perfil, expressão combinada com o gancho, gesto ligado ao número quando houver), o print da notícia quando o Reel tiver prova.
- Onde salvar: `{PASTA}` (caminho absoluto, texto copiável), e avisar com "gravei".

Nada mais acontece até ele voltar. Se ele voltar com ajuste no roteiro, voltar à Fase 3 (o estado continua `roteiro_aprovado` até a nova aprovação).

### Fase 5. Edição (`🔍 Próximo passo: editar o R0XX do bruto ao vídeo final (6 passos). Tempo estimado: 4 a 6 minutos.`)

1. Confirmar que o bruto está na pasta (`peca.py estado`). Se não estiver, dizer o que falta e parar.
2. **Fechar a capa antes de editar**, porque a edição coloca a capa no primeiro quadro e recorta o título dos 3 segundos dela: capa de rosto recebe a foto real (nunca gerada), cor conferida lado a lado com um quadro do bruto; exportar `CAPA_R0XX_Nome.png` (e a do YouTube, na aula). Mostrar a capa e pedir o ok em uma pergunta.
3. Acionar a skill `reels-editar` (via Skill tool) como sub-skill: ela suprime o próprio `🔍` e segue com `⏳ Passo X/6`. Ela faz a transcrição, a tabela de takes para aprovação, o resumo da edição para aprovação, a render, a conferência (quadros, zonas, volume e respiração um a um) e entrega o `R0XX_editado.mp4` com a prévia leve. Toda aprovação dela é feita com o Rodrigo, aqui na conversa.
4. Depois do vídeo aprovado, atualizar o HTML do roteiro: a duração real no `.meta` e o bloco `id="versao-publicada"` com a fala como foi gravada (a transcrição corrigida da edição), que é a fonte do que foi ao ar. A forma do documento não muda.
5. Gravar o estado: fase `editada`, com duração real, nome do arquivo final e cor da legenda usada.
6. **Limpeza, depois da aprovação do vídeo** (pedido do Rodrigo de 05/11/2026: na pasta ficam só o original e a versão final aprovada, mais o que a peça precisa para ser republicada ou reeditada). Rodar `{PY} {SKILL}/scripts/peca.py limpar R0XX --trabalho` (sem apagar: ele lista), mostrar em uma mensagem o que sai (versões anteriores, prévias, testes, prévias de capa, cópias de transcrição e a pasta de trabalho da edição no computador) e o que fica (bruto, vídeo final, roteiro, capa e telas, legenda, o `_edicao` para reedição, o estado e as fotos), e, com o ok dele, rodar de novo com `--apagar --trabalho`. Registrar no estado `--set edicao.limpeza=true`.

### Fase 6. Publicação (`🔍 Próximo passo: programar o R0XX no YouTube, no Instagram e no Facebook (5 passos). Tempo estimado: 6 a 10 minutos.`)

1. Data e hora vêm do brief (padrão 13h30; nunca entre 17h e 21h). Conferir a linha da grade com as duas peças anteriores e a seguinte: se a regra quebrar, trocar a capa, não a data.
2. Acionar a skill `publicar-reel` (via Skill tool) como sub-skill, passando o código e a data. Ela mostra a ficha 🛡️ única, programa o YouTube pela API, e conduz o Planner no Chrome, onde o Rodrigo escolhe o vídeo e a capa. Nenhuma legenda é reescrita aqui: o texto que vai ao ar é o da seção 3 do HTML.
3. Gravar o estado: fase `programada`, com data, hora, link do YouTube e os canais.

### Fase 7. Fechamento (`⏳ Passo 1/1: fechar a peça.`)

1. Perguntar se pode mover `{PASTA}` para `{REELS}/Publicados/`. Mover só com o ok.
2. Registrar a peça no catálogo de temas (memória `linha-editorial-temas-e-saturacao`: código, tema, família, data) e, se a peça trouxe lição nova de roteiro, capa ou edição, na memória correspondente.
3. Gravar o estado: fase `publicada`.
4. Encerrar com três linhas: o que saiu e quando, o que medir (turbinado julgado no terceiro dia, acima de R$ 1,30 por seguidor pausa; aula medida por salvamento e retenção) e a próxima peça do calendário com o código para abrir a próxima conversa.

```
✅ Concluído: R0XX publicado para {dia} às {hora}. Caminho: meus-produtos/linha-editorial/entregas/reels/Publicados/R0XX - Nome/.
```

Mais o caminho absoluto em texto copiável (regra 4a do CLAUDE.md).

---

## Trilha C. Carrossel

Carrossel da Linha Editorial: terça, quinta, sábado e domingo às 16h, didático, um assunto só, oito lâminas, medido por salvamento. Não tem gravação: o que o Reel resolve na pausa e na edição, o carrossel resolve na produção (fundos e lâminas), sem depender do Rodrigo. Nunca é turbinado. Anatomia do HTML e nomes de arquivo em `references/roteiro-carrossel.md`; nota pela `{CARROSSEIS}/REGUA-NOTA-CARROSSEIS.md`.

### Fase 1. Brief (`🔍 Próximo passo: ler o brief do C### e os últimos carrosséis (1 passo). Tempo estimado: cerca de 20 segundos.`)

1. Rodar `{PY} {SKILL}/scripts/peca.py brief C012`. Para carrossel, além da linha das Diretrizes e das vizinhas na grade (carrossel conta como capa de número), ele devolve os carrosséis recentes com o **layout** de cada um (o nome que fica no comentário do CSS, ex.: "etiqueta de cozinha", "placar de duas colunas") e o texto da capa, para a rotação não repetir.
2. Peça fora das Diretrizes: perguntar o assunto e a data em uma mensagem. O horário é 16h.
3. Ler, da base de conhecimento, só o que o brief aponta (uma aula já publicada, uma seção de `ganchos-consolidados.md`, uma notícia com fonte). Carrossel que nasce de aula de quarta (ex.: "Aula R032") lê a seção 1 do roteiro daquela aula: a conta que o carrossel vai desdobrar em lâminas já está lá.
4. Mostrar o brief em até oito linhas e seguir para a Fase 2.

Criar a pasta e gravar o estado: `{PY} {SKILL}/scripts/peca.py estado C012 --nome NomeEmCamelCase --fase brief --brief`.

### Fase 2. Caminhos (`🔍 Próximo passo: propor os caminhos do C### (1 passo). Tempo estimado: cerca de 60 segundos.`)

1. Propor **três caminhos**, cada um em cinco linhas: o texto da capa (lâmina 1, com o filtro), a ideia que as oito lâminas desdobram, o que vale salvar (a conta, a régua, a lista), o layout proposto (um nome, diferente dos três últimos carrosséis) e o fundo (só tipografia e cor, como o 009, ou fotos do Gemini, como o 003; capa com rosto só com foto real já existente).
2. Conferir cada caminho contra os recentes do brief: layout, tom e estilo que rotacionam; tema não usado nos últimos dois meses; capa dentro da grade; assunto dentro do domínio.
3. Recomendar um e perguntar qual ele quer (opções numeradas, mais "misturar" e "outro caminho"). Gravar o estado: fase `angulo`.

### Fase 3. Lâminas, legenda e nota (`🔍 Próximo passo: escrever o C### em HTML com as 8 lâminas, a legenda e a nota (3 passos). Tempo estimado: 3 a 5 minutos.`)

**Passo 1/3, o HTML.** Escrever `{PASTA}/Carrossel_###_Nome.html` pela anatomia de `references/roteiro-carrossel.md`: copiar o esqueleto de um carrossel recente (variáveis de cor, `.s` de 1080 x 1350, `.pg` com X/X, `.chip`, `body.solo` e o script do `?s=`), dar nome ao layout no comentário do CSS, e escrever as oito lâminas: capa full-bleed com "DONO DE RESTAURANTE" e pouca palavra; lâminas 2 a 7 com **uma ideia cada** e uma frase que puxa a próxima; lâmina 8 com "salva" e a pergunta de uma palavra. Números exatos, com separador; nada abaixo do bloco inferior quando houver foto. O bloco `.ficha` no topo do HTML (escondido no modo solo) guarda o brief, a nota com a tabela dos sete critérios, a legenda e os prompts de fundo. A legenda vai também em `legenda.txt`, que é o que a publicação envia.

**Passo 2/3, a revisão.** Manual da Copy e `revisora` sobre todas as lâminas e a legenda. Travas de `regras-da-linha.md` uma a uma (filtro na capa e na primeira frase da legenda, "para" e "em um", nada de "te paga", "sobra" só no negativo, margem só com custo variável, 13 nunca solto, nada fora do domínio, nenhum caso inventado). Nota pela régua, com o "por quê" em cada linha; abaixo de 8,0 reescreve antes de mostrar.

**Passo 3/3, mostrar.** Entregar o HTML com `SendUserFile` (abre no navegador com as oito lâminas empilhadas, que é a prévia do texto) e, no chat, a nota com os três pontos mais fracos e a legenda inteira. Perguntar:

```
1. Aprovar as lâminas
2. Quero ajustar algo
```

Ajuste é cirúrgico. Com a aprovação, gravar o estado: fase `roteiro_aprovado`, com nota, layout, fundo (tipografia ou fotos) e pendências (foto real para capa de rosto, número a confirmar).

### Fase 4. Produção (`🔍 Próximo passo: produzir as lâminas do C### (2 passos). Tempo estimado: {cerca de 30 segundos sem foto | 5 a 8 minutos com fotos do Gemini}.`)

**Passo 1/2, os fundos (só quando o layout usa foto).** Pelo Claude in Chrome, no Gemini, com a conta rodrigo.haertel@docustoaolucro.com (conferir a conta na tela antes de gerar). Uma conversa só para todas as fotos, para a luz não mudar. Cada prompt do `.ficha`: foto de fundo **sem texto e sem gente**, luz de dia clara, proporção pedida no prompt ("VERTICAL 4:5" para lâmina inteira; horizontal 3:2 para a metade de cima). Baixar e renomear para `Carrossel_###_Nome_fundo_0N.jpg` na pasta. Quando o Chrome barrar o download em série, usar o caminho da memória `carrossel-convencao-arquivo` (abrir a imagem pelo link direto, canvas, área de transferência e salvar pelo PowerShell). Capa com rosto usa foto real do Rodrigo (`Carrossel_###_Nome_foto_capa.jpg`), nunca gerada; se não houver foto adequada na pasta ou no kit, pedir uma a ele em uma mensagem e esperar.

**Passo 2/2, as lâminas.** Rodar `{PY} {SKILL}/scripts/laminas.py "{PASTA}"`: ele abre o HTML no Chrome sem janela, uma lâmina por vez (`?s=N`), grava `Carrossel_###_Nome_01.png` a `_08.png` em 1080 x 1350 e monta a prévia `_previa_###.jpg` (quatro por linha). Abrir a prévia e conferir: todo texto dentro da lâmina, acentos certos, X/X em todas, bloco inferior na mesma altura em todas as lâminas de conteúdo, fonte carregada (Inter, não a fonte do sistema). Problema → corrigir o HTML e rodar de novo.

Mostrar a prévia com `SendUserFile` e perguntar:

```
1. Aprovar e programar
2. Quero ajustar algo
```

Gravar o estado: fase `editada` (lâminas aprovadas), com o número de lâminas e se houve fundo gerado.

### Fase 5. Publicação (`🔍 Próximo passo: programar o C### no Instagram e no Facebook (4 passos). Tempo estimado: 3 a 5 minutos.`)

1. Data e hora do brief (16h; nunca entre 17h e 21h). Conferir a grade: as duas peças anteriores e a seguinte, com o carrossel valendo como capa de número.
2. **Ficha 🛡️ única**, e esperar o "sim": código, dia e hora, oito lâminas (nomes e tamanho total), primeiros 125 caracteres da legenda, tamanho e hashtags, canais (Facebook Rodrigo Haertel e Instagram rodrigohaertel), "Compartilhar no Story do Facebook" ligado, alertas. Reversível até o horário, pelo Planner.
3. Carregar as ferramentas do Chrome em uma chamada `ToolSearch` (`tabs_context_mcp, tabs_create_mcp, navigate, computer, find, read_page, file_upload, javascript_tool, get_page_text, browser_batch`) e seguir o roteiro de `references/roteiro-carrossel.md`, seção "Planner": abrir o calendário, Criar post, conferir "Postar em" com os dois canais, preparar o campo de arquivo (sobrescrever `HTMLInputElement.prototype.click` e `showPicker` para o input de arquivo ficar no DOM sem abrir a janela do Windows), clicar em Adicionar foto/vídeo por JavaScript, achar o input com `find` e subir as lâminas com `file_upload` em ordem (até 10 MB por chamada), conferir a contagem e a ordem na prévia, digitar a legenda de `legenda.txt` pela coordenada e conferir com `javascript_tool`, ligar "Definir data e hora", data pelo calendário e hora nos spinbuttons dos dois canais, conferir, botão azul **Programar**, fechar o aviso de turbinar em "Talvez mais tarde". Nunca "Compartilhar agora" nem "Publicar agora".
4. Confirmar os dois cards no dia e na hora. Gravar o estado: fase `programada`, com data e hora.

Se a aba travar com "Cannot access a chrome-extension:// URL", esperar até um minuto sem recarregar e tentar de novo; se não liberar, pedir ao Rodrigo um clique na aba.

### Fase 6. Fechamento (`⏳ Passo 1/1: fechar a peça.`)

1. Perguntar se pode mover `{PASTA}` para `{CARROSSEIS}/Publicados/`, avisando na mesma pergunta que a prévia `_previa_###.jpg` sai (fica o HTML, as lâminas, os fundos e a legenda). Mover e limpar (`peca.py limpar C### --apagar`) só com o ok.
2. Registrar o carrossel (código, tema, layout, tom) na memória de rotação `carrossel-convencao-arquivo`, e lição nova em `references/regras-da-linha.md` ou na régua.
3. Gravar o estado: fase `publicada`. Encerrar com três linhas: o que sai e quando, o que medir (salvamentos e compartilhamentos; o alcance vem do Story do dia) e a próxima peça do calendário.

```
✅ Concluído: C### programado para {dia} às 16h. Caminho: meus-produtos/linha-editorial/entregas/carrosseis/Publicados/Carrossel_###_Nome/.
```

---

## Trilha A. Anúncio em vídeo do Dono 14%

Anúncio de conversão da mentoria: vende a Sessão Estratégica de 30 minutos, para dono de restaurante de R$ 100 mil a R$ 300 mil por mês, em teste de 7 dias a R$ 60 por dia. A espinha é a do Reel (brief, ângulo, roteiro com nota, pausa para a gravação, edição, publicação, fechamento), com três diferenças: o brief vem da leva (não das Diretrizes), a edição carrega motion e tag fixa, e a publicação é uma escrita na conta Meta, que passa pelo gate 🛡️ do CLAUDE.md. Anatomia em `references/roteiro-anuncio.md`; regras em `references/regras-do-anuncio.md`; nota pela `{CRIATIVOS}/REGUA-NOTA-ANUNCIOS.md`.

### Fase 1. Brief (`🔍 Próximo passo: ler o brief do A## e as peças recentes da conta (1 passo). Tempo estimado: cerca de 20 segundos.`)

1. Produto ativo `dono-14`; ler `meus-produtos/dono-14/resumo-produto.md` (o contexto padrão do CLAUDE.md).
2. Rodar `{PY} {SKILL}/scripts/peca.py brief A58`. Ele procura a peça nos `briefing-*.html` da pasta de criativos (o mais recente primeiro) e devolve a linha dela (título, ângulo pela Mandala, gancho e prova, fonte, teste e capa), as outras peças da mesma leva e os **anúncios recentes** (código, título, nota, Mandala, conceito nomeado, inimigo), que servem para não repetir DNA.
3. Sem briefing com o código: perguntar em uma mensagem qual é o ângulo e a prova que ele quer (notícia com fonte, pesquisa dos 482, jornada de 5 a 14, uma ideia da call de copy), e seguir. Não inventar a leva.
4. Ler o cockpit só pela tabela do mapa (`meus-produtos/dono-14/trafego/analise/historico-criativos-a30-a38.html`) e, se existir, a régua de veredito em `meus-produtos/dono-14/trafego/reguas-criativos.md`. Não reler os roteiros antigos inteiros: o brief já trouxe o resumo.
5. Mostrar o brief em até oito linhas e seguir para a Fase 2. Se algo contrariar `regras-do-anuncio.md` (promessa acima do teto, caso de terceiro como filtro, tema fora do domínio, 13 solto), apontar antes.

Criar a pasta e gravar o estado: `{PY} {SKILL}/scripts/peca.py estado A58 --nome "Mentoria - 9x16" --fase brief --brief`.

### Fase 2. Ângulo (`🔍 Próximo passo: propor os ângulos do A## (1 passo). Tempo estimado: cerca de 60 segundos.`)

1. Propor **três ângulos**, cada um em seis linhas: o tipo da Mandala (e o de apoio), a primeira frase falada (QUEM e TAMANHO dentro dela, em segunda pessoa), o mecanismo de prova no corpo (dado com fonte e data, demonstração ou inimigo com virada), o conceito nomeado e o inimigo concreto, a redação nova do convite (escassez real na frente), e a textura de gravação (gancho em movimento em lugar real, corpo sentado).
2. Conferir cada ângulo contra os recentes do brief e a seção 3 de `regras-do-anuncio.md`: DNA de peça aposentada fora (o "de cabeça eu não sei" do A47, o personagem quebrando do A48, o faturamento em terceira pessoa do A50), Mandala que rotaciona, teto de promessa, nada político.
3. Recomendar um e perguntar qual ele quer (opções numeradas, mais "misturar" e "outro caminho"). Leva com vários ganchos sobre um corpo (padrão A54 a A57) é uma opção quando há prazo e uma notícia forte. Gravar o estado: fase `angulo`.

### Fase 3. Roteiro, nota, capa e plano de edição (`🔍 Próximo passo: escrever o roteiro do A## com nota, legenda da Meta, capa e plano de edição (4 passos). Tempo estimado: 3 a 5 minutos.`)

**Passo 1/4, o roteiro.** Escrever `{PASTA}/A## - Mentoria - roteiro.html` pela anatomia de `references/roteiro-anuncio.md`, copiando a estrutura do A52: `.meta`, nota, a prova número por número (com a tabela "como está na notícia / como vai na peça" e "o que a peça não diz"), as premissas aplicadas, A legenda da Meta, B headline e descrição, C roteiro em beats com a coluna "Na tela", D capa com os valores em pixel, E direção visual, F locução com contagem, H plano de edição com motion (um bloco por efeito, a palavra de entrada e o número exato; efeito inédito marcado), checagem Light Copy e teto de promessa, "o que o revisor marcou", "como será julgado" e "a leva".

**Passo 2/4, a revisão.** Manual da Copy e `revisora` sobre locução, legenda, headline e descrição. As dez conferências da seção 4 de `roteiro-anuncio.md`, uma a uma. Nota pela régua com o "por quê"; abaixo de 8,0 reescreve antes de mostrar.

**Passo 3/4, a capa e o efeito novo.**
- Capa: `_CAPA_A##_Nome.html` (1080 x 1920, chip com fonte e data em y 330, linha branca e resposta em amarelo `#f2c14e`, degradê a partir de y 1050, texto até y 1545, espaço reservado para a foto real). Headline com sujeito ou frase literal da fala, com número que está no vídeo. A foto entra na Fase 5.
- Efeito de tela que ainda não existe no motor da `/reels-editar`: anotar no plano de edição e, antes da gravação, construir e provar em `_teste_motion_A##.mp4` com um bruto antigo, pela `/reels-editar` (sub-skill). Sem aprovação do visual, o roteiro não vai para gravação.

**Passo 4/4, mostrar.** `SendUserFile` com o HTML e, no chat: a nota com os três pontos mais fracos, "o que o revisor marcou e não corrigiu" e a locução inteira em texto corrido (com a contagem de palavras e os dois tempos, a 2,2 e a 2,24 palavras por segundo). Perguntar:

```
1. Aprovar o roteiro
2. Quero ajustar algo
```

Ajuste é cirúrgico (versão N registrada no cabeçalho, com data). Ao tirar uma frase, conferir capa, título dos 3 s, headline e legenda na mesma hora. Com a aprovação, gravar o estado: fase `roteiro_aprovado`, com nota, Mandala, duração estimada, cor da legenda e pendências (dado a confirmar, foto, efeito a construir).

### Fase 4. Pausa para a gravação

Uma mensagem só, e esperar:

- Onde e como: lugar real (salão, entrada ou calçada de restaurante); gancho andando, câmera acompanhando, olhar direto, sem zoom; da cena em diante sentado, câmera parada, rosto cheio. Espaço acima da cabeça e ao redor dos ombros. Errou, respira e repete a frase inteira. Lapela com folga para não saturar. Se ele quiser, cronometrar a locução antes.
- As fotos da capa, no mesmo lugar, logo depois do take: seis a oito, a expressão combinada com a capa (sério e olhar direto para notícia ruim), mãos fora da zona do texto, microfone fora do quadro.
- O print da notícia, quando houver prova em página real.
- Onde salvar: `{PASTA}` (caminho absoluto, texto copiável), com o código na frente do nome do vídeo, e avisar com "gravei".

Nada mais acontece até ele voltar.

### Fase 5. Edição (`🔍 Próximo passo: editar o A## do bruto ao vídeo final (6 passos). Tempo estimado: 4 a 6 minutos.`)

1. Confirmar o bruto na pasta (`peca.py estado`). Mostrar as fotos da capa com uma prévia montada (`_A## - capa previa (foto N).jpg`) e pedir a escolha em uma pergunta; exportar `CAPA_A##_Nome.png` com o bloco de título do vídeo e a mesma cor do vídeo (regra do A52 na `/reels-editar`).
2. Acionar a skill `reels-editar` (via Skill tool) como sub-skill, com o código `A##`: ela reconhece a pasta do anúncio, transcreve, monta o `_edicao_A##.json` a partir do plano de edição (tag fixa "DONO DE RESTAURANTE" do segundo 3 ao fim, capa no primeiro quadro, `titulo_sem_entrada`, cartões em tela dividida com fundo vidro, número falado igual ao da tela, positivo em verde, até cinco cartões), mostra a tabela de takes e o resumo para aprovação, renderiza, confere e entrega `A##_editado.mp4` com a prévia leve. Versão palco só se ele pedir uma B de teste.
3. **Ficha do publicado**, pela transcrição do vídeo final: duração real, ritmo e **o segundo em que o filtro de faturamento é falado**. Acima de 15 s, avisar antes de seguir (cortar ou regravar o gancho); é o que separou o A47 do A48.
4. Atualizar o HTML: seção "I. Gravado em dd/mm. Notas para o editor" (take, duração, o que mudou da locução, versão escolhida) e a duração real no `.meta`.
5. Gravar o estado: fase `editada`, com duração real, segundo do filtro, arquivo final e cor da legenda.
6. **Limpeza, depois da aprovação do vídeo**, igual à do Reel: `peca.py limpar A## --trabalho` para listar, mostrar o que sai e o que fica (os recortes e cartões que o `_edicao` usa ficam; versões anteriores, testes de motion, prévias de capa e a cópia da transcrição saem), ok do Rodrigo, `--apagar --trabalho`. Uma versão B (palco) só fica se ele pediu teste A contra B. Registrar `--set edicao.limpeza=true`.

### Fase 6. Publicação na conta (`🔍 Próximo passo: criar o teste do A## na conta de anúncios (4 passos). Tempo estimado: 3 a 5 minutos, mais o envio do vídeo.`)

**Passo 1/4, conexão e mídia.** Ler `META_AUTH_MODO` e conferir `FB_AD_ACCOUNT_ID` pelo padrão da seção "LEITURA SEGURA DO .env" do CLAUDE.md (`grep -q`, nunca mostrar valor); vazio ou inválido, acionar `/trafego-conexao` e voltar. No `MCP_CONECTOR`, pedir ao Rodrigo em uma mensagem: subir `A##_editado.mp4` e `CAPA_A##_Nome.png` na Biblioteca de mídia do Gerenciador e avisar "subi"; achar o vídeo com `ads_get_ad_videos` (pelo título, conferir `status`) e a capa com `ads_get_ad_images` (hash). No `APP`, subir pelo `curl` (um por chamada, `graph-video` para o vídeo, token por substituição) e esperar `video_status` `ready`.

**Passo 2/4, o plano do teste.** Ler com `ads_get_ad_entities` a campanha ABO do Dono 14% e o último conjunto aprovado (A51 ou A52): id, `targeting`, otimização, atribuição, UTM do anúncio. Montar o plano: conjunto `A## - Frio 25-55 - Feed+Reels` copiado dele, R$ 60 por dia, do dia seguinte 00h01 ao sétimo dia 23h59; criativo com o vídeo, a capa como miniatura, legenda A, headline e descrição B, botão Saiba mais, link `/sessao` com os UTMs do padrão, "vários anunciantes" desligado; anúncio `A##` em rascunho ou pausado. Leva com vários ganchos: um conjunto, N anúncios, R$ 30 por anúncio por dia. Conferir a regra "no máximo duas peças novas por vez" e dizer o que sai.

**Passo 3/4, o gate.** Mostrar o bloco 🛡️ no formato do CLAUDE.md (operação, endpoint humano, objetos, o que vai mudar linha por linha com valores, reset de aprendizado: não, porque é conjunto novo; reversível: sim, pausando) e **esperar o "sim"**. Um bloco para o lote inteiro (conjunto, criativo e anúncio). Nunca mostrar `curl` nem token.

**Passo 4/4, criar e conferir.** Com o "sim": `ads_create_ad_set` (com `source_adset_id`, orçamento na unidade que o schema pedir, datas, `advantage_audience` 0 e `advantage_audience_off_reason` ADVERTISER_REQUESTED_OFF), `ads_create_creative` (vídeo, miniatura, página, Instagram, textos, botão, link, `contextual_multi_ads` OPT_OUT se o schema aceitar), `ads_create_ad`. Conferir `active_errors`. O conector cria em **rascunho**: dizer isso com todas as letras; quem publica é o Rodrigo no Gerenciador, ou a skill com `ads_activate_entity` na campanha, só com um segundo "sim" explícito dele. Depois, ler tudo de volta com `ads_get_ad_entities` e conferir orçamento, datas, targeting, otimização, UTM e status, e lembrar: "confere no Gerenciador se 'Anúncios com vários anunciantes' está desmarcado e se o texto principal é o da seção A". No modo `APP`, os mesmos passos por `curl`, um por chamada.

Caminho alternativo, se ele preferir criar à mão: entregar a lista de configuração da peça (a mesma do bloco 🛡️) para o Gerenciador e, quando ele disser "criei", conferir pela API.

Gravar o estado: fase `programada`, com ids do conjunto, do criativo e do anúncio, datas do teste e a data do veredito (dia 8).

### Fase 7. Fechamento (`⏳ Passo 1/1: fechar a peça.`)

1. Registrar a peça no cockpit (uma linha no mapa de construção: código, ângulo e Mandala, gancho em uma frase, conceito, origem e DNA, duração real, registro, link para o roteiro) e, se a rotina das 02h tiver plano de orçamento (`scripts/dono14-orcamento.py`), a entrada e a data de fim do teste.
2. Perguntar se pode mover `{PASTA}` para `{CRIATIVOS}/Publicados/` quando o anúncio estiver no ar. Mover só com o ok.
3. Lição nova (reprovação, padrão) entra em `references/regras-do-anuncio.md` ou na régua, na mesma sessão. Gravar o estado: fase `publicada`.
4. Encerrar com três linhas: o teste (datas e verba), o que se lê no dia 3 (hook contra 33 a 40%, CTR contra o A39) e no dia 8 (CPL de perfil até R$ 170, metade no perfil, uma Sessão, lead real pelo banco), e a próxima peça da leva.

```
✅ Concluído: A## criado na conta, teste de {dd/mm} a {dd/mm} a R$ 60 por dia. Caminho: meus-produtos/dono-14/entregas/criativos/A## - Mentoria - 9x16/.
```

---

## O arquivo de estado

`{ESTADO}` nasce na Fase 1 e é atualizado ao fim de cada fase, pelo script: `{PY} {SKILL}/scripts/peca.py estado R035 --fase roteiro_aprovado --set nota=9.4 --set cor_legenda=laranja` (cada `--set chave=valor` grava um campo; o histórico de fases com data é mantido pelo script). Modelo em `references/modelo-estado.json`. Fases, nesta ordem: `brief`, `angulo`, `roteiro_aprovado`, `editada`, `programada`, `publicada`.

Para que serve: a conversa de uma peça atravessa dias (o roteiro sai hoje, a gravação é amanhã, a publicação depois). O estado deixa a retomada segura quando a conversa for resumida pelo sistema ou quando a peça for aberta em outra sessão. Ele guarda decisões, não texto: o texto vive no HTML.

O arquivo começa com `_` para as skills de edição e publicação o ignorarem, como já fazem com `_edicao_R0XX.json`.

---

## Regras

- Entrada sempre por `/peca` com o código. Mensagem solta ("vamos fazer o próximo Reel") também cai aqui, mas o código é confirmado antes de criar pasta.
- A conversa se chama `{código} - {dd/mm}` (data de publicação). Sem data conhecida, perguntar antes de nomear.
- Depois da aprovação do vídeo, a pasta fica só com o original, a versão final e o que a peça precisa para republicar ou reeditar; a limpeza lista antes e apaga só com o ok (`peca.py limpar`).
- As bases do método (Mandala, anúncios em vídeo, conteúdo, elementos literários, checklist Light Copy, revisora) entram como referência na fase do roteiro, nunca como entrevista.
- Brief vem da sessão de planejamento (Diretrizes do mês). A peça não rediscute o calendário: se o Rodrigo quiser mudar dia, papel ou tema, anotar como pendência e seguir com o que ele decidir agora.
- Uma pergunta por mensagem. Aprovação em dois pontos fixos: roteiro (Fase 3) e capa (Fase 5), mais as aprovações internas da edição e a ficha da publicação.
- Nunca mostrar JSON, HTML ou comando. Nunca dizer que rodou a revisora.
- Nada de caso, número ou depoimento inventado. Fonte real ou não entra.
- Caminho absoluto em texto copiável sempre que um arquivo for salvo.
- Lição nova do Rodrigo (reprovou algo, pediu um padrão) vira linha em `references/regras-da-linha.md` ou na régua correspondente, na mesma sessão, para a próxima peça já nascer certa.

---

## Arquivos da skill

| Arquivo | Função |
|---|---|
| `scripts/peca.py` | `brief` (lê as Diretrizes ou o briefing da leva, mais as peças recentes da trilha), `estado` (lê a pasta e grava o `_peca_*.json`), `proximo` (próximos códigos R, C e A), `limpar` (lista e, com o ok, apaga os arquivos de trabalho da edição) |
| `scripts/laminas.py` | exporta as lâminas do carrossel em PNG pelo Chrome sem janela e monta a prévia `_previa_###.jpg` |
| `references/regras-da-linha.md` | tudo que vale para toda peça: voz, filtro, linguagem, método, fontes, estrutura, tela, capa, horário |
| `references/roteiro-reel.md` | anatomia do `Reels_0XX_*.html` e os encaixes com `/reels-editar` e `/publicar-reel` |
| `references/roteiro-carrossel.md` | anatomia do `Carrossel_###_*.html`, nomes de arquivo da produção e roteiro do Planner |
| `references/roteiro-anuncio.md` | anatomia do `A## - Mentoria - roteiro.html`, nomes de arquivo, brief por leva e resumo da publicação na conta |
| `references/regras-do-anuncio.md` | o que é só do anúncio: oferta e teto de promessa, público e filtro, estrutura, duração, produção, tela, capa, linguagem, fontes, teste e veredito |
| `references/trilhas-pendentes.md` | histórico: como cada trilha foi montada e o que ainda falta calibrar |
| `references/modelo-estado.json` | modelo do arquivo de estado |
