# Plano — Central Dono 14% (Admin + Área do Cliente + Embed no Painel do Dono)

**Data:** 03/07/2026
**Status:** proposta para aprovação (nada foi construído ainda)
**Projeto Supabase:** `sizhdcrnfylimhsdfdnf` (o mesmo do site)
**Repo:** `docustoaolucro.com` (React + Vite + React Router, admin em `/admin`)

---

## 1. Visão geral da arquitetura

Três peças que conversam, mas vivem em lugares diferentes:

1. **Admin da Central** — dentro de `docustoaolucro.com/admin` (reaproveita o login que você já usa, via `user_roles` = admin). É onde você cadastra mentorados, cria planos, sobe o vídeo da Reunião de Engenheiro para Dono, acompanha entregas e **gera o link mágico** de cada cliente.

2. **Área do Cliente** — uma rota tokenizada, tipo `docustoaolucro.com/central/{token}`. Sem senha: quem tem o link entra direto e edita a própria área (o mockup que já validamos). Os dados vivem no Supabase do projeto.

3. **Painel do Dono** (sistema/deploy separado) — terá uma tela que **abre a Área do Cliente embedada** (iframe) apontando pro link mágico daquele cliente. Assim o cliente mexe na área dele sem sair do Painel.

Fluxo em uma frase: *você cadastra o cliente no admin → o sistema gera um link único → o cliente acessa (direto ou dentro do Painel do Dono) e edita → você acompanha tudo no admin.*

```
[ADMIN /admin/dono14]  --cria/gera link-->  [SUPABASE (dados)]  <--lê/escreve--  [ÁREA DO CLIENTE /central/{token}]
        (você, login)                                                                        ^
                                                                                             | iframe (embed)
                                                                              [PAINEL DO DONO — deploy separado]
```

---

## 2. Modelo de dados (novas tabelas no Supabase)

Prefixo `dono14_` pra não misturar com o que já existe (`crm_cards`, `contact_submissions` etc). Todas com RLS ligado.

| Tabela | Função | Campos principais |
|---|---|---|
| `dono14_clients` | O mentorado | nome, sobrenome, apelido, email, telefone, país, cep, estado, endereço, rg, cpf, estado_civil, data_nascimento, renda_mensal, foto_url, dono14_desde, objetivos, nao_pode_faltar, mentor (default "Rodrigo Haertel"), status, parada_tecnica_creditos (default 2) |
| `dono14_restaurants` | Restaurante do cliente (1:N) | client_id, nome, site, instagram, facebook, cnpj, endereço, cargo, faturamento, lucro_operacional, sistema_gestao, data_fundacao, qtd_colaboradores, formas_atendimento |
| `dono14_plans` | Planos de ação | client_id, titulo, ordem, liberado_em, prazo, status (em_andamento / aguardando_reuniao / concluido) |
| `dono14_plan_tasks` | Entregáveis do plano | plan_id, ordem, titulo, descricao, status (pendente / finalizado), prazo, entregue_em, links (jsonb) |
| `dono14_reunioes` | Reunião de Engenheiro para Dono | client_id, plan_id, numero, tipo (mensal / parada_tecnica), agendada_para, status (aguardando / agendada / realizada), video_url, realizada_em |
| `dono14_access_tokens` | Link mágico | client_id, token_hash, created_at, expires_at (nullable), revoked (bool), last_used_at |

Notas:
- **Parada Técnica** = crédito no cliente (`parada_tecnica_creditos`, começa em 2) + o agendamento entra em `dono14_reunioes` com `tipo = parada_tecnica`, consumindo 1 crédito. Assim fica fácil mostrar "2 disponíveis" e decrementar.
- **Token nunca é salvo em texto puro.** Guardamos só o hash (SHA-256). O link completo aparece pra você uma vez, na hora de gerar (e dá pra regerar).

---

## 3. Autenticação da Área do Cliente (link mágico sem senha)

Essa é a parte mais sensível, porque dar acesso de edição sem senha exige cuidado. Recomendação para a fase de testes:

**Padrão A — Gateway por Edge Function (recomendado agora)**
- A Área do Cliente não fala direto com o banco. Ela chama uma Edge Function (`central-client`) passando o token.
- A função valida o token (busca o hash, confere que não está revogado nem expirado), descobre o `client_id` e faz a leitura/escrita **com service role, escopada só àquele cliente**.
- O RLS bloqueia qualquer acesso anônimo direto às tabelas. Ninguém lê dados de outro cliente mesmo adivinhando IDs.
- Vantagem: seguro e simples de raciocinar, sem criar usuário no Supabase Auth pra cada cliente.

**Padrão B — JWT com claim de client_id (evolução futura)**
- Uma função troca o token por um JWT curto do Supabase com `client_id` embutido, e o RLS libera `client_id = claim`. Mais elegante, deixamos pra depois.

