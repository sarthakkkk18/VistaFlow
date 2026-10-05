@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" main.py %*
) else if exist "..\..\.venv\Scripts\python.exe" (
  "..\..\.venv\Scripts\python.exe" main.py %*
) else (
  echo Install Python dependencies as described in README.md first.
  pause
  exit /b 1
)
