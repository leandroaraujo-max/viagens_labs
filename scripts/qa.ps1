param(
    [switch]$Integration
)

$ErrorActionPreference = "Stop"
$python = ".\venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Python da venv nao encontrado em .\\venv\\Scripts\\python.exe"
}

Write-Host "[QA] Rodando testes padrao (pytest)..." -ForegroundColor Cyan
& $python -m pytest tests -m "not integration"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($Integration) {
    Write-Host "[QA] Rodando testes de integracao (PostgreSQL)..." -ForegroundColor Cyan
    & $python -m pytest tests -m integration
    exit $LASTEXITCODE
}

Write-Host "[QA] Concluido com sucesso." -ForegroundColor Green
