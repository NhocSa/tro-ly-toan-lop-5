@echo off
cd /d "%~dp0"
where ollama >nul 2>nul
if errorlevel 1 (
  echo Chua tim thay Ollama.
  echo Hay cai Ollama cho Windows tu https://ollama.com/download/windows
  echo Sau khi cai xong, chay lai tep nay de tai mo hinh tro chuyen.
  pause
  exit /b 1
)
echo Dang tai mo hinh qwen3.5:2b. Lan dau can Internet va khoang 3 GB dung luong.
ollama pull qwen3.5:2b
if errorlevel 1 (
  echo Tai mo hinh that bai. Kiem tra Internet va thu chay lai tep nay.
  pause
  exit /b 1
)
echo Da san sang. Mo Ollama, chay run.bat roi thu tro chuyen.
pause
