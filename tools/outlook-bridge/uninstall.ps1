# Removes the bridge registration; with -Machine restores the original HKLM Outlook registration (run as Administrator).
param([switch]$Machine)
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Start-Transcript -Path (Join-Path $root 'uninstall.log') -Force | Out-Null
$clsid = '{0006F03A-0000-0000-C000-000000000046}'
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -match 'bridge\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; "killed $($_.ProcessId)" }
foreach ($v in @('CLSID', 'WOW6432Node\CLSID')) {
  $k = "HKCU:\Software\Classes\$v\$clsid"
  if (Test-Path $k) { Remove-Item -Recurse -Force $k; "removed $k" }
}
if (Test-Path 'HKCU:\Software\Classes\Outlook.Application') { Remove-Item -Recurse -Force 'HKCU:\Software\Classes\Outlook.Application' }
Remove-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' 'OutlookBridge' -ErrorAction SilentlyContinue
if ($Machine) {
  $data = Join-Path $env:LOCALAPPDATA 'OutlookBridge'
  foreach ($v in @('', 'WOW6432Node\')) {
    $k = "HKLM\SOFTWARE\Classes\${v}CLSID\$clsid"
    cmd /c "reg delete `"$k`" /f >nul 2>&1"
    "deleted $k"
    $f = Join-Path $data ("backup_hklm_" + ($v -replace '\\', '') + "clsid.reg")
    if (-not (Test-Path $f)) { "no backup for $k (key did not exist originally)"; continue }
    $txt = Get-Content $f -Raw
    if ($txt -match 'bridge\.py') { "skip $f (contains the bridge, not the original)"; continue }
    cmd /c "reg import `"$f`" 2>&1"
    "restored $k from $f"
  }
  foreach ($v in @('', 'WOW6432Node\')) { "--- HKLM\SOFTWARE\Classes\${v}CLSID\$clsid\LocalServer32:"; cmd /c "reg query `"HKLM\SOFTWARE\Classes\${v}CLSID\$clsid\LocalServer32`" 2>&1" }
}
'OK: bridge removed.'
Stop-Transcript | Out-Null
