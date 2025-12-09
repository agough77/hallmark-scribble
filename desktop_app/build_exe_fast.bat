@echo off
REM ========================================
REM Hallmark Scribble - Fast EXE Builder
REM ========================================
REM This builds a folder-based distribution
REM which starts much faster than single-file
REM ========================================

echo ========================================
echo Hallmark Scribble - Fast Build
echo ========================================
echo.

REM Step 1: Install PyInstaller
echo Step 1: Installing PyInstaller...
python3.11.exe -m pip install pyinstaller --quiet
echo.

REM Step 2: Clean previous builds
echo Step 2: Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "HallmarkScribble_Desktop" rmdir /s /q "HallmarkScribble_Desktop"
echo.

REM Step 3: Build in folder mode (FAST)
echo Step 3: Building executable in FOLDER mode (faster startup)...
python3.11.exe -m PyInstaller ^
    --name=HallmarkScribble_Desktop ^
    --windowed ^
    --add-data="..\shared;shared" ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=pyautogui ^
    --hidden-import=keyboard ^
    --hidden-import=pynput ^
    --hidden-import=google.generativeai ^
    --hidden-import=psutil ^
    --hidden-import=win32api ^
    --collect-all=PyQt5 ^
    --noconfirm ^
    main.py

echo.

REM Step 4: Rename dist folder
echo Step 4: Organizing distribution folder...
if exist "dist\HallmarkScribble_Desktop" (
    move "dist\HallmarkScribble_Desktop" "HallmarkScribble_Desktop"
    rmdir "dist"
    echo SUCCESS! Created HallmarkScribble_Desktop folder
) else (
    echo ERROR: Build folder not found
)
echo.

REM Step 5: Cleanup
echo Step 5: Cleaning up build files...
if exist "build" rmdir /s /q "build"
if exist "HallmarkScribble_Desktop.spec" del /q "HallmarkScribble_Desktop.spec"
echo.

echo ========================================
echo Build complete!
echo ========================================
echo.
echo Folder: HallmarkScribble_Desktop\
echo Run: HallmarkScribble_Desktop\HallmarkScribble_Desktop.exe
echo.
echo This folder mode starts MUCH FASTER than single-file!
echo Share the entire folder (not just the EXE).
echo ========================================
pause
