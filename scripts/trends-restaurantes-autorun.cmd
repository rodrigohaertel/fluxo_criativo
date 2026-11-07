@echo off
rem Rotina agendada 07h: os 3 topicos do dia no mercado de bares e restaurantes (Linha Editorial).
rem Registrada no Agendador de Tarefas por scripts\trends-restaurantes-registrar-tarefa.ps1. Log em scripts\trends-restaurantes.log
rem
rem 1) scripts\trends-restaurantes-coletar.py busca Instagram (Apify) e Google Noticias e grava
rem    meus-produtos\linha-editorial\trends\coleta\AAAA-MM-DD.json
rem 2) o Claude (headless) le a coleta, escolhe os 3 topicos, confere os fatos e grava
rem    meus-produtos\linha-editorial\trends\AAAA-MM-DD.json
rem 3) scripts\trends-restaurantes-html.py monta meus-produtos\linha-editorial\trends\AAAA-MM-DD.html
rem
rem A MARCA scripts\.trends-em-curso avisa os hooks de SessionStart que esta sessao e a rotina,
rem para eles nao injetarem a entrega do Dono 14% nem o aviso de atualizacao do projeto.
cd /d "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo"
echo trends em curso desde %date% %time% > scripts\.trends-em-curso
echo ===== %date% %time% inicio ===== >> scripts\trends-restaurantes.log
set PYTHONIOENCODING=utf-8
py -3 scripts\trends-restaurantes-coletar.py >> scripts\trends-restaurantes.log 2>&1
echo ----- coleta terminou (codigo %errorlevel%), curadoria comecando ----- >> scripts\trends-restaurantes.log
powershell -NoProfile -Command "$tok = (Get-Content .env | Where-Object { $_ -match '^CLAUDE_CODE_OAUTH_TOKEN=' }) -replace '^CLAUDE_CODE_OAUTH_TOKEN=',''; if ($tok) { $env:CLAUDE_CODE_OAUTH_TOKEN = $tok.Trim() } else { $api = (Get-Content .env | Where-Object { $_ -match '^ANTHROPIC_API_KEY=' }) -replace '^ANTHROPIC_API_KEY=',''; if ($api) { $env:ANTHROPIC_API_KEY = $api.Trim() } }; Get-Content -Raw -Encoding UTF8 'scripts/trends-restaurantes-prompt.md' | claude -p --permission-mode acceptEdits --allowedTools 'Read,Write,Glob,Grep,WebSearch,WebFetch,Bash(ls:*)' --max-turns 60" >> scripts\trends-restaurantes.log 2>&1
echo ----- curadoria terminou (codigo %errorlevel%), montando o HTML ----- >> scripts\trends-restaurantes.log
py -3 scripts\trends-restaurantes-html.py >> scripts\trends-restaurantes.log 2>&1
echo ===== %date% %time% fim (codigo %errorlevel%) ===== >> scripts\trends-restaurantes.log
del /q scripts\.trends-em-curso 2>nul
