@echo off
echo ========================================
echo Hallmark Scribble - Build All
echo ========================================
echo.

echo Step 1: Building Web Application...
cd web_app
call build_exe_web.bat
if %errorlevel% neq 0 (
    echo ERROR: Web app build failed
    pause
    exit /b 1
)
cd ..

echo.
echo Step 2: Building Desktop Application...
cd desktop_app
call build_exe_fast.bat
if %errorlevel% neq 0 (
    echo ERROR: Desktop app build failed
    pause
    exit /b 1
)
cd ..

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Both applications have been built successfully.
echo Run INSTALL.bat (as administrator) to install.
echo.
pause
