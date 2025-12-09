@echo off
echo ========================================
echo Hallmark Scribble - Build Restart Tool
echo ========================================
echo.

echo Step 1: Installing PyInstaller...
python3.11.exe -m pip install pyinstaller psutil --quiet
echo.

echo Step 2: Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "HallmarkScribble_RestartService.exe" del /q "HallmarkScribble_RestartService.exe"
echo.

echo Step 3: Building restart tool executable...
python3.11.exe -m PyInstaller ^
    --name=HallmarkScribble_RestartService ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=psutil ^
    --noconfirm ^
    restart_service.py

echo.

if exist "dist\HallmarkScribble_RestartService.exe" (
    echo Step 4: Moving restart tool to root...
    move "dist\HallmarkScribble_RestartService.exe" "HallmarkScribble_RestartService.exe"
    
    echo Step 5: Cleaning up...
    rmdir /s /q "build"
    rmdir /s /q "dist"
    del /q "HallmarkScribble_RestartService.spec"
    
    echo.
    echo ========================================
    echo Restart Tool Built Successfully!
    echo ========================================
    echo.
    echo File: HallmarkScribble_RestartService.exe
    echo.
    echo Double-click to restart services
    echo ========================================
) else (
    echo ERROR: Build failed
    pause
    exit /b 1
)

pause
