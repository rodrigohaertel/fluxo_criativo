$origem = "$env:USERPROFILE\Downloads"
$destino = "C:\Users\rodri\OneDrive\Documentos\fluxo-criativo\meus-produtos\dono-14\entregas\conteudo-social\carrossel-nunca"

# Criar pasta de destino se não existir
if (-not (Test-Path $destino)) {
    New-Item -ItemType Directory -Path $destino -Force | Out-Null
}

# Mover os 6 arquivos do carrossel
$arquivos = Get-ChildItem "$origem\carrosel-nunca-v2-*.png" -ErrorAction SilentlyContinue
if ($arquivos.Count -eq 0) {
    Write-Host "Nenhum arquivo carrosel-nunca-v2-*.png encontrado em $origem"
} else {
    foreach ($f in $arquivos) {
        Move-Item $f.FullName "$destino\$($f.Name)" -Force
        Write-Host "Movido: $($f.Name)"
    }
    Write-Host "Concluido! $($arquivos.Count) arquivos movidos para $destino"
}
Read-Host "Pressione Enter para fechar"
