# Removes the bridge registration; with -Machine restores the HKLM backup (run as Administrator).
param([switch]$Machine)
$clsid = '{0006F03A-0000-0000-C000-000000000046}'
foreach ($v in @('CLSID', 'WOW6432Node\CLSID')) {
  $k = "HKCU:\Software\Classes\$v\$clsid"
  if (Test-Path $k) { Remove-Item -Recurse -Force $k }
}
if (Test-Path 'HKCU:\Software\Classes\Outlook.Application') { Remove-Item -Recurse -Force 'HKCU:\Software\Classes\Outlook.Application' }
if ($Machine) {
  $data = Join-Path $env:LOCALAPPDATA 'OutlookBridge'
  foreach ($v in @('', 'WOW6432Node\')) {
    & reg delete "HKLM\SOFTWARE\Classes\${v}CLSID\$clsid" /f 2>$null | Out-Null
    $f = Join-Path $data ("backup_hklm_" + ($v -replace '\\', '') + "clsid.reg")
    if (Test-Path $f) { & reg import $f }
  }
}
Write-Host 'OK: bridge removed. Outlook is used again.'
