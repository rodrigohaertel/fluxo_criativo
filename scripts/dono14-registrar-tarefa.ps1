# Registra a tarefa agendada da leitura diaria do Dono 14% (02h, todos os dias).
# Rodar uma unica vez. Para remover depois: Unregister-ScheduledTask -TaskName "Dono14 Leitura Diaria 02h"
$action   = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo\scripts\dono14-autorun.cmd"'
$trigger  = New-ScheduledTaskTrigger -Daily -At 2:00AM
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 45)
Register-ScheduledTask -TaskName "Dono14 Leitura Diaria 02h" -Action $action -Trigger $trigger -Settings $settings -Description "Leitura diaria automatica do funil Dono 14% via Claude Code (somente leitura na conta Meta). Criada em 28/07/2026." -Force
Write-Host ""
Write-Host "Tarefa registrada. Proxima execucao: amanha as 02:00."
Write-Host "WakeToRun: acorda o PC se estiver dormindo. StartWhenAvailable: se o PC estiver desligado as 04h, roda assim que ligar."
