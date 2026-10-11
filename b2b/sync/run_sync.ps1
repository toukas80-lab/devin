# B2B-07: τρέχει export.py + photos.py + upload.py και γράφει μία γραμμή
# στο sync.log (ημερομηνία, OK/FAIL, χρόνος). Χωρίς secrets στο log.
$sync  = Split-Path -Parent $MyInvocation.MyCommand.Path
$py    = Join-Path (Resolve-Path (Join-Path $sync '..\..')) '.venv\Scripts\python.exe'
$log   = Join-Path $sync 'sync.log'
$t0    = Get-Date

$fail  = $null
& $py (Join-Path $sync 'export.py') *> $null
if ($LASTEXITCODE -ne 0) { $fail = "export rc=$LASTEXITCODE" }
if (-not $fail) {
    & $py (Join-Path $sync 'photos.py') *> $null
    if ($LASTEXITCODE -ne 0) { $fail = "photos rc=$LASTEXITCODE" }
}
if (-not $fail) {
    & $py (Join-Path $sync 'upload.py') *> $null
    if ($LASTEXITCODE -ne 0) { $fail = "upload rc=$LASTEXITCODE" }
}

$secs  = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$res   = if ($fail) { "FAIL $fail" } else { 'OK' }
Add-Content -Path $log -Value "$stamp $res ${secs}s" -Encoding UTF8
