# Waits (max 10 min) until SoftOne calls the bridge, then writes the new bridge.log lines to ..\..\bridge-result.txt
$log = Join-Path $env:LOCALAPPDATA 'OutlookBridge\bridge.log'
$out = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'bridge-result.txt'
$start = (Get-Content $log).Count
Write-Host 'Waiting: do Ektyposi -> E-Mail in SoftOne now...'
$t = 0
while ($t -lt 600) {
  $new = @(Get-Content $log | Select-Object -Skip $start)
  if ($new -match 'Application created|QI ') { break }
  Start-Sleep 5; $t += 5
}
Start-Sleep 20
$new = @(Get-Content $log | Select-Object -Skip $start)
"SoftOne capture $(Get-Date -Format s) waited=${t}s new_lines=$($new.Count)" | Set-Content $out -Encoding UTF8
$new | Add-Content $out -Encoding UTF8
Get-Content $out -Tail 60
