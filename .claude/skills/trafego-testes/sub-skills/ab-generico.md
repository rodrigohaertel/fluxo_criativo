# Sub-fluxo. A/B Genérico (parametrizado por dimensão)

Cria teste A/B disciplinado variando UMA dimensão entre criativo, headline, audiência (inclui faixa etária), posicionamento, lance, estrutura ou CTA. Mesma mecânica para todas. O que muda entre as dimensões: o nível em que o teste é criado (ad, adset, campanha), o campo Marketing API que é variado, a métrica primária de leitura e os avisos específicos.

## Quando esta sub-skill é usada

Toda opção de [1] a [8] do menu de `/trafego-testes` cai aqui, com `dimensao` diferente:

| Opção do menu | `dimensao` |
|---|---|
| [1] A/B de criativo | `criativo` |
| [2] A/B de headline | `headline` |
| [3] A/B de audiência | `audiencia` |
| [4] A/B de faixa etária | `faixa_etaria` (caso particular de `audiencia`) |
| [5] A/B de posicionamento | `posicionamento` |
| [6] A/B de lance | `lance` |
| [7] A/B de estrutura | `estrutura` |
| [8] A/B de CTA | `cta` |

As opções [9] (`duplicar-variando`) e [10] (`campanha-remarketing`) têm sub-skills próprias e não passam por aqui.

---

## Mapa das 8 dimensões (referência única)

| `dimensao` | Nível onde varia | Modelo recomendado | Campo(s) Marketing API que mudam | Métrica primária | Conversões mín./lado |
|---|---|---|---|---|---|
| `criativo` | ad | `adsets_separados` (preferido) ou `ads_mesmo_adset` | `creative.image_hash` ou `creative.video_id` | CPA | 50 (low/mid), 30 (high) |
| `headline` | ad | `ads_mesmo_adset` (preferido) ou `adsets_separados` | `creative.object_story_spec.link_data.name` | CTR (CPA secundário) | 50 |
| `audiencia` | adset | `adsets_separados` (obrigatório) | `targeting.custom_audiences`, `targeting.interests`, `targeting.behaviors`, `targeting.geo_locations` | CPA | 50 |
| `faixa_etaria` | adset | `adsets_separados` (obrigatório) | `targeting.age_min`, `targeting.age_max` (resto idêntico) | CPA | 50 |
| `posicionamento` | adset | `adsets_separados` (obrigatório) | `targeting.publisher_platforms`, `targeting.facebook_positions`, `targeting.instagram_positions` | CPA | 50 |
| `lance` | adset | `adsets_separados` (obrigatório) | `bid_strategy`, `bid_amount` | CPA + desvio padrão dia a dia | 50 |
| `estrutura` | campaign | `campanhas_separadas` (obrigatório) | `smart_promotion_type` (Adv+) ou `objective` + buying_type | CPA + volume | 50 (janela 14d em vez de 7d) |
| `cta` | ad | `ads_mesmo_adset` (preferido) ou `adsets_separados` | `creative.object_story_spec.link_data.call_to_action.type` | CTR + taxa_conversao_anuncio | 50 |

**Regra de modelo:**
- `ads_mesmo_adset` só vale para variar coisa dentro do criativo (headline, primary_text, CTA, image_hash). Audience define leilão e exige adset próprio.
- `adsets_separados` é o default para qualquer outra dimensão.
- `campanhas_separadas` só para `estrutura` (Advantage+ Shopping é uma propriedade da campanha, não do adset).

---

## Inputs comuns (toda dimensão)

| Input | Default | Descrição |
|---|---|---|
| `dimensao` | obrigatório | Uma das 8 da tabela acima |
| `campaign_id` ou `adset_id` | obrigatório | Onde criar (varia conforme dimensão e modelo) |
| `budget_diario` | obrigatório | Mesmo nos N lados |
| `hipotese` | obrigatório | "X performa Y% melhor que Z porque ___" |
| `produto_slug` | produto ativo | Lê de `meus-produtos/.ativo` |
| `janela_dias` | 7 (14 para `estrutura`) | Janela mínima até a leitura |
| `n_variacoes` | 2 (3 permitido só em `headline`) | Mais que isso dilui orçamento |

