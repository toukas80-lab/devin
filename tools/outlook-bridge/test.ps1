# Diagnostics + Outlook.Application call from 64-bit and 32-bit PowerShell (like SoftOne).
# Expected: NO Outlook; the bridge window "Apostoli apo info@crazysouvle.gr" opens (twice). Press Akyro on both.
$log = Join-Path $env:LOCALAPPDATA 'OutlookBridge\bridge.log'
$clsid = '{0006F03A-0000-0000-C000-000000000046}'
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
"elevated(admin token): " + ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
"--- OUTLOOK processes before:"; Get-Process OUTLOOK -ErrorAction SilentlyContinue | ForEach-Object { "$($_.Id) $($_.Path)" }
"--- Outlook App Path:"; (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE' -ErrorAction SilentlyContinue).'(default)'
"--- Office platform:"; (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' -ErrorAction SilentlyContinue).Platform
Add-Type -Namespace W -Name K -MemberDefinition '[DllImport("kernel32.dll")] public static extern bool IsWow64Process(System.IntPtr h, out bool w);'
"--- SoftOne-like processes (name path wow64=32bit):"
Get-Process | Where-Object { $_.Path -match 'soft|xplorer' } | ForEach-Object { $w = $false; try { [void][W.K]::IsWow64Process($_.Handle, [ref]$w) } catch {}; "$($_.Name) $($_.Path) wow64=$w" }
"--- registry LocalServer32:"
foreach ($k in @("HKCU\Software\Classes\CLSID\$clsid\LocalServer32", "HKCU\Software\Classes\WOW6432Node\CLSID\$clsid\LocalServer32", "HKLM\SOFTWARE\Classes\CLSID\$clsid\LocalServer32", "HKLM\SOFTWARE\Classes\WOW6432Node\CLSID\$clsid\LocalServer32")) {
  "$k = " + ((& reg query $k /ve 2>&1) -join ' ' -replace '\s+', ' ')
}
$pdf = Join-Path $env:TEMP 'bridge_test.pdf'
Set-Content -Path $pdf -Value '%PDF-1.4 bridge test' -Encoding Ascii
$code = "`$ErrorActionPreference = 'Stop'; `$s = 'start'; try { `$o = New-Object -ComObject Outlook.Application; `$s = 'created name=' + `$o.Name + ' ver=' + `$o.Version; `$m = `$o.CreateItem(0); `$m.To = 'toukas80@gmail.com'; `$m.Subject = 'Bridge test'; `$m.Body = 'test'; [void]`$m.Attachments.Add('$pdf'); `$s += ' subj=' + `$m.Subject; `$m.Display(); 'COM call OK: ' + `$s } catch { 'COM call FAILED after [' + `$s + ']: ' + `$_.Exception.Message }"
"--- 64-bit:"; & "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command $code
Start-Sleep 3
"--- 32-bit:"; & "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command $code
Start-Sleep 3
"--- OUTLOOK processes after:"; Get-Process OUTLOOK -ErrorAction SilentlyContinue | ForEach-Object { "$($_.Id) $($_.Path)" }
"--- bridge.log:"; if (Test-Path $log) { Get-Content $log -Tail 40 }
