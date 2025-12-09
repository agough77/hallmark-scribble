@echo off
echo ========================================
echo Hallmark Scribble - Complete Cleanup
echo ========================================
echo.
echo WARNING: This will remove ALL Hallmark Scribble installations
echo and related files from your system.
echo.
pause

echo.
echo [Step 1/8] Stopping all running processes...
taskkill /F /IM HallmarkScribble_Web.exe 2>nul
taskkill /F /IM HallmarkScribble_Desktop.exe 2>nul
taskkill /F /IM HallmarkScribble.exe 2>nul
taskkill /F /IM main.exe 2>nul
taskkill /F /IM HallmarkScribble_Updater.exe 2>nul
taskkill /F /IM HallmarkScribble_RestartService.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [Step 2/8] Removing Program Files installation...
cd /d "%TEMP%"
if exist "C:\Program Files\HallmarkScribble\" (
    rmdir /S /Q "C:\Program Files\HallmarkScribble" 2>nul
    if exist "C:\Program Files\HallmarkScribble\" (
        echo WARNING: Could not remove "C:\Program Files\HallmarkScribble"
        echo Please manually delete this folder after closing all applications
    ) else (
        echo SUCCESS: Removed Program Files installation
    )
) else (
    echo No Program Files installation found
)

echo.
echo [Step 3/8] Removing LocalAppData installation...
if exist "%LOCALAPPDATA%\HallmarkScribble\" (
    rmdir /S /Q "%LOCALAPPDATA%\HallmarkScribble" 2>nul
    if exist "%LOCALAPPDATA%\HallmarkScribble\" (
        echo WARNING: Could not remove LocalAppData installation
    ) else (
        echo SUCCESS: Removed LocalAppData installation
    )
) else (
    echo No LocalAppData installation found
)

echo.
echo [Step 4/8] Removing UserProfile installation...
if exist "%USERPROFILE%\HallmarkScribble\" (
    rmdir /S /Q "%USERPROFILE%\HallmarkScribble" 2>nul
    if exist "%USERPROFILE%\HallmarkScribble\" (
        echo WARNING: Could not remove UserProfile installation
    ) else (
        echo SUCCESS: Removed UserProfile installation
    )
) else (
    echo No UserProfile installation found
)

echo.
echo [Step 5/8] Removing desktop shortcuts...
del "%USERPROFILE%\Desktop\Hallmark Scribble Web.lnk" 2>nul
del "%USERPROFILE%\Desktop\Hallmark Scribble Desktop.lnk" 2>nul
del "%USERPROFILE%\Desktop\Hallmark Scribble.lnk" 2>nul
del "%USERPROFILE%\Desktop\HallmarkScribble.lnk" 2>nul
echo Desktop shortcuts removed

echo.
echo [Step 6/8] Removing Start Menu shortcuts...
if exist "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Hallmark Scribble\" (
    rmdir /S /Q "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Hallmark Scribble" 2>nul
    echo Removed ProgramData Start Menu folder
)

if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Hallmark Scribble\" (
    rmdir /S /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Hallmark Scribble" 2>nul
    echo Removed AppData Start Menu folder
)

if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\HallmarkScribble\" (
    rmdir /S /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\HallmarkScribble" 2>nul
    echo Removed AppData Start Menu folder (no space)
)

echo Start Menu shortcuts removed

echo.
echo [Step 7/8] Checking for Registry entries...
echo Note: Registry cleanup requires administrator privileges
reg query "HKLM\SOFTWARE\HallmarkScribble" >nul 2>&1
if %errorlevel% equ 0 (
    reg delete "HKLM\SOFTWARE\HallmarkScribble" /f >nul 2>&1
    echo Removed HKLM registry entries
) else (
    echo No HKLM registry entries found
)

reg query "HKCU\SOFTWARE\HallmarkScribble" >nul 2>&1
if %errorlevel% equ 0 (
    reg delete "HKCU\SOFTWARE\HallmarkScribble" /f >nul 2>&1
    echo Removed HKCU registry entries
) else (
    echo No HKCU registry entries found
)

echo.
echo [Step 8/8] Cleanup complete!
echo.
echo ========================================
echo Summary:
echo - All executables stopped
echo - All installation folders removed
echo - All shortcuts removed
echo - Registry entries cleaned
echo ========================================
echo.
echo NOTE: Output files in Downloads folder were NOT removed.
echo Location: %USERPROFILE%\Downloads\Hallmark Scribble Outputs
echo.
pause
