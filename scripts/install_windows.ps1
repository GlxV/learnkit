param(
    [switch]$DryRun,
    [switch]$SkipPythonInstall,
    [switch]$SkipWindowsOcr,
    [switch]$SkipTesseract,
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "OK  $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "AVISO  $Message" -ForegroundColor Yellow
}

function Test-IsWindows {
    return [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
}

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-External {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$DryRunText = ""
    )

    $display = if ($DryRunText) { $DryRunText } else { "$FilePath $($Arguments -join ' ')" }
    if ($DryRun) {
        Write-Host "[dry-run] $display" -ForegroundColor DarkGray
        return
    }

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Comando falhou ($LASTEXITCODE): $display"
    }
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$Arguments
    )
    & $Python.Exe @($Python.Args + $Arguments)
}

function Get-PythonVersion {
    param([hashtable]$Python)
    try {
        $output = & $Python.Exe @($Python.Args + @(
            "-c",
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        )) 2>$null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
        return [version]($output | Select-Object -First 1)
    } catch {
        return $null
    }
}

function Get-PythonCommand {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() },
        @{ Exe = "$env:LocalAppData\Programs\Python\Python312\python.exe"; Args = @() },
        @{ Exe = "$env:LocalAppData\Programs\Python\Python311\python.exe"; Args = @() },
        @{ Exe = "$env:ProgramFiles\Python312\python.exe"; Args = @() },
        @{ Exe = "$env:ProgramFiles\Python311\python.exe"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        if ($candidate.Exe -match "\\") {
            if (-not (Test-Path $candidate.Exe)) {
                continue
            }
        } elseif (-not (Test-Command $candidate.Exe)) {
            continue
        }

        $version = Get-PythonVersion $candidate
        if ($version -and $version -ge [version]"3.11") {
            $candidate.Version = $version
            return $candidate
        }
    }
    return $null
}

function Install-PythonIfNeeded {
    Write-Step "Verificando Python 3.11+"
    $python = Get-PythonCommand
    if ($python) {
        Write-Ok "Python $($python.Version) encontrado."
        return $python
    }

    if ($SkipPythonInstall) {
        throw "Python 3.11+ nao encontrado e -SkipPythonInstall foi usado."
    }
    if (-not (Test-Command "winget")) {
        throw "Python 3.11+ nao encontrado e winget nao esta disponivel para instalar automaticamente."
    }

    Write-Warn "Python 3.11+ nao encontrado. Instalando Python 3.12 via winget."
    Invoke-External "winget" @(
        "install",
        "--id",
        "Python.Python.3.12",
        "-e",
        "--accept-source-agreements",
        "--accept-package-agreements"
    )

    $python = Get-PythonCommand
    if (-not $python) {
        throw "Python foi instalado, mas ainda nao ficou disponivel neste terminal. Feche e abra o terminal, depois rode o instalador novamente."
    }
    Write-Ok "Python $($python.Version) pronto."
    return $python
}

function Install-PythonDependencies {
    param([hashtable]$Python)

    Write-Step "Criando ambiente virtual e instalando dependencias Python"
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Invoke-External $Python.Exe @($Python.Args + @("-m", "venv", ".venv")) "python -m venv .venv"
    } else {
        Write-Ok "Ambiente virtual .venv ja existe."
    }

    if ($DryRun) {
        Write-Host "[dry-run] .venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel" -ForegroundColor DarkGray
        Write-Host "[dry-run] .venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor DarkGray
        return
    }

    & $venvPython -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao atualizar pip/setuptools/wheel."
    }

    & $venvPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao instalar requirements.txt."
    }

    if ($Dev) {
        & $venvPython -m pip install -e ".[dev,ocr-windows]"
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao instalar extras de desenvolvimento."
        }
    }
    Write-Ok "Dependencias Python instaladas."
}

function Install-WindowsOcrLanguages {
    if ($SkipWindowsOcr) {
        Write-Warn "OCR local do Windows ignorado por parametro."
        return
    }
    if (-not (Test-IsWindows)) {
        Write-Warn "OCR local do Windows so pode ser instalado no Windows."
        return
    }
    if (-not (Test-Command "Get-WindowsCapability")) {
        Write-Warn "Get-WindowsCapability nao esta disponivel nesta versao do Windows."
        return
    }
    if (-not (Test-IsAdmin)) {
        Write-Warn "Para instalar idiomas OCR do Windows, rode install_learnkit_windows.bat como administrador."
        return
    }

    Write-Step "Instalando idiomas de OCR local do Windows"
    foreach ($language in @("pt-BR", "en-US")) {
        $capabilityName = "Language.OCR~~~$language~0.0.1.0"
        try {
            $capability = Get-WindowsCapability -Online -Name $capabilityName -ErrorAction Stop
            if ($capability.State -eq "Installed") {
                Write-Ok "OCR Windows $language ja instalado."
                continue
            }
            if ($DryRun) {
                Write-Host "[dry-run] Add-WindowsCapability -Online -Name $capabilityName" -ForegroundColor DarkGray
                continue
            }
            Add-WindowsCapability -Online -Name $capabilityName | Out-Null
            Write-Ok "OCR Windows $language instalado."
        } catch {
            Write-Warn "Nao consegui instalar OCR Windows $language`: $($_.Exception.Message)"
        }
    }
}

