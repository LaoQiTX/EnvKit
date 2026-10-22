@echo off
cd /d "%~dp0"
python EnvKit/main.py
if %ERRORLEVEL% NEQ 0 pause
