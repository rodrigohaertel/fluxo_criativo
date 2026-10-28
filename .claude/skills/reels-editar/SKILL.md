---
name: reels-editar
description: Edita um Reel da Linha Editorial (e os anúncios em vídeo do Dono 14%, padrão do A52) do bruto gravado até o MP4 final, no padrão aprovado pelo Rodrigo no R024 e no R027 (16 a 18/10/2026), sem CapCut. Faz áudio D (reduzir ruído + aprimorar voz 75% + volume a -14 LUFS), cor C medida no rosto, cortes só em pausa acima de 1 s, zoom suave nas frases de virada, legenda Montserrat maiúscula com uma cor por vídeo, título dos 3 primeiros segundos no padrão da capa, cartões de prova em tela dividida e capa no primeiro quadro. Use quando o usuário pedir "editar o R028", "edita o Reel", "monta o vídeo do R030", "tira o CapCut desse", "/reels-editar R028".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /reels-editar

Leva um Reel da pasta `meus-produtos/linha-editorial/entregas/reels/R0XX - Nome/` do bruto ao `R0XX_editado.mp4`, no padrão que o Rodrigo aprovou no R024 e no R027. O motor é `scripts/editar_reel.py`, guiado por um JSON de edição (`_edicao_R0XX.json`) que esta skill monta a partir da fala, do roteiro e da capa.

Regras de conversa (CLAUDE.md): pt-BR com acentuação, **uma pergunta por vez**, opções numeradas, **nenhum código, JSON ou comando mostrado ao Rodrigo**. Ele vê o resumo em linguagem de editor, não o arquivo.

Caminhos usados abaixo:
- `{SKILL}` = `.claude/skills/reels-editar`
- `{PY}` = o Python que roda os scripts (`py -3` no Windows do Rodrigo; conferir com `py -3 --version` na primeira vez da sessão, senão `python3`)
- `{TRAB}` = `%LOCALAPPDATA%\reels-editar\trabalho\R0XX\` (arquivos intermediários, fora do OneDrive)

---

## Anúncio inicial

Tempos da seção "Edição de Reels" de `.claude/rules/tempo-estimado.md`:

```
🔍 Próximo passo: editar o {código} do bruto ao vídeo final (6 passos). Tempo estimado: 4 a 6 minutos.
```

Sub-passos com `⏳ Passo X/6:`. O tempo de espera da aprovação do resumo não conta.

---

## Passo 0. Ferramentas instaladas

Rodar `{PY} {SKILL}/scripts/instalar.py --verificar`.

- Tudo ✅: seguir.
- Faltou algo: avisar em uma linha ("Falta instalar o {item} no computador, faço agora?") e, com o sim, rodar `{PY} {SKILL}/scripts/instalar.py` (sem `--verificar`). Detalhes e casos especiais em `references/instalacao.md`. Se faltar FFmpeg ou PyTorch com CUDA, o script diz o comando: repassar ao Rodrigo em português, sem mostrar o comando a menos que ele precise colar.

---

## Passo 1. Achar a pasta e preparar (`⏳ Passo 1/6: transcrever a fala e medir o enquadramento.`)

1. Código do Reel: vem da mensagem (ex.: R028). Se faltar, listar as pastas `R### - Nome` que têm vídeo bruto e ainda não têm `R0XX_editado.mp4`, e perguntar qual (opções numeradas).
2. Rodar `{PY} {SKILL}/scripts/preparar.py "{caminho da pasta}"`. Ele:
   - acha o **bruto** (maior `.mp4`/`.mov` sem `_` no começo e sem `editado` no nome; se a pasta tiver `… - Vertical.mp4` e `… - Horizontal.mp4`, pega o vertical, ou o horizontal com `--horizontal`, e o trabalho vai para `R0XXV` ou `R0XXH`), a **capa** `CAPA_*.png`, o **roteiro** `Reels_*.html` e os **cartões** `TELA_*.png`;
   - transcreve duas vezes com o Whisper na placa de vídeo: a fala inteira (`palavras.json`, base da legenda) e **fala por fala** (`palavras_por_fala.json`, que separa duas tentativas da mesma frase);
   - grava em `{TRAB}`: `fala.txt`, `fala_por_fala.txt` (cada fala entre pausas, com início e fim), `rosto_grade.jpg` e `preparo.json` (resumo, que ele também imprime).
3. Se sair `SEM_BRUTO`: avisar que a pasta ainda não tem o vídeo gravado e parar.
4. Se o Reel já tem `_edicao_R0XX.json` na pasta (reedição), partir dele e pular para o Passo 3 com as mudanças que o Rodrigo pediu.
5. **Sempre ler a `fala_por_fala.txt` inteira pelo sentido** e seguir "Erros e regravações" (no Passo 2) antes de montar o JSON. Mesmo em Reel curto de take único: erro de sentido não é repetição de palavra.

---

## Passo 2. Montar o JSON de edição (`⏳ Passo 2/6: marcar zoom, cartões, título e legenda.`)

Ler `fala.txt`, `preparo.json`, a imagem `rosto_grade.jpg`, o roteiro (seção "1. Roteiro com tempos, movimentos e cenas" e os blocos de edição) e o `_CAPA_R0XX_*.html`. Copiar `{SKILL}/references/modelo-edicao.json` para `_edicao_R0XX.json` na pasta do Reel e preencher. Caminhos de arquivo só com o nome (valem a partir da pasta do Reel). Não incluir `trabalho`, `audio16k` nem `palavras`: o editor acha sozinho pelo `codigo`.

