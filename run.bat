@echo off
if not "%_HIDDEN%"=="" goto :main

set _HIDDEN=1
powershell -WindowStyle Hidden -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -WindowStyle Hidden"
exit /b

:main
pip install --upgrade ai-mini-box-core ai-mini-box-web -q 2>nul
if not exist "config.json" ai-mini-box init >nul 2>&1
start "" http://127.0.0.1:8080
start /b ai-mini-box serve > "%TEMP%\ai-mini-box.log" 2>&1
exit
