#!/bin/bash
# Zenith AI Chat - Startup Script (Linux/macOS)
# Simplified Streamlit Interface

echo ""
echo "==============================================="
echo "   🤖 Zenith AI Chat - Starting Application"
echo "==============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "src/ui/simple_chat_app.py" ]; then
    echo "❌ Error: simple_chat_app.py not found!"
    echo "Please run this script from the Zenith project root directory."
    read -p "Press Enter to exit..."
    exit 1
fi

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

echo ""
echo "🔍 Checking system status..."
python main.py info

echo ""
echo "🚀 Starting Zenith AI Chat Interface..."
echo ""
echo "💡 Access the application at: http://localhost:8501"
echo "💡 Demo admin login is automatically enabled"  
echo "💡 Press Ctrl+C to stop the application"
echo ""

# Start the Streamlit application
python -m streamlit run src/ui/simple_chat_app.py --server.port 8501

echo ""
echo "👋 Zenith AI Chat stopped."
read -p "Press Enter to exit..."