| Campo | Como decidir |
|---|---|
| `inicio` | `inicio_sugerido` do preparo (primeira palavra menos 0,1 s). |
| `fim` | fim da **última palavra real** + **1,0 s** de respiro (padrão aprovado; terminar colado na palavra ficou "seco"). Palavras de confiança baixa depois do CTA são conversa pós-gravação (no R027, "There we go") e ficam de fora. |
| `rosto` | centro do rosto em fração da tela `[x, y]`, lido na grade de `rosto_grade.jpg` (linhas a cada 0,1). Ex.: R024 `[0.53, 0.43]`, R027 `[0.546, 0.344]`. É a âncora do zoom e da cor. |
| `zoom` | 3 a 5 frases de virada do roteiro: a tese, o número que vira a chave, a conclusão e sempre o CTA (`me segue` → `dono de restaurante`, 1.1). `de` e `ate` são trechos **exatos da fala** (como em `fala.txt`; número por extenso ou em algarismo dá no mesmo). Zoom 1.14 a 1.18 nas viradas; `empurra: true` com 1.22 a 1.30 na frase mais forte (aproximação lenta ao longo da frase inteira). Ordem cronológica. |
| `cartoes` | um por `TELA_*.png`, em ordem. `palavra` = a palavra falada em que o cartão entra (do roteiro, onde a cena pede a tela). `dura` 2 a 3 s. Cartões colados viram uma janela só. Sempre `tela_dividida: true` (nunca cartão por cima do rosto). |
| `contadores` | **número que cresce** (aprovado como teste em 18/10, no R024): cartão animado na tela dividida, em que o número sobe do `de` ao `ate` em `subida` segundos (desacelerando), pulsa ao parar e mostra o `detalhe` embaixo; barra dourada acompanha a contagem. `palavra` = trecho exato da fala em que o número começa a subir; `dura` 3 a 3,5 s; `casas` decimais da contagem; `prefixo`/`sufixo` (ex.: `R$ `); `texto_final` opcional quando o número para escrito de outro jeito (`R$ 4 BILHÕES`); `rotulo` em cima (o que é o número); `cor` `verde` (ganho), `vermelho` (perda) ou `tinta`. Entra na mesma janela de tela dividida dos cartões. Usar para o número central que o roteiro marca no plano de edição. Com `tipo` (padrão `numero`), o mesmo campo faz mais dois cartões animados, desenhados no `scripts/animacoes.py` (construídos em 20/10 para o R028): **`troca`, preço que cai**: `antes` e `depois` (`{"titulo", "valor"}`), `rotulo`, `selo` (ex.: `R$ 8,00 a menos no quilo`); o preço de sempre entra no centro, em `palavra_meio` desliza para a esquerda e entra a coluna nova com `R$ ?`, e em `palavra_troca` o preço novo aparece em verde, um risco vermelho corta o antigo e sobe o selo dourado. **`conta`, conta que monta**: `termos` (ex.: `["R$ 8,00", "400 kg"]`) entram um a um, e em `palavra_resultado` uma linha dourada corre e o resultado sobe até `ate`, com `detalhe` embaixo. Em qualquer tipo, `fim` ancora o fim do cartão no fim de uma palavra falada (mais `folga`, 0,4 s) no lugar de `dura`; cartão que acaba a menos de 0,6 s do próximo fica até o próximo entrar. Até quatro cartões animados por vídeo, sempre nos números que o dono confere. **Efeitos de 21/10 (construídos para o A52, em `scripts/animacoes2.py`, aprovados em vídeo de teste):** `destaque` (recorte real de uma página, `imagem`, com marca-texto varrendo a `caixa` do trecho em `palavra_marca` e aproximação lenta; `credito` embaixo), `grade` (grade de 10 × 10 que se preenche por `grupos` coloridos a partir de `palavra_preenche`; em `palavra_destaque` um grupo pulsa e o número grande sobe; `modo` `acende` para só N quadrados acenderem) e `regua` (régua de porcentagem, marcador desliza de `de` a `ate` em `palavra_desliza`, `valor_de`/`valor_ate` nas pontas, trecho dourado e `selo` em `palavra_selo`). O efeito de tela cheia `distancia` (dois chips que se afastam com a linha dourada, para o take andando) está no mesmo módulo e ainda precisa de uma camada de tela cheia no editor, a ser ligada quando o A52 for editado. **Tempo de leitura (R028):** o resultado de cada cartão fica pelo menos 3 s visível depois de revelado; emendar os cartões em sequência (o `fim` de um encostado no `palavra` do próximo), sem o rosto piscar entre eles; o número que cresce pode entrar na própria palavra do número para dar mais tempo ao cartão anterior; o último cartão segura 1,5 s depois da fala (`folga`). |
| `div_altura` e `div_topo` | rosto muito de perto (cabeça de y 0,17 a 0,72, como no R028): na tela dividida a câmera mostra um pedaço maior do quadro (`div_altura` 1250 px a partir de `div_topo` 240), reduzido para caber na metade de baixo, com o mesmo trecho desfocado nas laterais. Sem os campos, a metade de baixo é um recorte de 960 px. |
| `titulo` | as linhas da capa, em maiúscula: as de cima em preto, a **última** na tarja vermelha. Vêm do texto do `_CAPA_*.html` (a linha do selo vira `pilula`, normalmente `DONO DE RESTAURANTE`). Se a capa for longa demais para 3 s, usar o gancho do roteiro em 3 linhas curtas. |
| `titulo_fundo` | a cor de fundo da capa: o `backgroundColor:'#......'` do `_CAPA_*.html` (R024 amarelo `#F4C63A`, R028 lilás `#E6DDF3`). `titulo_selo` `#0A1712` em fundo claro. |
| `titulo_y` e `titulo_tamanho` | pelo enquadramento em `rosto_grade.jpg`: **rosto baixo** (cabeça abaixo de y 0.25, sobra parede) → título na parede, `titulo_y` 300, tamanho 56. **Rosto alto** (cabeça encostando em y 0.2) → título no peito, `titulo_y` 900, tamanho 64. O editor trava entre y 300 e 1248. |
| `palavras_chave` | 5 a 8 trechos marcados na cor da legenda o tempo todo: números centrais, o termo da tese, a conclusão e `me segue`. Trechos exatos da fala. |
| `cor_legenda` | `amarelo`, `laranja`, `dourado`, `lilas`, `rosa`, `ciano`, `verde` ou `vermelho`, **diferente da do Reel anterior** e que **case com os cartões e a capa** (R028: o verde brigava com o verde dos preços nos cartões; ficou dourado, a cor dos selos). Na dúvida, mostrar ao Rodrigo a prévia das cores num quadro do vídeo antes de renderizar: ler o `_edicao_R0XX.json` do maior código abaixo do atual que tiver um. Evitar a cor igual ao fundo do título. Uma cor fixa do começo ao fim. |
| `trocas` | sempre `["pra", "para"]` (padrão de fala na legenda); acrescentar correções de grafia que o Whisper errou. |
| `pausas_manter` | só se o roteiro marcar uma pausa dramática acima de 1 s que não pode ser encurtada (tempo de início da pausa, de `pausas_acima_de_1s`). |
| `remover` | takes descartados (erros e regravações), `[[início, fim], ...]` no tempo do bruto. Ver "Erros e regravações" abaixo. **Só preencher depois de o Rodrigo aprovar a lista.** |
| `cenas_obs` | `true` quando o bruto é aula gravada no OBS que alterna só rosto e tela dividida já montada (aula creme em cima). O editor detecta as cenas sozinho: zoom só no rosto, legenda da tela dividida em `legenda_div_y` (1130) e cor só com balanço de branco (sem mexer na exposição da tela). Usar com `zoom_base` `[1.0, 1.0]` e `cartoes` vazio. Aula gravada só com a câmera não usa `cenas_obs`: usa `telas` (ver "Aula gravada só com a câmera"). |
| `telas` e `tela_html` | aula gravada só com a câmera: a lista de trocas de cena e cliques ancorados na fala e o `_TELA_R0XX_*.html` de onde saem as telas. Ver a seção abaixo. |
| fixos | `pausa_min` 1.0, `pausa_fica` 0.8, `corte_minimo` 0.4 (só corta pausa se economizar 0,4 s), `legenda_base_y` 1516, `titulo_ate` 3.0, `cor` `C`, `aprimorar_voz` 75, `saida` `R0XX_editado.mp4`. Não mudar sem pedido do Rodrigo. |

