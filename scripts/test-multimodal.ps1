# Test script for multimodal inference support
# Tests both text and image models

Write-Host "=== Multimodal Inference Test Suite ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$errors = 0

# Test 1: Manager health
Write-Host "Test 1: Manager Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/healthz" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $health = $response.Content | ConvertFrom-Json
        Write-Host "  [OK] Manager is healthy" -ForegroundColor Green
        Write-Host "  Running models: $($health.running -join ', ')" -ForegroundColor Cyan
    } else {
        Write-Host "  [FAIL] Manager returned status $($response.StatusCode)" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  [FAIL] Cannot connect to manager: $_" -ForegroundColor Red
    $errors++
    exit 1
}

# Test 2: List models
Write-Host ""
Write-Host "Test 2: List Available Models" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/v1/models" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $models = $response.Content | ConvertFrom-Json
        $modelIds = $models.data | ForEach-Object { $_.id }
        Write-Host "  [OK] Found $($modelIds.Count) models" -ForegroundColor Green
        Write-Host "  Models: $($modelIds -join ', ')" -ForegroundColor Cyan
        
        # Check for image model
        $hasImageModel = $modelIds | Where-Object { $_ -like "*image*" }
        if ($hasImageModel) {
            Write-Host "  [OK] Image model found: $hasImageModel" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] No image model found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [FAIL] Failed to list models" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  [FAIL] Error listing models: $_" -ForegroundColor Red
    $errors++
}

# Test 3: Text model (quick test)
Write-Host ""
Write-Host "Test 3: Text Model Generation" -ForegroundColor Yellow
$textModel = "qwen2.5-14b-awq"
try {
    $body = @{
        model = $textModel
        messages = @(@{ role = "user"; content = "Say 'test successful' if you can read this." })
        max_tokens = 50
    } | ConvertTo-Json
    
    Write-Host "  Testing model: $textModel" -ForegroundColor Cyan
    $response = Invoke-WebRequest -Uri "$baseUrl/v1/chat/completions" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing `
        -TimeoutSec 60
    
    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        $content = $result.choices[0].message.content
        Write-Host "  [OK] Text model responded" -ForegroundColor Green
        Write-Host "  Response: $($content.Substring(0, [Math]::Min(100, $content.Length)))..." -ForegroundColor Cyan
    } else {
        Write-Host "  [FAIL] Text model returned status $($response.StatusCode)" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  [FAIL] Text model test failed: $_" -ForegroundColor Red
    Write-Host "  Note: This may fail if model is still loading (first request)" -ForegroundColor Yellow
    $errors++
}

# Test 4: Image model container check
Write-Host ""
Write-Host "Test 4: Image Model Container" -ForegroundColor Yellow
$imageContainer = docker ps -a --filter "name=qwen-image-server" --format "{{.Names}}"
if ($imageContainer -eq "qwen-image-server") {
    Write-Host "  [OK] Image model container exists" -ForegroundColor Green
    $status = docker inspect --format='{{.State.Status}}' qwen-image-server
    Write-Host "  Container status: $status" -ForegroundColor Cyan
} else {
    Write-Host "  [WARN] Image model container not found" -ForegroundColor Yellow
    Write-Host "  Run: ./build-image-server.sh and update setup.sh" -ForegroundColor Yellow
}

# Test 5: Image model endpoint (if container exists)
if ($imageContainer -eq "qwen-image-server") {
    Write-Host ""
    Write-Host "Test 5: Image Model Endpoint" -ForegroundColor Yellow
    Write-Host "  Note: Image generation test skipped (requires model to be loaded)" -ForegroundColor Yellow
    Write-Host "  To test manually, use the web UI or API with /v1/images/generations" -ForegroundColor Cyan
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "[OK] All tests passed!" -ForegroundColor Green
} else {
    Write-Host "[FAIL] $errors test(s) failed" -ForegroundColor Red
}
Write-Host ""
Write-Host "For full testing, see: local-ai/TESTING.md" -ForegroundColor Cyan

