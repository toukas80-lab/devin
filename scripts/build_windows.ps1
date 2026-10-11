param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

if ($SkipInstall) {
    $python = "python"
    $pyinstaller = "pyinstaller"
} else {
    if (-not (Test-Path ".venv")) {
        py -3.11 -m venv .venv
    }
    $python = ".\.venv\Scripts\python.exe"
    $pyinstaller = ".\.venv\Scripts\pyinstaller.exe"
    & $python -m pip install ".[build]"
}

& $pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "DEVIN-PDF" `
    --collect-all pypdf `
    --add-data "src\softone_pilot\devin-config.default.json;softone_pilot" `
    "src\softone_pilot\dropfolder_app.py"

Write-Host "Build ready: dist\DEVIN-PDF.exe"
