# Sub-fluxo. Duplicar Campanha/Adset com Variação

Pega uma entidade Meta Ads existente e duplica, alterando UMA dimensão. Diferente do A/B clássico porque o original continua rodando — a duplicata é uma extensão, não uma comparação.

## Perguntas que cobre

- "Duplica minha melhor campanha mas muda a segmentação para 25-34 anos"
- "Pega meu adset top e duplica trocando só o criativo"
- "Replica a campanha que tá indo bem mas em outra geo"
- "Cria uma cópia da campanha X com idade 35-44"

## Inputs

| Input | Default | Descrição |
|---|---|---|
| `entity_id` | obrigatório | ID da campanha, adset ou ad a duplicar |
| `dimensao_a_alterar` | obrigatório | `idade`, `geo`, `audience`, `criativo`, `posicionamento`, `lance`, `headline` |
| `valor_novo` | obrigatório | Valor da dimensão na duplicata |
| `nome_sufixo` | gerado | Sufixo do nome (ex: `-25_34`) |
| `manter_status_original` | true | Original continua rodando |

## Endpoint

```
POST /<entity_id>/copies
{
  "deep_copy": true,                     # copia campanha + adsets + ads
  "rename_options": {
    "rename_strategy": "DEEP_RENAME",
    "rename_suffix": "_dup-25-34"
  }
}
```

Resposta: `{ "copied_campaign_id": "...", "ad_object_ids": {...} }`

Depois, atualizar a entidade duplicada para aplicar a variação:

```
POST /<copied_adset_id>
{
  "targeting": {
    ...mesmo targeting original...,
    "age_min": 25,
    "age_max": 34
  }
}
```

## Dimensões suportadas e como aplicar

| Dimensão | Endpoint para alterar | Campo |
|---|---|---|
| `idade` | POST adset | `targeting.age_min`, `targeting.age_max` |
| `geo` | POST adset | `targeting.geo_locations` |
| `audience` | POST adset | `targeting.custom_audiences`, `targeting.interests` |
| `criativo` | POST ad | `creative` |
| `posicionamento` | POST adset | `targeting.publisher_platforms`, `targeting.facebook_positions`, `targeting.instagram_positions` |
| `lance` | POST adset | `bid_strategy`, `bid_amount` |
| `headline` | POST ad | `creative.object_story_spec.link_data.name` |

## Sugestão automática de variação (atalho VTSD)

Quando o aluno pede "duplica meu melhor anúncio em outro público mas me sugere qual público", a skill:
1. Identifica os interesses já em uso na campanha original.
2. Lê `idconsumidor.md` do produto ativo para descobrir interesses adjacentes.
3. Sugere 1 a 3 públicos alternativos com base na matriz de níveis (iniciante / intermediário / avançado).

Ex: campanha original em LAL1pct-Compradores. Sugestão de público alternativo: 
- "Saved-Intermediarios-curso-tarot" (já criado por `/trafego-publicos`), ou
- LAL2pct-Compradores (LAL com escala maior), ou
- Audience nova de carrinho abandonado 30d.

## Preview YAML

```yaml
sub_fluxo: duplicar_variando
entidade_original:
  tipo: campanha
  id: 6987654321
  nome: "[Campanha] Tarot LAL1pct"
  status: ACTIVE (continua rodando)

duplicata:
  nome: "[WS-AB] dup-campanha7384-mudando-idade-25_34-curso-tarot"
  dimensao_alterada: idade
  valor_original: 25-55
  valor_novo: 25-34
  estrutura_copiada: deep_copy (campanha + 2 adsets + 5 ads)

variacao_aplicada_em: adset_id 6987654322 (e os outros adsets também copiados terão a mesma idade)

orçamento_inicial: 30 BRL/dia (mesmo do original; aluno pode ajustar)
status_inicial: PAUSED

confirma duplicar e aplicar a variação? (digite SIM)
```

## Após criar

```
✅ Campanha duplicada: 7654321099 (PAUSED)
   Original: 6987654321 (continua ACTIVE)

Hipótese salva. Próxima leitura: 12/05/2026.

Para reverter (deletar a duplicata):
   DELETE /7654321099
```

## Avisos

- **`deep_copy: true`** copia a árvore inteira. Para apenas adset, usar `POST /<adset_id>/copies`.
- **Audiences são reutilizadas**, não duplicadas. As 2 versões compartilham as mesmas custom audiences.
- **Pixel é reutilizado**.
- **Cuidado com sobreposição de audience**: se a duplicata tem audience que sobrepõe muito com original (ex: idade 25-34 vs 25-55), elas competem entre si no leilão. Skill avisa quando overlap > 50%.
- **Não confundir com A/B clássico**: aqui o objetivo é replicar para escalar/variar, não comparar. Para comparar, usar sub-skills 1-7.
