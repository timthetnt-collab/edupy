@echo off
cd /d "%~dp0"
title Questoria
if not exist ".venv\Scripts\python.exe" (
    echo Questoria still needs its private game engine set up.
    echo Run "Setup EduPy.bat" once, then open Play Questoria again.
    pause
    exit /b 1
)
echo Entering Questoria...
".venv\Scripts\python.exe" run_edupy.py
if errorlevel 1 (
    echo.
    echo Questoria had trouble starting. Your progress is safe.
    pause
)
