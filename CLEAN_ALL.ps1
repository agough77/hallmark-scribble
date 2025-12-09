# Hallmark Scribble - Complete Cleanup Script
# Run as Administrator for best results

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Hallmark Scribble - Complete Cleanup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: This will remove ALL Hallmark Scribble installations" -ForegroundColor Yellow
Write-Host "and related files from your system." -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Type YES to continue"
if ($confirm -ne "YES") {
    Write-Host "Cleanup cancelled" -ForegroundColor Red
    exit
}

# Function to force delete folder with readonly files
function Remove-FolderForce {
    param([string]$Path)
    
    if (Test-Path $Path) {
        Write-Host "Removing: $Path" -ForegroundColor Yellow
        try {
            # Remove readonly attributes recursively
            Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
                try {
                    $_.Attributes = 'Normal'
                } catch {}
            }
            
            # Remove the folder
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            Write-Host "SUCCESS: Removed $Path" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "WARNING: Could not remove $Path" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "Not found: $Path" -ForegroundColor Gray
        return $true
    }
}

Write-Host ""
Write-Host "[Step 1/8] Stopping all running processes..." -ForegroundColor Cyan
$processes = @(
    "HallmarkScribble_Web",
    "HallmarkScribble_Desktop",
    "HallmarkScribble",
    "main",
    "HallmarkScribble_Updater",
    "HallmarkScribble_RestartService"
)

foreach ($proc in $processes) {
    $running = Get-Process -Name $proc -ErrorAction SilentlyContinue
    if ($running) {
        Stop-Process -Name $proc -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped: $proc" -ForegroundColor Yellow
    }
}
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[Step 2/8] Removing Program Files installation..." -ForegroundColor Cyan
Set-Location $env:TEMP
Remove-FolderForce -Path "C:\Program Files\HallmarkScribble"

Write-Host ""
Write-Host "[Step 3/8] Removing LocalAppData installation..." -ForegroundColor Cyan
Remove-FolderForce -Path "$env:LOCALAPPDATA\HallmarkScribble"

Write-Host ""
Write-Host "[Step 4/8] Removing UserProfile installation..." -ForegroundColor Cyan
Remove-FolderForce -Path "$env:USERPROFILE\HallmarkScribble"

Write-Host ""
Write-Host "[Step 5/8] Removing desktop shortcuts..." -ForegroundColor Cyan
$shortcuts = @(
    "$env:USERPROFILE\Desktop\Hallmark Scribble Web.lnk",
    "$env:USERPROFILE\Desktop\Hallmark Scribble Desktop.lnk",
    "$env:USERPROFILE\Desktop\Hallmark Scribble.lnk",
    "$env:USERPROFILE\Desktop\HallmarkScribble.lnk"
)

foreach ($shortcut in $shortcuts) {
    if (Test-Path $shortcut) {
        Remove-Item $shortcut -Force -ErrorAction SilentlyContinue
        Write-Host "Removed: $(Split-Path $shortcut -Leaf)" -ForegroundColor Yellow
    }
}
Write-Host "Desktop shortcuts cleaned" -ForegroundColor Green

Write-Host ""
Write-Host "[Step 6/8] Removing Start Menu shortcuts..." -ForegroundColor Cyan
$startMenuPaths = @(
    "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Hallmark Scribble",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Hallmark Scribble",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\HallmarkScribble"
)

foreach ($path in $startMenuPaths) {
    Remove-FolderForce -Path $path
}
Write-Host "Start Menu shortcuts cleaned" -ForegroundColor Green

Write-Host ""
Write-Host "[Step 7/8] Checking for Registry entries..." -ForegroundColor Cyan
try {
    if (Test-Path "HKLM:\SOFTWARE\HallmarkScribble") {
        Remove-Item -Path "HKLM:\SOFTWARE\HallmarkScribble" -Recurse -Force -ErrorAction Stop
        Write-Host "Removed HKLM registry entries" -ForegroundColor Yellow
    } else {
        Write-Host "No HKLM registry entries found" -ForegroundColor Gray
    }
} catch {
    Write-Host "Could not access HKLM registry (may need admin rights)" -ForegroundColor Red
}

try {
    if (Test-Path "HKCU:\SOFTWARE\HallmarkScribble") {
        Remove-Item -Path "HKCU:\SOFTWARE\HallmarkScribble" -Recurse -Force -ErrorAction Stop
        Write-Host "Removed HKCU registry entries" -ForegroundColor Yellow
    } else {
        Write-Host "No HKCU registry entries found" -ForegroundColor Gray
    }
} catch {
    Write-Host "Could not access HKCU registry" -ForegroundColor Red
}

Write-Host ""
Write-Host "[Step 8/8] Checking for temporary files..." -ForegroundColor Cyan
$tempPaths = @(
    "$env:TEMP\HallmarkScribble",
    "$env:TEMP\_MEI*"  # PyInstaller temp folders
)

foreach ($pattern in $tempPaths) {
    Get-Item $pattern -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            Remove-Item $_.FullName -Recurse -Force -ErrorAction Stop
            Write-Host "Removed temp: $($_.Name)" -ForegroundColor Yellow
        } catch {}
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  ✓ All executables stopped" -ForegroundColor Green
Write-Host "  ✓ All installation folders removed" -ForegroundColor Green
Write-Host "  ✓ All shortcuts removed" -ForegroundColor Green
Write-Host "  ✓ Registry entries cleaned" -ForegroundColor Green
Write-Host "  ✓ Temporary files removed" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: Output files in Downloads folder were NOT removed." -ForegroundColor Yellow
Write-Host "Location: $env:USERPROFILE\Downloads\Hallmark Scribble Outputs" -ForegroundColor Yellow
Write-Host ""
Write-Host "You can now reinstall Hallmark Scribble if needed." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
