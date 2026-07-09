@echo off
:: Run Job Hunter Copilot using the venv Python
:: Double-click this file to start the bot

cd /d "%~dp0"
echo Starting Job Hunter Copilot...
echo Using Python: %~dp0venv\Scripts\python.exe
echo.
"%~dp0venv\Scripts\python.exe" runAiBot.py
pause
