# Atualizacao automatica do Fluxo Criativo (Tarefa Agendada do Windows)
# Roda toda segunda-feira. Faz somente a parte segura:
# busca a atualizacao, guarda alteracoes locais, aplica o pull rapido.
# Se houver divergencia ou conflito, NAO mexe: anota no log e deixa
# para o usuario rodar o /atualizar-projeto manualmente.

$ErrorActionPreference = 'Continue'

# Detecta a raiz do projeto a partir da propria localizacao do script
# (scripts\atualizar-segunda.ps1), assim funciona em qualquer caminho.
$proj = Split-Path -Parent $PSScriptRoot
$log  = Join-Path $proj 'scripts\log-atualizacao-automatica.txt'

function Escrever-Log($msg) {
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $log -Value "[$stamp] $msg" -Encoding utf8
}

Set-Location $proj

try {
    git fetch origin 2>&1 | Out-Null

    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    $behind = [int](git rev-list --count "HEAD..origin/$branch")
    $ahead  = [int](git rev-list --count "origin/$branch..HEAD")

    if ($behind -eq 0) {
        Escrever-Log "Projeto ja estava atualizado (branch $branch)."
        exit 0
    }

    if ($ahead -gt 0) {
        Escrever-Log "Versoes divergiram (branch $branch): $ahead commits locais e $behind remotos. Nao atualizei por seguranca. Rode /atualizar-projeto manualmente."
        exit 0
    }

    # Guardar alteracoes locais, se houver
    $sujo = git status --porcelain
    $guardou = $false
    if ($sujo) {
        git stash push -u -m "auto-stash-pre-update-segunda" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $guardou = $true
        } else {
            Escrever-Log "Nao consegui guardar suas alteracoes locais. Nao atualizei. Rode /atualizar-projeto manualmente."
            exit 0
        }
    }

    # Aplicar atualizacao (somente avanco rapido, nunca merge ou rebase)
    git pull --ff-only 2>&1 | Out-Null
    $pullOk = ($LASTEXITCODE -eq 0)

    # Devolver alteracoes locais guardadas
    if ($guardou) {
        git stash pop 2>&1 | Out-Null
        $conflitos = git diff --name-only --diff-filter=U
        if ($conflitos) {
            Escrever-Log "Atualizacao baixada, mas houve conflito ao devolver suas alteracoes. Suas alteracoes continuam guardadas em seguranca. Rode /atualizar-projeto comigo para conciliar."
            exit 0
        }
    }

    if ($pullOk) {
        Escrever-Log "Projeto atualizado com sucesso (branch $branch, $behind novidade(s))."
    } else {
        Escrever-Log "Nao foi possivel aplicar a atualizacao automaticamente. Rode /atualizar-projeto manualmente."
    }
}
catch {
    Escrever-Log "Erro durante a atualizacao automatica: $($_.Exception.Message)"
}
