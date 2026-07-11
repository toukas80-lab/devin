$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -e ".[build]"
$output = "dist\SoftOne-PDF-Pilot"
New-Item -ItemType Directory -Force -Path $output | Out-Null

& ".\.venv\Scripts\pyinstaller.exe" `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "SoftOne-PDF-Pilot" `
    --distpath $output `
    --collect-all pypdf `
    --collect-all pywinauto `
    "src\softone_pilot\gui.py"

& ".\.venv\Scripts\pyinstaller.exe" `
    --noconfirm `
    --clean `
    --onefile `
    --console `
    --name "SoftOne-PDF-Automation" `
    --distpath $output `
    --collect-all pypdf `
    --collect-all pywinauto `
    "src\softone_pilot\cli.py"

New-Item -ItemType Directory -Force -Path "$output\config" | Out-Null
Copy-Item "config\local.example.json" "$output\config\local.example.json" -Force
Copy-Item "config\local.example.json" "$output\config\local.json" -Force
Copy-Item `
    "config\softone_workflow.example.json" `
    "$output\config\softone_workflow.example.json" `
    -Force
Copy-Item "scripts\run_workflow_preview.cmd" "$output\run_workflow_preview.cmd" -Force
Copy-Item `
    "scripts\run_softone_fill_no_save.cmd" `
    "$output\run_softone_fill_no_save.cmd" `
    -Force
Copy-Item "README.md" "$output\README.md" -Force

$archive = "dist\SoftOne-PDF-Pilot-Windows.zip"
Compress-Archive -Path "$output\*" -DestinationPath $archive -Force
Write-Host "Build ready: $archive"
