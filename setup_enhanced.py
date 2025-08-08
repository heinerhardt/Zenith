#!/usr/bin/env python3
"""
Setup script for Zenith PDF Chatbot enhanced features
Installs new dependencies and initializes the system
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"{'='*60}")
    print(f"Running: {description or command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings/Info:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("Installing new dependencies...")
    
    # Install new packages
    new_packages = [
        "bcrypt>=4.0.0",
        "PyJWT>=2.8.0", 
        "cryptography>=41.0.0",
        "requests>=2.31.0",
        "pydantic-settings>=2.0.0"
    ]
    
    for package in new_packages:
        success = run_command(f"pip install {package}", f"Installing {package}")
        if not success:
            print(f"Failed to install {package}")
            return False
    
    print("✅ All new dependencies installed successfully!")
    return True


def create_directories():
    """Create necessary directories"""
    print("Creating necessary directories...")
    
    directories = [
        "data",
        "logs", 
        "temp_pdfs"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    print("✅ Directories created successfully!")


def test_imports():
    """Test if all imports work correctly"""
    print("Testing imports...")
    
    try:
        # Test core imports
        from src.core.config import config
        print("✓ Core config import successful")
        
        # Test auth imports
        from src.auth.models import User, UserRole
        print("✓ Auth models import successful")
        
        # Test security imports
        from src.utils.security import PasswordManager, JWTManager
        print("✓ Security utils import successful")
        
        # Test enhanced modules
        from src.core.qdrant_manager import QdrantManager
        print("✓ Qdrant manager import successful")
        
        from src.core.enhanced_vector_store import UserVectorStore
        print("✓ Enhanced vector store import successful")
        
        from src.core.enhanced_chat_engine import EnhancedChatEngine
        print("✓ Enhanced chat engine import successful")
        
        from src.core.settings_manager import SettingsManager
        print("✓ Settings manager import successful")
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def setup_configuration():
    """Setup initial configuration"""
    print("Setting up configuration...")
    
    env_file = project_root / ".env"
    
    if env_file.exists():
        print("✓ Environment file already exists")
        
        # Read current config
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check if new variables exist
        required_vars = [
            "ENABLE_AUTH", "JWT_SECRET_KEY", "CHAT_PROVIDER", 
            "EMBEDDING_PROVIDER", "QDRANT_MODE"
        ]
        
        missing_vars = []
        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {missing_vars}")
            print("Please check your .env file and add the missing variables.")
        else:
            print("✓ All required environment variables present")
    else:
        print("❌ Environment file not found")
        print("Please create a .env file based on the template")
        return False
    
    print("✅ Configuration setup completed!")
    return True


def test_basic_functionality():
    """Test basic functionality"""
    print("Testing basic functionality...")
    
    try:
        # Test configuration loading
        from src.core.config import config
        print(f"✓ Config loaded - Debug mode: {config.debug_mode}")
        
        # Test password hashing
        from src.utils.security import PasswordManager
        test_password = "test123"
        hashed = PasswordManager.hash_password(test_password)
        verified = PasswordManager.verify_password(test_password, hashed)
        if verified:
            print("✓ Password hashing works correctly")
        else:
            print("❌ Password hashing failed")
            return False
        
        # Test JWT tokens
        from src.utils.security import JWTManager
        jwt_manager = JWTManager("test-secret")
        token = jwt_manager.create_token({"user": "test"}, expires_in_hours=1)
        payload = jwt_manager.verify_token(token)
        if payload and payload.get("user") == "test":
            print("✓ JWT tokens work correctly")
        else:
            print("❌ JWT tokens failed")
            return False
        
        print("✅ Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("="*60)
    print("ZENITH PDF CHATBOT - ENHANCED FEATURES SETUP")
    print("="*60)
    
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories), 
        ("Testing imports", test_imports),
        ("Setting up configuration", setup_configuration),
        ("Testing basic functionality", test_basic_functionality)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name.upper()} {'='*20}")
        success = step_func()
        
        if not success:
            print(f"\n❌ Setup failed at step: {step_name}")
            print("Please fix the errors above and run setup again.")
            sys.exit(1)
        
        print(f"✅ {step_name} completed successfully!")
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Review your .env file configuration")
    print("2. Make sure Qdrant is running (local or cloud)")
    print("3. Start the application with: python main.py ui")
    print()
    print("New features available:")
    print("• ✅ User authentication with role-based access")
    print("• ✅ Administrator and Chat User roles")
    print("• ✅ User-isolated document processing") 
    print("• ✅ Support for both local (Qdrant) and cloud vector stores")
    print("• ✅ Ollama integration for local AI models")
    print("• ✅ Enhanced chat interface with drag-and-drop file uploads")
    print("• ✅ System settings management for administrators")
    print("• ✅ Improved security and session management")
    print()
    print("Default admin credentials will be displayed on first run.")


if __name__ == "__main__":
    main()