## Inputs específicos por dimensão

### `dimensao = criativo`
| Input | Obrigatório | Descrição |
|---|---|---|
| `criativo_a` | sim | image_hash, video_id ou caminho local que será uploaded |
| `criativo_b` | sim | Idem |
| `headline`, `primary_text`, `cta` | iguais nos 2 | Para isolar criativo |

Aceita `tipo_mandala_a` e `tipo_mandala_b` (1 a 18) para registrar qual ângulo da Mandala VTSD está sendo testado. Skill apenas registra; o criativo em si é produzido por `/copy-anuncio` + `/criativo-estatico` ou `/video-heygen`.

### `dimensao = headline`
| Input | Obrigatório | Descrição |
|---|---|---|
| `headlines` | 2 a 3 | Lista de strings (≤ 40 chars Feed) |
| `criativo_id` | sim | Mesmo nos N ads |
| `primary_text`, `cta` | iguais | |

Receita Light Copy: a skill pode propor 3 variações aplicando 3 elementos literários distintos (especificidade, contraste temporal, questionamento implícito) a partir do Quadro do produto. Aluno aprova ou edita.

### `dimensao = audiencia`
| Input | Obrigatório | Descrição |
|---|---|---|
| `audiencia_a` | sim | ID de custom audience/lookalike OU spec de targeting |
| `audiencia_b` | sim | Idem |
| Restantes (criativo, headline, primary_text, posicionamento, bid_strategy, idade, gênero) | iguais | |

Pares com semântica VTSD recomendada: HOT vs COLD, Intermediário vs Avançado (das bases por nível), Comprador (LAL) vs Iniciante.

### `dimensao = faixa_etaria` (caso particular de audiência)
| Input | Obrigatório | Descrição |
|---|---|---|
| `idade_min_a`, `idade_max_a` | sim | Faixa A (ex: 25-34) |
| `idade_min_b`, `idade_max_b` | sim | Faixa B (ex: 35-44) |
| Restantes (audience, criativo, headline, posicionamento, lance) | iguais | |

### `dimensao = posicionamento`
| Input | Obrigatório | Descrição |
|---|---|---|
| `posicionamento_a` | sim | Slug ou lista (`feed_only`, `reels_only`, `stories_only`, `advantage_plus`) |
| `posicionamento_b` | sim | Idem |
| Restantes | iguais | |

Combinações comuns:

| Slug | publisher_platforms | facebook_positions | instagram_positions |
|---|---|---|---|
| `feed_only` | `[facebook, instagram]` | `[feed]` | `[stream]` |
| `reels_only` | `[facebook, instagram]` | `[facebook_reels]` | `[reels]` |
| `stories_only` | `[facebook, instagram]` | `[facebook_stories]` | `[story]` |
| `advantage_plus` | `[facebook, instagram, audience_network, messenger]` | (vazio) | (vazio) |

### `dimensao = lance`
| Input | Obrigatório | Descrição |
|---|---|---|
| `bid_strategy_a` | `LOWEST_COST_WITHOUT_CAP` (default) | Estratégia A |
| `bid_strategy_b` | `COST_CAP` ou `LOWEST_COST_WITH_BID_CAP` | Estratégia B |
| `cap_value` | obrigatório se B usa cap | Valor em reais (skill converte para centavos no `bid_amount`) |
| Restantes | iguais | |

Estratégias Marketing API suportadas: `LOWEST_COST_WITHOUT_CAP`, `LOWEST_COST_WITH_BID_CAP`, `COST_CAP`.

### `dimensao = estrutura`
| Input | Obrigatório | Descrição |
|---|---|---|
| `estrutura_a` | `MANUAL_ABO` (default) | Estrutura da campanha A |
| `estrutura_b` | `ADVANTAGE_PLUS_SHOPPING` (default) | Estrutura da campanha B |
| `criativos_ids` | mín. 4 se B é Adv+ | Adv+ exige pool |
| `objective` | `OUTCOME_SALES` ou `OUTCOME_LEADS` | Mesmo nas 2 campanhas |
| `pixel_id`, `evento_otimizado` | mesmos | |

