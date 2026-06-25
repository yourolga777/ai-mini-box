@echo off
echo Stopping server...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080 " ^| findstr LISTENING') do (
    taskkill /f /pid %%p >nul 2>nul
    echo Killed process %%p
)
echo Server stopped.
pause
