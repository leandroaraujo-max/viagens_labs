param(
    [string]$Branch = "main",
    [string]$ProjectRoot = "C:\Projetos\viagens_labs",
    [string]$ServiceName = "viagens_labs",
    [ValidateSet("IIS", "Nginx")]
    [string]$WebServer = "IIS",
    [string]$IISSiteName = "",
    [string]$IISAppPool = "",
    [string]$NginxConf = "C:\Projetos\viagens_labs\nginx_config\nginx.conf",
    [string]$HealthUrl = "http://127.0.0.1:8000/openapi.json",
    [switch]$Integration,
    [switch]$SkipBackup,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Assert-PathExists {
    param([string]$PathValue, [string]$Name)
    if (-not (Test-Path $PathValue)) {
        throw "$Name nao encontrado: $PathValue"
    }
}

function Run-Command {
    param(
        [scriptblock]$Command,
        [string]$FailureMessage
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Backup-ItemIfExists {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    if (Test-Path $SourcePath) {
        Copy-Item -Path $SourcePath -Destination $DestinationPath -Recurse -Force
        Write-Host "Backup criado: $SourcePath -> $DestinationPath" -ForegroundColor DarkGray
    }
}

function Invoke-SmokeTest {
    param([string]$Url)

    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 20
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
        throw "Smoke test falhou para $Url (status $($response.StatusCode))."
    }
}

function Restart-WebServer {
    param(
        [string]$ServerKind,
        [string]$SiteName,
        [string]$AppPool,
        [string]$NginxConfig
    )

    if ($ServerKind -eq "IIS") {
        Write-Step "Reciclando IIS"

        $webAdminLoaded = $false
        try {
            Import-Module WebAdministration -ErrorAction Stop
            $webAdminLoaded = $true
        }
        catch {
            Write-Warning "Modulo WebAdministration indisponivel. Tentando reiniciar servico W3SVC."
        }

        if ($webAdminLoaded -and $AppPool) {
            $pool = Get-Item "IIS:\AppPools\$AppPool" -ErrorAction SilentlyContinue
            if ($pool) {
                Restart-WebAppPool -Name $AppPool
            } else {
                throw "App Pool '$AppPool' nao encontrado no IIS."
            }
        }

        if ($webAdminLoaded -and $SiteName) {
            $site = Get-Item "IIS:\Sites\$SiteName" -ErrorAction SilentlyContinue
            if ($site) {
                Stop-Website -Name $SiteName
                Start-Website -Name $SiteName
            } else {
                throw "Site '$SiteName' nao encontrado no IIS."
            }
        }

        if (-not $AppPool -and -not $SiteName) {
            Restart-Service -Name "W3SVC" -Force
            $iisService = Get-Service -Name "W3SVC"
            if ($iisService.Status -ne "Running") {
                throw "Servico W3SVC nao voltou para estado Running."
            }
        }

        return
    }

    Write-Step "Recarregando Nginx"
    $nginxCmd = Get-Command nginx.exe -ErrorAction SilentlyContinue
    if (-not $nginxCmd) {
        throw "nginx.exe nao encontrado no PATH."
    }

    & nginx.exe -s reload
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Reload falhou. Tentando iniciar Nginx com config explicita."
        & nginx.exe -c $NginxConfig
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao recarregar/iniciar Nginx."
        }
    }
}

Push-Location $ProjectRoot

try {
    Write-Step "Validando estrutura do projeto"
    Assert-PathExists -PathValue ".git" -Name "Repositorio Git"
    Assert-PathExists -PathValue ".\venv\Scripts\python.exe" -Name "Python da venv"
    Assert-PathExists -PathValue ".\requirements.txt" -Name "requirements.txt"
    Assert-PathExists -PathValue ".\scripts\qa.ps1" -Name "Script QA"

    $dirty = git status --porcelain
    if ($dirty) {
        throw "Repositorio com alteracoes locais. Commit/stash antes do deploy."
    }

    Write-Step "Sincronizando codigo da branch '$Branch'"
    Run-Command -Command { git fetch --all } -FailureMessage "Falha no git fetch."
    Run-Command -Command { git checkout $Branch } -FailureMessage "Falha no git checkout $Branch."
    Run-Command -Command { git pull --rebase } -FailureMessage "Falha no git pull --rebase."

    if (-not $SkipBackup) {
        Write-Step "Criando backups de seguranca"
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupRoot = Join-Path $ProjectRoot "backup\deploy_$timestamp"
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

        Backup-ItemIfExists -SourcePath ".\.env" -DestinationPath (Join-Path $backupRoot ".env")
        if ($WebServer -eq "Nginx") {
            Backup-ItemIfExists -SourcePath ".\nginx_config\nginx.conf" -DestinationPath (Join-Path $backupRoot "nginx.conf")
        }
        Backup-ItemIfExists -SourcePath ".\uploads" -DestinationPath (Join-Path $backupRoot "uploads")

        $pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
        if ($pgDump) {
            $dbDumpPath = Join-Path $backupRoot "solicitacao_viagens_$timestamp.dump"
            Write-Host "Gerando dump PostgreSQL em: $dbDumpPath" -ForegroundColor DarkGray
            & $pgDump.Source -h 127.0.0.1 -p 5433 -U postgres -d solicitacao_viagens -F c -f $dbDumpPath
            if ($LASTEXITCODE -ne 0) {
                throw "Falha ao executar pg_dump."
            }
        } else {
            Write-Warning "pg_dump nao encontrado no PATH. Dump do banco foi ignorado."
        }
    }

    Write-Step "Atualizando dependencias Python"
    Run-Command -Command { .\venv\Scripts\python.exe -m pip install -r .\requirements.txt } -FailureMessage "Falha ao instalar dependencias Python."

    Write-Step "Executando QA"
    if ($Integration) {
        Run-Command -Command { .\scripts\qa.ps1 -Integration } -FailureMessage "QA (com integracao) falhou."
    } else {
        Run-Command -Command { .\scripts\qa.ps1 } -FailureMessage "QA padrao falhou."
    }

    if (-not $SkipFrontendBuild -and (Test-Path ".\frontend\package.json")) {
        Write-Step "Buildando frontend"
        Push-Location .\frontend
        try {
            Run-Command -Command { npm ci } -FailureMessage "Falha no npm ci."
            Run-Command -Command { npm run build } -FailureMessage "Falha no npm run build."
        }
        finally {
            Pop-Location
        }
    }

    Write-Step "Reiniciando backend"
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Restart-Service -Name $ServiceName -Force
        $service = Get-Service -Name $ServiceName
        if ($service.Status -ne "Running") {
            throw "Servico '$ServiceName' nao subiu corretamente."
        }
    } else {
        throw "Servico '$ServiceName' nao encontrado. Configure o servico antes do deploy automatizado."
    }

    Restart-WebServer -ServerKind $WebServer -SiteName $IISSiteName -AppPool $IISAppPool -NginxConfig $NginxConf

    Write-Step "Executando smoke test"
    Invoke-SmokeTest -Url $HealthUrl

    Write-Host "`nDEPLOY FINALIZADO COM SUCESSO ✅" -ForegroundColor Green
}
catch {
    Write-Host "`nDEPLOY FALHOU ❌" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
