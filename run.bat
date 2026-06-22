@echo off
cd /d "%~dp0"
echo Installing packages...
pip install -e packages/core/ -q
pip install -e packages/web/ -q
if not exist "config.json" python -m ai_mini_box init
start "" http://127.0.0.1:8080
echo Starting server at http://127.0.0.1:8080
python -m ai_mini_box serve
