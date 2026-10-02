@echo off
cd /d "%~dp0"

start "Padaria 4 Geracoes" /min "C:\apps\Python\python.exe" app.py

timeout /t 3 /nobreak >nul

start "" "http://127.0.0.1:5000"