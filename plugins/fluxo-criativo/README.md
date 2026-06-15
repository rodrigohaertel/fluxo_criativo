# Fluxo Criativo — Plugin do Cowork

Conjunto completo de skills do Workshop Marketing IA (metodologia VTSD) empacotado
como plugin instalavel no Claude Cowork. Assistente de marketing digital em
portugues do Brasil: concepcao de produto, copy Light Copy, paginas de vendas,
anuncios, low ticket, trafego pago, video e dashboards.

## O que vem dentro

| Componente | Quantidade | Observacao |
|---|---|---|
| Skills | 58 | inclui `vtsd-base-rules` (regras-base) |
| Comandos (legado) | 81 | formato single-file `.md` |
| Agentes | 18 | orquestradores e geradores |
| Scripts | pasta `scripts/` | Python/JS/PS1 de apoio |
| Regras | pasta `rules/` | checklists de copy e tempo |

## Como instalar no Cowork

1. No Cowork, adicione o marketplace pela URL do repositorio:
   `https://github.com/ReadyToGo-Education/fluxo_criativo`
2. Instale o plugin `fluxo-criativo` a partir do marketplace.
3. Atualize com `git pull` no repositorio; o Cowork pega a nova versao do
   marketplace.

## Como usar

- Acione qualquer skill pelo nome (ex: `produto-novo`, `copy-pagina`,
  `copy-anuncio`, `carrossel`, `trafego-analise`).
- Para gerar copy, a skill `vtsd-base-rules` carrega as regras de Light Copy,
  acentuacao pt_BR e vocabulario VTSD. Acione-a no inicio de tarefas de copy.

## Configuracao (variaveis de ambiente)

Skills de integracao leem credenciais de variaveis de ambiente / `.env` (nunca
hardcoded). Conforme o que for usar:

- `FB_ACCESS_TOKEN_PERMANENTE`, `FB_AD_ACCOUNT_ID`, `FB_PAGE_ID` — Meta Ads
- `APIFY_API_TOKEN` — dashboards (Instagram, TikTok, YouTube, LinkedIn)
- `OPENROUTER_API_KEY` — geracao de imagens
- `HEYGEN_API_KEY` — video com avatar
- credenciais Z-API, Telegram, ActiveCampaign, Lovable — conforme a skill

## Limitacoes do formato plugin

- No projeto original as regras do `CLAUDE.md` ficam sempre ativas e ha hooks que
  validam acentuacao, travessao e o painel automaticamente. Como plugin, as regras
  vivem na skill `vtsd-base-rules` (acione no inicio) e os hooks nao sao incluidos
  (evitam disparar em toda conversa do Cowork).
- Caminhos de scripts usam `${CLAUDE_PLUGIN_ROOT}/scripts/`, expandido pelo Cowork
  no runtime. Os scripts assumem dados de produto em `meus-produtos/` no diretorio
  de trabalho atual, criados pela skill `produto-novo`.