### Anúncio do Dono 14% (padrão do A52, aprovado em 23/10/2026)

A skill também edita os criativos de `meus-produtos/dono-14/entregas/criativos/A0XX - Nome - 9x16/`. O `preparar.py` aceita o código `A52` e o roteiro `A52 - … - roteiro.html`. O que muda em relação ao Reel:
- **Capa no primeiro quadro, como no Reel** (o Rodrigo pediu no A52 para o preview de quem recebe pelas redes). A capa do anúncio usa **o mesmo bloco de título do vídeo** (cartão creme com a pílula, as linhas pretas e a tarja vermelha, o `titulo.png` do trabalho) por cima da foto da capa, com **a mesma cor C do vídeo** (`filtro_cor` medido na própria foto, com o mesmo `cor_esfriar`). A capa feita só no gerador ficou "morta" ao lado do vídeo. Com a capa igual ao título, usar `titulo_sem_entrada: true` para o título não piscar na passagem da capa para o vídeo.
- **Tag fixa** `tag_fixa: "DONO DE RESTAURANTE"` com `tag_y` 286: fica do fim do título até o fim do vídeo, no alto, logo acima dos cartões da tela dividida (que começam em y 330). O filtro visual não pode ficar só nos 3 primeiros segundos: o A32 e o A34 carregavam a tag o tempo todo.
- O plano de motion vem da seção H do roteiro. O efeito de tela cheia (`tipo` `distancia`) fica fora da tela dividida, por cima do vídeo. Os outros entram na tela dividida com `fundo_divisao: "vidro"` (a metade de cima é o próprio vídeo desfocado, com um véu verde-escuro, no lugar do preto chapado).
- **Número na tela é o número falado.** Se ele fala "60", a grade destaca 60 (40 no zero + 19 no vermelho + 1 sem dado vai no detalhe), nunca 59. Resultado positivo é sempre verde: no A52, os 6 que reajustaram acima da inflação são os que fizeram certo e não podem ficar em vermelho.
- **Não repetir o mesmo gráfico duas vezes seguidas:** depois da grade de 100, o segundo dado do mesmo tipo vira rosca (`tipo` `rosca`, com a fatia de destaque saindo da rosca e o número no centro).
- **Nada pisca nem pulsa:** a grade fica parada no destaque (`pulsar` vem desligado). Quadrados crescendo e diminuindo atrapalham a leitura.
- **Prova em página real** (`tipo` `destaque`): fotografar a página com o Chrome sem janela em **largura de tablet e escala 2** (`--window-size=600,4200 --force-device-scale-factor=2`), recortar no formato do cartão (largura ÷ 2,08) e marcar uma caixa por linha em `trechos`. Usar **`parado: true`**: a página inteira, sem zoom e sem movimento lateral, só o marca-texto correndo. O `seguir` com zoom (1,5 e depois 1,25) cortava as pontas das linhas e impedia de ler a frase inteira. Ficou reprovado.
- **A distância** é um painel quase opaco (alfa 246) com a linha de vendas subindo e a de lucro parada. O vão dourado é desenhado numa camada à parte e misturado por cima: desenhar direto no painel abria um furo, e a camisa aparecia através do gráfico.
- **Cor em luz amarela de salão:** `cor_esfriar` 0,03 (meio ponto, tira vermelho e soma azul) quando a pele fica quente nos trechos de rosto.
- Medir o rosto num quadro do meio do bruto (no A52 o primeiro quadro estava mais longe) e conferir que o título não cobre a boca.
- Ruído de salão: a transcrição fala por fala mede o limiar do silêncio pelo ruído do lugar.
- **Modo palco** (`modo_div: "palco"`, versão B de teste do A52, inspirado num Reel do Politi). Nos momentos de dado, a tela vira fundo de marca cheio, com o cartão grande em cima (1040 px), o rosto num círculo de borda dourada embaixo e uma etiqueta por momento (`etiqueta` em cada cartão ou contador: A PESQUISA, O NÚMERO, QUEM ACERTOU, A CONTA, A SESSÃO). A legenda fica abaixo da etiqueta. Nas falas sem dado, o rosto continua em tela cheia. O Rodrigo escolheu a versão A (tela dividida) para o A52. O palco fica disponível para teste A/B.

