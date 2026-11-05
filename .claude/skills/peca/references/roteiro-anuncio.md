# Anatomia do roteiro de anúncio e os encaixes com o brief, a edição e a conta

> O arquivo `A## - Mentoria - roteiro.html` é a fonte única do anúncio: nota, prova, legenda da Meta, headline e descrição, roteiro, capa, direção, locução, plano de edição e como será julgado. A `/reels-editar` lê dele; o cockpit só resume e aponta para ele. **Copiar a estrutura do gabarito, nunca inventar layout.**

---

## 1. De onde copiar

- **Gabarito:** `meus-produtos/dono-14/entregas/criativos/A52 - Mentoria - 9x16/A52 - Mentoria - roteiro.html` (versão 3, gravado em 22/10/2026, editado pela skill com motion). Dele saem o CSS, o `.meta`, o scorecard, a tabela da prova, as seções A a I e os blocos de checagem.
- **Leva com vários ganchos sobre um corpo:** `A54 a A57 - Mentoria - 9x16/A54 a A57 - Mentoria - roteiros.html` (colunas por gancho, mecânica do teste da leva).
- **Brief de leva (prosa):** `criativos/briefing-A42-A44.html` (placar real, teto de promessa, briefing do ângulo). O brief novo, legível pelo script, está na seção 6.
- **Cockpit:** `meus-produtos/dono-14/trafego/analise/historico-criativos-a30-a38.html` (uma linha por criativo construído, com link para o roteiro).

## 2. Pasta e nomes

| Arquivo | Nome | Quem usa |
|---|---|---|
| Pasta | `meus-produtos/dono-14/entregas/criativos/A## - Mentoria - 9x16/` | tudo |
| Roteiro | `A## - Mentoria - roteiro.html` | `/reels-editar` (acha por `*roteiro*.html`), cockpit |
| Bruto | `A##_AAAAMMDDHHMMSSmmm.mp4` (o nome que sai do celular, com o código na frente) | `/reels-editar` (maior `.mp4` sem `_` e sem "editado") |
| Fotos da capa | `AAAAMMDD_HHMMSS.jpg` (as do celular) e `_A## - capa previa (foto N).jpg` | capa |
| Capa | `_CAPA_A##_Nome.html` (desenho) e `CAPA_A##_Nome.png` (exportada, 1080 x 1920) | `/reels-editar` (`CAPA_*.png`), conta (miniatura do vídeo) |
| Recortes de prova | `_A##_fonte_recorte.png` (a página da notícia), `_A##_cta.png` | plano de edição |
| Edição | `_edicao_A##.json`, `_A## - palavras.json`, `_teste_motion_A##.mp4`, `_A##_editado_vN.mp4` | `/reels-editar` |
| Vídeo final | `A##_editado.mp4` (versão B: `A##_editado_palco.mp4`) | conta |
| Estado | `_peca_A##.json` | `/peca` |
| Publicado | pasta inteira em `criativos/Publicados/` | histórico |

A pasta de trabalho da edição é `%LOCALAPPDATA%\reels-editar\trabalho\A##\` (o `preparar.py` reconhece `A\d{2,3}` no começo do nome da pasta).

## 3. As seções do HTML, na ordem do A52

**Cabeçalho e `.meta`.** `<h1>A##. Título</h1>`; linha "Leva A50-A53 · A52 · versão N · gravado em dd/mm/aaaa"; `.meta` com: Produto e oferta de topo; **Mandala** (tipo principal, tipo de apoio, base herdada); Estrutura de roteiro (os beats em uma linha); Fase (Conversão, Perpétuo, destino Sessão Estratégica); Formato (9:16, gancho em take em movimento, corpo sentado, edição pela skill); Conceito nomeado; Inimigo concreto; CTA e botão; Público (dono de restaurante, faixa de faturamento); Fonte (nome, título, data da publicação, data dos dados); Duração (palavras, segundos na régua de 2,2 por segundo, alvo).

**Nota do criativo** (`.scorecard`): o número grande (`9.5 / 10`), o veredito em um parágrafo (o que herda, o que muda de propósito, as versões com data), a tabela Critério / Peso / Nota / Por quê com os sete critérios de `REGUA-NOTA-ANUNCIOS.md` e a linha Total.

**A prova: a notícia, número por número.** Fonte, título, data de publicação e dos dados, data da leitura. Tabela Dado / Como está na notícia / Como vai na peça. Parágrafo "O que a peça não diz, de propósito". Comparação com a pesquisa anterior, quando houver.

