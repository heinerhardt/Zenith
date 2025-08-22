#!/usr/bin/env python3
"""
Test script for Zenith Three-Panel Chat Interface
Validates functionality without requiring Ollama instance
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        from src.core.config import config
        print("✅ Config imported successfully")
        
        from src.core.qdrant_manager import get_qdrant_client
        print("✅ Qdrant manager imported successfully")
        
        from src.auth.auth_manager import AuthenticationManager
        print("✅ Auth manager imported successfully")
        
        from src.ui.three_panel_chat_app import ZenithThreePanelApp
        print("✅ Three-panel app imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_app_initialization():
    """Test app can be initialized"""
    print("\n🧪 Testing app initialization...")
    
    try:
        from src.ui.three_panel_chat_app import ZenithThreePanelApp
        
        # Create app instance (this will test session state initialization)
        app = ZenithThreePanelApp()
        print("✅ App initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ App initialization error: {e}")
        return False

def test_dependencies():
    """Test external dependencies"""
    print("\n🧪 Testing dependencies...")
    
    try:
        import streamlit
        print("✅ Streamlit available")
        
        import qdrant_client
        print("✅ Qdrant client available")
        
        import langchain
        print("✅ LangChain available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n🧪 Testing configuration...")
    
    try:
        from src.core.config import config
        
        # Check critical config values
        print(f"✅ App port: {config.app_port}")
        print(f"✅ Qdrant URL: {config.qdrant_url}")
        print(f"✅ Debug mode: {config.debug_mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def create_test_env_file():
    """Create test .env file if it doesn't exist"""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("📝 Creating test .env file...")
        
        env_content = """
# Test configuration for Zenith Three-Panel App
APP_PORT=8501
DEBUG_MODE=true
LOG_LEVEL=INFO

# Qdrant Configuration
QDRANT_URL=http://localhost
QDRANT_PORT=6333

# JWT Configuration
JWT_SECRET_KEY=test-secret-key-for-development-only

# Chat Engine Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_TOKENS=2000

# UI Configuration
THEME_COLOR=#3b82f6
"""
        
        env_file.write_text(env_content.strip())
        print("✅ Test .env file created")
    else:
        print("✅ .env file already exists")

def test_file_structure():
    """Test required files exist"""
    print("\n🧪 Testing file structure...")
    
    required_files = [
        "src/ui/three_panel_chat_app.py",
        "src/core/config.py",
        "src/auth/auth_manager.py",
        "run_three_panel.py",
        "run_three_panel.bat"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {missing_files}")
        return False
    
    return True

def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("🚀 ZENITH THREE-PANEL CHAT INTERFACE")
    print("="*60)
    print("\n📋 USAGE INSTRUCTIONS:")
    print("\n1. Start the application:")
    print("   Windows: run_three_panel.bat")
    print("   Linux/Mac: python run_three_panel.py")
    print("\n2. Open browser to: http://localhost:8501")
    print("\n3. Create account (first user becomes admin)")
    print("\n4. Upload PDF documents in right panel")
    print("\n5. Start chatting in center panel")
    print("\n" + "="*60)
    print("🎨 FEATURES:")
    print("- Three-panel ChatGPT-inspired layout")
    print("- Left: Recent chat sessions")
    print("- Center: Main chat interface")
    print("- Right: Settings & admin controls")
    print("- Responsive design")
    print("- Professional styling")
    print("=" * 60)

def main():
    """Run all tests"""
    print("🔍 ZENITH THREE-PANEL APP TEST SUITE")
    print("=" * 50)
    
    # Create test environment
    create_test_env_file()
    
    # Run tests
    tests = [
        test_file_structure,
        test_imports,
        test_dependencies,
        test_config,
        test_app_initialization
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    # Results
    print("\n" + "="*50)
    print("📊 TEST RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed / (passed + failed) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! The three-panel interface is ready to run.")
        print_usage_instructions()
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        
        if failed == 1 and passed >= 3:
            print("\n💡 Most tests passed. You can try running the app anyway:")
            print("   python run_three_panel.py")

if __name__ == "__main__":
    main()