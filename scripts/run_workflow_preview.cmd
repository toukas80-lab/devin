@echo off
setlocal
for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.OpenFileDialog; $dialog.Filter = 'PDF files (*.pdf)|*.pdf'; if ($dialog.ShowDialog() -eq 'OK') { $dialog.FileName }"`) do set "PDF=%%I"
if not defined PDF exit /b 0

"%~dp0SoftOne-PDF-Automation.exe" workflow "%PDF%" ^
  --config "%~dp0config\local.json" ^
  --workflow "%~dp0config\softone_workflow.example.json" ^
  --profile creditor_expense.create

echo.
echo Preview finished. SoftOne was not changed.
pause
