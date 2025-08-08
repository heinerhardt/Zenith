#!/usr/bin/env python3
"""
Quick setup script for local Qdrant database
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], check=True, capture_output=True, text=True)
        print(f"✅ Docker is available: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker first.")
        print("Visit: https://docs.docker.com/get-docker/")
        return False

def stop_existing_qdrant():
    """Stop and remove existing Qdrant container"""
    try:
        subprocess.run(["docker", "stop", "qdrant"], check=True, capture_output=True)
        print("🛑 Stopped existing Qdrant container")
    except subprocess.CalledProcessError:
        pass  # Container doesn't exist
    
    try:
        subprocess.run(["docker", "rm", "qdrant"], check=True, capture_output=True)
        print("🗑️  Removed existing Qdrant container")
    except subprocess.CalledProcessError:
        pass  # Container doesn't exist

def start_qdrant():
    """Start new Qdrant container"""
    try:
        cmd = [
            "docker", "run", "-d",
            "--name", "qdrant",
            "-p", "6333:6333",
            "-p", "6334:6334",
            "-v", "qdrant_storage:/qdrant/storage",
            "qdrant/qdrant"
        ]
        
        print("🚀 Starting Qdrant container...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Qdrant container started: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Qdrant: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
        return False

def wait_for_qdrant():
    """Wait for Qdrant to become ready"""
    print("⏳ Waiting for Qdrant to start (this may take 30-60 seconds)...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:6333/health", timeout=5)
            if response.status_code == 200:
                print("✅ Qdrant is running and healthy!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"⏳ Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ Timeout waiting for Qdrant to start")
    return False

def test_qdrant():
    """Test Qdrant functionality"""
    try:
        # Test health
        response = requests.get("http://localhost:6333/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check: OK")
        
        # Test collections endpoint
        response = requests.get("http://localhost:6333/collections", timeout=5)
        if response.status_code == 200:
            collections = response.json()
            print(f"✅ Collections endpoint: OK (found {len(collections.get('result', {}).get('collections', []))} collections)")
        
        # Show dashboard info
        print("🌐 Qdrant dashboard available at: http://localhost:6333/dashboard")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection test failed: {e}")
        return False

def update_env_file():
    """Update .env file for local Qdrant"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("📝 Creating .env file...")
        with open(env_file, "w") as f:
            f.write("""# Zenith Configuration
# Qdrant Configuration
QDRANT_MODE=local
QDRANT_URL=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=zenith_documents
QDRANT_USERS_COLLECTION=zenith_users

# AI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OLLAMA_ENABLED=False
OLLAMA_BASE_URL=http://localhost:11434

# Authentication
ENABLE_AUTH=True
JWT_SECRET_KEY=zenith-jwt-secret-key
""")
    else:
        print("📝 .env file already exists")
        print("💡 Make sure to set QDRANT_MODE=local in your .env file")
    
    return True

def show_instructions():
    """Show next steps"""
    print("\n" + "="*60)
    print("🎉 LOCAL QDRANT SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Update your Zenith configuration:")
    print("   - Login to Zenith admin panel")
    print("   - Go to AI Models tab → Qdrant Settings")
    print("   - Select 'local' mode")
    print("   - Set Host: localhost, Port: 6333")
    print("   - Test connection and save")
    
    print("\n2. Restart Zenith application:")
    print("   python main.py ui --port 8505")
    
    print("\n📊 QDRANT INFORMATION:")
    print("   - API Endpoint: http://localhost:6333")
    print("   - Dashboard: http://localhost:6333/dashboard")
    print("   - Health Check: http://localhost:6333/health")
    print("   - Storage: Docker volume 'qdrant_storage'")
    
    print("\n🔧 USEFUL COMMANDS:")
    print("   - Check status: docker ps")
    print("   - View logs: docker logs qdrant")
    print("   - Stop Qdrant: docker stop qdrant")
    print("   - Start Qdrant: docker start qdrant")
    
    print("\n💡 BENEFITS OF LOCAL QDRANT:")
    print("   ✅ Complete data privacy")
    print("   ✅ No external dependencies")
    print("   ✅ Faster performance")
    print("   ✅ No API usage costs")
    
    print("\n🔒 SECURITY NOTE:")
    print("   This setup is for development. For production,")
    print("   consider enabling authentication and HTTPS.")

def main():
    """Main setup function"""
    print("🗄️ QDRANT LOCAL DATABASE SETUP")
    print("="*40)
    
    # Check prerequisites
    if not check_docker():
        return False
    
    # Setup process
    stop_existing_qdrant()
    
    if not start_qdrant():
        return False
    
    if not wait_for_qdrant():
        print("\n🚨 TROUBLESHOOTING:")
        print("1. Check Docker is running: docker ps")
        print("2. Check logs: docker logs qdrant")
        print("3. Try restarting: docker restart qdrant")
        return False
    
    if not test_qdrant():
        return False
    
    update_env_file()
    show_instructions()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
