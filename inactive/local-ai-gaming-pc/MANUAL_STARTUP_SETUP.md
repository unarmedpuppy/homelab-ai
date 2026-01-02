# Manual Startup Setup (No Admin Required)

If you can't run PowerShell as Administrator, here are simple alternatives:

## Method 1: Startup Folder (Easiest - No Admin)

**Run this script:**
```powershell
.\setup-startup-simple.ps1
```

This creates a shortcut in your Windows Startup folder. The services will start automatically when you log in.

**To remove:**
```powershell
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Local AI Startup.lnk"
```

## Method 2: Manual Startup Folder Setup

1. Press `Win + R`
2. Type: `shell:startup`
3. Press Enter (opens your Startup folder)
4. Create a shortcut:
   - Right-click in the folder → New → Shortcut
   - Target: `powershell.exe`
   - Arguments: `-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\micro\repos\home-server\local-ai\start-all.ps1"`
   - Name: `Local AI Startup`

## Method 3: Registry (No Admin for Current User)

1. Press `Win + R`
2. Type: `regedit`
3. Navigate to: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
4. Right-click → New → String Value
5. Name: `LocalAIStartup`
6. Value: `powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\micro\repos\home-server\local-ai\start-all.ps1"`

## Method 4: Task Scheduler (GUI - May Prompt for Admin)

1. Press `Win + R`, type `taskschd.msc`, press Enter
2. Click "Create Basic Task..." (right panel)
3. Name: `Local AI Startup`
4. Description: `Starts Local AI on login`
5. Trigger: `When I log on`
6. Action: `Start a program`
7. Program: `powershell.exe`
8. Arguments: `-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\micro\repos\home-server\local-ai\start-all.ps1"`
9. Start in: `C:\Users\micro\repos\home-server\local-ai`
10. Click Finish

**Note:** If it asks for admin, you can choose "Run only when user is logged on" which doesn't require admin.

## Method 5: Docker Desktop Auto-Start Only

If you just want Docker to start automatically:

1. Open Docker Desktop
2. Settings → General
3. Check "Start Docker Desktop when you log in"
4. Then manually run `docker compose up -d` when needed

Or create a simple batch file in Startup folder:
```batch
@echo off
cd /d C:\Users\micro\repos\home-server\local-ai
docker compose up -d
```

## Recommended: Method 1 (Startup Folder)

The simplest approach is Method 1 - just run:
```powershell
.\setup-startup-simple.ps1
```

This works without admin privileges and will start everything when you log in.

## Testing

After setup, test it:

1. **Test manually:**
   ```powershell
   .\start-all.ps1
   ```

2. **Check if services started:**
   ```powershell
   docker ps
   ```

3. **Test the dashboard:**
   - Open: http://localhost:8080

4. **Test auto-start:**
   - Log out and log back in
   - Check if services are running

## Troubleshooting

### Services Don't Start

Check the startup log:
```powershell
cat local-ai/startup.log
```

### Docker Not Ready

Make sure Docker Desktop is set to auto-start:
- Docker Desktop → Settings → General → "Start Docker Desktop when you log in"

### PowerShell Execution Policy

If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## See Also

- [AUTO_START.md](AUTO_START.md) - Full auto-start guide (with admin methods)
- [README.md](README.md) - Main documentation

