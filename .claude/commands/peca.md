---
name: workshop-marketing:peca
description: Uma conversa por criativo. Conduz a peça (Reel R###, carrossel C###, anúncio A##) do brief da sessão de planejamento até a publicação, retomando de onde parou. Ex.: /peca R035, /peca R035 gravei, /peca (sem código lista os próximos).
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, WebSearch, WebFetch, ToolSearch, SendUserFile, mcp__claude-in-chrome__*
---

# /peca

Acionar a skill `peca` e seguir do Passo 0 (código, pasta e estado) até a fase em que a peça está.

O código vem do argumento (ex.: `/peca R035`). Sem argumento, a skill lista o próximo Reel, o próximo carrossel e o próximo anúncio, e pergunta qual abrir. Palavras depois do código ("gravei", "publica", "ajusta o roteiro") dizem em que ponto o Rodrigo quer entrar; o estado da pasta confirma.

A skill cuida de tudo: brief das Diretrizes do mês, debate do ângulo, roteiro em HTML com nota, capa e telas, pausa para a gravação, edição pela `/reels-editar`, publicação pela `/publicar-reel` e fechamento em `Publicados/`. Carrossel e anúncio ainda estão em construção: a skill avisa e segue pelo caminho atual.
