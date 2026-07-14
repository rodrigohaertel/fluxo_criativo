$origem = "$env:USERPROFILE\Downloads"
$destino = "C:\Users\rodri\OneDrive\Documentos\fluxo-criativo\meus-produtos\dono-14\entregas\conteudo-social\carrossel-sempre"

$count = 0
1..6 | ForEach-Object {
    $nome = "carrossel-sempre-{0:D2}.png" -f $_
    $src = Join-Path $origem $nome
    $dst = Join-Path $destino $nome
    if (Test-Path $src) {
        Move-Item $src $dst -Force
        $count++
        Write-Host "Movido: $nome"
    } else {
        Write-Host "Nao encontrado: $nome"
    }
}
Write-Host ""
Write-Host "$count de 6 imagens movidas para a pasta carrossel-sempre."
Start-Sleep -Seconds 3
