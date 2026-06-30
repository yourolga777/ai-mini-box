@echo off
cd /d "%~dp0"

:: Use consistent database path
set AI_BOX_DB_PATH=%~dp0data\app.db

echo [1/6] Installing packages...
pip install -e packages/core/ -q
pip install -e packages/web/ -q
pip install -e packages/llm/ -q

echo [2/6] Running database migrations...
cd /d "%~dp0packages\core"
python -m alembic upgrade head
if %errorlevel% neq 0 (
    echo Migration failed. Press any key to exit.
    pause >nul
    exit /b 1
)

echo [3/6] Building frontend...
cd /d "%~dp0packages\web\frontend"
call npm run build
if %errorlevel% neq 0 (
    echo Frontend build failed. Press any key to exit.
    pause >nul
    exit /b 1
)

echo [4/6] Initializing config...
cd /d "%~dp0"
if not exist "data\config.json" python -m ai_mini_box init

echo [6/6] Starting server at http://127.0.0.1:8080
start "" http://127.0.0.1:8080
python -m ai_mini_box serve
