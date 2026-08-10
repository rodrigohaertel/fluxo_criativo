# Registra a tarefa agendada da analise por criativo do Dono 14%.
# Execucao unica: segunda-feira, 10/08/2026, as 03h.
# Para remover depois: Unregister-ScheduledTask -TaskName "Dono14 Analise Criativos 10-08"
# Para reagendar em outra data, mudar a linha do $trigger e rodar de novo (o -Force sobrescreve).
$action   = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo\scripts\dono14-criativos-autorun.cmd"'
$trigger  = New-ScheduledTaskTrigger -Once -At (Get-Date "2026-08-10 03:00:00")
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "Dono14 Analise Criativos 10-08" -Action $action -Trigger $trigger -Settings $settings -Description "Atualiza a analise por criativo (A30 em diante) do Dono 14% e regenera o dashboard HTML. Somente leitura na conta Meta e no banco. Criada em 07/08/2026." -Force

Write-Host ""
Write-Host "Tarefa registrada. Execucao unica: 10/08/2026 as 03:00."
Write-Host "WakeToRun acorda o PC se estiver dormindo. StartWhenAvailable roda assim que o PC ligar, caso esteja desligado no horario."
Write-Host "Saida: meus-produtos\dono-14\trafego\analise\criativos-a30-a41-ATUAL.html"
Write-Host "Log:   scripts\criativos-autorun.log"
