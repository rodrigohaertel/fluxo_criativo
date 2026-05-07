# Sub-fluxo. Eventos Rastreados

Drill-down em um pixel específico. Lista todos os eventos disparados nos últimos 7 dias com contagem, frequência e deduplicate rate.

## Perguntas que cobre

- "Quais eventos o pixel está rastreando?"
- "PageView, Purchase, Lead estão chegando?"
- "Tem evento custom no meu pixel?"
- "Meu CAPI está enviando direito?"
- "Qual a frequência de disparo de cada evento?"

## Dados necessários (Graph API)

```
GET /{pixel_id}?fields=id,name,last_fired_time,is_unavailable,can_proxy
GET /{pixel_id}/stats?aggregation=event_total_counts&start_time={now-7d}&end_time={now}
GET /{pixel_id}/stats?aggregation=event_match_quality&start_time={now-7d}&end_time={now}
GET /{pixel_id}/stats?aggregation=event_total_counts&start_time={now-14d}&end_time={now-7d}   # janela anterior, para comparação
```

A primeira chamada confirma metadata. **A segunda é a fonte canônica de "Total 7d" por evento** (formato `data: [{ event, value }]` direto). A terceira traz EMQ se disponível. A quarta puxa a janela anterior (D-14 a D-7) para detectar quedas — usar `event_total_counts` também aqui, não série temporal.

> **Atenção:** NÃO usar `aggregation=event` para somar totais. Esse formato é série temporal e não retorna o campo `value` no shape esperado pelo parser. Ver SKILL.md seção 2.1 e 2.2 (bug conhecido de contagem zerada).

Se o aluno pedir gráfico temporal explicitamente (ex: "mostra a curva de Purchase no dia"), aí sim chamar `aggregation=event` como complemento. Mas nunca como fonte de totais.

## O que entregar

### Bloco 1. Header do pixel
```
📡 Pixel "{nome}" ({id})
Último disparo: há 12 minutos
Status geral: 🟢 Ativo
Janela analisada: últimos 7 dias
```

### Bloco 2. Eventos padrão (sempre na ordem)
```
EVENTOS PADRÃO

| Evento               | Total 7d | Por dia (média) | Último disparo | Saúde |
|----------------------|----------|-----------------|----------------|-------|
| PageView             | 14.230   | 2.033           | há 12 min      | 🟢    |
| ViewContent          | 3.180    | 454             | há 14 min      | 🟢    |
| AddToCart            | 420      | 60              | há 1h          | 🟢    |
| InitiateCheckout     | 210      | 30              | há 2h          | 🟢    |
| Purchase             | 48       | 6.8             | há 3h          | 🟢    |
| Lead                 | 0        | 0               | nunca          | —     |
| CompleteRegistration | 0        | 0               | nunca          | —     |
| Subscribe            | 0        | 0               | nunca          | —     |
```

**Saúde do evento:**
| Estado | Critério |
|---|---|
| 🟢 | Disparou nas últimas 24h e contagem > 0 |
| 🟡 | Disparou nos últimos 7d mas há > 24h, ou queda > 50% vs janela anterior |
| 🔴 | Não disparou nos últimos 7d **e** o evento é esperado para o tipo de conta |
| — | Não disparou e não é esperado |

"Esperado para o tipo de conta": determinado pelo `tipo_funil` do produto ativo. Conta de venda direta espera `Purchase`. Conta de captação espera `Lead`.

### Bloco 3. Eventos custom
```
EVENTOS CUSTOM

| Evento               | Total 7d | Por dia | Último disparo |
|----------------------|----------|---------|----------------|
| ClickWhatsApp        | 180      | 25.7    | há 22 min      |
| Watch50pctVSL        | 92       | 13.1    | há 1h          |
| ClickButtonOferta    | 48       | 6.8     | há 4h          |
```

Quando não há eventos custom, exibir: `Nenhum evento custom configurado.`

### Bloco 4. Deduplicate Rate (CAPI)
Quando disponível:
```
🔁 DEDUPLICATE RATE (CAPI vs Browser)

Total recebido: 22.418 eventos
Deduplicados:  16.180 (72%)

Status: 🟢 Saudável (faixa 60% a 90%)
```

Faixas:
| Range | Status | Diagnóstico |
|---|---|---|
| 60% a 90% | 🟢 Saudável | CAPI + browser pareando bem |
| 30% a 59% | 🟡 Atenção | CAPI cobre menos eventos do que deveria, ou chaves de match incompletas |
| < 30% | 🔴 CAPI quase inativo | CAPI não está enviando, ou está enviando sem `event_id` ou chaves de match (email, phone, click_id) |
| > 95% | 🟡 Suspeito | Pixel browser bloqueado pelo navegador (Safari ITP, ad block) |

Quando não disponível, exibir: `Deduplicate rate não disponível (CAPI não detectada ou Graph API não retornou).`

### Bloco 5. Sinais críticos consolidados
```
⚠️ SINAIS CRÍTICOS

1. 🔴 Lead = 0 nos últimos 7d.
   Esperado para conta de venda direta? Não.
   Esperado para conta de captação? Sim — investigar página de captura.

2. 🟡 Purchase caiu 38% vs semana anterior (78 → 48).
   Causas possíveis: queda de tráfego, fluxo de checkout quebrado, evento de compra deixando de disparar.
   Próximo passo: cruzar com /trafego-analise [8] (Problemas Ocultos).
```

## Detecção de anomalias

Comparar contagem de cada evento com janela anterior (7d a 14d atrás):

| Variação | Sinal |
|---|---|
| Queda > 50% | 🔴 Crítico |
| Queda 20% a 50% | 🟡 Atenção |
| Variação < 20% | 🟢 Estável |
| Aumento > 100% | 🟢 Crescimento (não é problema) |

## Handoffs

| Achado | Para onde |
|---|---|
| `Purchase` zerado em conta de venda direta | `/pagina-checkout` (verificar disparo) + Events Manager manual |
| `Lead` zerado em conta de captação | `/pagina-pixel` + verificação manual da página de captura |
| Deduplicate rate < 30% | Investigação manual no Events Manager (chaves de match server-side) |
| Custo evento personalizado quer virar audience | `/trafego-publicos` (opção evento personalizado) |
| Queda > 50% em evento padrão | `/trafego-analise` [8] (Problemas Ocultos) para correlacionar com campanhas |

## Cache

Salvar payload em `meus-produtos/{ativo}/trafego/pixel/eventos-{pixel_id}-{YYYY-MM-DD}-{hh}.md` com TTL 1h.
