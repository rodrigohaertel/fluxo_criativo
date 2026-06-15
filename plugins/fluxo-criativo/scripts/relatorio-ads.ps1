# Relatorio Diario Meta Ads
# Gerado automaticamente pelo Workshop Marketing IA
# Roda todo dia via Task Scheduler do Windows ou CronCreate do Claude

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ProjectRoot ".env"
$LogFile = Join-Path $ScriptDir "relatorio-ads.log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $linha = "$ts - $msg"
    Write-Host $linha
    Add-Content -Path $LogFile -Value $linha -Encoding UTF8
}

function Load-DotEnv($path) {
    $config = @{}
    if (-not (Test-Path $path)) {
        return $config
    }

    Get-Content -Path $path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $parts = $line.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($key) {
            $config[$key] = $value
        }
    }
    return $config
}

function Get-Config($name, $config, $default = "") {
    $fromEnv = [Environment]::GetEnvironmentVariable($name)
    if ($fromEnv) {
        return $fromEnv
    }
    if ($config.ContainsKey($name) -and $config[$name]) {
        return $config[$name]
    }
    return $default
}

function Redact-Secrets($text) {
    if (-not $text) {
        return ""
    }

    $safe = "$text"
    $safe = $safe -replace '(access_token=)[^&\s]+', '$1[removido]'
    $safe = $safe -replace '(token/)[^/\s]+', '$1[removido]'
    $safe = $safe -replace '(bot)[0-9]+:[A-Za-z0-9_-]+', '$1[removido]'
    $safe = $safe -replace '(Client-Token["'':=\s]+)[A-Za-z0-9_-]+', '$1[removido]'
    $safe = $safe -replace '(Bearer\s+)[A-Za-z0-9._-]+', '$1[removido]'
    return $safe
}

$Config = Load-DotEnv $EnvFile

# --- Credenciais Facebook ---
$FB_ACCESS_TOKEN_PERMANENTE = Get-Config "FB_ACCESS_TOKEN_PERMANENTE" $Config
$FB_ACCESS_TOKEN_TEMPORARIO = Get-Config "FB_ACCESS_TOKEN_TEMPORARIO" $Config
$FB_AD_ACCOUNT_ID           = Get-Config "FB_AD_ACCOUNT_ID" $Config

# Prioriza token permanente
if ($FB_ACCESS_TOKEN_PERMANENTE -and $FB_ACCESS_TOKEN_PERMANENTE -ne "") {
    $FB_ACCESS_TOKEN = $FB_ACCESS_TOKEN_PERMANENTE
} elseif ($FB_ACCESS_TOKEN_TEMPORARIO -and $FB_ACCESS_TOKEN_TEMPORARIO -ne "") {
    $FB_ACCESS_TOKEN = $FB_ACCESS_TOKEN_TEMPORARIO
} else {
    Log "ERRO: Nenhum token encontrado. Configure FB_ACCESS_TOKEN_PERMANENTE ou FB_ACCESS_TOKEN_TEMPORARIO no .env."
    exit 1
}

if (-not $FB_AD_ACCOUNT_ID) {
    Log "ERRO: FB_AD_ACCOUNT_ID nao encontrado. Configure no .env."
    exit 1
}

# --- Canal de envio ---
$RELATORIO_CANAL = (Get-Config "RELATORIO_CANAL" $Config "TELEGRAM").ToUpperInvariant()

# --- Credenciais Telegram (usado se RELATORIO_CANAL = TELEGRAM) ---
$TELEGRAM_BOT_TOKEN = Get-Config "TELEGRAM_BOT_TOKEN" $Config
$TELEGRAM_CHAT_ID   = Get-Config "TELEGRAM_CHAT_ID" $Config

# --- Credenciais Z-API / WhatsApp (usado se RELATORIO_CANAL = WHATSAPP) ---
$ZAPI_INSTANCE_ID   = Get-Config "ZAPI_INSTANCE_ID" $Config
$ZAPI_TOKEN         = Get-Config "ZAPI_TOKEN" $Config
$ZAPI_CLIENT_TOKEN  = Get-Config "ZAPI_CLIENT_TOKEN" $Config
$WHATSAPP_NUMERO    = Get-Config "RELATORIO_WHATSAPP_NUMERO" $Config

Log "=== Iniciando relatorio Meta Ads ==="

# --- Data de ontem ---
$ontem    = (Get-Date).AddDays(-1)
$ontemISO = $ontem.ToString("yyyy-MM-dd")
$ontemBR  = $ontem.ToString("dd/MM/yyyy")
Log "Data: $ontemBR"

