@echo off
setlocal
pushd "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"
if errorlevel 1 (
  echo.
  echo Build failed.
) else (
  echo.
  echo Ready: dist\SoftOne-PDF-Pilot-Windows.zip
)
pause
popd
