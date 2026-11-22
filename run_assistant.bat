@echo off
title Voice-PC-Assistant
echo Starting Voice-PC-Assistant...
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" main.py
) else (
    python main.py
)
pause
