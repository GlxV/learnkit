param(
    [string]$Version = "0.1.2",
    [string]$ReleaseUrl = "https://github.com/GlxV/learnkit/releases/tag/v$Version",
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python -m pip install -e ".[build]"

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist

& $Python -m PyInstaller `
    --name LearnKit `
    --onedir `
    --windowed `
    --add-data "app/ui/assets;app/ui/assets" `
    app/main.py

& $Python -m PyInstaller `
    --name LearnKitUpdater `
    --onefile `
    --console `
    app/updater_main.py

Copy-Item -Force "dist\LearnKitUpdater.exe" "dist\LearnKit\LearnKitUpdater.exe"

$PackageName = "LearnKit-$Version-win.zip"
$PackagePath = Join-Path "dist" $PackageName
Remove-Item -Force -ErrorAction SilentlyContinue $PackagePath

@{
    version = $Version
    platform = "windows"
    asset_name = $PackageName
    release_url = $ReleaseUrl
} | ConvertTo-Json | Set-Content -Encoding UTF8 "dist\LearnKit\manifest.json"

$Excluded = @("data", "backups", "logs", ".learnkit_update_backup", ".venv", "__pycache__")
Get-ChildItem "dist\LearnKit" |
    Where-Object { $Excluded -notcontains $_.Name } |
    Compress-Archive -DestinationPath $PackagePath

& $Python scripts\make_release_manifest.py `
    --version $Version `
    --asset $PackagePath `
    --platform windows `
    --release-url $ReleaseUrl `
    --output "dist\latest.json"

Write-Host "Build ready:"
Write-Host "  $PackagePath"
Write-Host "  dist\latest.json"
