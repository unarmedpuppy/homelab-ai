# Windows Auto-Start Setup for Local AI

This guide shows you how to automatically start your local AI system when Windows boots up.

## Option 1: Windows Task Scheduler (Recommended)

### 1. Create Startup Script

First, create a startup script that will run when Windows starts:

```batch
@echo off
REM Local AI Auto-Start Script
REM This script starts Docker Desktop, waits for it to be ready, then starts the local AI manager

echo Starting Local AI System...

REM Wait for Docker Desktop to start (adjust path if needed)
timeout /t 30 /nobreak >nul

REM Navigate to the local-ai directory
cd /d "C:\Users\%USERNAME%\repos\home-server\local-ai"

REM Start the manager service
docker compose up -d

echo Local AI Manager started successfully!
echo Manager is running on port 8000
echo Available models: llama3-8b, qwen2.5-14b-awq, deepseek-coder, qwen-image-edit
```

Save this as `start-local-ai.bat` in your `local-ai` directory.

### 2. Create Task Scheduler Entry

1. **Open Task Scheduler:**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task:**
   - Click "Create Basic Task..." in the right panel
   - Name: "Local AI Auto-Start"
   - Description: "Automatically start local AI manager on Windows boot"

3. **Set Trigger:**
   - Select "When the computer starts"
   - Click Next

4. **Set Action:**
   - Select "Start a program"
   - Program/script: Browse to your `start-local-ai.bat` file
   - Start in: `C:\Users\%USERNAME%\repos\home-server\local-ai`

5. **Configure Advanced Settings:**
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"
   - Check "Hidden" (optional)

6. **Finish:**
   - Click Finish
   - Enter your Windows password when prompted

## Option 2: Docker Desktop Auto-Start + Startup Folder

### 1. Enable Docker Desktop Auto-Start

1. Open Docker Desktop
2. Go to Settings → General
3. Check "Start Docker Desktop when you log in"
4. Apply & Restart

### 2. Create Startup Script for Manager

Create a PowerShell script for more robust startup:

```powershell
# Local AI Manager Auto-Start Script
# Save as: start-local-ai-manager.ps1

Write-Host "Starting Local AI Manager..." -ForegroundColor Green

# Wait for Docker to be ready
$maxAttempts = 30
$attempt = 0

do {
    try {
        docker version | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        Write-Host "Waiting for Docker... (attempt $($attempt + 1)/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        $attempt++
    }
} while ($attempt -lt $maxAttempts)

if ($attempt -eq $maxAttempts) {
    Write-Host "Docker failed to start within timeout period" -ForegroundColor Red
    exit 1
}

# Navigate to local-ai directory
Set-Location "C:\Users\$env:USERNAME\repos\home-server\local-ai"

# Start the manager service
Write-Host "Starting Local AI Manager service..." -ForegroundColor Green
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "Local AI Manager started successfully!" -ForegroundColor Green
    Write-Host "Manager is running on port 8000" -ForegroundColor Cyan
    Write-Host "Available models: llama3-8b, qwen2.5-14b-awq, deepseek-coder, qwen-image-edit" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start Local AI Manager" -ForegroundColor Red
    exit 1
}
```

### 3. Add to Startup Folder

1. Press `Win + R`, type `shell:startup`, press Enter
2. Copy your PowerShell script to this folder
3. Create a shortcut to `powershell.exe` with arguments:
   ```
   -ExecutionPolicy Bypass -File "C:\Users\%USERNAME%\repos\home-server\local-ai\start-local-ai-manager.ps1"
   ```

## Option 3: Windows Service (Advanced)

For the most robust solution, create a Windows service:

### 1. Install NSSM (Non-Sucking Service Manager)

1. Download NSSM from: https://nssm.cc/download
2. Extract to `C:\nssm`
3. Add `C:\nssm\win64` to your PATH

### 2. Create Service

```batch
REM Run as Administrator
nssm install "LocalAIManager" "C:\Users\%USERNAME%\repos\home-server\local-ai\start-local-ai-manager.ps1"
nssm set "LocalAIManager" AppParameters "-ExecutionPolicy Bypass -File"
nssm set "LocalAIManager" AppDirectory "C:\Users\%USERNAME%\repos\home-server\local-ai"
nssm set "LocalAIManager" DisplayName "Local AI Manager"
nssm set "LocalAIManager" Description "Automatically starts the Local AI Manager service"
nssm set "LocalAIManager" Start SERVICE_AUTO_START
nssm start "LocalAIManager"
```

## Option 4: Registry Auto-Start (Simple)

### 1. Create Registry Entry

1. Press `Win + R`, type `regedit`, press Enter
2. Navigate to: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
3. Right-click → New → String Value
4. Name: `LocalAIManager`
5. Value: `"C:\Users\%USERNAME%\repos\home-server\local-ai\start-local-ai.bat"`

## Recommended Setup

**For most users, I recommend Option 1 (Task Scheduler)** because it:
- ✅ Runs even when not logged in
- ✅ Has proper error handling
- ✅ Can be easily managed
- ✅ Works reliably

## Testing Your Setup

1. **Test the script manually:**
   ```batch
   cd C:\Users\%USERNAME%\repos\home-server\local-ai
   start-local-ai.bat
   ```

2. **Test auto-start:**
   - Restart your computer
   - Check if the manager is running: `docker ps`
   - Test the API: `curl http://localhost:8000/healthz`

3. **Monitor logs:**
   ```batch
   docker logs vllm-manager
   ```

## Troubleshooting

### Common Issues:

1. **Docker not ready:**
   - Increase the timeout in the startup script
   - Ensure Docker Desktop is set to auto-start

2. **Permission issues:**
   - Run Task Scheduler as Administrator
   - Check "Run with highest privileges"

3. **Path issues:**
   - Use absolute paths in scripts
   - Verify the local-ai directory exists

4. **Network issues:**
   - Ensure Windows firewall allows Docker
   - Check if port 8000 is available

### Monitoring Commands:

```batch
REM Check if manager is running
docker ps | findstr vllm-manager

REM Check manager logs
docker logs vllm-manager

REM Test API endpoint
curl http://localhost:8000/healthz

REM Check model status
curl http://localhost:8000/v1/models
```

## Security Considerations

- The manager service runs with Docker socket access
- Consider firewall rules to restrict access to port 8000
- Monitor logs for any unauthorized access attempts
- Keep Docker Desktop updated for security patches

Choose the option that best fits your needs and technical comfort level!
