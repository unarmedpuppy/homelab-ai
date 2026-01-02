@echo off
REM Local AI Auto-Start Setup Script
REM This script helps you set up automatic startup for your Local AI system

echo ========================================
echo    Local AI Auto-Start Setup
echo ========================================
echo.

echo Choose your preferred auto-start method:
echo.
echo 1. Task Scheduler (Recommended - runs even when not logged in)
echo 2. Startup Folder (Simple - runs when you log in)
echo 3. Registry Entry (Simple - runs when you log in)
echo 4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto task_scheduler
if "%choice%"=="2" goto startup_folder
if "%choice%"=="3" goto registry_entry
if "%choice%"=="4" goto exit
goto invalid_choice

:task_scheduler
echo.
echo Setting up Task Scheduler auto-start...
echo.
echo Please follow these steps:
echo 1. Press Win + R, type 'taskschd.msc', press Enter
echo 2. Click "Create Basic Task..."
echo 3. Name: "Local AI Auto-Start"
echo 4. Description: "Automatically start local AI manager on Windows boot"
echo 5. Trigger: "When the computer starts"
echo 6. Action: "Start a program"
echo 7. Program: "%cd%\start-local-ai.bat"
echo 8. Start in: "%cd%"
echo 9. Check "Run whether user is logged on or not"
echo 10. Check "Run with highest privileges"
echo.
echo The script file is ready at: %cd%\start-local-ai.bat
goto end

:startup_folder
echo.
echo Setting up Startup Folder auto-start...
echo.
echo Opening Startup Folder...
start shell:startup
echo.
echo Please copy the following files to the Startup Folder:
echo - %cd%\start-local-ai.bat
echo.
echo Or create a shortcut to PowerShell with these arguments:
echo -ExecutionPolicy Bypass -File "%cd%\start-local-ai-manager.ps1"
goto end

:registry_entry
echo.
echo Setting up Registry auto-start...
echo.
echo WARNING: This will modify your Windows Registry!
echo Press any key to continue or Ctrl+C to cancel...
pause >nul
echo.
echo Adding registry entry...
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "LocalAIManager" /t REG_SZ /d "\"%cd%\start-local-ai.bat\"" /f
if %errorlevel% equ 0 (
    echo ✅ Registry entry added successfully!
    echo Local AI will now start automatically when you log in.
) else (
    echo ❌ Failed to add registry entry. Please run as Administrator.
)
goto end

:invalid_choice
echo.
echo Invalid choice. Please run the script again and choose 1-4.
goto end

:exit
echo.
echo Setup cancelled.
goto end

:end
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Test your setup:
echo 1. Restart your computer
echo 2. Check if manager is running: docker ps
echo 3. Test API: curl http://localhost:8000/healthz
echo.
echo Troubleshooting:
echo - Ensure Docker Desktop is set to auto-start
echo - Check Windows Firewall allows Docker
echo - Monitor logs: docker logs vllm-manager
echo.
pause
