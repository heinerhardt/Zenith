@echo off
echo 🚀 Starting Zenith Three-Panel Chat Interface...
echo.
echo ⚙️  Activating virtual environment...
call venv\Scripts\activate.bat

echo 🌐 Launching Streamlit application...
python run_three_panel.py

echo.
echo 👋 Zenith Chat Interface stopped.
pause