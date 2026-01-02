@echo off
REM Local AI Auto-Start Script
REM This script starts Docker Desktop, waits for it to be ready, then starts the local AI manager

echo Starting Local AI System...

REM Wait for Docker Desktop to start (adjust path if needed)
echo Waiting for Docker Desktop to be ready...
timeout /t 30 /nobreak >nul

REM Navigate to the local-ai directory
cd /d "%~dp0"

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Docker is ready! Starting Local AI Manager...

REM Start the manager service
docker compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ Local AI Manager started successfully!
    echo 🌐 Manager is running on port 8000
    echo 🤖 Available models: llama3-8b, qwen2.5-14b-awq, deepseek-coder, qwen-image-edit
    echo.
    echo Test with: curl http://localhost:8000/healthz
) else (
    echo ❌ Failed to start Local AI Manager
    echo Check Docker Desktop is running and try again
)

echo.
echo Press any key to close...
pause >nul
