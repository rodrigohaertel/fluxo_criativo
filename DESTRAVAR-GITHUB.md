# Publicar no GitHub — como funciona agora

Atualizado em 05/08/2026. Vale para o repositório `Do-Custo-ao-Lucro/docustoaolucro`.

## O mapa (simples)

Existem dois lugares onde o Claude trabalha:

| | Onde roda | Push no GitHub |
|---|---|---|
| **Claude Code (no app)** | **Na sua máquina**, na pasta que você abrir | **Funciona sempre** — usa o seu git e as suas credenciais |
| **Cowork** (o chat de tarefas) | Num computador da Anthropic ("nuvem") | Travado por tarefa — dá 403 se a tarefa não nascer com o repositório nas fontes |

**Conclusão: publicação de site é no Code.** O clone do site está em `C:\Users\rodri\dev\docustoaolucro`, e o manual que o Code lê sozinho é o `CLAUDE.md` na raiz dessa pasta (mesclado em 05/08 com as regras do projeto — peça ao Code para commitar e publicar, homolog primeiro e main depois).

## Divisão de trabalho

- **Code:** tudo que termina em commit/push — editar página, hotfix, migração, edge function.
- **Cowork:** copy, tráfego, CRM, análises, relatórios — e verificação de produção (conferir o site no ar, PSI, CI), que é só leitura e funciona normal.
- **Misto:** o Cowork prepara e grava o arquivo pronto direto na pasta do clone; o Code commita e publica.

## Se um dia o Cowork precisar publicar direto (avançado)

A tarefa precisa **nascer** com o repositório nas fontes (não dá para adicionar depois, e retomar conversa antiga perde a permissão). Primeira mensagem da tarefa deve começar com o teste de sanidade:

```
git clone https://github.com/Do-Custo-ao-Lucro/docustoaolucro.git /tmp/dcal && cd /tmp/dcal && git push --dry-run origin HEAD:homolog
```

Falhou com 403 ou "could not read Username"? A tarefa nasceu sem a fonte — não deixe a sessão trabalhar "para publicar depois"; leve para o Code.

## Plano B (última opção)

A sessão presa gera um `.patch` e te entrega os comandos para colar no seu terminal. Foi assim que o hotfix da agenda entrou em 05/08. Funciona, mas hoje o Code resolve isso melhor.