Estruturas suportadas: `MANUAL_ABO`, `MANUAL_CBO`, `ADVANTAGE_PLUS_SHOPPING`.

### `dimensao = cta`
| Input | Obrigatório | Descrição |
|---|---|---|
| `cta_a` | sim | Slug Marketing API do CTA da variação A (ex: `LEARN_MORE`) |
| `cta_b` | sim | Slug Marketing API do CTA da variação B (ex: `SHOP_NOW`) |
| `cta_c` | opcional | Terceira variação (ex: `SIGN_UP`). Limite: 3 variações |
| `criativo_id` | sim | Mesmo nos N ads (image_hash ou video_id) |
| `headline`, `primary_text` | iguais | Para isolar o CTA como única variável |
| `link_destino` | mesmo | URL final idêntica nos N |

CTAs Marketing API mais usados em infoproduto:

| Slug API | Texto exibido | Quando usar |
|---|---|---|
| `LEARN_MORE` | "Saiba mais" | Topo de funil, descoberta |
| `SHOP_NOW` | "Compre agora" | Fundo de funil, oferta direta |
| `SIGN_UP` | "Cadastre-se" | Captura de lead em lançamento |
| `GET_OFFER` | "Aproveitar oferta" | Promoção ativa, escassez |
| `SUBSCRIBE` | "Assinar" | Recorrência |
| `BOOK_TRAVEL` | "Reservar" | Eventos, agendamento |
| `DOWNLOAD` | "Baixar" | Isca digital (e-book, planilha) |
| `WATCH_MORE` | "Assistir mais" | VSL, conteúdo em vídeo |
| `CONTACT_US` | "Fale conosco" | High ticket, qualificação |

A skill rejeita CTAs incompatíveis com o objetivo da campanha (ex: `BOOK_TRAVEL` em campanha `OUTCOME_SALES` sem catálogo).

---

## Construção do payload (algoritmo genérico)

```
1. Carregar inputs comuns + inputs específicos da dimensão
2. Determinar nivel = ad | adset | campaign (tabela acima)
3. Determinar modelo:
     - se dimensao == headline e n_variacoes ≤ 3: ads_mesmo_adset
     - se dimensao == criativo e aluno preferiu: ads_mesmo_adset
     - se dimensao == estrutura: campanhas_separadas
     - caso contrário: adsets_separados
4. Para cada variação (A, B, [C]):
     a. Montar nome: [WS-AB-{slug}] {dimensao}-{variacao_slug}-{produto_slug}
     b. Clonar template do nivel (ad/adset/campaign) com defaults idênticos
     c. Sobrescrever APENAS os campos da coluna "Campo(s) Marketing API que mudam" da tabela
     d. status: PAUSED
5. Validar simetria: budget igual nos N lados, audience igual (exceto se dimensao=audiencia/faixa_etaria), posicionamento igual (exceto se dimensao=posicionamento), lance igual (exceto se dimensao=lance)
6. Gerar Preview YAML (formato abaixo)
7. Aguardar SIM
8. POST nas N entidades em sequência
9. Se modelo == campanhas_separadas: também POST adsets e ads de cada campanha
10. Salvar arquivo de hipótese em meus-produtos/{ativo}/trafego/testes/{teste-slug}.md
11. Invalidar cache do /trafego-insights
12. Devolver: IDs criados + comandos DELETE de rollback + data_leitura_em (today + janela_dias)
```

---

## Endpoint Marketing API por modelo

### `ads_mesmo_adset` (apenas `criativo` e `headline`)
```
POST /act_<id>/ads (xN)
{
  "name": "[WS-AB-{slug}] {dimensao}-{variacao}-{produto}",
  "adset_id": "<adset_id>",
  "creative": { ... },             # varia por variação
  "status": "PAUSED"
}
```