**As premissas aplicadas.** As cinco premissas da call de copy (filtro nos 3 s, movimento e lugar real, dúvida antes de explicar, prova no meio, CTA ligado à tese com outro desenho), cada uma dizendo como a peça cumpre.

**A. Legenda do anúncio (texto principal da Meta).** Abre pelo filtro, carrega os números que a fala não diz, a história, a conta, o convite com a escassez e o filtro de faturamento, "Clica em Saiba mais".

**B. Headline e descrição.** Headline até 40 caracteres (o número da capa), uma alternativa de teste, descrição com fonte e data. Observação sobre onde cada uma aparece.

**C. Roteiro do Reels 9:16.** Os beats com a contagem de palavras; tabela Tempo / Cena e fala / Na tela, cada efeito com a palavra em que entra.

**D. A capa.** Mockup em escala, a frase da capa e de onde ela vem na fala, as regras (branco arma e amarelo resolve, chip com fonte e data, rosto, degradê, sem aspas e sombra). **D1** a foto escolhida e as descartadas, enquadramento. **D2** tabela de valores (elemento, posição y, fonte, cor).

**E. Direção visual.** Gancho andando, lugar real, troca para a notícia, números em tela dividida, corpo sentado, sem b-roll, texto na tela e paleta.

**F. Locução para copiar e colar.** Uma frase por linha, botão de copiar, contagem de palavras e segundos, "para" e "em um". Cortes opcionais marcados.

**H. Plano de edição com motion.** Um bloco por efeito (H1, H2, ...): tipo no motor (`distancia`, `destaque`, `grade`, `regua`, `rosca`, `contador`, `troca`, `conta`, `veredito`), a palavra falada em que entra, o que acontece, o número exato, a fonte no cartão, o que ainda não existe e precisa ser construído e provado. Título dos 3 s, zoom, cor da legenda, palavras-chave, tag fixa.

**I. Gravado em dd/mm. Notas para o editor.** Entra depois da gravação: take, duração do bruto, o que saturou, o que mudou da locução, versões da edição e qual foi escolhida.

**Checagem Light Copy e teto de promessa.** Bloco A (vícios absolutos), B (argumento e especificidade: cada número com a origem), C (estrutura VTSD: razão e emoção, conceito, inimigo, Quadro e Decorado, autoridade com virada), D (loop e referências: cada "isso" apontando), terminologia, fatos da oferta que vão ao ar, teto de promessa.

**O que o revisor de anúncio marcou e não corrigiu.** Numerado, com a aposta e o critério de leitura ("se o hook ficar abaixo de 30%, a leitura é essa").

**Como será julgado.** Os sete dias, o que se lê no dia 3 (hook contra 33 a 40%, CTR contra o A39), o que se lê no dia 8 (CPL de perfil, metade no perfil, uma Sessão), base mínima, o controle.

**A leva.** Onde a peça entra no plano (o que sai, o que fica, verba da conta).

## 4. Conferências antes de mostrar o roteiro

1. "Dono de restaurante" na primeira frase; faixa de faturamento falada até 15 s e de novo no convite, em segunda pessoa.
2. Um argumento só; mecanismo de prova no corpo; cena antes de estatística no gancho.
3. Cada número com a origem (notícia com data, pesquisa dos 482, aritmética sobre a jornada); o que a fala arredonda, a tela mostra exato; nada inventado; "até" em estimativa.
4. Teto de promessa: 30 minutos, de graça, três ações; nada de prato a prato nem Painel na sessão.
5. Terminologia (lucro x margem, ordem da DRE), proibidos da seção 8 de `regras-do-anuncio.md`, nada político, 13 nunca solto.
6. Palavras contadas por extenso; duração a 2,2 por segundo e a 2,24; cortes opcionais prontos se passar de 80 s.
7. Capa: headline com sujeito ou frase literal, número que está no vídeo, chip em y 330, branco e amarelo.
8. Plano de edição com a palavra de entrada e o número exato de cada efeito; efeito inédito marcado para teste.
9. DNA conferido contra as peças aposentadas e as recentes (o brief traz a lista).
10. Nota com o "por quê" em cada linha; o que o revisor marcou e não corrigiu, escrito.

## 5. O que a edição espera e devolve

O `preparar.py` da `/reels-editar` aceita a pasta `A## - ...`: acha o bruto, `CAPA_*.png`, o roteiro por `*roteiro*.html`, transcreve e grava o trabalho em `trabalho\A##\`. O `_edicao_A##.json` segue o modelo do Reel com os campos do anúncio: `tag_fixa` ("DONO DE RESTAURANTE"), `tag_y`, `titulo_sem_entrada`, `pilula` (fonte e data), `titulo` (as linhas da capa), `contadores` com os efeitos de `animacoes2.py`, `fundo_divisao` "vidro", `cor_esfriar`, `cor_legenda`. Devolve `A##_editado.mp4` e a prévia leve. Depois da edição, a ficha do publicado sai da transcrição (`trabalho\A##\fala.txt`): duração real, ritmo e o segundo em que o filtro de faturamento é falado.