# --- Buscar metricas ---
$timeRange = "{`"since`":`"$ontemISO`",`"until`":`"$ontemISO`"}"
$fields    = "spend,impressions,reach,clicks,ctr,cpm,cpc,actions,cost_per_action_type"
$urlFB     = "https://graph.facebook.com/v25.0/act_$($FB_AD_ACCOUNT_ID)/insights?time_range=$([uri]::EscapeDataString($timeRange))&fields=$fields&level=account"
$headersFB = @{ "Authorization" = "Bearer $FB_ACCESS_TOKEN" }

try {
    Log "Buscando metricas no Facebook Ads..."
    $resp  = Invoke-RestMethod -Uri $urlFB -Method GET -Headers $headersFB -TimeoutSec 30
    $dados = $resp.data
} catch {
    Log "ERRO ao buscar metricas: $(Redact-Secrets $_)"
    exit 1
}

# --- Montar mensagem ---
function FmtBRL($v) {
    try { return "R$ " + ([double]$v).ToString("N2", [System.Globalization.CultureInfo]::GetCultureInfo("pt-BR")) }
    catch { return "R$ $v" }
}
function FmtNum($v) {
    try { return ([long][double]$v).ToString("N0", [System.Globalization.CultureInfo]::GetCultureInfo("pt-BR")) }
    catch { return "$v" }
}

if (-not $dados -or $dados.Count -eq 0) {
    $mensagem = "*Relatorio Meta Ads - $ontemBR*`n`nSem dados para ontem. Verifique se ha campanhas ativas."
    Log "Sem dados para ontem."
} else {
    $d = $dados[0]

    $linhas = @()
    $linhas += "*Relatorio Meta Ads - $ontemBR*"
    $linhas += ""
    $linhas += "*Investimento e Alcance*"
    $linhas += "Gasto: $(FmtBRL $d.spend)"
    $linhas += "Alcance: $(FmtNum $d.reach)"
    $linhas += "Impressoes: $(FmtNum $d.impressions)"
    $linhas += ""
    $linhas += "*Engajamento*"
    $linhas += "Cliques: $(FmtNum $d.clicks)"
    $linhas += "CTR: $([double]$d.ctr -replace '\.',',')%"
    $linhas += "CPM: $(FmtBRL $d.cpm)"
    $linhas += "CPC: $(FmtBRL $d.cpc)"

    $conv = $d.actions | Where-Object { $_.action_type -in @("purchase","lead") } | Select-Object -First 1
    if ($conv) {
        $cpa = ($d.cost_per_action_type | Where-Object { $_.action_type -eq $conv.action_type } | Select-Object -First 1).value
        $linhas += ""
        $linhas += "*Conversoes*"
        $linhas += "Resultados: $(FmtNum $conv.value)"
        $linhas += "Custo por resultado: $(FmtBRL $cpa)"
    }

    $mensagem = $linhas -join "`n"
}

Log "Mensagem montada."

# --- Enviar ---
if ($RELATORIO_CANAL -eq "TELEGRAM") {
    if (-not $TELEGRAM_BOT_TOKEN -or -not $TELEGRAM_CHAT_ID) {
        Log "ERRO: Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env."
        exit 1
    }

    $urlTelegram     = "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage"
    $payloadTelegram = @{
        chat_id    = $TELEGRAM_CHAT_ID
        text       = $mensagem
        parse_mode = "Markdown"
    } | ConvertTo-Json
    try {
        Log "Enviando via Telegram..."
        $resultado = Invoke-RestMethod -Uri $urlTelegram -Method POST -ContentType "application/json" -Body $payloadTelegram -TimeoutSec 30
        Log "=== Relatorio enviado com sucesso ==="
    } catch {
        Log "ERRO ao enviar Telegram: $(Redact-Secrets $_)"
        exit 1
    }
} else {
    if (-not $ZAPI_INSTANCE_ID -or -not $ZAPI_TOKEN -or -not $ZAPI_CLIENT_TOKEN -or -not $WHATSAPP_NUMERO) {
        Log "ERRO: Configure ZAPI_INSTANCE_ID, ZAPI_TOKEN, ZAPI_CLIENT_TOKEN e RELATORIO_WHATSAPP_NUMERO no .env."
        exit 1
    }

    $urlZapi  = "https://api.z-api.io/instances/$ZAPI_INSTANCE_ID/token/$ZAPI_TOKEN/send-text"
    $headers  = @{ "Content-Type" = "application/json"; "Client-Token" = $ZAPI_CLIENT_TOKEN }
    $payload  = @{ phone = $WHATSAPP_NUMERO; message = $mensagem } | ConvertTo-Json
    try {
        Log "Enviando via Z-API..."
        $resultado = Invoke-RestMethod -Uri $urlZapi -Method POST -Headers $headers -Body $payload -TimeoutSec 30
        Log "Z-API resposta: $($resultado | ConvertTo-Json -Compress)"
        Log "=== Relatorio enviado com sucesso ==="
    } catch {
        Log "ERRO ao enviar Z-API: $(Redact-Secrets $_)"
        exit 1
    }
}
