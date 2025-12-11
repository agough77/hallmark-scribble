@echo off
REM ========================================
REM Hallmark Scribble Web - EXE Builder
REM ========================================
REM This builds the Flask web application
REM ========================================

echo ========================================
echo Hallmark Scribble Web - Build
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
if exist "HallmarkScribble_Web" rmdir /s /q "HallmarkScribble_Web"
echo.

REM Step 3: Build in folder mode
echo Step 3: Building executable in FOLDER mode...
python3.11.exe -m PyInstaller ^
    --name=HallmarkScribble_Web ^
    --noconsole ^
    --windowed ^
    --add-data="../shared;shared" ^
    --add-data="templates;templates" ^
    --hidden-import=flask ^
    --hidden-import=flask_cors ^
    --hidden-import=flask.__main__ ^
    --hidden-import=flask.views ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=pyautogui ^
    --hidden-import=keyboard ^
    --hidden-import=pynput ^
    --hidden-import=pynput.mouse ^
    --hidden-import=pynput.keyboard ^
    --hidden-import=google.generativeai ^
    --hidden-import=psutil ^
    --hidden-import=win32api ^
    --hidden-import=werkzeug ^
    --hidden-import=jinja2 ^
    --hidden-import=markupsafe ^
    --hidden-import=edge_tts ^
    --hidden-import=gtts ^
    --hidden-import=mss ^
    --collect-all=flask ^
    --collect-all=flask_cors ^
    --collect-all=pynput ^
    --collect-all=edge_tts ^
    --collect-all=gtts ^
    --noconfirm ^
    web_app.py

echo.

REM Step 4: Rename dist folder
echo Step 4: Organizing distribution folder...
if exist "dist\HallmarkScribble_Web" (
    move "dist\HallmarkScribble_Web" "HallmarkScribble_Web"
    rmdir "dist"
    echo SUCCESS! Created HallmarkScribble_Web folder
) else (
    echo ERROR: Build folder not found
    exit /b 1
)
echo.

REM Step 5: Cleanup
echo Step 5: Cleaning up build files...
if exist "build" rmdir /s /q "build"
if exist "HallmarkScribble_Web.spec" del /q "HallmarkScribble_Web.spec"
echo.

echo ========================================
echo Build complete!
echo ========================================
echo.
echo Folder: HallmarkScribble_Web\
echo Run: HallmarkScribble_Web\HallmarkScribble_Web.exe
echo.
echo This will start the Flask web server.
echo Open browser to http://localhost:5000
echo ========================================
