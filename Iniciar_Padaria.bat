@echo off

cd /d "%~dp0"

echo Iniciando Padaria 4 Geracoes...
echo.

start "Padaria 4 Geracoes" /min "C:\apps\Python\python.exe" "API, DB, APP\app.py"

timeout /t 3 /nobreak >nul

start "" "http://127.0.0.1:5000"