function Find-TesseractExe {
    $command = Get-Command "tesseract" -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }
    $candidates = @(
        "$env:ProgramFiles\Tesseract-OCR\tesseract.exe",
        "${env:ProgramFiles(x86)}\Tesseract-OCR\tesseract.exe"
    )
    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) {
            return $path
        }
    }
    return $null
}

function Add-TesseractToUserPath {
    param([string]$TesseractExe)

    $dir = Split-Path -Parent $TesseractExe
    if ($env:Path -notlike "*$dir*") {
        $env:Path = "$env:Path;$dir"
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$dir*") {
        if ($DryRun) {
            Write-Host "[dry-run] Adicionar $dir ao PATH do usuario" -ForegroundColor DarkGray
            return
        }
        $newPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $dir } else { "$userPath;$dir" }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Ok "Tesseract adicionado ao PATH do usuario."
    }
}

function Install-TesseractFallback {
    if ($SkipTesseract) {
        Write-Warn "Tesseract ignorado por parametro."
        return
    }

    Write-Step "Verificando Tesseract OCR local como fallback"
    $tesseract = Find-TesseractExe
    if (-not $tesseract) {
        if (-not (Test-Command "winget")) {
            Write-Warn "winget nao esta disponivel; Tesseract nao sera instalado automaticamente."
            return
        }
        Invoke-External "winget" @(
            "install",
            "--id",
            "UB-Mannheim.TesseractOCR",
            "-e",
            "--accept-source-agreements",
            "--accept-package-agreements"
        )
        $tesseract = Find-TesseractExe
    }

    if (-not $tesseract) {
        Write-Warn "Tesseract nao foi encontrado apos a tentativa de instalacao."
        return
    }

    Add-TesseractToUserPath $tesseract
    Write-Ok "Tesseract encontrado em $tesseract"

    $tessdata = Join-Path (Split-Path -Parent $tesseract) "tessdata"
    if (-not (Test-Path $tessdata)) {
        Write-Warn "Pasta tessdata nao encontrada; pulando download de idioma portugues."
        return
    }

    $porFile = Join-Path $tessdata "por.traineddata"
    if (Test-Path $porFile) {
        Write-Ok "Idioma portugues do Tesseract ja instalado."
        return
    }

    $url = "https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/por.traineddata"
    if ($DryRun) {
        Write-Host "[dry-run] Baixar $url para $porFile" -ForegroundColor DarkGray
        return
    }

    try {
        Invoke-WebRequest -Uri $url -OutFile $porFile
        Write-Ok "Idioma portugues do Tesseract instalado."
    } catch {
        Write-Warn "Nao consegui baixar por.traineddata: $($_.Exception.Message)"
    }
}

function Test-LearnKitEnvironment {
    Write-Step "Testando ambiente LearnKit"
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if ($DryRun) {
        Write-Host "[dry-run] .venv\Scripts\python.exe -c `"from app.core.extractors.ocr_extractor import OcrExtractor; ...`"" -ForegroundColor DarkGray
        return
    }
    if (-not (Test-Path $venvPython)) {
        throw "Ambiente virtual nao encontrado em .venv."
    }

    & $venvPython -c "from app.core.extractors.ocr_extractor import OcrExtractor; o=OcrExtractor(); print('OCR disponivel:', o.available, o.backend_name or o.unavailable_reason); import PySide6, fitz, pptx, PIL; print('Dependencias principais: OK')"
    if ($LASTEXITCODE -ne 0) {
        throw "Teste de ambiente falhou."
    }
}

try {
    Write-Host "LearnKit - instalador Windows" -ForegroundColor Cyan
    Write-Host "Pasta do projeto: $ProjectRoot"
    if ($DryRun) {
        Write-Warn "Modo DryRun ativo: nada sera instalado."
    }

    $python = Install-PythonIfNeeded
    Install-PythonDependencies $python
    Install-WindowsOcrLanguages
    Install-TesseractFallback
    Test-LearnKitEnvironment

    Write-Step "Concluido"
    Write-Ok "Ambiente preparado."
    Write-Host "Para abrir o app: .\abrir_learnkit.bat"
    exit 0
} catch {
    Write-Host ""
    Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
