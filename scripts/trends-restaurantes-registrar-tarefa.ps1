# Registra a tarefa agendada dos trends do mercado de bares e restaurantes (07h, todos os dias).
# Rodar uma unica vez. Para remover depois: Unregister-ScheduledTask -TaskName "Trends Restaurantes 07h"
$action   = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "C:\Users\rodri\OneDrive\Documentos\Claude\Projects\fluxo-criativo\scripts\trends-restaurantes-autorun.cmd"'
$trigger  = New-ScheduledTaskTrigger -Daily -At 7:00AM
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 45)
Register-ScheduledTask -TaskName "Trends Restaurantes 07h" -Action $action -Trigger $trigger -Settings $settings -Description "Os 3 topicos do dia no mercado de bares e restaurantes (Apify + Google Noticias + curadoria do Claude). Criada em 06/11/2026." -Force
Write-Host ""
Write-Host "Tarefa registrada. Proxima execucao: amanha as 07:00, com o arquivo pronto antes das 08:00."
Write-Host "WakeToRun: acorda o PC se estiver dormindo. StartWhenAvailable: se o PC estiver desligado as 07h, roda assim que ligar."