### Versão horizontal 16:9 (aula do YouTube, padrão do R026)

Quando a aula foi gravada no OBS nas duas saídas (`R0XX - Bruta - Vertical.mp4` e `R0XX - Bruta - Horizontal.mp4`), editar **primeiro o vertical** até a aprovação e depois derivar o horizontal:
1. Medir o deslocamento entre os dois áudios (correlação do volume a cada 10 ms; no R026 o horizontal estava 0,13 s depois, constante).
2. Copiar `_edicao_R0XX_vertical.json` para `_edicao_R0XX_horizontal.json` com `formato` `16:9`, o bruto e a capa do YouTube (`CAPA_*_YouTube_1920x1080.png`), `inicio`, `fim` e `remover` somados ao deslocamento, e a transcrição corrigida do vertical deslocada (mesma legenda, mesmos takes).
3. Ajustar o enquadramento: `rosto` e `rosto_caixa` em pixels de 1920 × 1080, `titulo_x`/`titulo_y` no lado livre (R026: `titulo_x` 400, `titulo_y` 110, tamanho 52, à esquerda do rosto), `legenda_base_y` e `legenda_div_y` 930 (embaixo e centralizada, como no R023 publicado).
4. Na horizontal do OBS, a tela dividida é a aula em tela cheia com a câmera no canto inferior direito; o editor detecta sozinho.

### Aula gravada só com a câmera (padrão a partir de 18/10/2026)

Desde 18/10 as aulas da Linha Editorial são gravadas **só com a câmera**: sem OBS, sem clicar na tela e sem trocar de cena. O editor cria as telas a partir do `_TELA_R0XX_*.html` e as troca na palavra marcada no roteiro.

**Orientação de gravação para o Rodrigo** (repassar quando ele for gravar uma aula, em linguagem simples):
- câmera em 4K na horizontal, se possível; se for o celular, na vertical;
- deixar espaço acima da cabeça (a legenda sobe para ali quando a tela aparece);
- falar a aula inteira olhando para a câmera, no ritmo do roteiro: não precisa clicar em nada nem trocar de cena;
- errou, respira e repete a frase inteira (a última tentativa completa é a que fica).

**Montagem** (vale para o vertical e para o horizontal, a partir do mesmo bruto):
1. Rodar `{PY} {SKILL}/scripts/telas.py roteiro "{pasta}/Reels_0XX_*.html" "{pasta}/_edicao_R0XX.json"`. Ele lê a tabela da seção 1.1 (fala, cena e clique, frase por frase) e grava no JSON a lista `telas`: cada troca de cena (`"cena": "tela"` ou `"rosto"`) e cada clique (`"clique": N`) ancorados nas 4 primeiras palavras da frase, ou no trecho entre aspas quando o roteiro diz `clique 9 em "fora da ficha técnica"`.
2. **Conferir cada âncora contra a `fala.txt`** e trocar pelo trecho exato do que ele falou (no teste do R026, o roteiro dizia "A primeira: quanto você" e ele falou "A primeira questão é…", e "Agora divide" virou "E então você divide"). O plano aceita fala parecida (80%) e avisa "âncora aproximada", mas o certo é a âncora exata. Âncora dentro de um take removido não existe mais: mover para a tentativa que ficou.
3. Preencher `tela_html` com o nome do `_TELA_R0XX_*.html`. **Não usar** `cenas_obs` nem `cartoes` junto com `telas`.
4. `rosto` é o centro do rosto em fração do **bruto** (lido na `rosto_grade.jpg`). Se o bruto tem outra proporção (câmera 16:9 para o Reel, celular 9:16 para o YouTube), o editor recorta em volta do rosto sozinho.
5. Rodar o plano: ele imprime as janelas de tela e o tempo de cada clique. No resumo para aprovação (Passo 3), incluir: "Telas: {N} cliques, tela de {a} a {b} s, ..., cada clique na palavra marcada".

