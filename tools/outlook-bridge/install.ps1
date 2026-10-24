# Registers bridge.py as Outlook.Application for the current user (HKCU).
# -Machine also overrides HKLM (run PowerShell as Administrator); a backup is exported first.
param([switch]$Machine, [string]$Python = '')
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Join-Path $env:LOCALAPPDATA 'OutlookBridge'
New-Item -ItemType Directory -Force $data | Out-Null
if (-not $Python) {
  if (Get-Command py -ErrorAction SilentlyContinue) { $Python = (& py -3 -c "import sys;print(sys.executable)").Trim() }
  else { $Python = 'C:\Users\User\Documents\devin\softone-bot\.venv\Scripts\python.exe' }
}
if (-not (Test-Path $Python)) { throw "python.exe not found: $Python (use -Python <path>)" }
$base = (& $Python -c "import sys;print(getattr(sys,'_base_executable',sys.executable))").Trim()
$pyw = Join-Path (Split-Path -Parent $base) 'pythonw.exe'
if (-not (Test-Path $pyw)) { throw "pythonw.exe not found next to $base" }
& $base -c "import tkinter" ; if ($LASTEXITCODE -ne 0) { throw "tkinter missing in $base" }
$venv = Join-Path $dir '.venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) { & $base -m venv $venv ; if ($LASTEXITCODE -ne 0) { throw 'venv failed' } }
& "$venv\Scripts\python.exe" -m pip install --quiet pywin32
if ($LASTEXITCODE -ne 0) { throw 'pip install pywin32 failed' }
& $pyw "$dir\bridge.py" --selftest
Start-Sleep 2
Write-Host ("selftest: " + (Get-Content (Join-Path $data 'bridge.log') -Tail 1))
$clsid = '{0006F03A-0000-0000-C000-000000000046}'
$server = "`"$pyw`" `"$dir\bridge.py`" --serve"
$roots = @('HKCU:\Software\Classes')
if ($Machine) {
  foreach ($v in @('', 'WOW6432Node\')) {
    $f = Join-Path $data ("backup_hklm_" + ($v -replace '\\', '') + "clsid.reg")
    if (-not (Test-Path $f)) { & reg export "HKLM\SOFTWARE\Classes\${v}CLSID\$clsid" $f /y 2>$null | Out-Null }
  }
  $roots += 'HKLM:\SOFTWARE\Classes'
}
foreach ($root in $roots) {
  foreach ($v in @('CLSID', 'WOW6432Node\CLSID')) {
    $k = "$root\$v\$clsid"
    New-Item -Force $k | Out-Null
    Set-Item $k 'Outlook Bridge (SoftOne)'
    foreach ($pair in @(@('LocalServer32', $server), @('PythonCOM', 'bridge.OutlookApplication'),
                        @('PythonCOMPath', $dir), @('PythonCOMPolicy', 'win32com.server.policy.DynamicPolicy'),
                        @('ProgID', 'Outlook.Application'))) {
      New-Item -Force "$k\$($pair[0])" | Out-Null
      Set-Item "$k\$($pair[0])" $pair[1]
    }
    if (Test-Path "$k\InprocServer32") { Remove-Item -Recurse -Force "$k\InprocServer32" }
  }
  New-Item -Force "$root\Outlook.Application\CLSID" | Out-Null
  Set-Item "$root\Outlook.Application\CLSID" $clsid
}
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -match 'bridge\.py.*--serve' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' 'OutlookBridge' $server
Start-Process $pyw -ArgumentList "`"$dir\bridge.py`" --serve"
Start-Sleep 3
Write-Host "OK: bridge registered ($($roots -join ', ')). Server: $server"
Write-Host '--- comtest (in-process) ---'
& "$venv\Scripts\python.exe" "$dir\bridge.py" --comtest
