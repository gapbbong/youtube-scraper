@echo off
echo ===================================================
echo   YouTube Channel Scraper - Automated Launcher
echo ===================================================

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.x and check the "Add Python to PATH" option.
    pause
    exit /b
)

REM Create virtual environment if it doesn't exist
if not exist .venv (
    echo [INFO] Creating Python virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo [INFO] Installing/Updating dependencies...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

REM Launch the browser automatically after 2 seconds
echo [INFO] Server launching on http://localhost:8000
start "" cmd /c "timeout /t 2 >nul && start http://localhost:8000"

REM Run FastAPI application
python app.py

pause
