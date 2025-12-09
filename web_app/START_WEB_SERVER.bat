@echo off
echo ========================================
echo Hallmark Scribble - Web Server
echo ========================================
echo.
echo Installing dependencies...
python -m pip install -r web_requirements.txt
echo.
echo Starting web server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python web_app.py
pause