**Regras de segurança do link (todas na Fase 1):**
- Token aleatório de 32+ bytes, na URL.
- Guardar só o hash; mostrar o link cheio uma vez.
- **Revogável** a qualquer momento pelo admin (invalida o link na hora).
- Validade configurável (sugestão: sem expirar durante os testes, mas revogável; depois 90 dias).
- Rate limit por token e HTTPS obrigatório. Token nunca aparece em log.

> Trade-off honesto: link sem senha é ótimo pra fricção zero nos testes, mas quem tiver o link entra. Por isso: revogação fácil + não expor o link em lugares públicos. Pra produção, dá pra subir pra Padrão B ou pedir um código no primeiro acesso.

---

## 4. Rotas e telas

**Admin (`/admin/dono14`, protegido por `user_roles = admin`)** — vira a versão real do lado admin do mockup:
- Painel: KPIs, fila "Aguardando Reunião de Engenheiro", agenda.
- Mentorados: tabela + cadastrar novo → **botão "Gerar link" que copia o link mágico**.
- Planos de Ação: criar plano, montar entregáveis, subir vídeo da reunião.
- Entregas: kanban (Aguardando reunião → Reunião agendada → Reunião realizada).

**Área do Cliente (`/central/{token}`, pública mas travada por token)** — vira a versão real do lado mentorado do mockup:
- Início (planos, reuniões, Parada Técnica com 2 disponíveis).
- Detalhe do plano (vídeo da reunião, entregáveis, timeline).
- Meu Cadastro (todos os campos, editáveis e salvando no Supabase).

---

## 5. Embed no Painel do Dono (deploy separado)

- A rota `/central/{token}` precisa **permitir ser aberta em iframe** a partir do domínio do Painel. Isso é um header de resposta: `Content-Security-Policy: frame-ancestors 'self' https://<dominio-do-painel>` e **não** enviar `X-Frame-Options: DENY`. Configurável no servidor (openresty/nginx que já serve o site).
- O Painel do Dono monta `<iframe src="https://docustoaolucro.com/central/{token}">` numa tela "Minha Central".
- Como as bases são diferentes, o Painel precisa saber o token do cliente. Para os testes: você cola o link mágico no cadastro do cliente dentro do Painel. Evolução: uma Edge Function `resolve-central-link?email=` que o Painel consulta e recebe o link pronto.

---

## 6. Vídeo da Reunião de Engenheiro para Dono

Duas opções (dá pra suportar as duas):
- **Link YouTube/Vimeo (não listado)** — recomendado pra começar. Zero custo de storage, player pronto, é só colar a URL.
- **Upload nativo** — bucket privado no Supabase Storage (`reunioes`) + signed URL. Mais controle, custo de storage, fica pra depois.

---

## 7. Roadmap incremental (pra aprovar por etapa)

| Fase | Entrega | Depende de |
|---|---|---|
| **0** | Schema `dono14_*` + RLS + seed de 1 cliente teste | aprovação deste plano |
| **1** | Admin `/admin/dono14`: cadastrar mentorado + **gerar/copiar/revogar link mágico** | Fase 0 |
| **2** | Área do Cliente `/central/{token}` com Meu Cadastro editável (Edge Function gateway) | Fase 0 |
| **3** | Planos + entregáveis + reuniões (vídeo por link) + Parada Técnica + kanban de entregas | Fases 1–2 |
| **4** | Embed no Painel do Dono (CSP `frame-ancestors` + iframe apontando pro link) | Fase 2 |
| **5** | Hardening: expiração, revogação em massa, auditoria de acesso, upload de vídeo nativo | Fases 3–4 |

Enquanto o admin (Fase 1) não estiver pronto, você consegue operar cadastrando clientes direto no Supabase — como você mesmo mencionou que vai controlar por lá.

---

## 8. Decisões em aberto (preciso do seu ok antes de codar)

1. **Vídeo:** começamos só com link YouTube/Vimeo? (recomendo sim)
2. **Validade do link:** sem expirar durante os testes, só revogável? (recomendo sim)
3. **Ordem de execução:** faço a Fase 0 (banco) + Fase 2 (área do cliente + link mágico) primeiro, já que é o que destrava seus testes e o embed no Painel? Ou prefere o Admin (Fase 1) antes?
4. **Domínio do Painel do Dono:** qual é? (preciso pra liberar o `frame-ancestors` do embed)
5. **Onde o cliente entra primeiro:** ele recebe o link direto de você, ou sempre entra pelo Painel do Dono e a Central aparece embedada lá?

---

## 9. Riscos e cuidados

- **Link sem senha** dá acesso a quem o tiver: mitigado com revogação fácil e não expor publicamente.
- **Embed cross-domain** (Painel separado): cookies/sessão não são compartilhados entre domínios; por isso o token na URL é o que carrega o acesso. Precisamos acertar CSP e testar o iframe cedo (Fase 4).
- **Dados pessoais** (RG, CPF, renda): tabelas com RLS restrito, acesso do cliente só via gateway escopado, e nada de expor em log. Vale confirmar necessidade de cada campo sensível.
- **Isolamento entre clientes:** todo acesso do cliente é escopado por `client_id` derivado do token, nunca por ID vindo do front.
