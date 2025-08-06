@echo off
REM Windows batch script to run Zenith PDF Chatbot

echo Zenith PDF Chatbot Launcher
echo ===========================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Setup environment
echo Setting up environment...
python main.py setup
if errorlevel 1 (
    echo ERROR: Environment setup failed
    pause
    exit /b 1
)

REM Show menu
:menu
echo.
echo Select an option:
echo 1. Run Streamlit Web Interface
echo 2. Run FastAPI Server
echo 3. Run Both (API + UI)
echo 4. Show System Information
echo 5. Run Tests
echo 6. Exit
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo Starting Streamlit interface...
    python main.py ui
    goto menu
)

if "%choice%"=="2" (
    echo Starting FastAPI server...
    python main.py api
    goto menu
)

if "%choice%"=="3" (
    echo Starting both API and UI...
    start "Zenith API" python main.py api
    timeout /t 5 >nul
    start "Zenith UI" python main.py ui
    goto menu
)

if "%choice%"=="4" (
    python main.py info
    pause
    goto menu
)

if "%choice%"=="5" (
    echo Running tests...
    python main.py test
    pause
    goto menu
)

if "%choice%"=="6" (
    echo Goodbye!
    exit /b 0
)

echo Invalid choice. Please try again.
goto menu
