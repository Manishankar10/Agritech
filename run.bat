@echo off
title Uzhavan Desk - Tamil Nadu Farm Manager
echo ========================================================
echo        Uzhavan Desk (உழவன் மேலாளர்) - Starting Up
echo ========================================================
echo.

:: Check py launcher first, then python
set PY_CMD=
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :start_app
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :start_app
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set PY_CMD="%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    goto :start_app
)

echo [ERROR] Python was not found!
echo Please use "py app.py" or install Python from https://www.python.org/
pause
exit /b

:start_app
echo [1/2] Checking Python packages...
%PY_CMD% -m pip install -r requirements.txt >nul 2>&1

echo [2/2] Starting Uzhavan Desk Web Server...
echo.
echo ========================================================
echo  Server is Running! Open your browser and visit:
echo  http://127.0.0.1:5000
echo ========================================================
echo (Keep this window open while using the application)
echo.

%PY_CMD% app.py
pause
