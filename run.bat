@echo off
echo ===================================================
echo   YouTube Channel Scraper - Automated Launcher
echo ===================================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.x and check the "Add Python to PATH" option.
    pause
    exit /b
)

REM If .venv already exists, skip creation and installation
if exist .venv goto activate

echo [INFO] Creating Python virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate

echo [INFO] Installing dependencies (first-time setup)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)
goto start_server

:activate
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate

:start_server
REM Launch the browser automatically after 2 seconds
echo [INFO] Server launching on http://127.0.0.1:8000
start "" cmd /c "timeout /t 2 >nul && start http://127.0.0.1:8000"

REM Run FastAPI application
python app.py
if errorlevel 1 (
    echo [ERROR] Application failed to run.
    pause
)
