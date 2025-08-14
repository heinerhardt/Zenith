#!/usr/bin/env python3
"""
Langfuse setup and verification script for Zenith
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Docker is available")
            return True
        else:
            print("[ERROR] Docker is not available")
            return False
    except FileNotFoundError:
        print("[ERROR] Docker is not installed")
        return False

def start_langfuse():
    """Start Langfuse with Docker Compose"""
    try:
        print("Starting Langfuse with Docker Compose...")
        
        # Check if docker-compose file exists
        compose_file = project_root / "docker-compose.langfuse.yml"
        if not compose_file.exists():
            print(f"[ERROR] Docker compose file not found: {compose_file}")
            return False
        
        # Start services
        result = subprocess.run([
            'docker-compose', '-f', str(compose_file), 'up', '-d'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] Langfuse services started successfully")
            print("Waiting for services to be ready...")
            time.sleep(10)  # Give services time to start
            return True
        else:
            print(f"[ERROR] Failed to start Langfuse: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to start Langfuse: {e}")
        return False

def check_langfuse_health():
    """Check if Langfuse is accessible"""
    try:
        import requests
        
        print("Checking Langfuse health...")
        response = requests.get("http://localhost:3000", timeout=10)
        
        if response.status_code == 200:
            print("[OK] Langfuse is accessible at http://localhost:3000")
            return True
        else:
            print(f"[WARNING] Langfuse returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Langfuse. Is it running?")
        return False
    except ImportError:
        print("[WARNING] requests library not available. Cannot check health.")
        return True  # Assume it's working
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False

def check_langfuse_package():
    """Check if Langfuse Python package is installed"""
    try:
        import langfuse
        print(f"[OK] Langfuse package is installed (version: {langfuse.__version__})")
        return True
    except ImportError:
        print("[ERROR] Langfuse package is not installed")
        print("Install with: pip install langfuse")
        return False

def check_environment():
    """Check environment configuration"""
    print("Checking environment configuration...")
    
    required_vars = [
        'LANGFUSE_ENABLED',
        'LANGFUSE_HOST',
        'LANGFUSE_PUBLIC_KEY',
        'LANGFUSE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            if 'KEY' in var:
                print(f"[OK] {var} is set (hidden)")
            else:
                print(f"[OK] {var} = {value}")
    
    if missing_vars:
        print(f"[WARNING] Missing environment variables: {', '.join(missing_vars)}")
        print("Make sure to set these in your .env file")
        return False
    
    # Check if enabled
    if os.getenv('LANGFUSE_ENABLED', '').lower() != 'true':
        print("[WARNING] LANGFUSE_ENABLED is not set to 'true'")
        return False
    
    return True

def test_langfuse_connection():
    """Test Langfuse connection with the configured settings"""
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        print("Testing Langfuse connection...")
        client = get_langfuse_client()
        
        if client and client.is_enabled():
            print("[OK] Langfuse client is initialized and enabled")
            
            # Try to create a test trace
            trace_id = client.trace_chat_interaction(
                user_input="Test message",
                response="Test response",
                provider="test",
                model="test-model",
                metadata={"test": True}
            )
            
            if trace_id:
                print(f"[OK] Test trace created successfully: {trace_id}")
                client.flush()
                return True
            else:
                print("[WARNING] Could not create test trace")
                return False
        else:
            print("[ERROR] Langfuse client is not enabled")
            return False
            
    except Exception as e:
        print(f"[ERROR] Langfuse connection test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Access Langfuse dashboard: http://localhost:3000")
    print("2. Create an account (if first time)")
    print("3. Create a new project: 'zenith-pdf-chatbot'")
    print("4. Get API keys: Settings → API Keys")
    print("5. Update your .env file:")
    print("   LANGFUSE_ENABLED=True")
    print("   LANGFUSE_PUBLIC_KEY=pk-...")
    print("   LANGFUSE_SECRET_KEY=sk-...")
    print("6. Restart your Streamlit app")
    print("7. Start chatting and check traces in Langfuse!")

def main():
    """Main setup function"""
    print("=" * 60)
    print("LANGFUSE SETUP FOR ZENITH")
    print("=" * 60)
    
    success = True
    
    # Check prerequisites
    success &= check_docker()
    success &= check_langfuse_package()
    
    if not success:
        print("\n[ERROR] Prerequisites not met. Please fix the issues above.")
        return 1
    
    # Start Langfuse
    success &= start_langfuse()
    
    if success:
        success &= check_langfuse_health()
    
    # Check configuration
    env_ok = check_environment()
    
    if env_ok:
        success &= test_langfuse_connection()
    
    print("\n" + "=" * 60)
    if success and env_ok:
        print("[SUCCESS] Langfuse is fully set up and working!")
        print("\nYou can now:")
        print("- Use your Streamlit app with full observability")
        print("- View traces at http://localhost:3000")
        print("- Monitor performance and user interactions")
    elif success:
        print("[PARTIAL SUCCESS] Langfuse is running but needs configuration")
        show_next_steps()
    else:
        print("[ERROR] Setup failed. Please check the errors above.")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
