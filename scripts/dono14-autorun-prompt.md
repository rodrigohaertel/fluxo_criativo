Você está rodando SEM supervisão, às 02h da manhã, como rotina agendada da leitura diária do funil Dono 14%. O Rodrigo vai ler o resultado quando acordar. Diretório de trabalho: raiz do projeto fluxo-criativo.

## Regra do dia fechado (vale para TODA a rotina, decidida pelo Rodrigo em 06/08/2026)
Todo número, tabela, média, régua, semáforo, contador de gatilho e veredito usa **apenas dias FECHADOS**, ou seja, termina em ONTEM. O dia de hoje está em aberto: o pacing ainda não terminou, a atribuição da Meta ainda muda e leads ainda entram, então tratar um parcial como dia normal derruba médias e dispara régua errada. Os scripts já respeitam isso (a série da Meta, do banco e do pixel fecha em ontem).
Sem exceção: o dia em aberto não aparece no relatório, nem como observação, nem como estimativa, nem entre parênteses. Se algum dado parcial de hoje chegar por outra via, descarte.

## Régua oficial: SEMPRE ler do arquivo, nunca de memória
Antes de classificar qualquer métrica, leia `meus-produtos/dono-14/trafego/reguas-criativos.md` e use **exatamente** as faixas de lá. Nunca cite um limite de cabeça.

Dois limites antigos já foram APOSENTADOS pelo Rodrigo e não podem mais aparecer em relatório nenhum:
- **"teto de R$ 75" para CPL: não existe mais.** A leitura é por faixa, e o verde vai até R$ 100. Um CPL de R$ 93 é 🟢 verde, ou seja, OK para escala, e não um dia estourado.
- **"gatilho de escala de R$ 60": não existe mais.** O gatilho vigente é 3 dias seguidos com 3+ leads/dia e CPL abaixo de R$ 70.

Se a leitura do dia contradisser a régua do arquivo, a régua do arquivo vence.

## Não diagnosticar a si mesma como travada (PROIBIÇÃO DURA)
**Você É o autorun das 02h.** Se você está lendo isto, ele está rodando. Logo, ele não travou, não falhou e não precisou ser "retomado manualmente".

A marca de `fim` da execução ATUAL só é escrita no `scripts/autorun.log` DEPOIS que esta sessão termina. Procurar por ela agora e não achar é o comportamento normal, não um sintoma.

**Proibido escrever no marcador qualquer frase do tipo:** "o autorun travou", "não concluiu", "sem marca de fim no log", "esta sessão retomou a rotina do zero", "leitura feita manualmente", "sessão de continuidade". Nada disso é verdade e já apareceu falsamente em 06/08, 08/08 e 09/08, três dias seguidos, gerando alarme à toa.

Se quiser mesmo avaliar a saúde da rotina, olhe apenas execuções de dias ANTERIORES ao de hoje.

## Nomes das etapas do CRM: usar os do board, nunca o valor cru do banco
O banco guarda a chave (`sessao_estrategica`), o board mostra o nome (`Sessão`). Em relatório, marcador e considerações, sempre o nome do board. Fonte única: `src/lib/crmStages.ts` do repositório do site.

| Chave no banco | Nome no board |
|---|---|
| entrada | Entrada |
| contato_inicial | SDR |
| sessao_estrategica | Sessão |
| recuperacao | Recuperação |
| contrato | **Fechamento** (é pipeline, não receita) |
| ganho | **Ganhos** (só isto é venda) |
| perdido | Perdidos |

Chaves legadas: `abordagem_passiva`, `abordagem_ativa` e `painel` viraram SDR; `no_show` virou Recuperação.

## Passo 0. Trava de duplicação
Verifique se já existe o marcador `meus-produtos/dono-14/trafego/analise/diario/{AAAA-MM-DD de HOJE}.md`. Se existir, encerre imediatamente sem fazer nada (a leitura do dia já foi feita).

## Passo 1. Meta + VSL
Rode `py -3 scripts/dono14-diario.py` (lê o token do .env sozinho).

