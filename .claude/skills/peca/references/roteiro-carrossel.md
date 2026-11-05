# Anatomia do carrossel e os encaixes com a produção e a publicação

> O arquivo `Carrossel_###_Nome.html` é a fonte única do carrossel: as oito lâminas desenhadas, a ficha (brief, nota, legenda e prompts de fundo) e o modo solo que o `laminas.py` usa para exportar cada lâmina. **Copiar o esqueleto de um carrossel recente, nunca inventar do zero.**

---

## 1. De onde copiar

- **Gabarito de pasta e de HTML:** `entregas/carrosseis/Carrossel_009_PerdaOuDesperdicio/` (layout "etiqueta de cozinha": fita crepe e carimbo, só tipografia e cor, sem foto). Dele saem as variáveis de cor, a `.s` de 1080 x 1350, o `.pg` X/X, o `.chip`, o `body.solo` e o script do `?s=`.
- **Layout de duas colunas:** `Carrossel_008_OCmvDaFichaContraOCmvDoMes` (layout "placar": a ficha contra o mês).
- **Com fotos do Gemini:** `Publicados/Carrossel_003_AsTresPerguntasDaSessao/` (`_fundo_02.jpg` a `_fundo_07.jpg` e `_foto_capa.jpg`, carregados pelo HTML pela variável `BASE`).
- Antes de escrever, abrir o gabarito e o carrossel com o layout mais parecido do que se pretende, ler os dois e só então trocar conteúdo e layout.

## 2. Pasta e nomes

| Arquivo | Nome | Quem usa |
|---|---|---|
| Pasta | `entregas/carrosseis/Carrossel_###_NomeEmCamelCase/` | tudo |
| HTML | `Carrossel_###_NomeEmCamelCase.html` | `laminas.py`, prévia no navegador |
| Lâminas | `Carrossel_###_NomeEmCamelCase_01.png` a `_08.png` (1080 x 1350) | Planner (sobem nesta ordem) |
| Prévia | `_previa_###.jpg` (quatro lâminas por linha, metade do tamanho) | aprovação do Rodrigo |
| Legenda | `legenda.txt` (texto puro, parágrafos separados por linha em branco) | Planner |
| Fundos (se houver) | `Carrossel_###_NomeEmCamelCase_fundo_0N.jpg` | HTML |
| Foto da capa (se rosto) | `Carrossel_###_NomeEmCamelCase_foto_capa.jpg` (foto real) | HTML |
| Estado | `_peca_C###.json` | `/peca` |
| Publicado | pasta inteira em `entregas/carrosseis/Publicados/` | histórico |

Arquivos que começam com `_` são trabalho e não sobem ao Planner. O acervo antigo em `entregas/conteudo-social/carrossel-{estilo}/` é histórico e não se mexe.

## 3. O HTML

**Cabeçalho.** `<title>Carrossel ### · Título</title>`; Google Fonts (Inter 500 a 900 e, se o layout pedir, uma fonte de caráter como a Permanent Marker do 009); `:root` com as cores da marca (`--esm #0B3B2E` esmeralda, `--ouro #C8A44D`, `--creme #F7F2E8`, `--terra #C0532E`); `body` cinza com as lâminas empilhadas e `body.solo` sem padding e sem fundo.

**Comentário do layout.** Logo depois do `body`, uma linha `/* layout {nome}: {o que ele é} */`. É esse nome que o `peca.py brief` lê para a rotação. Cada carrossel tem um layout próprio; o mesmo não volta antes de três carrosséis.

**A lâmina.** `<div class="s {esm|creme|terra}">` com 1080 x 1350, `overflow:hidden`, padding de 110 px em cima, 90 nas laterais e 120 embaixo. Dentro: `<div class="marca">@rodrigohaertel</div>` no canto superior esquerdo e `<div class="pg">N/8</div>` no canto superior direito de **todas** as lâminas, inclusive a capa (`.marca{position:absolute;top:52px;left:90px;font:800 30px Inter;letter-spacing:.5px;opacity:.8}`). A marca vai em toda lâmina porque quem reposta costuma levar uma lâmina solta, sem a legenda (regra de 05/11/2026, C009). A única contagem na lâmina é o `N/8`: nada de "ITEM 1 DE 4" ou outra numeração junto, porque duas contagens na mesma tela confundem. `.chip` (etiqueta espaçada) com "DONO DE RESTAURANTE" na capa e o rótulo da lâmina nas outras ("A REGRA", "POR QUE SEPARAR", "SALVA ESTE POST"); título `.h` ou `.h2`, texto `.t`, destaque `.o`; `.rodape` para fonte ou observação. Comentário `<!-- N · nome da lâmina -->` antes de cada uma.

**Com foto.** O bloco inferior sólido fica em **y 742** (55% da altura) em toda lâmina de conteúdo, idêntico em todas; a foto ocupa a parte de cima; o texto fica dentro do bloco (reduzir a fonte para caber, nunca mover a linha). A capa é a única full-bleed: foto inteira, texto integrado sobre leve gradiente, pouca palavra. Fotos pela variável `BASE` do script, com `_fundo_0N.jpg` por lâmina.

