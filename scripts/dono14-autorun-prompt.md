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

## Como contar lead: CAPTAÇÃO é o número oficial (decidido pelo Rodrigo em 16/08/2026)

O `dono14-banco.py` devolve duas contagens por dia. Use cada uma no seu lugar:

- **CAPTAÇÃO** (coluna `CAPTACAO`): cadastros que a mídia entregou. **Inclui ressubmissão**, porque o anúncio pagou por aquele preenchimento e o reengajamento tem valor real. **Exclui falso e spam** (lista em `meus-produtos/dono-14/trafego/cadastros-falsos.json`). **É o número oficial: manda no CPL real, na régua, no gatilho de escala e na série `leads_banco` do contexto.**
- **lead_novo**: pessoas únicas no dia. Serve para projeção comercial e CAC, e para dizer quantas pessoas novas entraram no funil. Nunca usar para CPL.

Quando os dois diferirem, diga isso no marcador em uma linha, sem tratar como problema. Exemplo real de 15/08: captação 3, pessoas novas 2, porque o Lúcio (lead de 02/08, hoje em Fechamento) preencheu de novo e o Rodrigo unificou. CPL do dia é R$ 61,11 pela captação, não R$ 91,67.

**Evento órfão não é divergência.** O `dono14-banco.py` agora tem a coluna `orfaos`: eventos em `lead_events` sem lead correspondente em `contact_submissions`, casados por prefixo de hash do e-mail. Isso acontece quando o Rodrigo apaga um cadastro falso ou unifica dois cadastros do mesmo lead e remove o duplicado: a linha sai da tabela de leads, o evento fica. **Não abrir investigação, não pedir consulta extra, não registrar como pendência.** Basta escrever no marcador, em uma linha, quantos órfãos houve e a causa. O número oficial é sempre `leads_banco`. Casos conhecidos: 10/08 (cadastro falso do João Silva) e 15/08 (unificação do Lúcio).

**Cadastro falso não conta como lead.** Quando o Rodrigo identifica um, ele apaga do banco, e a partir daí os scripts já param de contar sozinhos. O que NÃO se corrige sozinho é a série `leads_banco` do `.contexto.json`, que guarda o número do dia em que o falso ainda existia. Se o total do `.contexto.json` divergir do que o `dono14-banco.py` devolve, **o banco vence**: corrija o dia no contexto e registre a correção no marcador. Casos já tratados: Bryan (23/07) e João Silva (10/08, apagado em 11/08, o dia caiu de 3 para 2 leads).

## Passo 2b. Comercial detalhado (venda, valor e pipeline)
Rode `py -3 scripts/dono14-comercial.py` (autorizado na allowlist desde 08/08). Ele traz cada card com stage, valor de contrato, tags e os motivos de perda.

**Regra dura de contagem, não confie na linha pronta do script:** a linha "Vendas com tag 'Dono 14%'" conta TODO card que carrega a tag, incluindo perdidos e em negociação, e por isso infla a receita. **Venda confirmada é somente `stage=ganho`.** Some você mesmo o `valor` dos cards em `ganho` para chegar na receita real. Cards em `contrato` são pipeline, nunca receita.

Registre no marcador: quantas vendas em ganho, a receita somada, e o pipeline em contrato (valor e nomes). Se o número de ganhos mudou desde a leitura anterior, isso é o fato mais importante do dia e vai no topo do resumo, com nome e valor.

## Passo 2c. Orçamento real da conta
Rode `py -3 scripts/dono14-orcamento.py`. Ele devolve o orçamento diário dos conjuntos ATIVOS e compara com o plano combinado.

**Use esse número para julgar o gasto do dia**, nunca o plano de memória. E **nunca mais escreva "não foi possível confirmar o orçamento via API"**: esse aviso falso se repetiu de 24 a 27/08 porque a chamada era feita inline e barrada pelo detector do terminal. O script resolve isso. Se ele próprio falhar, aí sim registre o erro real que apareceu.

## Passo 3. Clarity
Rode `py -3 scripts/dono14-clarity.py` (Data Export API direto, token no .env; devolve sessões, scroll médio, tempo ativo e dead/rage clicks por URL do último dia). **UMA execução só: a API aceita no máximo 10 chamadas/dia.** Use o resultado para o placar de engajamento das páginas da Sessão.

**Como ler o scroll (mudou em 12/08/2026):** a dobra da `/sessao` foi revisada e publicada pelo Rodrigo, e o CTA principal agora nasce DENTRO da primeira tela do celular (y=388 num viewport de 812). Antes ele ficava em y=872, fora da tela. Portanto **scroll baixo deixou de ser sintoma de "não chega ao botão"**: a pessoa pode converter sem rolar. Reportar o número, sim; tratar 13% ou 15% como problema automático, não. E **não cobrar mais a revisão da dobra como pendência**, ela está feita.
Se o script falhar (token ausente/erro), tente as ferramentas MCP do Clarity se disponíveis; senão, anote "Clarity pendente". Gravações de sessão (jornadas individuais) não saem pela API: ficam para a sessão interativa da manhã, quando necessário.

