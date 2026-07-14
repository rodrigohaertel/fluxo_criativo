# /dono14-diario. Leitura diária do funil Dono 14%

Rotina de acompanhamento do tráfego e da captação da Mentoria Dono 14%. Roda 1x por dia (gatilho de início de sessão) ou sob demanda quando o usuário pedir.

## Passo 0. Contexto fixo
- Campanha consolidada CBO: `120246284721790527` (conta `act_760723921231720`).
- Pixel/dataset: `223799232011558`. Página: docustoaolucro.com/dono14.
- Regra de ouro: contar leads REAIS pelo BANCO (`contact_submissions`), nunca pela Meta.
- Metas do Rodrigo: 10 leads/dia + 2 reuniões/dia, CPL teto R$ 75.

## Passo 1. Meta + VSL (um comando só)
Rode: `py -3 scripts/dono14-diario.py`
Devolve a campanha por dia (gasto, cliques, LPV, lead Meta, CTR, CPM, reach, CPL Meta) e os eventos do VSL no pixel (Play, Unmute, retenção 25/50/75/100) com a taxa de ativar som. O script lê o token do `.env` sozinho.

## Passo 2. Leads reais pelo banco (execute_sql)
Reconciliação por dia (últimos 8 dias):
```sql
with dias as (select generate_series((current_date - 8), current_date, interval '1 day')::date as d)
select to_char(d,'DD/MM') dia,
 (select count(*) from contact_submissions cs where (cs.source ilike 'mentoria%' or cs.source ilike 'sess%') and (cs.created_at at time zone 'America/Sao_Paulo')::date=d) leads_banco,
 (select count(*) from contact_submissions cs where cs.source ilike 'mentoria%' and (cs.created_at at time zone 'America/Sao_Paulo')::date=d) leads_a,
 (select count(*) from contact_submissions cs where cs.source ilike 'sess%' and (cs.created_at at time zone 'America/Sao_Paulo')::date=d) leads_b,
 (select count(*) from lead_events le where le.event_name='Lead' and (le.created_at at time zone 'America/Sao_Paulo')::date=d) eventos_meta
from dias order by d;
```
Nomes dos leads do dia fechado (ontem):
```sql
select to_char(created_at at time zone 'America/Sao_Paulo','DD/MM HH24:MI') quando, name, whatsapp,
       case when source ilike 'sess%' then 'B' when source ilike 'mentoria%' then 'A' else '-' end funil
from contact_submissions
where (source ilike 'mentoria%' or source ilike 'sess%') and (created_at at time zone 'America/Sao_Paulo')::date = (current_date - 1)
order by created_at;
```

## Passo 2.5. Comercial do CRM (crm_cards)
Puxe o funil comercial direto do CRM e monte o objeto `comercial` para o `.contexto.json`. Tabelas: `crm_cards` (com `submission_id` ligando ao lead, `stage`, `valor_contrato`, `faturamento_medio`, `uf`, `motivo_perda`), `crm_tags` e `crm_card_tags`. Etiquetas de desfecho: "Dono 14%" (venda alto ticket), "Painel do Dono" (downsell), "Sessão Agendada", "No Show", "Sumiu".
```sql
select cs.name, c.stage::text as stage, c.valor_contrato, c.faturamento_medio, c.uf, c.motivo_perda,
 (select string_agg(t.name,', ' order by t.position) from crm_card_tags ct join crm_tags t on t.id=ct.tag_id where ct.card_id=c.id) tags
from crm_cards c left join contact_submissions cs on cs.id=c.submission_id where c.deleted_at is null order by coalesce(c.valor_contrato,0) desc;
```
Monte `comercial` = { fonte, total_cards, vendas_dono14 (cards com tag "Dono 14%"), receita_dono14 (soma do valor_contrato deles), vendas_painel (tag "Painel do Dono"), perdidos (stage perdido), em_recuperacao (stage recuperacao), no_show, agendada_pendente (stage sessao_estrategica), novo (stage contato_inicial), principais_perdas[] (resumo dos motivo_perda) }. O script calcula CAC (gasto/venda) e ROAS sobre o gasto.

## Passo 3. Clarity (opcional)
Sessões da /dono14 e engajamento, se ajudar a explicar o dia.

## Passo 4. Síntese (a leitura do dia fechado)
Apresente o dia de ontem com:
- Leads reais (banco) e a reconciliação com a Meta (bateu? quantos fantasmas?).
- CPL real = gasto do dia dividido pelos leads do banco. Comparar com o teto R$ 75.
- Entrega (gasto, reach, LPV, CTR, CPM) e a tendência da semana.
- Bloco do VSL: plays, ativações de som (Unmute) e retenção. Lembrar que o YouTube não conta autoplay mudo, a fonte é o pixel.
- Veredito do que observar, ancorado no plano atual: a campanha está em observação após a virada de 21/06 (9 leads). Gatilho para escalar orçamento = CPL real abaixo de R$ 60 com 3 ou mais leads/dia por 3 dias seguidos. Enquanto não confirmar, NÃO mexer em orçamento, público ou criativo (não resetar o aprendizado que virou a favor).

## Passo 5. Gerar o DASHBOARD (entregável final, sempre)
1. Escreva o contexto em `meus-produtos/dono-14/trafego/analise/diario/.contexto.json` com: `gerado_em` (hoje), `dia_fechado` (ontem), `leads_banco` (mapa "DD/MM": número de leads reais do banco, dos últimos ~8 dias), `veredito_titulo` (curto) e `consideracoes` (lista de frases com o diagnóstico e o que observar).
2. Rode `py -3 scripts/dono14-dashboard.py`. Ele lê esse JSON, puxa Meta e VSL ao vivo, e gera `meus-produtos/dono-14/trafego/analise/dashboard-dono14.html`.
3. Abra com `py -3 scripts/abrir-html.py "<caminho absoluto do dashboard>"` e entregue o caminho ao usuário. O dashboard é o entregável final de toda leitura diária.

## Passo 6. Marcar como concluído
Salve uma cópia curta da leitura em `meus-produtos/dono-14/trafego/analise/diario/{AAAA-MM-DD}.md` com a data de HOJE. Esse arquivo é o marcador que o gatilho de início de sessão usa para não repetir a leitura no mesmo dia.

## Regras
- pt_BR com acentuação. Proibido travessão.
- Token só do `.env` (o script lê sozinho). Nunca exibir token.
- A leitura é só consulta. Qualquer mudança na conta Meta (orçamento, pausar, escalar) passa pelo gate de aprovação no chat antes de executar.
