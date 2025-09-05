#!/usr/bin/env python3
"""
Wrapper script to run enterprise setup without import path issues.
This script can be called directly from the startup scripts.
"""

import os
import sys
import asyncio

def setup_python_path():
    """Setup Python path to handle relative imports correctly."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    
    # Add both current directory and src directory to Python path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Set the working directory to project root
    os.chdir(current_dir)

def run_setup():
    """Run the enterprise setup with proper error handling."""
    try:
        # Setup Python path first
        setup_python_path()
        
        # Now try to import with absolute paths
        from setup.enterprise_setup import run_enterprise_setup
        
        async def main():
            print("🚀 Starting enterprise setup...")
            success, results = await run_enterprise_setup(interactive=True)
            return success
        
        success = asyncio.run(main())
        
        if success:
            print("✅ Enterprise setup completed successfully!")
            return True
        else:
            print("❌ Enterprise setup failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📍 Make sure all dependencies are installed: pip install -r requirements.txt")
        print("📍 Ensure all required __init__.py files exist in src/ subdirectories")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_setup()
    sys.exit(0 if success else 1)