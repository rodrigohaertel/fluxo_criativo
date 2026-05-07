# Sub-fluxo. Programação Liga/Pausa de Adset (Delivery Schedule)

Configura o adset_schedule do Meta Ads para que o adset entregue apenas em horários/dias específicos da semana. Útil para pausar o adset fora do horário comercial, fim de semana ou madrugada.

## Perguntas que cobre

- "Programa pra ligar minhas campanhas na segunda e pausar no domingo"
- "Pausa anúncios entre meia-noite e 6h da manhã"
- "Quero rodar só de segunda a sexta, das 8h às 22h"
- "Pausa minha campanha no fim de semana inteiro"
- "Roda só nos horários de pico do meu público (18h às 23h)"

## Inputs

| Input | Default | Descrição |
|---|---|---|
| `adset_id` | obrigatório | Adset alvo (pode ser múltiplos) |
| `dias_semana` | seg a sex | 0=dom, 1=seg, ..., 6=sáb |
| `hora_inicio` | 08:00 | Horário em que entrega começa |
| `hora_fim` | 22:00 | Horário em que entrega termina |
| `timezone` | da ad account | Timezone usada pelo Meta |

## Pré-requisito crítico: lifetime_budget

`adset_schedule` **só funciona** com adset que tem `lifetime_budget` (orçamento total). Não funciona com `daily_budget`.

A skill verifica antes de aplicar:

```python
adset = GET /<adset_id>?fields=daily_budget,lifetime_budget,...
if adset.daily_budget is not None:
    # Bloqueia
    return "⚠️ Esse adset usa orçamento diário (daily_budget). adset_schedule só funciona com orçamento total (lifetime_budget). Quer que eu converta? (não muda o valor, só a forma de cobrança)."
```

Se aluno autoriza converter:
1. Calcular `lifetime_budget = daily_budget × dias_da_campanha`
2. Pedir `end_time` se a campanha não tem (lifetime_budget exige `end_time`)
3. Aplicar conversão **antes** do schedule

## Endpoint

```
POST /<adset_id>
{
  "adset_schedule": [
    { "start_minute": 480, "end_minute": 1320, "days": [1, 2, 3, 4, 5] }
  ],
  "pacing_type": ["standard", "day_parting"]
}
```

`start_minute` e `end_minute` são minutos desde meia-noite. Conversões úteis:
- 0 = 00:00
- 360 = 06:00
- 480 = 08:00
- 720 = 12:00
- 1080 = 18:00
- 1320 = 22:00
- 1440 = 24:00 (= dia seguinte)

Múltiplos blocos no mesmo array são permitidos (ex: rodar 8h-12h e 14h-18h):
```json
[
  { "start_minute": 480,  "end_minute": 720,  "days": [1,2,3,4,5] },
  { "start_minute": 840,  "end_minute": 1080, "days": [1,2,3,4,5] }
]
```

## Receitas pré-configuradas

A skill oferece atalhos:

### Receita 1. Horário comercial (seg a sex, 8h-22h)
```yaml
days: [1,2,3,4,5]
start_minute: 480  # 08:00
end_minute: 1320   # 22:00
```

### Receita 2. Sem fim de semana (seg a sex, 24h)
```yaml
days: [1,2,3,4,5]
start_minute: 0
end_minute: 1440
```

### Receita 3. Sem madrugada (todo dia, 6h-23h)
```yaml
days: [0,1,2,3,4,5,6]
start_minute: 360   # 06:00
end_minute: 1380    # 23:00
```

### Receita 4. Só fim de semana (sáb e dom, 9h-23h)
```yaml
days: [0,6]
start_minute: 540   # 09:00
end_minute: 1380    # 23:00
```

### Receita 5. Custom
Aluno define dias e horários manualmente.

## Preview YAML

```yaml
sub_fluxo: liga_pausa_schedule
adset_id: 6123456789
adset_nome: "[Adset] LAL1pct - 25-44"
adset_budget_atual: lifetime_budget = R$ 5.000

schedule:
  dias: [1, 2, 3, 4, 5]                # seg a sex
  janela: 08:00 às 22:00               # 14h por dia
  timezone: America/Sao_Paulo
  total_horas_semanais: 70             # vs 168 (full week) → 41% do tempo

efeitos_esperados:
  - delivery_paused_em_outros_horarios: sim
  - reset_aprendizado: SIM (mudança de pacing)
  - novo_orcamento_diario_efetivo: R$ 5000 / 7 dias / (70/168) = R$ 1714/dia equivalente

confirma aplicar? (digite SIM)
```

## Após aplicar

```
✅ Schedule aplicado: [Adset] LAL1pct - 25-44
   Adset ID: 6123456789

Agora o adset entrega apenas:
- Segunda a sexta
- 08:00 às 22:00 (horário Brasília)

Reset de aprendizado disparado.
Próxima reanálise sugerida: 48h após primeira execução do schedule.

Para reverter (voltar a rodar 24/7):
   POST /6123456789 { "adset_schedule": [], "pacing_type": ["standard"] }

Para ver entrega ao longo do dia depois de 7d:
   /trafego-analise → opção [5] Timing & Sazonalidade
```

## Múltiplos adsets de uma vez

A skill aceita aplicar o mesmo schedule a vários adsets:

```
Quer aplicar essa programação:
[1] Só nesse adset
[2] Em todos os adsets ativos da campanha {nome}
[3] Em todos os adsets ativos da conta (cuidado, vai gerar reset em todos)

Digite o número:
```

## Avisos

- **Reset de aprendizado obrigatório.** Toda mudança de adset_schedule reseta. Não use em campanha em fase de aprendizado ativa, exceto se a perda de dado compensa.
- **Timezone é da ad account**, não do produto. Se a conta foi criada em outro timezone, conferir com `GET /act_<id>?fields=timezone_name`.
- **lifetime_budget exige end_time.** Se adset não tem, a skill pergunta data de término ou não aplica.
- **Delivery não é instantâneo.** Pode levar até 30 min após o `start_minute` para entrega começar (Meta otimiza por leilão).
- **Schedule não funciona com Advantage Campaign Budget (CBO).** Se o adset estiver dentro de campanha CBO, o budget é da campanha e não pode ter `lifetime_budget` por adset. Nesse caso, a skill avisa e sugere mudar a campanha para ABO antes.