### `adsets_separados` (criativo, audiencia, faixa_etaria, posicionamento, lance)
```
POST /act_<id>/adsets (xN)
{
  "name": "[WS-AB-{slug}] adset-{dimensao}-{variacao}-{produto}",
  "campaign_id": "<campaign_id>",
  "targeting": { ... },            # idêntico exceto na dimensão variada
  "daily_budget": <budget_em_centavos>,
  "billing_event": "IMPRESSIONS",
  "optimization_goal": "OFFSITE_CONVERSIONS",
  "promoted_object": { "pixel_id": "...", "custom_event_type": "PURCHASE" },
  "bid_strategy": "...",           # idêntico exceto se dimensao=lance
  "status": "PAUSED"
}

POST /act_<id>/ads (x1 por adset)  # criativo idêntico nos N
```

### `campanhas_separadas` (apenas `estrutura`)
```
POST /act_<id>/campaigns (xN)
{
  "name": "[WS-AB-{slug}] campaign-{estrutura}-{produto}",
  "objective": "OUTCOME_SALES",
  "buying_type": "AUCTION",
  "smart_promotion_type": "AUTOMATED_SHOPPING_ADS",   # APENAS para Adv+
  "special_ad_categories": [],
  "status": "PAUSED"
}

POST /act_<id>/adsets ...          # 1+ adsets para variação manual; Adv+ cria automaticamente
POST /act_<id>/ads ...
```

---

## Preview YAML padrão

```yaml
sub_fluxo: ab_generico
dimensao: criativo | headline | audiencia | faixa_etaria | posicionamento | lance | estrutura | cta
nome_teste: "[WS-AB] {dimensao}-{slug-A}-vs-{slug-B}-{produto}"
modelo: ads_mesmo_adset | adsets_separados | campanhas_separadas
nivel_criado: ad | adset | campaign
campaign_id: 6987654321                      # ou null se modelo=campanhas_separadas

hipotese: "{frase clara: X performa Y% melhor que Z porque ___}"

variacao_A:
  nome: "[WS-AB-A] {dimensao}-{slug}-{produto}"
  campos_variados:                            # apenas os da coluna da tabela
    {campo_1}: {valor_A}
    {campo_2}: {valor_A}
  budget_diario: 30 BRL
  tamanho_estimado: 2000000                   # apenas se dimensao=audiencia/faixa_etaria

variacao_B:
  nome: "[WS-AB-B] {dimensao}-{slug}-{produto}"
  campos_variados:
    {campo_1}: {valor_B}
    {campo_2}: {valor_B}
  budget_diario: 30 BRL

constantes:                                   # tudo que é igual nos 2 lados
  audience: ...                               # se dimensao != audiencia/faixa_etaria
  criativo: ...                               # se dimensao != criativo
  headline: ...                               # se dimensao != headline
  posicionamento: ...                         # se dimensao != posicionamento
  bid_strategy: ...                           # se dimensao != lance
  optimization_goal: PURCHASE
  pixel_id: ...

janela_minima_dias: 7                         # 14 se dimensao=estrutura
conversoes_minimas_por_lado: 50               # 30 se trilha=high
metrica_primaria: CPA | CTR (headline)
data_leitura_em: 2026-05-12

confirma criar {N} {ad|adset|campanha}(s) PAUSED? (digite SIM)
```

---

## Avisos por dimensão (apresentar ao aluno antes do preview)

### `criativo`
- Posicionamento Advantage+ mistura Feed/Reels/Stories. Para testar criativo em superfície específica, fixar posicionamento manualmente.
- Bidding strategy igual nos 2 lados, senão você está testando criativo + bidding ao mesmo tempo.
- Dimensione budget para garantir 50+ conversões por lado em 7d.

### `headline`
- Headlines em Feed ≤ 40 caracteres recomendado. Reels não tem limite mas trunca em ~50 no mobile.
- CTR é a métrica primária; CPA confirma se o headline atrai a pessoa certa.
- Limite recomendado: 3 variações. Mais que isso dilui orçamento por variação.

### `audiencia`
- Audience pequena (< 50K) com budget alto satura rápido.
- Audience muito grande (> 50M) vira broad de fato — algoritmo mistura tudo.
- Não use Advantage+ Audience num lado e segmentação manual no outro: vira teste de "expansão" + "audience" misturados.

