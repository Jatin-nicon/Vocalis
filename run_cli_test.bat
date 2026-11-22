@echo off
title Voice-PC-Assistant CLI Test
echo Starting Voice-PC-Assistant in Interactive CLI Test Mode...
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" main.py --cli
) else (
    python main.py --cli
)
pause
