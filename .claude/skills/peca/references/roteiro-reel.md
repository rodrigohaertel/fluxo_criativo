# Anatomia do roteiro de Reel e os encaixes com a edição e a publicação

> O arquivo `Reels_0XX_Nome.html` é a fonte única da peça: roteiro, nota, plano de edição, legenda e textos do YouTube. A `/reels-editar` e a `/publicar-reel` leem dele. Por isso a forma não pode mudar: **copiar a estrutura do gabarito, nunca inventar layout.**

---

## 1. De onde copiar

- **Gabarito oficial:** `entregas/reels/Publicados/R019 - OTomateSubiuESeuPrecoNao/Reels_019_OTomateSubiuESeuPrecoNao.html` (cobrado pelo Rodrigo em 06/10/2026). Dele saem o CSS (Calibri, `.page` 860 px, h1 com filete dourado, blocos `.obs` âmbar, `.alerta` vermelho, `.voz` azul, `.edicao` roxo, `.dados` verde), o badge e o `.meta`, o bloco `.nota`, a tabela de quatro colunas, o teleprompter com botão de copiar e as seções 2 a 5.
- **Blocos de gravação e de edição:** copiar do Reel publicado mais recente (hoje o R034, `Reels_034_NaoTaNosPlanos.html`), porque eles evoluem com a `/reels-editar`.
- Antes de escrever, abrir os dois arquivos e ler. Depois, trocar só o conteúdo.

## 2. Pasta e nomes

- Pasta: `entregas/reels/R0XX - NomeEmCamelCase/` (três dígitos, espaço, hífen, espaço, nome sem espaços). Exemplo: `R035 - QuantoValeOClienteQueVolta`.
- Roteiro: `Reels_0XX_NomeEmCamelCase.html`. A `/publicar-reel` procura `Reels_*.html` na pasta; a `/reels-editar` também.
- Capa: `_CAPA_R0XX_Nome.html` (o desenho) e `CAPA_R0XX_Nome.png` (o exportado). A `/reels-editar` procura `CAPA_*.png` para o primeiro quadro e recorta o título dos 3 segundos do HTML (`titulo_da_capa`, seletores `.tag` e `.quadro` ou os da capa). A `/publicar-reel` pega a capa pelo nome com "capa" e pela orientação (vertical para Meta e Short; horizontal para o YouTube da aula).
- Capa do YouTube (aula): `_CAPA_R0XX_Nome_YouTube.html` e `CAPA_R0XX_Nome_YouTube.png` em 1920 x 1080.
- Telas da aula: `_TELA_R0XX_Nome.html` (click-through; o `telas.py` da edição exporta um PNG por clique e lê a seção 1.1 do roteiro para trocar na palavra certa). Cartões prontos: `TELA_*.png`.
- Fotos e prints: `R0XX_foto_capa.jpg`, `R0XX_img_*.png` (prefixo do código). O bruto é o `.mp4` ou `.mov` **sem** `_` no começo e sem "editado" no nome; a edição pega o maior. Aula: `... - Vertical.mp4` e `... - Horizontal.mp4`.
- Trabalho e versões antigas começam com `_` (`_edicao_R0XX.json`, `_peca_R0XX.json`, `_PREVIA_R0XX_v2.mp4`, `_teste_*.mp4`): as duas skills ignoram.
- Depois de publicado, a pasta inteira vai para `entregas/reels/Publicados/`.

## 3. As seções do HTML, na ordem

**Cabeçalho.** `<h1>` com o nome do arquivo; linha de `.tags` (Linha Editorial, DESCOBERTA ou AULA, família, duração, "só rosto" ou "com telas", "roteiro aprovado em dd/mm"); bloco `.meta` com: Formato (papel do dia, público, turbinado previsto), Tipo (ex.: identificação com virada de tese), Duração (palavras e segundos estimados a 2,24 palavras por segundo; "a duração real entra depois da gravação"), Publicação (dia da semana, data e hora), Objetivo, Pilar (território e por que é novo na linha), CTA (o pedido e a condição), De onde vem (código da fala na base, com a frase literal entre aspas e o que fica fora por ser de cliente), ajustes que o Rodrigo pediu, com data.

**Bloco `.nota`.** O número grande (ex.: `9,4 / 10`), o veredito pela faixa, um parágrafo dizendo por que a nota é essa, e a tabela Critério / Peso / Nota / Por quê com os sete critérios de `REGUA-NOTA-REELS.md` (gancho 25, retenção e meio 15, filtro 15, alinhamento com o objetivo do dia 15, voz 10, Light Copy 10, diferenciação 10) e a linha Total (100 pontos, equivalente a x,x / 10). Depois, "Três cuidados" quando houver (história de cliente, tema sensível, promessa).

**Bloco `.voz`.** Como falar: a primeira frase, as pausas, o ritmo da lista, onde desacelerar e olhar para a lente, "para" e "em um".

**Bloco `.edicao`, "Gravação".** Câmera (vertical; aula também horizontal), enquadramento (espaço acima da cabeça para o título; de mais longe se houver veredito), o que mandar (foto da capa, print), a regra de erro (respira e repete a frase inteira).

