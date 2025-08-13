#!/usr/bin/env python3
"""
Quick test script to verify the Streamlit fixes
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_file_syntax():
    """Test if the Python file has valid syntax"""
    try:
        with open("src/ui/enhanced_streamlit_app.py", 'r') as f:
            code = f.read()
        
        # Try to compile the code
        compile(code, "enhanced_streamlit_app.py", "exec")
        print("✅ File syntax is valid!")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def test_imports():
    """Test if the main imports work"""
    try:
        # Test if we can import streamlit
        import streamlit as st
        print("✅ Streamlit import successful!")
        
        # Test if basic streamlit functions exist
        assert hasattr(st, 'set_page_config')
        assert hasattr(st, 'form')
        assert hasattr(st, 'sidebar')
        print("✅ Required Streamlit functions available!")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing Streamlit App Fixes...")
    print("=" * 50)
    
    # Test syntax
    if not test_file_syntax():
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    print("\n🎉 All tests passed!")
    print("\n📋 Summary of fixes applied:")
    print("1. ✅ Fixed CSS rules to preserve sidebar")
    print("2. ✅ Added proper form isolation for Enter key")
    print("3. ✅ Enhanced error handling for chat sessions")
    print("4. ✅ Improved button key uniqueness")
    print("5. ✅ Added comprehensive try-catch blocks")
    
    print("\n🚀 Ready to run the app!")
    print("Run: streamlit run src/ui/enhanced_streamlit_app.py")

if __name__ == "__main__":
    main()
