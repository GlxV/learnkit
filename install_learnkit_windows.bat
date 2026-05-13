@echo off
setlocal

cd /d "%~dp0"

if not exist "scripts\install_windows.ps1" (
    echo Nao encontrei scripts\install_windows.ps1.
    echo Verifique se voce extraiu/clonou o projeto inteiro.
    pause
    exit /b 1
)

echo.
echo LearnKit - instalador Windows
echo Este script instala Python/dependencias e prepara OCR local quando possivel.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1" %*
set "RESULT=%ERRORLEVEL%"

echo.
if "%RESULT%"=="0" (
    echo Instalacao finalizada.
    echo Para abrir o app, execute: abrir_learnkit.bat
) else (
    echo A instalacao terminou com erro. Veja as mensagens acima.
)
echo.
pause
exit /b %RESULT%
