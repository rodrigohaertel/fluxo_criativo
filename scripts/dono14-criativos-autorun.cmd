@echo off
rem Rotina agendada: atualiza a analise por criativo do Dono 14% e regenera o dashboard HTML.
rem Registrada no Agendador de Tarefas do Windows. Log em scripts\criativos-autorun.log
rem Somente leitura na conta Meta e no banco. Nao altera campanha nem registro.
cd /d "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo"
echo ===== %date% %time% inicio ===== >> scripts\criativos-autorun.log
py -3 scripts\dono14-analise-criativos.py >> scripts\criativos-autorun.log 2>&1
if errorlevel 1 (
  echo [FALHA] coleta de dados interrompida, dashboard nao regenerado >> scripts\criativos-autorun.log
  echo ===== %date% %time% fim com erro ===== >> scripts\criativos-autorun.log
  exit /b 1
)
py -3 scripts\dono14-dashboard-criativos.py >> scripts\criativos-autorun.log 2>&1
echo ===== %date% %time% fim (codigo %errorlevel%) ===== >> scripts\criativos-autorun.log
