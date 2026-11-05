# Registra a tarefa agendada da leitura diaria do perfil do Instagram (03h, todos os dias).
# Rodar uma unica vez. Para remover depois: Unregister-ScheduledTask -TaskName "Instagram Perfil Leitura Diaria 03h"
$action   = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo\scripts\instagram-perfil-autorun.cmd"'
$trigger  = New-ScheduledTaskTrigger -Daily -At 3:00AM
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName "Instagram Perfil Leitura Diaria 03h" -Action $action -Trigger $trigger -Settings $settings -Description "Leitura diaria do perfil @rodrigohaertel pela Graph API (somente leitura). Criada em 04/11/2026." -Force
Write-Host ""
Write-Host "Tarefa registrada. Proxima execucao: amanha as 03:00."
Write-Host "WakeToRun: acorda o PC se estiver dormindo. StartWhenAvailable: se o PC estiver desligado as 03h, roda assim que ligar."
