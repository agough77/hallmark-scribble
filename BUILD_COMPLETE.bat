@echo off
REM ========================================
REM Hallmark Scribble - Complete Build Script
REM Builds: Web App, Updater, Installer
REM ========================================

echo.
echo ========================================
echo Hallmark Scribble - Complete Build
echo ========================================
echo.

REM Step 1: Build Web Application
echo Step 1/3: Building Web Application...
echo ----------------------------------------
cd "%~dp0web_app"
call build_exe_web.bat
if errorlevel 1 (
    echo ERROR: Web app build failed!
    exit /b 1
)
cd "%~dp0"
echo.

REM Step 2: Build Updater
echo Step 2/3: Building Updater...
echo ----------------------------------------
call BUILD_UPDATER.bat
if errorlevel 1 (
    echo ERROR: Updater build failed!
    exit /b 1
)
echo.

REM Step 3: Build Installer
echo Step 3/3: Building Installer...
echo ----------------------------------------
call BUILD_INSTALLER.bat
if errorlevel 1 (
    echo ERROR: Installer build failed!
    exit /b 1
)
echo.

REM Display final results
echo.
echo ========================================
echo BUILD COMPLETE - All Components Built!
echo ========================================
echo.
echo Created files:
echo   - web_app\dist\HallmarkScribble_Web\
echo   - HallmarkScribble_Updater.exe
echo   - HallmarkScribble_Installer.exe
echo.
if exist "HallmarkScribble_Installer.exe" (
    echo Installer size:
    for %%F in (HallmarkScribble_Installer.exe) do echo   %%~zF bytes ^(%%~fF^)
    echo.
)
echo ========================================
echo Ready to distribute: HallmarkScribble_Installer.exe
echo ========================================
echo.
