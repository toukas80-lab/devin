# Run as Administrator AFTER install.ps1. Points the machine-wide Outlook.Application (64- and 32-bit views)
# to the bridge, because the 32-bit view (SoftOne is 32-bit) ignores the per-user registration while
# Outlook 2007 is installed. Backs up the original keys; uninstall.ps1 -Machine restores them.
$data = Join-Path $env:LOCALAPPDATA 'OutlookBridge'
Start-Transcript -Path (Join-Path $data 'machine.log') -Force | Out-Null
$clsid = '{0006F03A-0000-0000-C000-000000000046}'
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
"admin: $isAdmin  user: $env:USERNAME  data: $data"
if (-not $isAdmin) { 'FAILED: not running as Administrator' }
elseif (-not (Test-Path "HKCU:\Software\Classes\CLSID\$clsid\LocalServer32")) { 'FAILED: run install.ps1 first' }
else {
  foreach ($v in @('', 'WOW6432Node\')) {
    $k = "HKLM\SOFTWARE\Classes\${v}CLSID\$clsid"
    $f = Join-Path $data ("backup_hklm_" + ($v -replace '\\', '') + "clsid.reg")
    if (-not (Test-Path $f)) { cmd /c "reg export `"$k`" `"$f`" /y >nul 2>&1"; "backup $k -> $f exists=$(Test-Path $f)" }
    cmd /c "reg delete `"$k`" /f >nul 2>&1"
    cmd /c "reg copy `"HKCU\Software\Classes\CLSID\$clsid`" `"$k`" /s /f"
    cmd /c "reg query `"$k`" /s"
  }
  'OK: machine-wide registration points to the bridge'
}
Stop-Transcript | Out-Null
