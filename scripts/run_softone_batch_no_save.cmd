@echo off
setlocal
echo SoftOne will open automatically and process the configured inbox.
echo The first ready PDF will be filled, but Save is disabled.
echo.
pause

"%~dp0SoftOne-PDF-Automation.exe" batch ^
  --config "%~dp0config\local.json" ^
  --workflow "%~dp0config\softone_workflow.example.json" ^
  --execute

echo.
echo Finished without Save. Check the open SoftOne form.
pause