O que o editor faz no render:
- exporta um PNG por clique pelo Chrome sem janela (`?p=1`, `?p=2`…), em 1920 × 1080 e no recorte da metade de cima do vertical (1080 × 960, a zona útil x 385 a 1535 com a altura inteira), e monta a trilha das telas com dissolvência de 0,3 s em cada clique;
- **vertical 9:16:** cena "tela" = tela em cima (y 0 a 960) e a câmera embaixo, em plano aberto recortado pelo rosto; legenda na linha acima da cabeça (`legenda_div_y`, 1130);
- **horizontal 16:9:** cena "tela" = tela cheia com a câmera num quadradinho de cantos redondos no canto inferior direito (360 × 296, fora da zona útil), com moldura verde; legenda em `legenda_div_y` (1000);
- cena "rosto" = só a câmera, com o zoom suave de sempre; nas telas o zoom fica em 1;
- a cor C é medida e aplicada só na câmera: a tela entra por cima, sem mexer na exposição dela.

Campos opcionais: `camera_altura` (fração da altura do bruto usada na câmera da cena "tela": padrão 1.0 no vertical e 0.75 no canto do horizontal; menor aproxima), `camera_canto` (tamanho do quadradinho do horizontal, padrão `[360, 296]`).

O horizontal sai do mesmo bruto e do mesmo JSON: copiar `_edicao_R0XX.json` para `_edicao_R0XX_horizontal.json` com `formato` `16:9`, o `codigo` com `H`, a capa do YouTube, `saida` própria, `titulo_x`/`titulo_y` no lado livre e `legenda_base_y` 930. Não há deslocamento de áudio: é a mesma gravação.

### Aula animada no palco (padrão do R029, aprovado em 28/10/2026)

O R029 levou quatro rodadas e fixou o padrão das aulas com muito motion. Tudo abaixo foi pedido ou aprovado pelo Rodrigo.

**Tela animada (motion):** o `_TELA_*.html` expõe `window.cena(p, t, T)`: desenha o clique `p` `t` segundos depois de ele entrar, com `T` = tempo do vídeo (o fundo segue vivo entre os cliques). O editor detecta `window.cena` sozinho (`telas.tem_motion`) e grava quadro a quadro pelo Chrome sem janela (`telas.gravar_motion`), segurando o último quadro de cada clique até o próximo. Sem `window.cena`, cai no PNG por clique de sempre.
- Motor de efeitos no HTML: atributos `data-fx` (`sobe`, `fade`, `pop`, `giro`, `varre`, `esq`, `dir`, `cai`, `vira`, `slam`, `risco`, `enche`), `data-p` (clique que dispara; sem ele, o primeiro clique da vista), `data-at` e `data-dur`; `data-num` para número que conta (com `data-de`, `data-ate`, `data-casas`), `data-cor-de`/`data-cor-ate` para cor que muda e `data-sh` para o brilho que passa. Modelo pronto: `R029 - AFichaTecnicaQueMente/_TELA_R029_AFichaTecnicaQueMente.html`.
- Visual aprovado: fundo verde-escuro da marca (`#08170F`) com grade que desliza e manchas de luz, cartões de vidro, dourado `#E2BE62`, verde claro `#5ED38C` para o número certo, vermelho `#FF6A4D` para o risco e o "× mais". O visual creme simples foi reprovado ("feijão com arroz").
- **A animação entra na palavra** (rodada 4): todo elemento que mostra algo que ele fala leva `data-fala="trecho exato da fala"`. O editor acha o trecho na transcrição depois do início do clique e faz o elemento entrar 0,25 s antes da palavra; os filhos andam junto, e `data-fala-mais` soma segundos (o brilho depois do número). A render imprime `na fala: [trecho, segundos]` para cada um: conferir que nenhum saiu "não achei". Sem isso a informação aparecia muito antes da fala.
- Unidade como ele fala: "300 gramas", nunca "0,3 kg"; dinheiro com 2 casas ("0,37", nunca "0,375").
- O primeiro clique segura o primeiro quadro até a tela aparecer (na v1 a tela entrava travada em "R$ 0,00").
- Clique ancorado na frase que pede o elemento novo, não na frase seguinte (o 3º passo entrava em "pelo peso limpo" e foi para "Divide o preço").

**Palco (`modo_div` `palco`):** a cena "tela" vira tela grande em cima (1080 × 720 a partir de `palco_y`, bordas esfumadas) e o rosto num círculo com anel dourado embaixo, sobre o fundo da marca. Valores aprovados: `palco_y` 280, `palco_diametro` 540, `palco_cy` 1275.
- **O rosto do círculo vem do bruto horizontal** (`camera_bruto`, `camera_desloc` medido pela correlação do áudio, 0,19 s no R029, `camera_rosto` em fração do horizontal, `camera_lado` 860, `camera_rosto_y` 0,5). O vertical do OBS é um recorte ampliado do rosto: no círculo cortava a testa e o queixo, e a ampliação deixava brilhos em olhos, nariz e boca. Gravação com as duas saídas: sempre usar o horizontal no círculo.
- Zoom só nas cenas longas de rosto (abertura e CTA). Volta curta ao rosto entre duas telas fica sem zoom (reprovado na v3).

