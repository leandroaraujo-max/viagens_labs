# ============================================================
# Test-Conectividade.ps1
# Rodar em OUTRA máquina da rede para diagnosticar acesso
# ao servidor Viagens Labs (10.6.2.40)
# ============================================================

$servidor = "10.6.2.40"
$hostname = "viagenslabs.magazineluiza.intranet"

Write-Host "`n=== DIAGNÓSTICO DE ACESSO AO VIAGENS LABS ===" -ForegroundColor Cyan
Write-Host "Servidor: $servidor | Hostname: $hostname"
Write-Host "Máquina cliente: $env:COMPUTERNAME ($env:USERDOMAIN)" 
Write-Host ""

# 1. Ping (ICMP)
Write-Host "--- [1] Ping (ICMP) ---" -ForegroundColor Yellow
$ping = Test-Connection -ComputerName $servidor -Count 2 -Quiet
if ($ping) { Write-Host "PING: OK — servidor alcançável na rede" -ForegroundColor Green }
else       { Write-Host "PING: FALHOU — verifique rotas/VLAN" -ForegroundColor Red }

# 2. Porta 80 TCP
Write-Host ""
Write-Host "--- [2] Porta 80 (HTTP / Nginx) ---" -ForegroundColor Yellow
$tcp80 = Test-NetConnection -ComputerName $servidor -Port 80 -WarningAction SilentlyContinue
if ($tcp80.TcpTestSucceeded) { 
    Write-Host "PORTA 80: ABERTA — nginx acessível" -ForegroundColor Green 
} else {
    Write-Host "PORTA 80: BLOQUEADA — firewall de rede está bloqueando HTTP" -ForegroundColor Red
    Write-Host "  → Acione a equipe de infraestrutura/redes para liberar porta 80 para $servidor" -ForegroundColor Yellow
}

# 3. Porta 8000 TCP
Write-Host ""
Write-Host "--- [3] Porta 8000 (FastAPI) ---" -ForegroundColor Yellow
$tcp8k = Test-NetConnection -ComputerName $servidor -Port 8000 -WarningAction SilentlyContinue
if ($tcp8k.TcpTestSucceeded) {
    Write-Host "PORTA 8000: ABERTA" -ForegroundColor Green
} else {
    Write-Host "PORTA 8000: BLOQUEADA" -ForegroundColor Red
}

# 4. DNS
Write-Host ""
Write-Host "--- [4] Resolução DNS do hostname ---" -ForegroundColor Yellow
try {
    $dns = [System.Net.Dns]::GetHostAddresses($hostname)
    $dns | ForEach-Object { Write-Host "DNS: $hostname → $($_.IPAddressToString)" -ForegroundColor Green }
    if ($dns.IPAddressToString -notcontains $servidor) {
        Write-Host "ATENÇÃO: DNS resolve para IP diferente de $servidor!" -ForegroundColor Red
    }
} catch {
    Write-Host "DNS ERRO: não resolveu $hostname — verifique o registro no AD" -ForegroundColor Red
}

# 5. HTTP real
Write-Host ""
Write-Host "--- [5] Requisição HTTP ---" -ForegroundColor Yellow
if ($tcp80.TcpTestSucceeded) {
    try {
        $r = Invoke-WebRequest -Uri "http://$hostname/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "HTTP: $($r.StatusCode) $($r.StatusDescription) — sistema acessível!" -ForegroundColor Green
    } catch {
        Write-Host "HTTP ERRO: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "HTTP: pulado (porta 80 bloqueada)" -ForegroundColor Gray
}

# 6. Traceroute (mostra onde está bloqueando)
Write-Host ""
Write-Host "--- [6] Traceroute (mostra onde o tráfego é bloqueado) ---" -ForegroundColor Yellow
tracert -d -h 10 $servidor 2>&1 | Select-Object -First 15

Write-Host ""
Write-Host "=== FIM DO DIAGNÓSTICO ===" -ForegroundColor Cyan
Write-Host "Copie e envie o resultado para o responsável pela infraestrutura." -ForegroundColor White
