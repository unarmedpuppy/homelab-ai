# Local AI Setup Verification Script
# This script verifies your local AI setup is working correctly

Write-Host "[*] Verifying Local AI Setup..." -ForegroundColor Cyan
Write-Host ""

# 1. Check Docker is running
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
try {
    $null = docker version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Docker is running" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# 2. Check manager container
Write-Host "2. Checking manager container..." -ForegroundColor Yellow
$manager = docker ps --filter "name=vllm-manager" --format "{{.Names}}"
if ($manager -eq "vllm-manager") {
        Write-Host "   [OK] Manager container is running" -ForegroundColor Green
} else {
        Write-Host "   [FAIL] Manager container is not running" -ForegroundColor Red
    Write-Host "   Run: docker compose up -d" -ForegroundColor Yellow
    exit 1
}

# 3. Check manager health
Write-Host "3. Checking manager health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $health = $response.Content | ConvertFrom-Json
        Write-Host "   [OK] Manager is healthy" -ForegroundColor Green
        Write-Host "   Running models: $($health.running -join ', ')" -ForegroundColor Cyan
    }
} catch {
        Write-Host "   [FAIL] Manager health check failed: $_" -ForegroundColor Red
    exit 1
}

# 4. Check model containers exist
Write-Host "4. Checking model containers..." -ForegroundColor Yellow
$models = @("vllm-llama3-8b", "vllm-qwen14b-awq", "vllm-coder7b", "vllm-qwen-image")
$allExist = $true
foreach ($model in $models) {
    $container = docker ps -a --filter "name=$model" --format "{{.Names}}"
    if ($container -eq $model) {
        Write-Host "   [OK] $model exists" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] $model not found" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host "   Run: ./setup.sh to create missing containers" -ForegroundColor Yellow
}

# 5. Check Windows IP
Write-Host "5. Checking Windows IP..." -ForegroundColor Yellow
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.86.*" }).IPAddress
if ($ip) {
    Write-Host "   [OK] Windows IP: $ip" -ForegroundColor Green
    Write-Host "   Make sure this matches WINDOWS_AI_HOST in apps/local-ai-app/docker-compose.yml" -ForegroundColor Cyan
} else {
    Write-Host "   [WARN] Could not find 192.168.86.x IP address" -ForegroundColor Yellow
}

# 6. Check firewall rule
Write-Host "6. Checking firewall rule..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "*LLM*" -ErrorAction SilentlyContinue
if ($firewallRule) {
    Write-Host "   [OK] Firewall rule exists" -ForegroundColor Green
} else {
    Write-Host "   [WARN] No firewall rule found for port 8000" -ForegroundColor Yellow
    Write-Host "   You may need to allow port 8000 from your server IP" -ForegroundColor Yellow
    Write-Host "   Run: New-NetFirewallRule -DisplayName 'LLM Manager 8000' -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow" -ForegroundColor Cyan
}

# 7. Test port accessibility
Write-Host "7. Testing port 8000 accessibility..." -ForegroundColor Yellow
try {
    $test = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue
    if ($test.TcpTestSucceeded) {
        Write-Host "   [OK] Port 8000 is accessible locally" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Port 8000 is not accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "   [WARN] Could not test port accessibility" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[OK] Setup verification complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. If server-side proxy is not running, deploy it:" -ForegroundColor White
Write-Host "   cd apps/local-ai-app" -ForegroundColor Gray
Write-Host "   docker compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test the API:" -ForegroundColor White
Write-Host "   curl http://localhost:8000/v1/models" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access the web interface at local-ai.server.unarmedpuppy.com" -ForegroundColor White