## Passo 4. Atualizar o contexto
Atualize `meus-produtos/dono-14/trafego/analise/diario/.contexto.json`:
- **NUNCA trunque o mapa `leads_banco`**: ele guarda a série completa desde 09/06. Apenas acrescente o dia FECHADO novo. Não grave o dia corrente parcial na série (regra do dia fechado).
- Leads reais = banco. Exclusões conhecidas: a submissão falsa de 23/07 (Bryan) conta 0.
- Atualize `comercial` com os stages do CRM (venda = só stage ganho).
- Escreva `consideracoes` com julgamento, respeitando o plano vigente (atualizado em 10/08/2026):
  - **PLANO VIGENTE desde 05/09/2026: RODIZIO DE 4 CRIATIVOS a R$ 60/dia cada, total R$ 240/dia.** A39 (baixado de R$ 140 para R$ 60), A42, A43 e A44. Decisao do Rodrigo: recuperar volume de lead e achar o proximo campeao, porque o A39 sozinho nao sustenta o funil. A43 e A44 comecam em 06/09 00h01. Conferir sempre pelo `dono14-orcamento.py`, nunca de memoria.
  - **Fim programado dos conjuntos novos:** A42 termina em 08/09 23h59, A43 e A44 em 12/09 23h59. Sem acao do Rodrigo, o programado cai sozinho para R$ 180/dia em 09/09 e para R$ 60/dia (so o A39) em 13/09. **Avisar com um dia de antecedencia**, na leitura de 08/09 e na de 12/09.
  - **Janela de teste dos criativos novos (A42, A43, A44): 7 dias cheios, sem veredito antes.** A R$ 60/dia, cada um acumula cerca de R$ 420 na janela, o que da poucas unidades de lead. Isso basta para julgar topo e ponte (CTR, CPC, CPV, connect) e para pegar CPL extremo, mas **nao basta para julgar venda**. Nao declarar criativo vencedor nem perdedor por numero de fechamento nessa janela.
  - **Nao chamar o A39 de criativo saturado.** A frequencia dele ficou entre 1,05 e 1,16 por sete semanas e o CTR semanal nao caiu (1,33% na primeira semana, 1,45% na ultima). O que subiu foi o CPL: R$ 83 nas quatro primeiras semanas contra R$ 132 nas tres ultimas. Reportar como encarecimento do lead, nao como fadiga de criativo.
  - **SÓ A DUPLA ÂNCORA, A39 + A40, a R$ 100/dia cada. Programado: R$ 200/dia.** Aplicado pelo Rodrigo em 11/08 às 09h24 (subiu de R$ 85), confirmado no registro de atividades da conta. Não comparar com R$ 204 nem com R$ 230, que são planos antigos.
  - **A41 foi PAUSADO em 11/08 às 09h23**, ao fim dos 7 dias de teste (04/08 a 10/08). Fechou com 3 leads reais, CPL real R$ 139, 1 sessão e nenhum fechamento. Não citar como campanha zerada nem cobrar decisão sobre ele: está encerrado. A cauda de atribuição dele pode pingar por alguns dias.
  - **PLANO VIGENTE desde 31/08 (aplicado pelo Rodrigo às 09h58 e 09h59, conferido no registro da conta): SÓ O A39, a R$ 120/dia. O A40 foi PAUSADO.** Fecha o mês com 48 leads, 11 sessões e ZERO venda, contra 3 vendas e R$ 51.000 do A39.
  - **O A42 entra em 01/09.** Criativo novo, sem histórico: os primeiros dias não têm base de comparação. Trate como janela de teste, do mesmo jeito que foi o A41 (7 dias cheios antes de veredito), e **não dispare régua de recuo sobre ele antes disso**. Quando ele subir, o programado passa a ser R$ 120 mais o que for definido para o A42; confirme sempre pelo `dono14-orcamento.py`, nunca de memória.
  - **Degrau de R$ 100 para R$ 120 no A39 em 31/08.** Os dias 31/08 e 01/09 são transição: reportar números, sem veredito sobre o criativo.
  - **A cauda de atribuição do A40 ainda pode pingar** por alguns dias depois da pausa. Lead atribuído a ele agora é resíduo, não entrega nova.
  - **PLANO NOVO desde 24/08 (decisão do Rodrigo): A39 e A40 a R$ 80/dia cada, total R$ 160/dia.** Ele baixou o orçamento para liberar caixa e foco no desenvolvimento de criativos novos. A41 segue pausado. **Confira o valor real na conta antes de comparar gasto com programado**: se ainda estiver em R$ 100, use R$ 200 e registre que a redução não foi aplicada.
  - **Com R$ 160/dia, o volume de leads cai junto, e isso é esperado, não é piora de criativo.** Proporcionalmente são cerca de 20% menos leads por dia. **Não tratar queda de volume como fadiga nem disparar régua de recuo por causa dela.** O que continua valendo é o CPL: se o custo por lead se mantiver na faixa verde com menos verba, o criativo está saudável.
  - **O gatilho de escala fica mais difícil de bater** (exige 3+ leads/dia) simplesmente porque há menos verba. Sinalize isso quando a contagem não avançar, em vez de sugerir que o funil piorou.
  - **Degrau para baixo também reabre aprendizado.** Os 2 primeiros dias após a redução (24 e 25/08) são transição: reportar os números, sem veredito sobre criativo.
  - **A decisão sobre o A40 foi substituída por esta.** Ele NÃO foi pausado: segue no ar com orçamento menor, enquanto o Rodrigo produz criativo novo. Não cobrar de novo a decisão de pausar.
  - **CONGELADO ATÉ DOMINGO 23/08 (decisão do Rodrigo em 18/08).** A janela de julgamento fechou em 17/08 com a dupla âncora APROVADA (16 leads, CPL médio R$ 63,92). O Rodrigo está em treinamento esta semana e não consegue gravar criativo novo, então **nada muda na conta até domingo**: A39 e A40 seguem a R$ 100/dia cada, A41 pausado.
    **Não cobrar decisão sobre o A40 nas leituras de 19 a 22/08.** Ele já sabe do quadro (30 leads, CPL R$ 55, 10 sessões e zero fechamento, CTR entrando no vermelho). Repetir isso todo dia é ruído. Reportar os números normalmente, sem pedir ação.
    **Na leitura de domingo 23/08**, trazer o balanço consolidado do A40 desde 11/08 (leads, CPL, sessões, fechamentos, CTR por semana) para ele decidir com o quadro fechado.
  - **Janela combinada: 11/08 a segunda-feira 17/08**, só com as duas âncoras. **Ler o resultado pela janela de 13 a 17**, descartando 11 e 12 como transição do degrau, porque mudança de orçamento reabre aprendizado. Dizer isso no relatório em vez de tratar 12/08 como veredito.
  - **Atenção ao efeito do degrau:** no dia em que o orçamento subiu (09/08), o gasto foi a R$ 296,52 e o CPL real saltou de R$ 44,58 para R$ 148,26. Um dia não prova, mas mexer em orçamento reabre aprendizado. Sempre olhar 2 ou 3 dias depois de um degrau antes de julgar o criativo.
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
5. **Análise do criativo fechando cada cartão** (texto determinístico: topo, retenção, ponte, lead, comercial, tendência e veredito pela régua). Substituiu o gráfico semanal, removido em 11/08 por decisão do Rodrigo.
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

