@echo off
rem Rotina agendada 03h: leitura diaria do perfil @rodrigohaertel (somente leitura na Graph API).
rem Registrada no Agendador de Tarefas do Windows por scripts\instagram-perfil-registrar-tarefa.ps1.
rem Nao usa o Claude: o script Python busca os numeros e grava o relatorio do dia em
rem meus-produtos\linha-editorial\trafego\analise\perfil-diario\. Log em scripts\instagram-perfil.log
cd /d "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo"
echo ===== %date% %time% inicio ===== >> scripts\instagram-perfil.log
py -3 scripts\instagram-perfil-diario.py >> scripts\instagram-perfil.log 2>&1
echo ===== %date% %time% fim (codigo %errorlevel%) ===== >> scripts\instagram-perfil.log
