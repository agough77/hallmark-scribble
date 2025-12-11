@echo off
echo ========================================
echo Hallmark Scribble - Build Installer EXE
echo ========================================
echo.

echo Step 1: Installing PyInstaller...
python3.11.exe -m pip install pyinstaller --quiet
echo.

echo Step 2: Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "HallmarkScribble_Installer.exe" del /q "HallmarkScribble_Installer.exe"
echo.

echo Step 3: Building installer executable...
python3.11.exe -m PyInstaller ^
    --name=HallmarkScribble_Installer ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --add-data="web_app\HallmarkScribble_Web;web_app\HallmarkScribble_Web" ^
    --add-data="HallmarkScribble_Updater.exe;." ^
    --add-data="version.json;." ^
    --noconfirm ^
    installer.py

echo.

if exist "dist\HallmarkScribble_Installer.exe" (
    echo Step 4: Moving installer to root...
    move "dist\HallmarkScribble_Installer.exe" "HallmarkScribble_Installer.exe"
    
    echo Step 5: Cleaning up...
    rmdir /s /q "build"
    rmdir /s /q "dist"
    del /q "HallmarkScribble_Installer.spec"
    
    echo.
    echo ========================================
    echo Installer Built Successfully!
    echo ========================================
    echo.
    echo File: HallmarkScribble_Installer.exe
    echo.
    echo To install:
    echo 1. Right-click HallmarkScribble_Installer.exe
    echo 2. Select "Run as administrator"
    echo ========================================
) else (
    echo ERROR: Build failed
    exit /b 1
)