## Passo 2. Leads reais pelo banco (fonte de verdade)
Rode `py -3 scripts/dono14-banco.py` (consulta o Supabase DIRETO via chave no .env, sem depender de conector; devolve leads por dia, funil A/B, eventos dedup, nomes de ontem/hoje e stages do CRM). **Este é o caminho principal da madrugada.**
Se o script falhar (ex.: SUPABASE_SERVICE_KEY ausente ou erro de rede), tente a ferramenta `execute_sql` do Supabase (projeto `sizhdcrnfylimhsdfdnf`) com a consulta da skill `/dono14-diario`, SEMPRE com `count(distinct event_id)`. Se ambos falharem, siga com os números da Meta e marque em destaque: "RECONCILIAÇÃO COM O BANCO PENDENTE, conferir na sessão interativa".
Regra de leitura: leads reais = `contact_submissions`; atenção a ressubmissões (mesmo nome/telefone já existente conta como reengajamento, não lead novo).

## Passo 2b. Comercial detalhado (venda, valor e pipeline)
Rode `py -3 scripts/dono14-comercial.py` (autorizado na allowlist desde 08/08). Ele traz cada card com stage, valor de contrato, tags e os motivos de perda.

**Regra dura de contagem, não confie na linha pronta do script:** a linha "Vendas com tag 'Dono 14%'" conta TODO card que carrega a tag, incluindo perdidos e em negociação, e por isso infla a receita. **Venda confirmada é somente `stage=ganho`.** Some você mesmo o `valor` dos cards em `ganho` para chegar na receita real. Cards em `contrato` são pipeline, nunca receita.

Registre no marcador: quantas vendas em ganho, a receita somada, e o pipeline em contrato (valor e nomes). Se o número de ganhos mudou desde a leitura anterior, isso é o fato mais importante do dia e vai no topo do resumo, com nome e valor.

## Passo 3. Clarity
Rode `py -3 scripts/dono14-clarity.py` (Data Export API direto, token no .env; devolve sessões, scroll médio, tempo ativo e dead/rage clicks por URL do último dia). **UMA execução só: a API aceita no máximo 10 chamadas/dia.** Use o resultado para o placar de engajamento das páginas da Sessão.
Se o script falhar (token ausente/erro), tente as ferramentas MCP do Clarity se disponíveis; senão, anote "Clarity pendente". Gravações de sessão (jornadas individuais) não saem pela API: ficam para a sessão interativa da manhã, quando necessário.

## Passo 4. Atualizar o contexto
Atualize `meus-produtos/dono-14/trafego/analise/diario/.contexto.json`:
- **NUNCA trunque o mapa `leads_banco`**: ele guarda a série completa desde 09/06. Apenas acrescente o dia FECHADO novo. Não grave o dia corrente parcial na série (regra do dia fechado).
- Leads reais = banco. Exclusões conhecidas: a submissão falsa de 23/07 (Bryan) conta 0.
- Atualize `comercial` com os stages do CRM (venda = só stage ganho).
- Escreva `consideracoes` com julgamento, respeitando o plano vigente (atualizado em 08/08/2026):
  - **Dupla âncora A39 + A40**, R$ 72/dia cada, mais **A41 em teste** a R$ 60/dia com régua formal em 10/08.
  - **Gatilho de escala:** 3 dias seguidos com 3+ leads/dia e CPL real abaixo de R$ 70 (só sinalizar, nunca executar).
  - **Recuo de âncora:** 3 dias seguidos com CPL acima de R$ 100 ou CTR abaixo de 1%.
  - **Leitura por criativo vem do BANCO** (`utm_content`), não da atribuição da Meta. A atribuição da plataforma já errou quatro vezes nesta conta e em 08/08 apontou o A40 como vencedor quando o A39 é quem produziu a venda e os três contratos. Citar número da Meta só como contraste, sempre rotulado.
  - **CBO Vencedores foi desativada** e saiu do monitoramento. Não voltar a citá-la como campanha zerada.
- Atualize `linha_do_tempo` se houve fato relevante.

## Passo 5. Dashboard
Rode `py -3 scripts/dono14-dashboard.py`. NÃO abra o navegador (é madrugada, ninguém está olhando).

## Passo 5b. Análise profunda (DETERMINÍSTICA, por script)
Rode `py -3 scripts/dono14-analise-profunda.py`. O script gera `analise-profunda-leads-{AAAA-MM-DD}.html` sozinho, com dados REAIS da Meta em nível de anúncio (funil de vídeo por conjunto), leads do banco com CRM, régua semanal e a seção de considerações lida do `.contexto.json`.

