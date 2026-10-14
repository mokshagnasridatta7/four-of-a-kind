@echo off
cd /d "%~dp0"
echo Starting Pygame...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Game exited with error code: %ERRORLEVEL%
    pause
)
