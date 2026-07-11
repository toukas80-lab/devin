$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -e ".[build]"
& ".\.venv\Scripts\pyinstaller.exe" `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "SoftOne-PDF-Pilot" `
    --collect-all pypdf `
    "src\softone_pilot\gui.py"

Write-Host "Build ready: dist\SoftOne-PDF-Pilot.exe"
