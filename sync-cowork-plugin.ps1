<#
.SYNOPSIS
  Ressincroniza o plugin do Cowork e publica no fork.

.DESCRIPTION
  1. Roda sync-cowork-plugin.py (recopia skills/commands/agents/rules/scripts da fonte,
     limpa lixo, reaplica rewrite de caminhos e conserta frontmatter).
  2. Valida o plugin (se o claude CLI estiver disponivel).
  3. Faz git add + commit das mudancas do plugin.
  4. Faz push para o remote fork (main), a menos que -NoPush seja passado.

.EXAMPLE
  ./sync-cowork-plugin.ps1
  ./sync-cowork-plugin.ps1 -NoPush      # so sincroniza e commita, sem enviar pro GitHub
  ./sync-cowork-plugin.ps1 -Message "atualiza skills de trafego"
#>
param(
  [switch]$NoPush,
  [string]$Message = "chore: ressincroniza plugin do Cowork"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 1. Detecta o comando Python (py -3 ou python3)
$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) { $py = @("py", "-3") }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $py = @("python3") }
else { throw "Python nao encontrado (py -3 ou python3)." }

Write-Host "==> Ressincronizando arquivos do plugin..." -ForegroundColor Cyan
& $py[0] $py[1..($py.Length-1)] "sync-cowork-plugin.py"
if ($LASTEXITCODE -ne 0) { throw "Falha no sync-cowork-plugin.py" }

# 2. Validacao opcional
if (Get-Command claude -ErrorAction SilentlyContinue) {
  Write-Host "==> Validando o plugin..." -ForegroundColor Cyan
  try { claude plugin validate plugins/fluxo-criativo/.claude-plugin/plugin.json } catch {
    Write-Warning "Validacao retornou avisos/erros (veja acima)."
  }
}

# 3. Commit
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
git add plugins/fluxo-criativo .claude-plugin/marketplace.json
$pending = git diff --cached --name-only
if (-not $pending) {
  Write-Host "Nada mudou no plugin. Nada para commitar." -ForegroundColor Yellow
  return
}
Write-Host "==> Commitando ($(( $pending | Measure-Object -Line).Lines) arquivos)..." -ForegroundColor Cyan
git commit -q -m $Message

# 4. Push para o fork
if ($NoPush) {
  Write-Host "Commit feito. Push pulado (-NoPush). Rode 'git push fork main' quando quiser." -ForegroundColor Yellow
  return
}
if (-not (git remote | Select-String -Pattern "^fork$")) {
  Write-Warning "Remote 'fork' nao existe. Crie com: git remote add fork https://github.com/rodrigohaertel/fluxo_criativo.git"
  return
}
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
Write-Host "==> Enviando para o fork (main)..." -ForegroundColor Cyan
git push fork main
Write-Host "Pronto. No Cowork, sincronize o marketplace para puxar a versao nova." -ForegroundColor Green
