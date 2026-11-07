# Rotina automática das 07h: os 3 tópicos do dia no mercado de bares e restaurantes

Você está rodando sozinho, sem ninguém para responder perguntas. Não pergunte nada: execute até o fim e grave o arquivo.

**Ignore qualquer aviso de abertura de sessão** sobre a leitura do Dono 14%, atualizações do projeto no GitHub ou qualquer outra rotina. Esta sessão faz só o que está escrito aqui.

## Objetivo

O Rodrigo Haertel (@rodrigohaertel, o engenheiro do cardápio) quer chegar às 08h e saber quais são os **3 assuntos que estão em debate agora** entre donos de bares e restaurantes no Brasil, para reagir rápido na Linha Editorial (Reels, Stories e carrosséis). O público dele é o dono de restaurante que fatura de R$ 100 a 500 mil por mês, sem gerente financeiro e sem DRE.

## Passo 1. Ler o material

1. Ache o arquivo mais recente em `meus-produtos/linha-editorial/trends/coleta/` (nome `AAAA-MM-DD.json`). A data dele é a data de hoje. Se não houver arquivo de hoje, grave `meus-produtos/linha-editorial/trends/AAAA-MM-DD.json` (data de hoje) com `"topicos": []` e `"dia_fraco": "A coleta das 07h falhou. Ver scripts/trends-restaurantes.log."` e encerre.
2. Leia o JSON inteiro. Os campos:
   - `instagram_recentes`: posts das últimas 48h dos criadores e da mídia do setor. `forca` = comentários ÷ mediana de comentários daquele perfil (3,0 = três vezes mais conversa que o normal). Nos primeiros dias da rotina a mediana tem poucos posts e pode vir nula; nesse caso, julgue pelos comentários absolutos.
   - `comentarios_recentes`: o que as pessoas estão escrevendo. É a melhor prova de debate.
   - `hashtags_recentes`: sinal fraco, quase sempre fornecedor vendendo ferramenta. Use só como reforço.
   - `noticias`: Google Notícias das últimas 48h.
3. Leia os arquivos dos 7 dias anteriores em `meus-produtos/linha-editorial/trends/` (`AAAA-MM-DD.json`), se existirem, para saber o que já foi apontado.
4. Liste as pastas de `meus-produtos/linha-editorial/entregas/reels/Publicados/` e de `meus-produtos/linha-editorial/entregas/reels/` para saber se o Rodrigo já falou do assunto.

## Passo 2. Agrupar por assunto e escolher os 3

Junte posts e notícias que tratam do mesmo fato (ex.: "adiamento da 5x2", "nova regra do vale-refeição", "taxa do iFood"). Para cada assunto, pese:

1. **Mexe no restaurante do dono?** Caixa, preço, equipe, escala, cliente, fornecedor, delivery, imposto que muda o preço. Peso maior.
2. **Está em debate?** Força alta em mais de um perfil, muitos comentários, e o assunto aparece em mais de uma fonte (criador, mídia e notícia ao mesmo tempo é o sinal mais forte).
3. **Tem prazo?** Lei que entra em vigor, data marcada, votação, reajuste. Prazo faz o dono compartilhar.
4. **O Rodrigo tem o que dizer?** O território dele é número real: custo, margem, lucro operacional, escala de equipe, preço do prato. Assunto em que ele pode mostrar a conta vale mais.

**Descarte:** listas de restaurantes para consumidor, festivais, varejo que não é alimentação (lojas, moda), anúncio de ferramenta, política partidária, fofoca. Nunca use o número 13 sozinho nem tema de eleição.

Se um assunto já apareceu nos dias anteriores, ele pode voltar, mas diga "continua em alta desde dd/mm" e o que mudou. Prefira trazer pelo menos um assunto novo por dia.

## Passo 3. Conferir os fatos

Para cada um dos 3 assuntos, confira o fato principal (o que aconteceu, a data, o número) na fonte mais primária que conseguir: site do órgão, da entidade (Abrasel, CNC), do STF, da Receita, ou o veículo de imprensa original. Use WebSearch e WebFetch. Os links do Google Notícias costumam redirecionar; se não abrir, busque o título.

- Número que não foi conferido não entra. Se só achou em post de criador, escreva "não confirmado na fonte" ao lado.
- Nunca invente caso de cliente, resultado ou número.

