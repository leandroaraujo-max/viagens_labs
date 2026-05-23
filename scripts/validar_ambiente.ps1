Clear-Host
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  VALIDAÇÃO DE AMBIENTE - SISTEMA DE VIAGENS (INTRANET)  " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "Servidor: $env:COMPUTERNAME | Usuário: $env:USERNAME" -ForegroundColor Gray
Write-Host ""

$AllPassed = $true

# 1. Validando Versão do Windows Server
Write-Host "[1/6] Verificando Versão do Sistema Operacional..." -NoNewline
$OS = Get-CimInstance Win32_OperatingSystem
if ($OS.Caption -like "*Windows Server 2022*") {
    Write-Host " [OK] ($($OS.Caption))" -ForegroundColor Green
} else {
    Write-Host " [ATENÇÃO] ($($OS.Caption)) - O ideal planejado é Windows Server 2022." -ForegroundColor Yellow
}

# 2. Verificando se o WSL está habilitado
Write-Host "[2/6] Verificando Recurso do WSL..." -NoNewline
$wslCheck = Get-WindowsFeature | Where-Object {$_.Name -eq "Microsoft-Windows-Subsystem-Linux"}
if ($wslCheck -and $wslCheck.Installed) {
    Write-Host " [OK] (Instalado e ativo)" -ForegroundColor Green
} else {
    # Verifica alternativamente via comando wsl
    $wslCmd = Get-Command wsl -ErrorAction SilentlyContinue
    if ($wslCmd) {
        Write-Host " [OK] (Comando wsl encontrado no PATH)" -ForegroundColor Green
    } else {
        Write-Host " [FALHA] WSL não detectado. Ative o recurso do WSL 2 para melhor performance do Docker." -ForegroundColor Red
        $AllPassed = $false
    }
}

# 3. Verificando Docker
Write-Host "[3/6] Verificando Docker Engine..." -NoNewline
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    try {
        $dockerVer = & docker --version
        # Testa se o daemon do docker está respondendo
        $daemonActive = & docker ps 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK] ($dockerVer - Rodando)" -ForegroundColor Green
        } else {
            Write-Host " [ERRO] Docker instalado, mas o serviço/daemon NÃO está rodando!" -ForegroundColor Red
            $AllPassed = $false
        }
    } catch {
        Write-Host " [ERRO] Falha ao comunicar com o Docker." -ForegroundColor Red
        $AllPassed = $false
    }
} else {
    Write-Host " [FALHA] Docker não está instalado ou não foi adicionado ao PATH do sistema." -ForegroundColor Red
    $AllPassed = $false
}

# 4. Verificando Docker Compose
Write-Host "[4/6] Verificando Docker Compose..." -NoNewline
$composeCmd = Get-Command docker-compose -ErrorAction SilentlyContinue
if ($composeCmd) {
    $composeVer = & docker-compose --version
    Write-Host " [OK] ($composeVer)" -ForegroundColor Green
} else {
    # Tenta rodar como subcomando do docker v2: "docker compose"
    $v2Check = & docker compose version 2>$null
    if ($LASTEXITCODE -eq 0) {
         Write-Host " [OK] (Docker Compose V2 ativo via comando 'docker compose')" -ForegroundColor Green
    } else {
         Write-Host " [FALHA] Docker Compose não encontrado." -ForegroundColor Red
         $AllPassed = $false
    }
}

# 5. Verificando Instalação do Python (Dev / Scripting)
Write-Host "[5/6] Verificando interpretador Python..." -NoNewline
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pyVer = & python --version 2>&1
    Write-Host " [OK] ($pyVer)" -ForegroundColor Green
} else {
    Write-Host " [AVISO] Python local não detectado no host (Opcional se rodar tudo 100% isolado no contêiner)." -ForegroundColor Yellow
}

# 6. Verificando Portas Críticas (FastAPI: 8000 | PostgreSQL: 5432)
Write-Host "[6/6] Checando portas de rede críticas no Host..." -NoNewline
$Ports = @(8000, 5432)
$PortConflict = $false
foreach ($Port in $Ports) {
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "`n       [CONFLITO] A porta $Port já está sendo utilizada pelo processo ID $($connection.OwningProcess[0])!" -ForegroundColor Red
        $PortConflict = $true
        $AllPassed = $false
    }
}
if (-not $PortConflict) {
    Write-Host " [OK] (Portas 8000 e 5432 estão totalmente livres)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
if ($AllPassed) {
    Write-Host " RESULTADO: Ambiente preparado com sucesso para o deploy! " -BackgroundColor Green -ForegroundColor Black
} else {
    Write-Host " RESULTADO: Ajustes necessários antes de subir os containers. " -BackgroundColor Yellow -ForegroundColor Black
}
Write-Host "=========================================================" -ForegroundColor Cyan
