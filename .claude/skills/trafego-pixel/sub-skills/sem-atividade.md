# Sub-fluxo. Pixels Sem Atividade

Destaque exclusivo de pixels da conta sem disparo nos últimos 7 dias. É o output que o aluno acessa quando suspeita que algum pixel está com problema mas não sabe qual.

## Perguntas que cobre

- "Tem algum pixel sem atividade nos últimos 7 dias?"
- "Quais pixels estão silenciosos?"
- "Tem pixel obsoleto que eu deveria limpar?"
- "Por que minha audience de remarketing está secando?"

## Dados necessários (Graph API)

```
GET /act_{ad_account_id}/adspixels?fields=id,name,last_fired_time,is_unavailable,creation_time
```

Para cada pixel com `last_fired_time` ausente ou > 7d, complementar com:

```
GET /{pixel_id}/stats?aggregation=event_total_counts&start_time={now-30d}&end_time={now}
```

Janela de 30d permite distinguir entre "pixel novo nunca disparou" e "pixel ativo que parou de disparar".

> **Importante:** sempre `aggregation=event_total_counts`. Se o parser retornar 0 mas `last_fired_time` for recente (< 24h), **não classificar como sem atividade**. É sintoma de parser lendo o shape errado — refazer com `event_total_counts`. Ver SKILL.md seção 2.2.

### Checagem extra automática

Após o Bloco 4 (Cruzamento com audiences), executar a "Checagem extra: pixel usado pelas campanhas" descrita em SKILL.md seção 1.4. Pixel sem atividade que está sendo usado por uma campanha ativa é o sinal mais grave possível e merece destaque imediato.

## Critério

Um pixel entra nesta lista se **qualquer** das condições for verdadeira:

- `last_fired_time` é `null`
- `last_fired_time` > 7 dias atrás
- `is_unavailable: true`

## O que entregar

### Bloco 1. Resumo
```
🔴 PIXELS SEM ATIVIDADE (últimos 7 dias)

Total: 2 de 4 pixels da conta
```

Quando todos estão ativos, exibir: `🟢 Todos os pixels da conta dispararam nos últimos 7 dias.`

### Bloco 2. Tabela detalhada
```
| Pixel              | Último disparo | Criado em   | Eventos 30d | Diagnóstico       |
|--------------------|----------------|-------------|-------------|-------------------|
| Pixel Antigo (BR)  | há 9 dias      | 2024-08-12  | 1.205       | parou recentemente|
| Pixel Teste        | nunca          | 2025-11-03  | 0           | nunca instalado   |
```

### Bloco 3. Diagnóstico por pixel

Para cada pixel sem atividade, classificar em uma das categorias:

| Categoria | Critério | Causa provável | Ação |
|---|---|---|---|
| **Nunca instalado** | `last_fired_time = null` E `eventos 30d = 0` | Tag não foi colocada na página | `/pagina-pixel` para instalar |
| **Parou recentemente** | Disparou nos últimos 30d mas não nos 7d | Página mudou, tag removida, redirect novo | Verificar a página + reinstalar tag se necessário |
| **Obsoleto** | Último disparo > 60 dias | Site antigo, projeto encerrado | Considerar arquivar no Business Manager |
| **Desativado** | `is_unavailable: true` | Pixel desativado pelo Business Manager | Reativar ou usar outro pixel |
| **Pixel duplicado** | Mais de 1 pixel ativo na conta com nome similar | Aluno criou novo sem desativar o velho | Limpeza manual |

### Bloco 4. Cruzamento com audiences

Se o aluno tem custom audiences alimentadas pelo pixel inativo, sinalizar:

```
🔗 IMPACTO EM AUDIENCES

O pixel "Pixel Antigo (BR)" alimenta as seguintes custom audiences:

- Visitantes 30d (atual: 8.500, há 30d: 14.000, queda 39%)
- Carrinho abandonado (atual: 320, há 30d: 480, queda 33%)
- Compradores (atual: 180, há 30d: 175, estável)

Sem disparo do pixel, essas audiences vão continuar encolhendo.
Toda campanha de remarketing que depende delas perde alcance progressivamente.
```

A skill recupera essa informação consultando `/act_{ad_account_id}/customaudiences?fields=id,name,subtype,rule_aggregator,operation_status,approximate_count` e cruzando com o pixel.

## Handoffs

| Achado | Para onde |
|---|---|
| Nunca instalado | `/pagina-pixel` (instalar) |
| Parou recentemente | Verificar a página manualmente; depois `/pagina-pixel` se a tag foi mesmo removida |
| Obsoleto | Limpeza manual no Business Manager |
| Audiences secando junto | `/trafego-publicos` (recriar audience) **depois** de resolver o pixel; senão a nova audience também esvazia |
| Múltiplos pixels duplicados | Decisão manual de qual manter; depois `/pagina-pixel` para apontar a página para o pixel definitivo |

## Cache

Salvar payload em `meus-produtos/{ativo}/trafego/pixel/sem-atividade-{YYYY-MM-DD}-{hh}.md` com TTL 1h.
