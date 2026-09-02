@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo        Phone Web Cam - Windows Launcher
echo ==============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  %PY% -m venv .venv
  if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
python run.py
set EXITCODE=%errorlevel%
goto :end

:error
echo.
echo Setup failed. Make sure Python 3.10 or newer and internet access are available.
set EXITCODE=1

:end
echo.
if not "%EXITCODE%"=="0" pause
exit /b %EXITCODE%
