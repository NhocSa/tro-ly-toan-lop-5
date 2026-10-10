@echo off
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
if errorlevel 1 (
  echo Cai thu vien that bai. Kiem tra ket noi Internet roi chay lai run.bat.
  pause
  exit /b 1
)
python app.py
