# Sub-fluxo. Status dos Pixels

Visão geral de saúde de todos os pixels da conta. É o output mais comum quando o aluno pergunta "meu pixel está funcionando?".

## Perguntas que cobre

- "Meus pixels estão recebendo eventos?"
- "Qual foi o último disparo?"
- "Tem algum pixel com problema?"
- "Quantos pixels eu tenho na conta? Algum sobrando?"

## Dados necessários (Graph API)

```
GET /act_{ad_account_id}/adspixels?fields=id,name,last_fired_time,is_unavailable,creation_time
```

Para cada pixel retornado, complementar com:

```
GET /{pixel_id}?fields=id,name,last_fired_time,is_unavailable,can_proxy,data_use_setting,owner_business
GET /{pixel_id}/stats?aggregation=event_total_counts&start_time={now-7d}&end_time={now}
```

Total: 1 + 2N chamadas onde N = pixels da conta. Em paralelo quando possível.

> **Importante:** sempre `aggregation=event_total_counts` — nunca `aggregation=event` para totais. Ver SKILL.md seção 2.1 e 2.2 (bug conhecido de contagem zerada quando o parser lê o formato errado).

### Checagem extra automática quando há 2+ pixels ativos

Após o Bloco 4 desta sub-skill, executar a "Checagem extra: pixel usado pelas campanhas" descrita em SKILL.md seção 1.4. É bloco final automático, não pergunta. Apenas pula em contas com 1 único pixel.

## O que entregar

### Bloco 1. Resumo
```
📡 PIXELS DA CONTA

Total: 3 pixels
🟢 Ativos:        2
🟡 Em atenção:    0
🔴 Sem atividade: 1
```

### Bloco 2. Tabela por pixel
```
| Pixel              | Status        | Último disparo  | Eventos 7d | Sinais críticos |
|--------------------|---------------|-----------------|------------|-----------------|
| Loja Principal     | 🟢 Ativo      | há 12 minutos   | 18.420     | —               |
| Captura Lançamento | 🟢 Ativo      | há 2 horas      | 1.205      | —               |
| Pixel Antigo (BR)  | 🔴 Sem ativ.  | há 9 dias       | 0          | desativar/limpar|
```

### Bloco 3. Drill-down rápido por pixel ativo
Para cada pixel verde, listar contagem dos 8 eventos padrão na janela:

```
🟢 Loja Principal — últimos 7 dias

PageView           14.230
ViewContent         3.180
AddToCart             420
InitiateCheckout      210
Purchase               48
Lead                    0   (esperado: conta de venda direta)
CompleteRegistration    0
Subscribe               0

Custom events: 2
- ClickWhatsApp        180
- Watch50pctVSL         92
```

### Bloco 4. Sinais críticos consolidados
Lista priorizada de problemas que apareceram:

```
⚠️ SINAIS CRÍTICOS

1. 🔴 Pixel "Pixel Antigo (BR)" sem disparo há 9 dias.
   Causa provável: tag removida da página antiga ou pixel obsoleto.
   Ação: confirmar se ainda está em uso. Se não, desativar no Business Manager.

2. 🟡 Loja Principal: deduplicate_rate = 22%.
   Causa provável: CAPI não está enviando metade dos eventos, ou chaves de match (email/phone)
   estão incompletas no payload server-side.
   Ação: investigar configuração CAPI no Events Manager. Considerar `/pagina-pixel` para revisar instalação.
```

## Critério de status (recap)

| Status | Critério |
|---|---|
| 🟢 Ativo | Último disparo ≤ 24h **e** eventos > 0 nos últimos 7d |
| 🟡 Atenção | Último disparo entre 24h e 7d **ou** eventos < 50 nos 7d |
| 🔴 Sem atividade | Último disparo > 7d **ou** `last_fired_time = null` **ou** `is_unavailable: true` |

## Handoffs típicos

| Achado | Para onde |
|---|---|
| Pixel verde sem `Purchase` (em conta perpétuo) | Investigar CAPI / checkout. Apontar `/pagina-checkout` se aplicável |
| Pixel sem `PageView` ou `last_fired_time = null` | `/pagina-pixel` (reinstalar tag) |
| Pixel duplicado / não usado | Limpeza manual no Business Manager |
| Pixel ativo mas deduplicate_rate < 30% | Investigação manual no Events Manager (não é função desta skill) |
| Audiences de remarketing secando + pixel inativo | `/trafego-publicos` (recriar audience) + `/trafego-analise` [8] |

## Cache

Salvar payload em `meus-produtos/{ativo}/trafego/pixel/status-{YYYY-MM-DD}-{hh}.md` com TTL 1h. Próxima chamada na mesma hora lê direto do arquivo.