**Oito lâminas, nesta ordem.** 1 capa (filtro, promessa ou lacuna, convite ao arraste); 2 a 7 uma ideia cada, com a frase que puxa a próxima. Em jogo ou pergunta, a pergunta e a resposta ficam **no mesmo card**: separar a resposta na lâmina seguinte deixa a leitura confusa, e o carrossel tem que ser entendido por qualquer pessoa (C009). A capa e a última lâmina seguem essa lógica: nada de "tenta acertar" ou "quantos você acertou" quando a resposta já está à vista; 8 pedido de salvar mais a pergunta de uma palavra para o comentário. Conta em lâminas: um termo por lâmina, o resultado fecha exato na última lâmina da conta.

**Bloco `.ficha`** (novo a partir do C010), no topo do `body`, escondido no modo solo (`body.solo .ficha{display:none}`): o brief (dia, hora, formato, gancho, fonte, capa na grade), a nota com a tabela dos sete critérios de `REGUA-NOTA-CARROSSEIS.md` e o veredito, a legenda (a mesma do `legenda.txt`), os prompts de fundo numerados (quando houver foto) e as pendências. É a parte que o Rodrigo lê no navegador antes de descer para as lâminas.

**O script do solo** (fim do HTML, obrigatório, sem alteração):

```html
<script>
const n=new URLSearchParams(location.search).get('s');
if(n){document.body.classList.add('solo');document.querySelectorAll('.s').forEach((e,i)=>{if(i+1!=n)e.remove()})}
</script>
```

## 4. A legenda

Abre com o filtro ("Dono de restaurante, ..."), desdobra a ideia em dois ou três parágrafos curtos (a conta inteira, com os números das lâminas), pede "salva" com um motivo concreto ("salva e mostra para a sua equipe"), traz a pergunta de uma palavra para o comentário, fecha com o convite a seguir e o bordão ("Aqui é para dono de restaurante") e as hashtags. Até 2.200 caracteres. "Para" e "em um", sem travessão, sem exclamação. Fonte por extenso quando for notícia.

## 5. Conferências antes de mostrar

1. Capa com "DONO DE RESTAURANTE", pouca palavra, promessa ou lacuna que faz arrastar.
2. Uma ideia por lâmina; a lâmina 8 pede "salva" e faz a pergunta de uma palavra.
3. Conta recalculada; número exato e com separador em toda lâmina; o total fecha.
4. Travas de `regras-da-linha.md` em cada lâmina e na legenda.
5. Layout com nome no comentário do CSS, diferente dos três últimos; tom e estilo rotacionados.
6. X/X em todas as lâminas; fonte Inter carregada; nada cortado nas bordas (ver na prévia).
7. Fotos: sem texto, sem gente, luz de dia, mesma luz em todas; capa com rosto só com foto real.
8. Nota com o "por quê" em cada linha.

## 6. Produção das lâminas

`py -3 .claude/skills/peca/scripts/laminas.py "caminho/da/pasta"`: acha o HTML, conta as `.s`, abre cada `?s=N` no Chrome (ou Edge) sem janela em 1080 x 1350 e grava os PNG com o prefixo do HTML; depois monta `_previa_###.jpg`. Opções: `--so 1,3` exporta só algumas; `--espera 4000` dá mais tempo para a fonte carregar; `--saida pasta` grava em outro lugar (teste). Ele imprime o tamanho de cada PNG e avisa se algum não saiu em 1080 x 1350.

## 7. Planner (publicação pelo Chrome, sem o Rodrigo escolher arquivo)

Validado em 30/10/2026 com o Carrossel_005.

1. `https://business.facebook.com/latest/content_calendar`. Fechar aviso de novidade em "Done" ou "Concluído" se cobrir o menu.
2. **Criar post**. Conferir "Postar em": Rodrigo Haertel (Facebook) e rodrigohaertel (Instagram).
3. **Preparar o campo de arquivo** com `javascript_tool`, antes de clicar: sobrescrever `HTMLInputElement.prototype.click` e `showPicker` para que, quando o input for `type=file`, ele receba um `aria-label` (ex.: "upload-laminas"), fique no DOM e não abra a janela do Windows.
4. Clicar em **Adicionar foto/vídeo** por JavaScript. Achar o input com `find` ("upload-laminas") e usar `file_upload` com as lâminas em ordem, até 10 MB por chamada (dividir em duas chamadas se passar). Soltar arquivo por evento de arrastar **não** funciona.
5. Conferir na prévia que as oito entraram, na ordem. Lâmina fora de ordem: remover e subir de novo.
6. Clicar no campo **Texto** pela coordenada e digitar a legenda de `legenda.txt` (o `type` pode dar timeout, mas o texto entra). Conferir com `javascript_tool` o tamanho e o final do `[contenteditable=true]`. Não apertar Escape.
7. Ligar **Definir data e hora**. Data pelo calendário; hora nos spinbuttons "horas" e "minutos" dos dois canais (16 e 00). Em inglês, três campos por canal e PM. Conferir com `zoom`.
8. "Compartilhar em: Story do Facebook" fica ligado (padrão mantido pelo Rodrigo).
9. Botão azul **Programar**. Fechar o aviso de turbinar em **Talvez mais tarde**. Nunca "Compartilhar agora".
10. Confirmar os dois cards no calendário. Não clicar em espaço vazio do calendário (abre post novo).

Depois do horário, conferir pela API do Instagram (`/{ig_user}/media?limit=1`) que o carrossel saiu; o card do Planner continua "programado" quando o post trava.