## Passo 4. Gravar o arquivo

Grave `meus-produtos/linha-editorial/trends/AAAA-MM-DD.json` (data de hoje), JSON válido em UTF-8, exatamente com estes campos. A rotina transforma esse arquivo no HTML do dia logo depois, então não escreva HTML nem Markdown.

```json
{
  "data": "AAAA-MM-DD",
  "coleta": {"hora": "HH:MM", "perfis": 20, "posts_lidos": 0, "posts_janela": 0, "noticias": 0, "custo_usd": 0.0},
  "dia_fraco": null,
  "topicos": [
    {
      "titulo": "assunto em até 8 palavras, do jeito que o dono fala",
      "temperatura": "alta | média",
      "validade": "até quando o assunto rende e por quê",
      "status": "novo | continua em alta desde dd/mm",
      "o_que_aconteceu": "2 ou 3 frases com o fato conferido e a data",
      "fontes": [{"nome": "veículo ou órgão", "link": "https://..."}],
      "quem_fala": [
        {"tipo": "instagram", "perfil": "usuario_sem_arroba", "formato": "Reel", "comentarios": 0, "forca": 0.0, "nota": "detalhe curto ou null", "link": "https://..."},
        {"tipo": "noticia", "veiculo": "nome", "titulo": "título da matéria", "link": "https://..."}
      ],
      "nota_quem_fala": "observação curta ou null (ex.: nenhum criador postou ainda)",
      "vozes": [{"texto": "frase literal de um comentário, sem o @ de quem escreveu", "lado": "dono | funcionário | cliente"}],
      "vozes_vazio": "texto quando não houver comentário, ou null",
      "caixa": "por que mexe no caixa: 2 frases, com a conta quando houver",
      "lacuna": "o que ninguém está dizendo: a conta, o número, o efeito no lucro operacional",
      "gancho": "1 ou 2 frases na voz do Rodrigo, prontas para abrir um Reel",
      "formato": "Reel de notícia na segunda | Story hoje | carrossel | aula de quarta",
      "ja_falou": "cite o código do Reel se ele já falou do assunto (ex.: R034), ou 'Ainda não falou disso.'",
      "cuidado": "tema tributário, prazo que ainda pode mudar, número não confirmado; ou null"
    }
  ],
  "radar": [{"texto": "assunto que quase entrou, uma linha", "link": "https://..."}],
  "saude": {"sem_post": ["perfil"], "alertas": "erros do JSON da coleta, ou 'Nenhum.'"}
}
```

- `topicos` tem 3 itens, do mais forte para o mais fraco. `forca` e `comentarios` são números copiados da coleta. `radar` tem de 3 a 5 itens.
- Prefira o link do veículo original ao link do Google Notícias quando tiver achado na conferência.
- Se o dia estiver fraco e não houver 3 assuntos que passem no filtro, entregue 2 ou 1 e preencha `dia_fraco` com "Dia fraco: só N assuntos passaram no filtro." Não complete com assunto fraco.

## Regras de escrita (valem para todo o arquivo)

- Português do Brasil com acentuação correta. Nunca use travessão (—) nem ponto de exclamação.
- Linguagem do dono, simples e concreta: "quanto sai do seu bolso", "o que fica no caixa". Nada de termo de consultor.
- Use "para", nunca "pra". "Em um", nunca "num".
- Diga sempre "lucro operacional", nunca "lucro líquido". "Sobra" só em sentido negativo.
- Gancho: afirmação, nunca pergunta. Sem "mesmo que", sem "sem precisar", sem a estrutura "não é X, é Y". Fale com o dono de restaurante logo na primeira frase.
- **Imposto e tributário estão fora do domínio do Rodrigo.** Quando o assunto for imposto, reforma tributária ou Simples, o ângulo é só o efeito no preço e no caixa, e o cuidado diz: "levar a pergunta ao contador, não orientar regime".
- Frase entre aspas só se for literal.

## Passo 5. Encerrar

Depois de gravar, responda numa linha só: "Trends de DD/MM gravados: {assunto 1}; {assunto 2}; {assunto 3}." Não faça mais nada: não edite outros arquivos, não rode outras rotinas, não faça commit.