**O script também faz BACKUP AUTOMÁTICO** (desde 10/08/2026): commita sozinho o que mudou em `scripts/`, `.claude/commands/`, `.claude/agents/`, `.claude/rules/`, `.claude/skills/`, `.claude/settings.json`, `CLAUDE.md` e `ARQUITETURA.md`, e envia para o fork pessoal. Registre no marcador o que ele disser:
- **"BACKUP: N arquivo(s) salvos"**: escreva quantos e siga.
- **"BACKUP: nada novo para salvar"**: escreva isso mesmo.
- **"BACKUP ABORTADO: o conteúdo parece conter credencial"**: isso é grave. Vai em **AVISOS EM DESTAQUE**, dizendo que algum arquivo tem algo parecido com token escrito nele e que o backup do dia não aconteceu. Não tente contornar, não commite à mão, não edite o arquivo para "limpar". A conferência é do Rodrigo.

Nada fora dessa lista de pastas é commitado, de propósito, para lixo de terminal e arquivo temporário nunca entrarem no repositório.

**Proibido tentar resolver o conflito na madrugada.** Sem o Rodrigo para escolher entre as duas versões, a decisão não é sua. A única resolução automática permitida é a do `.gitignore` (união dos dois blocos), e ela já está dentro do script.

Nunca use `git reset`, `git checkout --`, `git clean`, rebase ou push forçado, nem aqui nem em nenhum outro passo.

## Regras absolutas
- Esta rotina é SOMENTE LEITURA na conta Meta. Proibido criar, pausar, ativar ou alterar qualquer campanha, conjunto, anúncio ou orçamento. Mudanças são decisão do Rodrigo, no chat, durante o dia.
- Português brasileiro com acentuação correta. Proibido travessão.
- Nunca exibir tokens.
- Se um passo falhar, siga para o próximo e registre a falha no marcador; o objetivo é o Rodrigo acordar com o máximo de leitura possível e a lista clara do que ficou pendente.