**Legenda em caixa (`legenda_estilo` `caixa`):** caixa verde-escura arredondada atrás da linha, pílula na cor do vídeo atrás da palavra falada e palavras-chave na cor. No palco ela fica sempre no mesmo lugar, embaixo (`legenda_base_y` 1625), na tela e no rosto: nunca sobe para a testa.

**Capa:** o cartão da capa acompanha o visual das telas (vidro escuro, verde claro, risco vermelho); ao mudar as telas, atualizar o `_CAPA_*.html` e exportar o PNG de novo (1080 × 1920 exatos).

**Volume depois da render:** a render às vezes sai com pico em -1,0. Corrigir copiando o vídeo e passando só o áudio por `volume` + `alimiter` até ficar entre -14,5 e -13,5 LUFS e pico até -1,5.

**Prévia para o celular:** o arquivo cheio (100 a 150 MB) não chega ao celular. Entregar uma prévia de até 30 MB (540 × 960, 1250 kbps) como `_PREVIA_R0XX_vN.mp4`; o final fica na pasta. **Nível do H.264 sempre 4.2** (render e prévia): o x264 marcava o vídeo como nível 6.2 (de 8K), e o decodificador por hardware do computador e do celular mostrava manchas marrons na camisa e brilhos no rosto, que o ffmpeg não vê (R029 e R030; o editor agora força `-profile:v high -level:v 4.2`). Prévia: `-c:v libx264 -profile:v main -level:v 4.0 -preset medium -pix_fmt yuv420p -movflags +faststart`. Para conferir um arquivo: `ffprobe` deve mostrar `level=42` (ou menos), nunca 62.

### Capa, título e áudio (pedidos do R030, 28/10/2026)

- **Cor da capa perto da do vídeo, sempre conferir.** A foto da capa sai do celular com outro balanço de cor que o vídeo depois da cor C (no R030, a camisa amarela ficou bem diferente). Conferir lado a lado a capa e um quadro do vídeo editado antes de entregar. Casar a cor por histograma com o quadro do vídeo foi reprovado no R030 ("ficou horrível, nada a ver com a gravação"): o ajuste tem que ser leve e feito à vista, e mostrado ao Rodrigo lado a lado antes de virar a capa.
- **Título dos 3 s = o mesmo bloco da capa.** Quando a capa tem título próprio (selo e quadro), usar `titulo_da_capa` no JSON: `{"html": "_CAPA_R0XX_*.html", "seletores": [".tag", ".quadro"], "dy": -30}` (classes do selo e do quadro naquele HTML; `dy` sobe o bloco para não cobrir a testa) e `titulo_sem_entrada` `true`, porque a capa do primeiro quadro já mostra o mesmo título. O título desenhado pelo editor fica para capa sem bloco de título.
- **Título do editor mais arejado:** as letras não se apertam mais e o espaço entre palavras cresceu (`ESP_PAL`); o Inter 900 tem espaço estreito e as palavras grudavam.
- **Texto da tela = o que ele fala.** Balão, carimbo e frase de efeito usam as palavras exatas da fala ("MEU DEUS DO CÉU", não "DEUS DO CÉU").
- **Elemento de impacto com destaque cheio:** carimbo, tarja e selo em bloco sólido (fundo vermelho, contorno e sombra pretos), nunca contorno transparente com mistura de cor, que some sobre o fundo.
- **Respiração com microfone perto da boca** (`respiracao` `voz`): a inspiração antes da frase passa pela IA e aparece depois do ganho. O editor procura trechos sem tom de voz, fora das palavras, com pico abaixo de -28 dB, e abaixa 20 dB. Usar sempre que o microfone estiver na mão ou na lapela perto da boca; a render imprime quantos trechos abaixou.
- **Aula de tela dividida sem palco** (R030): tela animada em cima, câmera embaixo com a cabeça inteira (`camera_rosto_y` 0,5) e legenda em caixa na linha da divisão (`legenda_div_y` 1000), acima da cabeça; no rosto cheio, embaixo (`legenda_base_y` 1540). Zoom só no rosto cheio da abertura e do CTA, e nunca nos 3 s do título.

### Erros e regravações (padrão do R026, 18/10/2026)

