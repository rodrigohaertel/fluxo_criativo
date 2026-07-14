# Script: mover-carrossel-sempre-v2.ps1
# Move e renomeia os 6 slides do carrossel da pasta Downloads para o destino final

$downloads = "$env:USERPROFILE\Downloads"
$destino   = "C:\Users\rodri\OneDrive\Documentos\fluxo-criativo\meus-produtos\dono-14\entregas\conteudo-social\carrossel-sempre"

# Pega os 6 arquivos de imagem mais recentes no Downloads (webp ou png)
$arquivos = Get-ChildItem -Path $downloads -Include "*.webp","*.png" -File |
            Sort-Object LastWriteTime |
            Select-Object -Last 6

if ($arquivos.Count -ne 6) {
    Write-Host "AVISO: encontrei $($arquivos.Count) arquivo(s) de imagem recente(s) — esperava 6."
    Write-Host "Arquivos encontrados:"
    $arquivos | ForEach-Object { Write-Host "  $($_.Name)  ($($_.LastWriteTime))" }
    exit 1
}

Write-Host "Movendo e renomeando 6 slides para:`n  $destino`n"

for ($i = 0; $i -lt 6; $i++) {
    $origem = $arquivos[$i].FullName
    $novo   = Join-Path $destino "carrosel-sempre-v2-$($i+1).png"
    Copy-Item -Path $origem -Destination $novo -Force
    Write-Host "  Slide $($i+1): $($arquivos[$i].Name) -> carrosel-sempre-v2-$($i+1).png"
}

Write-Host "`nConcluído. 6 slides salvos em:`n  $destino"
