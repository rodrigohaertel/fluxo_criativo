@echo off
rem Rotina agendada 02h: leitura diaria do funil Dono 14% (headless).
rem Registrada no Agendador de Tarefas do Windows. Log em scripts\autorun.log
cd /d "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo"
echo ===== %date% %time% inicio ===== >> scripts\autorun.log
powershell -NoProfile -Command "$tok = (Get-Content .env | Where-Object { $_ -match '^CLAUDE_CODE_OAUTH_TOKEN=' }) -replace '^CLAUDE_CODE_OAUTH_TOKEN=',''; if ($tok) { $env:CLAUDE_CODE_OAUTH_TOKEN = $tok.Trim() } else { $api = (Get-Content .env | Where-Object { $_ -match '^ANTHROPIC_API_KEY=' }) -replace '^ANTHROPIC_API_KEY=',''; if ($api) { $env:ANTHROPIC_API_KEY = $api.Trim() } }; $p = Get-Content -Raw 'scripts/dono14-autorun-prompt.md'; claude -p $p --permission-mode acceptEdits --max-turns 160" >> scripts\autorun.log 2>&1
echo ===== %date% %time% fim (codigo %errorlevel%) ===== >> scripts\autorun.log
