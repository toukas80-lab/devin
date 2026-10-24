# Registers bridge.py as Outlook.Application for the current user (HKCU).
# -Machine also overrides HKLM (run PowerShell as Administrator); a backup is exported first.
param([switch]$Machine)
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Join-Path $env:LOCALAPPDATA 'OutlookBridge'
New-Item -ItemType Directory -Force $data | Out-Null
$pyw = (& py -3 -c "import sys,os;print(os.path.join(sys.base_exec_prefix,'pythonw.exe'))").Trim()
if (-not (Test-Path $pyw)) { throw "pythonw.exe not found: $pyw" }
& py -3 -m pip install --user --quiet pywin32
if ($LASTEXITCODE -ne 0) { throw 'pip install pywin32 failed' }
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
Write-Host "OK: bridge registered ($($roots -join ', ')). Server: $server"