### `faixa_etaria`
- Faixas próximas (ex: 25-34 vs 30-39) sobrepõem público; audience efetiva fica menor que a soma.
- Faixas extremas (18-24 vs 55+) podem precisar de criativo diferente. Se o aluno só quer testar idade, manter criativo igual mesmo se subótimo para uma das faixas.

### `posicionamento`
- Vídeo 9:16 funciona em Reels/Stories; vídeo 1:1 trunca em Reels.
- Audience Network e Messenger costumam puxar CPA pra baixo na média mas convertem pior. Para teste limpo Feed vs Reels, excluir Audience Network.

### `lance`
- Bid cap muito baixo (< 70% do CPA target da trilha) faz adset não entregar. Skill avisa.
- Cost cap em low ticket geralmente não compensa: algoritmo precisa de margem para otimizar.
- Mudar bidding em adset existente reseta aprendizado. Para teste limpo, criar adsets novos (modelo `adsets_separados`).

### `estrutura`
- Advantage+ exige pool de criativos (mínimo 4 ads de qualidade variada). Skill bloqueia se < 4.
- Adv+ não permite exclusões granulares (ex: excluir compradores). Funciona melhor para topo de funil novo.
- Comparação em 7d pode não bastar para Adv+. Janela default: 14d.
- Reset de aprendizado ao mover orçamento entre as 2 estruturas. Não deletar o "perdedor" muito cedo.

### `cta`
- A Graph API NÃO devolve breakdown por CTA. Por isso teste é a única forma de comparar (`SHOP_NOW` vs `LEARN_MORE` etc.).
- CTR é a métrica primária; `taxa_conversao_anuncio` (purchases ÷ link_clicks) confirma se o CTA atrai o clique certo. Um CTA agressivo (`SHOP_NOW`) pode subir CTR e derrubar conversão se o público ainda não está pronto pra comprar.
- Validar compatibilidade objetivo × CTA antes do POST. `SHOP_NOW` em `OUTCOME_LEADS` é desperdício; `SIGN_UP` em `OUTCOME_SALES` confunde o algoritmo.
- Manter headline, primary_text, criativo e link_destino idênticos. Senão você está testando CTA + outra coisa ao mesmo tempo.
- Texto que aparece ao lado do botão é definido pelo Meta (vem da localidade do usuário), não pela skill. Aluno não pode personalizar "Compre Agora" para "Adquirir Agora" via API — só escolher o slug.

---

## Após criar (mensagem padrão)

```
✅ Teste A/B criado (PAUSED):
   Variação A: {nivel} {id_A} ("{nome_A}")
   Variação B: {nivel} {id_B} ("{nome_B}")
   {variação C se houver}

Hipótese salva em:
   meus-produtos/{produto}/trafego/testes/{teste-slug}.md

Próximos passos:
1. Ativar as {N} entidades no Gerenciador (PAUSED → ACTIVE).
2. Aguardar {janela_dias} dias com {conversoes_minimas}+ conversões em cada lado.
3. Em {data_leitura}, rodar /trafego-analise opção [3] Criativos para ler resultado.

Para reverter (deletar as {N} entidades criadas):
   DELETE /{id_A}
   DELETE /{id_B}
   {DELETE /{id_C} se houver}
```

---

## Princípios desta sub-skill

1. **UMA dimensão por execução.** Se o aluno pedir 2 dimensões variando, recusar e oferecer rodar 2 testes em sequência.
2. **Simetria obrigatória.** Validar que tudo que NÃO é da dimensão variada está idêntico antes do preview.
3. **Modelo escolhido pela tabela.** Não deixar aluno forçar `ads_mesmo_adset` para `audiencia` ou `posicionamento`.
4. **Avisos da dimensão sempre apresentados** antes do preview.
5. **Toda criação é PAUSED.** Ativação manual após confirmação.
6. **Hipótese registrada** em arquivo .md antes do POST. Sem hipótese, sem teste.
7. **Métrica primária da dimensão usada** na leitura D+7 (CTR para `headline`, CPA para o resto).
8. **Convenção `[WS-AB-{slug}]`** no nome de toda entidade criada.