**Bloco `.edicao`, "Edição: pela /reels-editar".** Nos campos que a skill usa: título dos 3 segundos (o bloco da capa); telas ou cartões com **a palavra falada em que cada um entra**, o tipo (cartão em tela dividida, contador, troca, conta, grade, régua, destaque, veredito) e o número exato; 3 a 5 frases de zoom (uma com "empurra") ou "sem zoom" se gravado em movimento; **cor da legenda, diferente da dos dois Reels anteriores**, nomeando as anteriores; 5 a 8 palavras-chave; o que é proibido na peça (B-roll genérico sempre).

**Seção 1. Roteiro com tempos, movimentos e cenas.** Tabela de **quatro colunas: Tempo / Fala / Câmera / Texto na tela**. Tempo estimado por bloco (0 a 3 s, 3 a 10 s...), fala em blocos de uma ou duas frases, câmera (cheia, meio plano, "de mais longe"), texto na tela só nos quatro casos da régua, com a justificativa em letra miúda (`.small`) e a âncora na palavra falada. Aula: subseção **1.1** frase por frase (fala, cena, clique), que o `telas.py` lê. Notícia: subseção com o print e o que enquadrar, e como citar a fonte em cada canal.

**Seção 2. Texto puro / Teleprompter.** A fala inteira em texto corrido, no bloco `.teleprompter` com o botão de copiar (`tp-copiar`) e a contagem de palavras (`tp-nota`).

**Seção 3. Legenda do post.** `<div class="legenda">` com um `<p>` por parágrafo (a `/publicar-reel` lê **exatamente** este bloco: quebra de linha só com `<br>`; parágrafos virarem linhas em branco). A legenda abre repetindo a tensão do gancho, desenvolve em duas ou três frases, traz a pergunta de uma palavra para o comentário, a fonte por extenso quando for notícia, e as hashtags. Até 2.200 caracteres.

**Seção 4. Capa.** Tipo (rosto ou número) e por quê pela grade; o que a foto precisa ter; o texto exato das linhas (tag, título, tarja); a cor do fundo e por que difere da anterior; o link para o `_CAPA_*.html`.

**Seção 5. YouTube (Short ou vídeo). Título e descrição.** `<p><b>Título</b> ...</p>` seguido de um `<p>` com o título (até 100 caracteres; a `/publicar-reel` lê o `<p>` seguinte ao rótulo), depois `<div class="legenda">` com a descrição em `<p>` (o texto do vídeo e as hashtags; o cabeçalho da Sessão e o rodapé de redes o script acrescenta se faltarem). Aula horizontal entra como vídeo normal, sem `#Shorts`.

**Seção 6. Pendências.** O que falta antes de gravar e antes de publicar (foto, print, número a confirmar, autorização).

**Bloco `id="versao-publicada"`** (entra depois da edição). A fala como foi gravada, a duração real, a data e o que mudou em relação ao roteiro. É a fonte do que foi ao ar.

## 4. Conferências antes de mostrar o roteiro

1. Primeira frase falada tem o filtro, em forma diferente do Reel anterior.
2. Nenhuma trava da seção 5 de `regras-da-linha.md` quebrada (para, em um, te paga, sobra, margem x despesa fixa, 13 solto, tempo real, lucro líquido).
3. Checklist Light Copy e `revisora` sobre fala, legenda, título e descrição.
4. Texto na tela passa no teste da legenda tapada; números da tela recalculados e exatos.
5. Palavras contadas com número por extenso; duração estimada a 2,24 palavras por segundo; descoberta até 80 s; aula 4 a 6 minutos.
6. CTA do dia certo, "Aqui é para dono de restaurante" por último na descoberta.
7. Capa: tipo pela grade (vizinhas do brief), fundo diferente da anterior, headline com sujeito, número que está no vídeo, tag em y 330.
8. Cor da legenda diferente das duas anteriores.
9. Fonte de cada afirmação conferida; nada de cliente sem autorização; nada fora do domínio.
10. Nota dada com o "por quê" em cada linha; veredito pela faixa.

## 5. O que a edição espera da pasta (resumo do `preparar.py`)

| Ela procura | Nome |
|---|---|
| Bruto | maior `.mp4` ou `.mov` sem `_` e sem "editado"; na aula, `... - Vertical` e `... - Horizontal` |
| Capa | `CAPA_*.png` |
| Roteiro | `Reels_*.html` (anúncio: `*roteiro*.html`) |
| Cartões prontos | `TELA_*.png` |
| Telas da aula | `_TELA_*.html` |

Ela grava `_edicao_R0XX.json` (campos: `codigo`, `bruto`, `saida`, `capa`, `cor_legenda`, `palavras_chave`, `titulo`, `zoom`, `cartoes`, `contadores`, `tela_dividida` e outros) e entrega `R0XX_editado.mp4` mais `_PREVIA_R0XX_vN.mp4`. O `peca.py` lê `cor_legenda` dos Reels publicados para a regra da cor.

## 6. O que a publicação espera da pasta (resumo do `extrair.py`)

Vídeo final vertical (o `saida` do `_edicao_*.json`, ou o maior `.mp4` sem "bruto" e sem `_`), vídeo horizontal quando houver (YouTube), capa pelo nome com "capa" e pela orientação, `Reels_*.html` com a seção 3 (`<div class="legenda">`) e a seção 5 (`<b>Título</b>` seguido do `<p>` do título e `<div class="legenda">` da descrição). Vertical acima de 900 MB é comprimido antes do Planner, pela própria skill.
