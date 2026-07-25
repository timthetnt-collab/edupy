@echo off
cd /d "%~dp0"
echo Preparing Questoria's private game engine...
python -m venv .venv
if errorlevel 1 (
    echo.
    echo Setup could not find Python. Install Python, then run this file again.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Setup did not finish. Check the internet connection and try again.
    pause
    exit /b 1
)
echo.
echo Questoria is ready. You can now double-click Play Questoria.
pause
