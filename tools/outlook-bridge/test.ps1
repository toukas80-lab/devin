# Calls Outlook.Application from 64-bit and 32-bit PowerShell like SoftOne does.
# Expected: NO Outlook; the bridge window "Apostoli apo info@crazysouvle.gr" opens (twice). Press Akyro on both.
$ErrorActionPreference = 'Stop'
$pdf = Join-Path $env:TEMP 'bridge_test.pdf'
Set-Content -Path $pdf -Value '%PDF-1.4 bridge test' -Encoding Ascii
$code = "`$ErrorActionPreference = 'Stop'; try { `$o = New-Object -ComObject Outlook.Application; `$m = `$o.CreateItem(0); `$m.To = 'toukas80@gmail.com'; `$m.Subject = 'Bridge test'; `$m.Body = 'test'; [void]`$m.Attachments.Add('$pdf'); `$m.Display(); 'COM call OK' } catch { 'COM call FAILED: ' + `$_.Exception.Message }"
& "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command $code
& "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command $code
Start-Sleep 3
Get-Content (Join-Path $env:LOCALAPPDATA 'OutlookBridge\bridge.log') -Tail 25
