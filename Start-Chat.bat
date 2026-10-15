@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  start "ChatLink Server" cmd /k "python server.py"
  start "ChatLink Client" cmd /c "python client.py"
) else (
  start "ChatLink Server" cmd /k "py -3 server.py"
  start "ChatLink Client" cmd /c "py -3 client.py"
)
