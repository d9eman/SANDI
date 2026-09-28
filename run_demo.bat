@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD=python"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 set "PYTHON_CMD=py"

if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto global_python
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto global_python
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
goto end

:global_python
echo.
echo Could not create or activate .venv. Using the active Python installation instead.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

:end
endlocal
