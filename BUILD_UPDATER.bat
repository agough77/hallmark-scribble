@echo off
echo ========================================
echo Hallmark Scribble - Build Updater EXE
echo ========================================
echo.

echo Step 1: Installing PyInstaller...
python3.11.exe -m pip install pyinstaller --quiet
echo.

echo Step 2: Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "HallmarkScribble_Updater.exe" del /q "HallmarkScribble_Updater.exe"
echo.

echo Step 3: Building updater executable...
python3.11.exe -m PyInstaller ^
    --name=HallmarkScribble_Updater ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --icon=NONE ^
    --add-data="version.json;." ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --noconfirm ^
    updater.py

echo.

if exist "dist\HallmarkScribble_Updater.exe" (
    echo Step 4: Moving updater to root...
    move "dist\HallmarkScribble_Updater.exe" "HallmarkScribble_Updater.exe"
    
    echo Step 5: Cleaning up...
    rmdir /s /q "build"
    rmdir /s /q "dist"
    del /q "HallmarkScribble_Updater.spec"
    
    echo.
    echo ========================================
    echo Updater Built Successfully!
    echo ========================================
    echo.
    echo File: HallmarkScribble_Updater.exe
    echo.
    echo Double-click to check for updates
    echo ========================================
) else (
    echo ERROR: Build failed
    exit /b 1
)