## 6. O brief por leva, legível pelo script

Arquivo `meus-produtos/dono-14/entregas/criativos/briefing-{leva}.html` (ex.: `briefing-A58-A60.html`), escrito pela sessão que planeja a leva. Pode ter o texto em prosa que quiser (placar, lições, teto de promessa), desde que traga **uma tabela com uma linha por peça** neste formato, que o `peca.py brief A58` lê:

```html
<table class="pecas">
<tr><th>Peça</th><th>Ângulo (Mandala)</th><th>Gancho e prova</th><th>Fonte</th><th>Teste e capa</th></tr>
<tr>
  <td><span class="pc">A58</span><br>Título curto da peça</td>
  <td>Atualidades (18) com Contraste (11), sobre a base do A39</td>
  <td><div class="quote">A primeira frase falada, com o filtro.</div>O que a peça prova, o conceito nomeado, o inimigo, o CTA.</td>
  <td>Abrasel, 02/10/2026; pesquisa dos 482 donos</td>
  <td>7 dias a R$ 60 a partir de 12/11; capa de número, chip ABRASEL · 02/10</td>
</tr>
</table>
```

O script procura o código no `span.pc` (ou em um `td.pc`), lê as cinco colunas nesta ordem e devolve a linha, as outras peças da mesma leva e os anúncios recentes (título, nota, Mandala e conceito de cada roteiro). Sem briefing com o código, a skill pergunta o ângulo ao Rodrigo e segue.

## 7. Publicação na conta (resumo; o passo a passo está na Fase 6 da trilha A)

- Modo da conexão pelo `META_AUTH_MODO` do `.env` (padrão da seção "LEITURA SEGURA DO .env" do CLAUDE.md): `MCP_CONECTOR` usa as tools `ads_*`; `APP` usa `curl` com o token por substituição, um por chamada.
- **Vídeo e capa na biblioteca da conta.** No conector não há upload: o Rodrigo sobe `A##_editado.mp4` e `CAPA_A##_*.png` na Biblioteca de mídia do Gerenciador e avisa; a skill acha o vídeo com `ads_get_ad_videos` (pelo título) e a imagem com `ads_get_ad_images` (hash). No modo App, `POST graph-video /advideos` e `POST /adimages`, miniatura `is_preferred` do vídeo ou a capa.
- **Conjunto de teste** criado com `ads_create_ad_set` a partir do último conjunto aprovado (`source_adset_id` do A51/A52, lido com `ads_get_ad_entities`, nunca de memória), nome `A## - Frio 25-55 - Feed+Reels`, R$ 60 por dia em centavos na unidade que o schema pedir, `start_time` 00h01 e `end_time` 23h59 do sétimo dia, `targeting_automation.advantage_audience` 0 com `advantage_audience_off_reason` ADVERTISER_REQUESTED_OFF (pedido do Rodrigo, conferido no targeting dos conjuntos anteriores).
- **Criativo** com `ads_create_creative`: `video_id`, `image_hash` da capa (miniatura obrigatória), `page_id` e `instagram_user_id` da conta (lidos com `ads_get_ad_account_pages` e `ads_get_ig_accounts`), `message` = legenda A, `headline` e `description` = seção B, `call_to_action_type` LEARN_MORE, `link_url` = `/sessao` com os UTMs dinâmicos do padrão da conta, `name` = `A## - {título}`. "Vários anunciantes" desligado: `contextual_multi_ads` com `enroll_status` OPT_OUT no criativo quando o schema aceitar; conferir depois no Gerenciador.
- **Anúncio** com `ads_create_ad` no conjunto novo, `creative_id` do criativo, nome `A##`. O conector cria em rascunho: quem publica é o Rodrigo no Gerenciador, ou a skill com `ads_activate_entity` na campanha, só com um segundo "sim" explícito.
- **Conferência pela API** depois de criar: orçamento, datas, targeting (Advantage+ 0, idades, Brasil, Feed e Reels, só celular), otimização Lead, atribuição, UTM, status. Texto principal e vídeo de anúncio criado a partir de publicação não são legíveis: conferir no Gerenciador.
- **Caminho alternativo:** o Rodrigo cria o conjunto e o anúncio no Gerenciador seguindo a lista de configuração da peça aprovada, e a skill confere pela API.
