@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Hallmark Scribble - Installation
echo ========================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This installer requires administrator privileges.
    echo Please right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

:: Set installation directory
set "INSTALL_DIR=%ProgramFiles%\HallmarkScribble"
echo Installing to: %INSTALL_DIR%
echo.

:: Create installation directory
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo Created installation directory
)

:: Copy web app
echo Copying Web Application...
if exist "web_app\HallmarkScribble_Web" (
    xcopy /E /I /Y "web_app\HallmarkScribble_Web" "%INSTALL_DIR%\Web" >nul
    echo - Web app copied
) else (
    echo ERROR: Web app build not found. Please run build_exe_web.bat first.
    pause
    exit /b 1
)

:: Copy desktop app
echo Copying Desktop Application...
if exist "desktop_app\dist\HallmarkScribble_Desktop" (
    xcopy /E /I /Y "desktop_app\dist\HallmarkScribble_Desktop" "%INSTALL_DIR%\Desktop" >nul
    echo - Desktop app copied
) else (
    echo WARNING: Desktop app build not found. Skipping.
)

:: Copy shared folder
echo Copying Shared Resources...
xcopy /E /I /Y "shared" "%INSTALL_DIR%\shared" >nul
echo - Shared resources copied

:: Create shortcuts on desktop
echo Creating Desktop Shortcuts...
set "DESKTOP=%USERPROFILE%\Desktop"

:: Web app shortcut
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Hallmark Scribble Web.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Web\HallmarkScribble_Web.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%\Web'; $Shortcut.Description = 'Hallmark Scribble Web Application'; $Shortcut.Save()"
echo - Web app shortcut created

:: Desktop app shortcut
if exist "%INSTALL_DIR%\Desktop\HallmarkScribble_Desktop.exe" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Hallmark Scribble Desktop.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Desktop\HallmarkScribble_Desktop.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%\Desktop'; $Shortcut.Description = 'Hallmark Scribble Desktop Application'; $Shortcut.Save()"
    echo - Desktop app shortcut created
)

:: Create Start Menu shortcuts
echo Creating Start Menu Shortcuts...
set "STARTMENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs\Hallmark Scribble"
if not exist "%STARTMENU%" mkdir "%STARTMENU%"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU%\Hallmark Scribble Web.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Web\HallmarkScribble_Web.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%\Web'; $Shortcut.Save()"

if exist "%INSTALL_DIR%\Desktop\HallmarkScribble_Desktop.exe" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU%\Hallmark Scribble Desktop.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Desktop\HallmarkScribble_Desktop.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%\Desktop'; $Shortcut.Save()"
)

:: Create uninstaller
echo Creating Uninstaller...
(
echo @echo off
echo echo Uninstalling Hallmark Scribble...
echo rmdir /S /Q "%INSTALL_DIR%"
echo del "%DESKTOP%\Hallmark Scribble Web.lnk" 2^>nul
echo del "%DESKTOP%\Hallmark Scribble Desktop.lnk" 2^>nul
echo rmdir /S /Q "%STARTMENU%"
echo echo Hallmark Scribble has been uninstalled.
echo pause
) > "%INSTALL_DIR%\Uninstall.bat"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTMENU%\Uninstall Hallmark Scribble.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Uninstall.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Installed to: %INSTALL_DIR%
echo Desktop shortcuts created
echo Start Menu shortcuts created
echo.
echo To uninstall, run: %INSTALL_DIR%\Uninstall.bat
echo or use the Start Menu shortcut
echo.
pause
