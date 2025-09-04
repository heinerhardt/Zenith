#!/usr/bin/env python3
"""
Launcher script for Zenith Three-Panel Chat Interface
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the three-panel Streamlit app"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    app_path = project_root / "src" / "ui" / "three_panel_chat_app.py"
    
    if not app_path.exists():
        print(f"Error: Application file not found at {app_path}")
        sys.exit(1)
    
    # Launch Streamlit
    try:
        print("🚀 Starting Zenith Three-Panel Chat Interface...")
        print(f"📂 App location: {app_path}")
        print("🌐 Opening in browser...")
        
        # Run streamlit with the three-panel app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false",
            "--theme.base", "light",
            "--theme.backgroundColor", "#f8f9fa",
            "--theme.secondaryBackgroundColor", "#ffffff",
            "--theme.textColor", "#1f2937"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down Zenith Chat Interface...")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()