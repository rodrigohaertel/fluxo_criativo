---
name: workshop-marketing:google-conexao
description: Porta única de entrada para conectar o projeto com o Google (YouTube Analytics, YouTube Data e, quando o token de desenvolvedor existir, Google Ads). Guia a criação da credencial no Google Cloud, salva tudo no .env e faz a autorização única da conta. Skill reutilizável, chamada por qualquer skill que leia dados do YouTube ou do Google Ads quando a conexão ainda não está configurada.
allowed-tools: Read, Edit, Bash
---

# Conexão Google (YouTube e Google Ads)

Equivalente do `/trafego-conexao` para o lado Google. É idempotente: pode ser chamada várias vezes sem efeito colateral.

Todas as regras globais do CLAUDE.md valem aqui: credencial só no `.env`, valor nunca ecoado no chat, confirmação com "salvo (mascarado)".

## Variáveis no `.env`

| Chave | O que é | Quem preenche |
|---|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | ID do cliente criado no Google Cloud | Aluno cola, Severino salva |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Chave secreta do mesmo cliente | Aluno cola, Severino salva |
| `GOOGLE_OAUTH_REFRESH_TOKEN` | Autorização permanente da conta | Gravada sozinha por `autorizar.py` |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Token de desenvolvedor do Google Ads | Só depois da aprovação do Google |
| `GOOGLE_ADS_CUSTOMER_ID` | Número da conta de anúncios (só dígitos) | Severino salva |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Número da conta de administrador (só dígitos) | Severino salva |

## Passo 0. Detectar estado

Leia o `.env` e verifique quais das chaves acima já têm valor (sem exibir os valores).

- As 3 chaves `GOOGLE_OAUTH_*` preenchidas: rode o teste do Passo 4. Se passar, informe "Conexão Google ativa" e encerre.
- Só `CLIENT_ID` e `CLIENT_SECRET` preenchidas: pule para o Passo 3.
- Nada preenchido: comece no Passo 1.

## Passo 1. Criar a credencial no Google Cloud (o aluno faz, guiado)

Instrua, um bloco por vez, esperando o "feito" de cada um:

1. Acessar `https://console.cloud.google.com/` com a mesma conta Google dona do canal e criar um projeto (ex: "Severino").
2. Em "APIs e serviços", "Biblioteca", ativar três APIs: **YouTube Analytics API**, **YouTube Data API v3** e **Google Ads API**.
3. Em "Tela de permissão OAuth" (Google Auth Platform): tipo de usuário **Externo**, preencher nome do app e e-mail. Depois, em "Público-alvo", clicar em **Publicar app** (status "Em produção").
   - Motivo: com o app em modo de teste, a autorização expira a cada 7 dias. Em produção ela não expira.
   - Como o app não é verificado, na hora de autorizar o Google mostra um aviso "app não verificado". É esperado: clicar em "Avançado" e continuar. O app é do próprio aluno.
4. Em "Credenciais", "Criar credenciais", "ID do cliente OAuth", tipo **App para computador**. O Google mostra o ID do cliente e a chave secreta.

## Passo 2. Salvar no `.env`

Caminho preferido (a chave nunca passa pelo chat): o aluno clica em **Baixar JSON** na tela do cliente OAuth e informa onde o arquivo ficou (normalmente a pasta Downloads, nome começando com `client_secret_`). Rode:

```bash
python3 .claude/skills/google-conexao/scripts/autorizar.py --importar "CAMINHO_DO_JSON"
```

O script copia os dois valores para o `.env`, apaga o JSON e já segue para a autorização do Passo 3.

Caminho alternativo: peça o ID do cliente e a chave secreta, um por vez. Salve com Edit cirúrgico no `.env`. Confirme apenas:

```
✅ Salvo no .env:
- GOOGLE_OAUTH_CLIENT_ID = (salvo, mascarado)
- GOOGLE_OAUTH_CLIENT_SECRET = (salvo, mascarado)
```

## Passo 3. Autorização única

Determine o comando Python da sessão (regra do CLAUDE.md) e rode:

```bash
python3 .claude/skills/google-conexao/scripts/autorizar.py
```

O navegador abre, o aluno escolhe a conta do canal (se for conta de marca, escolher a conta de marca) e autoriza. O script grava `GOOGLE_OAUTH_REFRESH_TOKEN` no `.env` sem exibir o valor. O script espera até 5 minutos.

## Passo 4. Testar

```bash
python3 .claude/skills/google-conexao/scripts/youtube_analytics.py testar
```

Resposta esperada: `Conexão ok. Canal: ... | inscritos: ... | vídeos: ...`

## Leituras disponíveis depois de conectado

| Comando | O que traz |
|---|---|
| `youtube_analytics.py lista` | Todos os vídeos publicados, com data, duração e marcação de possível Short |
| `youtube_analytics.py videos --dias 28` | Top vídeos do período: visualizações, percentual assistido, inscritos ganhos |
| `youtube_analytics.py origens --dias 28 [--video ID]` | De onde vêm as visualizações (anúncio pago, Shorts, busca, sugeridos) |
| `youtube_analytics.py canal --dias 28` | Totais do canal no período |

Os JSONs ficam em `meus-produtos/{ativo}/entregas/youtube-analytics/`.

Regra de leitura: a origem "Anúncio (pago)" separa a visualização comprada da orgânica. Ao julgar distribuição paga, olhar percentual assistido, inscritos ganhos por vídeo e o crescimento das origens orgânicas (sugeridos, busca, Shorts) depois do empurrão.

## Google Ads (fase seguinte)

A leitura e a escrita de campanhas pela API exigem o token de desenvolvedor, que só é emitido dentro de uma conta de administrador do Google Ads (Central de API) e passa por aprovação do Google. Enquanto `GOOGLE_ADS_DEVELOPER_TOKEN` não existir, as campanhas são operadas pelo painel.

Quando a skill de escrita no Google Ads existir, ela herda o mesmo gate de confirmação no chat usado na Meta: bloco de confirmação antes de qualquer criação, pausa, ativação ou mudança de orçamento, e nunca exibir o comando com credencial.

## Erros comuns

| Mensagem | Causa | Solução |
|---|---|---|
| Autorização recusada (HTTP 400 ou 401) no teste | App ficou em modo de teste e a autorização expirou, ou foi revogada | Publicar o app (Passo 1.3) e rodar `autorizar.py` de novo |
| "A conta autorizada não tem canal" | Autorizou a conta pessoal em vez da conta de marca | Rodar `autorizar.py` de novo e escolher a conta do canal |
| Erro 403 com "API not enabled" | Faltou ativar alguma API | Voltar ao Passo 1.2 |
