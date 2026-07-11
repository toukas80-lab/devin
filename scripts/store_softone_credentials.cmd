@echo off
setlocal
set /p USERNAME=SoftOne username:
"%~dp0SoftOne-PDF-Automation.exe" store-credentials ^
  --config "%~dp0config\local.json" ^
  --username "%USERNAME%"
pause
