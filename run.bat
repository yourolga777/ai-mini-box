@echo off
if not "%_HIDDEN%"=="" goto :main

set _HIDDEN=1
powershell -WindowStyle Hidden -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -WindowStyle Hidden"
exit /b

:main
cd /d "%~dp0"
pip install -e packages/core/ -q
pip install -e packages/web/ -q
if not exist "config.json" python -m ai_mini_box init
start "" http://127.0.0.1:8080
start /b python -m ai_mini_box serve > "%TEMP%\ai-mini-box.log" 2>&1
exit