0. **Em vídeo com regravação, transcrever também fala por fala**: `{PY} {SKILL}/scripts/transcrever_por_fala.py "{TRAB}/audio16k.wav" "{TRAB}/palavras_por_fala.json"`. A transcrição inteira **funde duas tentativas da mesma frase** (R026: "a referência que eu utilizo" dita duas vezes virou uma frase só, com o "32%" esticado por 5 s, e passou batido). A fala por fala separa as tentativas, mas erra mais palavras isoladas. Usar a fala por fala para **achar** os erros. Na legenda, usar a inteira e trocar só os trechos fundidos pela fala por fala (sem perder palavra na emenda).
1. **Ler a fala inteira pelo sentido**, bloco por bloco, como editor, e não só procurar repetição. Pergunta para cada frase: ela se completa? Diz o que ele quis dizer? Contradiz o que veio antes? No R026 o Rodrigo apontou dois erros de sentido que não eram repetição: "despesa pessoal paga **com o dinheiro do próprio dono**" (sai, retoma na frase seguinte) e uma frase que não se completava ("toda a mercadoria, pós-preparo, algumas outras não…"; sai inteira).
2. Procurar frases repetidas: sequências de 3 ou 4 palavras iguais em até 40 s. Separar **erro** (frase recomeçada ou regravada) de **repetição de propósito** (retomada do exemplo, lista, reforço da tese). Frase reformulada logo em seguida ("vou fazer ela para ti nesse momento. Eu posso te perguntar agora") vira corte opcional.
3. Conferir palavra esticada (mais de 1,5 s) ou de confiança baixa: costuma ser tentativa fundida, pausa de pensamento ou tropeço que o Whisper engoliu.
4. **Fica a última tentativa completa**, a menos que ela tenha hesitação e uma anterior esteja limpa. Hesitação solta ("E…" antes do CTA) também sai. Os cortes vão **no meio do silêncio** entre as falas (silencedetect a -40 dB, porque o Whisper adianta o começo da palavra e corta palavra pela metade).
5. Mostrar ao Rodrigo, antes de renderizar, uma tabela com os tempos do bruto: o que sai, o que fica e por quê, mais os cortes opcionais separados para ele decidir.
6. Na conferência, ouvir/ler cada emenda: a legenda não pode ter palavra que o corte tirou nem perder palavra que ficou. Números sempre com separador (150.000, R$ 1.500, nunca 150000) e erro de transcrição que muda o sentido corrigido com `trocas_frase` (ex.: "quando está sobrando" → "quanto está sobrando").

Conferir o plano rodando `{PY} {SKILL}/scripts/editar_reel.py "{pasta}/_edicao_R0XX.json"` (sem `--render`, leva segundos). Se sair "Frase não encontrada na fala", trocar o trecho pelo texto exato de `fala.txt`.

---

## Passo 3. Resumo para aprovação

Mostrar em linguagem de editor (sem JSON), a partir da saída do plano:

```
Edição do R0XX pronta para renderizar:

- Duração: {X} s ({N} cortes de pausa longa; o resto fica no ritmo natural)
- Título nos 3 primeiros segundos: "{linhas}", no {amarelo/lilás/...} da capa, {na parede acima da cabeça | no peito}
- Zoom em: "{frase 1}", "{frase 2}", ..., CTA
- Cartões em tela dividida: {nome} em "{palavra}" ({t} s), ...
- Legenda em {cor} (o R0YY foi {cor anterior}), com destaque em: {palavras-chave}
- Áudio D, cor C e capa no primeiro quadro

1. Pode renderizar
2. Quero ajustar algo
```

Esperar a resposta. Ajuste pedido → mudar o JSON, rodar o plano de novo e mostrar só o que mudou.

---

## Passo 4. Renderizar (`⏳ Passo 4/6: renderizar com áudio, cor, legenda e título.`)

`{PY} {SKILL}/scripts/editar_reel.py "{pasta}/_edicao_R0XX.json" --render`, em segundo plano (2 a 4 minutos para 1 minuto de bruto 4K). Na primeira vez no computador o modelo do aprimorar voz (212 MB) desce antes.

---

## Passo 5. Conferir (`⏳ Passo 5/6: conferir quadros, zonas seguras e volume.`)

`{PY} {SKILL}/scripts/conferir.py R0XX` gera `{TRAB}/conferencia.jpg` (capa, título, cada cartão, pico de cada zoom e fim, com as zonas desenhadas) e mede o volume. Abrir a imagem e conferir:

- primeiro quadro é a capa;
- título inteiro entre as linhas azuis (y 300 a 1248), sem cobrir olhos e boca;
- nos cartões, notícia na metade de cima e o rosto inteiro na metade de baixo;
- legenda dentro da faixa amarela e fora das áreas vermelhas (fora do corte 4:5);
- zoom sem cortar a testa ou o queixo;
- volume integrado entre -14,5 e -13,5 LUFS e pico até -1,5 dBFS.

Problema → corrigir o JSON e renderizar de novo antes de entregar.

---

## Passo 6. Entregar (`⏳ Passo 6/6: entregar o vídeo.`)

```
✅ Concluído: R0XX editado ({X} s). Caminho: meus-produtos/linha-editorial/entregas/reels/R0XX - Nome/R0XX_editado.mp4.
```

Mais o caminho absoluto em texto copiável (regra 4a do CLAUDE.md) e o vídeo com SendUserFile. Vídeo até 30 MB vai direto; acima disso (aula longa), mandar a prévia leve `_PREVIA_R0XX_vN.mp4` (ver "Aula animada no palco"). Folha de quadros só se o Rodrigo pedir. Próximo passo sugerido: `/publicar-reel R0XX`.

Versões anteriores do mesmo Reel, se houver re-render, vão para `_R0XX_editado_vN.mp4` antes de gravar a nova.

---

## O padrão aprovado (não mudar sem pedido)

Fonte: R024, R025, R026 (vertical e horizontal) e R027, 16 a 18/10/2026, e R029 (aula animada no palco), 28/10/2026. Detalhes na memória `reels-edicao-padrao`.

