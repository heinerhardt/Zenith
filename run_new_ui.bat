@echo off
REM Windows batch script to run Zenith PDF Chatbot with New UI Design
REM Based on Sercompe-inspired modern design

echo Zenith PDF Chatbot - New UI Launcher
echo =====================================

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
echo Select Option:
echo 1. Run Zenith AI Chat Interface (Latest UI)
echo 2. Run Main App (Legacy UI)
echo 3. Show System Information
echo 4. Run Tests
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Starting Zenith AI Chat Interface...
    echo This is the latest sophisticated chat interface with clean design
    echo Open your browser to: http://localhost:8502
    echo Press Ctrl+C to stop the server
    echo.
    streamlit run zenith_working_ui.py --server.port 8502
    goto menu
)

if "%choice%"=="2" (
    echo Starting Zenith Main App (Legacy UI)...
    echo Open your browser to: http://localhost:8501
    echo.
    python main.py ui --host 0.0.0.0 --port 8501
    goto menu
)

if "%choice%"=="3" (
    python main.py info
    pause
    goto menu
)

if "%choice%"=="4" (
    echo Running tests...
    python main.py test
    pause
    goto menu
)

if "%choice%"=="5" (
    echo Goodbye! Thank you for using Zenith AI.
    exit /b 0
)

echo Invalid choice. Please try again.
goto menu