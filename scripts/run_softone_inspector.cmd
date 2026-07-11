@echo off
setlocal
title SoftOne UI Inspector
echo Keep SoftOne open on the target entry form.
echo This tool only reads the Windows UI Automation tree.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$raw = Get-Content -Raw -LiteralPath '%~f0';" ^
  "$marker = 'REM__POWER' + 'SHELL_PAYLOAD__';" ^
  "$script = $raw.Substring($raw.IndexOf($marker) + $marker.Length);" ^
  "& ([scriptblock]::Create($script))"
if errorlevel 1 (
  echo.
  echo Inspector failed. Send a screenshot of this window.
) else (
  echo.
  echo Ready: softone_controls.txt on your Desktop.
)
pause
exit /b

REM__POWERSHELL_PAYLOAD__
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$automationElement = [System.Windows.Automation.AutomationElement]
$root = $automationElement::RootElement
$windows = $root.FindAll(
    [System.Windows.Automation.TreeScope]::Children,
    [System.Windows.Automation.Condition]::TrueCondition
)

$candidates = foreach ($window in $windows) {
    $name = [string]$window.GetCurrentPropertyValue(
        $automationElement::NameProperty,
        $true
    )
    $class = [string]$window.GetCurrentPropertyValue(
        $automationElement::ClassNameProperty,
        $true
    )
    $rectangle = $window.Current.BoundingRectangle
    $area = [double]$rectangle.Width * [double]$rectangle.Height
    if (
        $area -gt 10000 -and (
            $name -match '(?i)softone|series\s*6' -or
            $class -match '(?i)softone|Chrome_WidgetWin_1'
        )
    ) {
        [pscustomobject]@{
            Element = $window
            Name = $name
            Class = $class
            Area = $area
        }
    }
}

if (-not $candidates) {
    throw 'No open SoftOne / Chrome window was found.'
}

$desktop = [Environment]::GetFolderPath('Desktop')
$output = Join-Path $desktop 'softone_controls.txt'
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("Captured: $([DateTime]::Now.ToString('s'))")
$lines.Add("Candidate windows: $($candidates.Count)")

foreach ($candidate in ($candidates | Sort-Object Area -Descending)) {
    $target = $candidate.Element
    $lines.Add('')
    $lines.Add('=== WINDOW ===')
    $lines.Add("Window: $($candidate.Name)")
    $lines.Add("Class: $($candidate.Class)")
    $lines.Add("Area: $($candidate.Area)")

    $controls = $target.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition
    )

    foreach ($control in $controls) {
        try {
            $name = [string]$control.GetCurrentPropertyValue(
                $automationElement::NameProperty,
                $true
            )
            $automationId = [string]$control.GetCurrentPropertyValue(
                $automationElement::AutomationIdProperty,
                $true
            )
            $className = [string]$control.GetCurrentPropertyValue(
                $automationElement::ClassNameProperty,
                $true
            )
            $controlType = $control.GetCurrentPropertyValue(
                $automationElement::ControlTypeProperty,
                $true
            )
            $isPassword = [bool]$control.GetCurrentPropertyValue(
                $automationElement::IsPasswordProperty,
                $true
            )

            if ($isPassword) {
                $name = '<password>'
            }
            $name = ($name -replace '[\r\n|]+', ' ').Trim()
            if ($name.Length -gt 160) {
                $name = $name.Substring(0, 160)
            }
            if (-not $name -and -not $automationId) {
                continue
            }

            $typeName = if ($controlType) {
                $controlType.ProgrammaticName -replace '^ControlType\.', ''
            } else {
                ''
            }
            $rectangle = $control.Current.BoundingRectangle
            $bounds = '{0},{1},{2},{3}' -f `
                [int]$rectangle.X, `
                [int]$rectangle.Y, `
                [int]$rectangle.Width, `
                [int]$rectangle.Height
            $lines.Add(
                "title='$name' | auto_id='$automationId' | type='$typeName' | " +
                "class='$className' | bounds='$bounds'"
            )
        } catch {
            continue
        }
    }
}

[IO.File]::WriteAllLines($output, $lines, [Text.UTF8Encoding]::new($false))
Write-Host $output
