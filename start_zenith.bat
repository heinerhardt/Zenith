@echo off
REM Zenith AI Chat - Startup Script
REM Simplified Streamlit Interface

echo.
echo ===============================================
echo    🤖 Zenith AI Chat - Starting Application
echo ===============================================
echo.

REM Check if we're in the right directory
if not exist "src\ui\simple_chat_app.py" (
    echo ❌ Error: simple_chat_app.py not found!
    echo Please run this script from the Zenith project root directory.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment not found, using system Python
)

echo.
echo 🔍 Checking system status...
python main.py info

echo.
echo 🚀 Starting Zenith AI Chat Interface...
echo.
echo 💡 Access the application at: http://localhost:8501
echo 💡 Demo admin login is automatically enabled
echo 💡 Press Ctrl+C to stop the application
echo.

REM Start the Streamlit application
python -m streamlit run src/ui/simple_chat_app.py --server.port 8501

echo.
echo 👋 Zenith AI Chat stopped.
pause