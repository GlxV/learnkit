@echo off
setlocal

cd /d "%~dp0"

set "LEARNKIT_PYTHON=%~dp0.venv\Scripts\python.exe"

if exist "%LEARNKIT_PYTHON%" (
    "%LEARNKIT_PYTHON%" -m app.main
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python nao foi encontrado no PATH e o ambiente .venv nao existe.
        echo Rode install_learnkit_windows.bat primeiro.
        pause
        exit /b 1
    )
    python -m app.main
)

if errorlevel 1 (
    echo.
    echo O LearnKit fechou com erro. Veja a mensagem acima.
    pause
    exit /b 1
)

endlocal
