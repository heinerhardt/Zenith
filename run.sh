#!/bin/bash
# Linux/macOS script to run Zenith PDF Chatbot

echo "Zenith PDF Chatbot Launcher"
echo "==========================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

# Setup environment
echo "Setting up environment..."
python main.py setup
if [ $? -ne 0 ]; then
    echo "ERROR: Environment setup failed"
    exit 1
fi

# Function to show menu
show_menu() {
    echo
    echo "Select an option:"
    echo "1. Run Streamlit Web Interface"
    echo "2. Run FastAPI Server"
    echo "3. Run Both (API + UI)"
    echo "4. Show System Information"
    echo "5. Run Tests"
    echo "6. Exit"
    echo
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1)
            echo "Starting Streamlit interface on 0.0.0.0:8501..."
            python main.py ui --host 0.0.0.0 --port 8501
            ;;
        2)
            echo "Starting FastAPI server on 0.0.0.0:8000..."
            python main.py api --host 0.0.0.0 --port 8000
            ;;
        3)
            echo "Starting both API and UI..."
            python main.py api --host 0.0.0.0 --port 8000 &
            sleep 5
            python main.py ui --host 0.0.0.0 --port 8501 &
            wait
            ;;
        4)
            python main.py info
            read -p "Press Enter to continue..."
            ;;
        5)
            echo "Running tests..."
            python main.py test
            read -p "Press Enter to continue..."
            ;;
        6)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done
