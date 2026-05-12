@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao foi encontrado no PATH.
    echo Instale o Python 3.11+ ou adicione o Python ao PATH.
    pause
    exit /b 1
)

python -m app.main
if errorlevel 1 (
    echo.
    echo O LearnKit fechou com erro. Veja a mensagem acima.
    pause
    exit /b 1
)

endlocal
