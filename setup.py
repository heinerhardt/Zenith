"""
Quick setup script for Zenith PDF Chatbot
Handles initial setup and validation
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️ Docker not found - you'll need to install Qdrant manually")
    return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "data/pdfs",
        "temp_pdfs", 
        "logs",
        "qdrant_storage"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️ Please edit .env file and add your OpenAI API key")
        return False
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    try:
        print("📦 Installing Python dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def start_qdrant():
    """Start Qdrant using Docker"""
    try:
        print("🚀 Starting Qdrant with Docker...")
        result = subprocess.run([
            "docker", "compose", "up", "-d", "qdrant"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Qdrant started successfully")
            print("🔗 Qdrant UI: http://localhost:6333/dashboard")
            return True
        else:
            print(f"❌ Failed to start Qdrant: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error starting Qdrant: {e}")
        return False

def validate_openai_key():
    """Check if OpenAI API key is configured"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "your_openai_api_key_here" not in content and "OPENAI_API_KEY=" in content:
                # Extract the key to check if it looks valid
                for line in content.split('\n'):
                    if line.startswith('OPENAI_API_KEY=') and '=' in line:
                        key = line.split('=', 1)[1].strip().strip('"\'')
                        if key and len(key) > 10:
                            print("✅ OpenAI API key appears to be configured")
                            return True
        
        print("⚠️ OpenAI API key not configured in .env file")
        print("Please add your OpenAI API key to the .env file")
        return False
    return False

def create_sample_data():
    """Create sample data directory structure"""
    sample_dir = Path("data/pdfs/samples")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple text file as placeholder
    readme_file = sample_dir / "README.txt"
    with open(readme_file, 'w') as f:
        f.write("""Sample PDF Directory
====================

Place your PDF files in this directory or its subdirectories.

The system will automatically discover and process all PDF files
when you select this directory in the application.

For testing, you can:
1. Add any PDF documents you want to chat with
2. Use the web interface to upload files directly
3. Specify this directory path in the application

Example structure:
- data/pdfs/samples/document1.pdf
- data/pdfs/samples/research/paper1.pdf
- data/pdfs/samples/manuals/manual1.pdf
""")
    
    print(f"✅ Created sample data directory: {sample_dir}")

def main():
    """Main setup function"""
    print("🚀 Zenith PDF Chatbot Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check Docker
    docker_available = check_docker()
    
    # Create directories
    create_directories()
    
    # Create sample data structure
    create_sample_data()
    
    # Create .env file
    env_created = create_env_file()
    if not env_created:
        success = False
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Start Qdrant if Docker is available
    if docker_available:
        if not start_qdrant():
            print("⚠️ Qdrant startup failed, but you can start it manually later")
    
    # Validate OpenAI key
    validate_openai_key()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit .env file and add your OpenAI API key")
        print("2. Add PDF files to data/pdfs/ directory")
        print("3. Run: python main.py ui (for web interface)")
        print("   Or: python main.py api (for API server)")
        print("   Or: ./run.bat (Windows) / ./run.sh (Linux/Mac)")
        
        if docker_available:
            print("4. Qdrant is running at http://localhost:6333")
        else:
            print("4. Install and start Qdrant manually")
            print("   See: https://qdrant.tech/documentation/quick-start/")
    else:
        print("❌ Setup completed with errors")
        print("Please fix the issues above and run setup again")
    
    print("\n🔗 Useful links:")
    print("- Documentation: README.md")
    print("- Qdrant Dashboard: http://localhost:6333/dashboard")
    print("- API Documentation: http://localhost:8000/docs (when API is running)")

if __name__ == "__main__":
    main()