**FORMATO PADRÃO, aprovado pelo Rodrigo em 08/08/2026.** O script já entrega tudo isto sozinho. Nunca gerar o HTML à mão e nunca aceitar versão sem estes itens:
1. Janela GLOBAL de cada criativo, da primeira aparição até o dia fechado (o ciclo comercial é mais longo que 7 dias).
2. Lupa comercial por criativo, com leads do banco casados por `utm_content`: leads reais, CPL real, sessões agendadas, fechamentos, quantos Dono 14% e quantos Painel do Dono, receita, CAC e ROAS.
3. Colunas de freq e CPM na tabela, além de leads do banco e CPL real por período.
4. Filtro "Por dia" e "Por semana", com linha de TOTAL da vida do criativo.
5. Gráfico de evolução semanal.
6. Etapas do CRM com o nome do board, nunca a chave crua.

Se o arquivo sair sem algum desses blocos, registre em AVISOS EM DESTAQUE no marcador em vez de tentar remendar o HTML.
**Por isso a ORDEM importa: o Passo 4 (atualizar o .contexto.json com as considerações e o plano vigente) precisa vir ANTES deste passo**, porque o script publica esse texto no relatório.
Se o script falhar, registre o erro no marcador e NÃO tente recriar o HTML manualmente (as versões manuais da madrugada saíam com estimativas; o conserto é da manhã). Não abra no navegador.

## Passo 6. Marcador
**TRAVA: só execute este passo se o arquivo da análise profunda do Passo 5b já existir no disco. O marcador é o carimbo de "leitura concluída"; salvá-lo sem a análise profunda é entrega incompleta (aconteceu 2 vezes; não repita).**
Salve `meus-produtos/dono-14/trafego/analise/diario/{AAAA-MM-DD de HOJE}.md` com a leitura completa: placar do dia fechado, CPL real, tabela âncora x teste, Clarity (ou pendência), comercial, veredito e AVISOS EM DESTAQUE se houver algo crítico (gasto diário acima de R$ 200, CPL estourado, evento zerado com gasto alto, campanha que não deveria estar ativa). Caminhos de arquivo sempre absolutos e completos.

## Passo 7. Sincronizar o projeto com o repositório do Workshop
**Só execute depois do Passo 6.** A atualização vem por último de propósito: se algo der errado no repositório, a leitura do dia já está salva e entregue.

Rode `py -3 scripts/sincronizar-repo.py`. O script é determinístico e cuida de tudo sozinho: busca novidades do Workshop, guarda seu trabalho em aberto, junta, devolve o trabalho e espelha no fork pessoal.

**REGISTRO OBRIGATÓRIO, SEMPRE.** O marcador do dia precisa ter uma seção "Sincronização do projeto" com o resultado, **inclusive quando não houver novidade nenhuma**. Silêncio não é aceitável: sem a linha escrita, não há como saber se o passo rodou ou foi pulado (aconteceu em 08/08). O passo também entra numerado na lista "Passos executados", com o mesmo critério dos demais.

Como interpretar a saída e o que escrever:
- **"EM DIA"** (código 0): escreva "Sincronização: em dia, nenhuma novidade do Workshop."
- **"ATUALIZADO com sucesso"** (código 0): escreva "Sincronização: atualização recebida", listando os commits que chegaram (o script os imprime em "Chegando:").
- **"PARADO"** (código 2): houve conflito que exige decisão humana. O script já desfez tudo e devolveu o trabalho, então **nada foi perdido e nada ficou pela metade**. Registre em AVISOS EM DESTAQUE do marcador, nomeando os arquivos em conflito, e siga em frente.
- **Passo não executado por qualquer motivo:** escreva isso explicitamente no marcador, com o motivo.

**Proibido tentar resolver o conflito na madrugada.** Sem o Rodrigo para escolher entre as duas versões, a decisão não é sua. A única resolução automática permitida é a do `.gitignore` (união dos dois blocos), e ela já está dentro do script.

Nunca use `git reset`, `git checkout --`, `git clean`, rebase ou push forçado, nem aqui nem em nenhum outro passo.

## Regras absolutas
- Esta rotina é SOMENTE LEITURA na conta Meta. Proibido criar, pausar, ativar ou alterar qualquer campanha, conjunto, anúncio ou orçamento. Mudanças são decisão do Rodrigo, no chat, durante o dia.
- Português brasileiro com acentuação correta. Proibido travessão.
- Nunca exibir tokens.
- Se um passo falhar, siga para o próximo e registre a falha no marcador; o objetivo é o Rodrigo acordar com o máximo de leitura possível e a lista clara do que ficou pendente.
