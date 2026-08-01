Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = [System.Windows.Automation.Condition]::TrueCondition
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)

$out = "$env:USERPROFILE\Desktop\uia_dump.txt"
"=== WINDOWS ===" | Out-File -FilePath $out -Encoding utf8

foreach ($w in $windows) {
    $name = $w.Current.Name
    $cls = $w.Current.ClassName
    "WINDOW | name=$name | class=$cls | pid=$($w.Current.ProcessId)" | Out-File -FilePath $out -Append -Encoding utf8
}

$target = $null
foreach ($w in $windows) {
    if ($w.Current.Name -match 'Soft1|SoftOne|S1' -or $w.Current.ClassName -match 'TfrmS1|Soft') {
        $target = $w
        break
    }
}

if ($null -eq $target) {
    "" | Out-File -FilePath $out -Append -Encoding utf8
    "NO SOFTONE WINDOW MATCHED" | Out-File -FilePath $out -Append -Encoding utf8
} else {
    "" | Out-File -FilePath $out -Append -Encoding utf8
    "=== CONTROLS OF: $($target.Current.Name) ===" | Out-File -FilePath $out -Append -Encoding utf8
    $all = $target.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)
    "COUNT=$($all.Count)" | Out-File -FilePath $out -Append -Encoding utf8
    foreach ($e in $all) {
        $c = $e.Current
        "type=$($c.ControlType.ProgrammaticName) | name=$($c.Name) | autoid=$($c.AutomationId) | class=$($c.ClassName) | enabled=$($c.IsEnabled)" |
            Out-File -FilePath $out -Append -Encoding utf8
    }
}

Get-Content $out | Select-Object -First 60
"----"
"FULL DUMP: $out"