- **Takes:** fala inteira lida pelo sentido; fica a última tentativa completa; frase errada ou que não se completa sai; corte no meio do silêncio; tabela de takes aprovada pelo Rodrigo antes da render (R026).
- **Pausas:** só corta acima de 1,0 s, deixando 0,8 s, e só se o corte economizar 0,4 s, com dissolvência de 0,12 s. Cortar mais ficou "muito acelerado" (v1 e v2 do R027 reprovadas).
- **Números na legenda:** separador de milhar sempre (150.000, R$ 1.500, nunca 150000); ano sem ponto (2026). Erro de transcrição que muda o sentido vai em `trocas_frase`.
- **Aulas do OBS:** zoom só na cena de rosto, legenda acima da cabeça na tela dividida, cor sem mexer na exposição da tela; horizontal 16:9 derivado do vertical aprovado.
- **Aulas só de câmera (desde 18/10, testado com a simulação do R026):** telas geradas do `_TELA_*.html`, trocadas na palavra da seção 1.1; vertical com tela em cima e câmera embaixo, horizontal com tela cheia e câmera no canto; as mesmas regras de zoom, legenda, cor e áudio das aulas do OBS.
- **Aula animada (R029):** tela em motion com o visual escuro da marca, cada elemento entrando na palavra falada (`data-fala`), palco com o rosto do bruto horizontal no círculo, legenda em caixa sempre embaixo, sem zoom nas voltas curtas ao rosto. Detalhes em "Aula animada no palco".
- **Zoom:** suave e contínuo (curva S), ancorado no rosto. Nunca punch-in seco. **Gravado caminhando ou com a câmera na mão: sem zoom** (`zoom` vazio, `zoom_base` `[1.0, 1.0]`); o movimento da gravação já basta (R028).
- **Legenda:** Montserrat ExtraBold, maiúscula, palavra falada em destaque, base em y 1516; na tela dividida sobe para a linha da divisão (y 962), trocando de lugar no instante em que o cartão entra ou sai, mesmo no meio de um bloco (R028).
- **Título:** o mesmo bloco da capa (`titulo_da_capa`) quando a capa tem título; senão, cartão na cor da capa, selo espaçado, linhas em preto (Inter 900, palavras bem separadas), última linha branca na tarja vermelha inclinada.
- **Cartões:** tela dividida, notícia em cima (fundo `#0A1712`), vídeo embaixo.
- **Cartões animados (A52):** o número na tela é o número falado; resultado positivo em verde; nada pisca nem pulsa; prova em página real aparece inteira, parada, só com o marca-texto; gráfico repetido vira outro desenho (grade, depois rosca).
- **Contador (número que cresce):** cartão branco na tela dividida, rótulo verde espaçado, número em Montserrat Black subindo em 1,4 s com desaceleração, pulso de 0,3 s ao parar, barra dourada de progresso e detalhe cinza que aparece no fim. Testado no R024 em 18/10 (`_teste_contador_R024.mp4`); estreia no R028.
- **Preço que cai e conta que monta** (`tipo` `troca` e `conta`): mesmo cartão branco, colunas DE SEMPRE e COTANDO com seta dourada, risco vermelho no preço antigo, destaque verde-claro e selo dourado com a diferença; a conta entra termo a termo e o resultado sobe. Testados no R024 em 20/10 com os números do R028; estreiam no R028.
- **Áudio D:** DeepFilterNet + ClearerVoice 75% + ganho linear a -14 LUFS com limitador em -1,5 dB (o loudnorm levantava a respiração).
- **Cor C:** balanço de branco pela pele e exposição pelo rosto, medidos em cada vídeo, com acabamento Instagram leve. Com camisa ou parede branca no quadro, o branco neutro manda (90%) para não amarelar (R025).
- **Capa** no primeiro quadro (miniatura do WhatsApp) e **1 s de respiro** no fim, com o áudio sumindo em 0,6 s.

## Arquivos da skill

| Arquivo | Função |
|---|---|
| `scripts/instalar.py` | instalação de primeira vez e conferência (`--verificar`) |
| `scripts/preparar.py` | acha os arquivos, transcreve, grava a grade do rosto e o resumo |
| `scripts/transcrever.py` | faster-whisper large-v3-turbo com o tempo de cada palavra (fala inteira, base da legenda) |
| `scripts/transcrever_por_fala.py` | mesma transcrição, mas fala por fala (corta nos silêncios): separa tentativas repetidas |
| `scripts/editar_reel.py` | plano (sem `--render`) e render completo (com `--render`) |
| `scripts/cor.py` | cor C |
| `scripts/aprimorar_voz.py` | aprimorar voz do áudio D (roda no Python com PyTorch CUDA) |
| `scripts/telas.py` | aula só de câmera: exporta as telas do `_TELA_*.html` (um PNG por clique), grava a tela animada quadro a quadro (`gravar_motion`, com a sincronia `data-fala`) e monta a lista `telas` da seção 1.1 do roteiro |
| `scripts/conferir.py` | folha de conferência (com cada clique e cada volta ao rosto, na aula) e medição de volume |
| `scripts/ambiente.py` | onde ficam as ferramentas pesadas e quais Pythons usar |
| `fonts/` | Montserrat e Inter (licença OFL, ver `fonts/LICENCA.md`) |
| `references/modelo-edicao.json` | modelo do JSON de edição |
| `references/instalacao.md` | instalação de primeira vez |
