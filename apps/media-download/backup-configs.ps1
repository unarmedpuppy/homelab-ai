# Backup all configuration files for Windows
# Usage: .\backup-configs.ps1

$ErrorActionPreference = "Stop"

$BackupDir = "..\backups\media-download"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupFile = "media-download-backup-$Timestamp.tar.gz"

Write-Host "💾 Creating backup..." -ForegroundColor Cyan
Write-Host ""

# Create backup directory
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# Create compressed backup of all config directories
Write-Host "📦 Compressing configuration files..." -ForegroundColor Yellow

$configDirs = @(
    "nzbhydra2\config",
    "jackett\config",
    "nzbget\config",
    "qbittorrent\config",
    "sonarr\config",
    "radarr\config",
    "lidarr\config",
    "bazarr\config",
    "wireguard\config"
)

# Use tar via docker or native Windows tar
if (Get-Command tar -ErrorAction SilentlyContinue) {
    $tarArgs = "-czf"
    foreach ($dir in $configDirs) {
        if (Test-Path $dir) {
            $tarArgs += " $dir"
        }
    }
    
    # Create archive name and run tar
    $archivePath = Join-Path $BackupDir $BackupFile
    tar -czf $archivePath $tarArgs
    
    Write-Host "✅ Backup created: $archivePath" -ForegroundColor Green
} else {
    Write-Host "⚠️  tar command not found" -ForegroundColor Yellow
    Write-Host "Using 7-Zip or zip instead..." -ForegroundColor Yellow
    
    # Alternative: use Compress-Archive if available
    $backupPath = Join-Path $BackupDir $BackupFile.Replace(".tar.gz", ".zip")
    Compress-Archive -Path $configDirs -DestinationPath $backupPath -Force
    Write-Host "✅ Backup created: $backupPath" -ForegroundColor Green
}

$backupSize = Get-ChildItem $BackupDir | Where-Object { $_.Name -like "*$Timestamp*" } | Select-Object -First 1
if ($backupSize) {
    Write-Host ""
    Write-Host "📊 Backup size: $([math]::Round($backupSize.Length / 1MB, 2)) MB" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📝 To restore:" -ForegroundColor Yellow
Write-Host "   tar -xzf $BackupDir\$BackupFile" -ForegroundColor Gray
Write-Host ""
Write-Host "🗑️  To list existing backups:" -ForegroundColor Yellow
Write-Host "   Get-ChildItem $BackupDir" -ForegroundColor Gray
Write-Host ""

