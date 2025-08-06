"""
Project validation script - checks that all files are properly created
"""

import os
from pathlib import Path

def check_file_structure():
    """Check that all expected files and directories exist"""
    
    expected_structure = {
        # Root files
        'main.py': 'file',
        'setup.py': 'file', 
        'requirements.txt': 'file',
        'README.md': 'file',
        'LICENSE': 'file',
        '.env.example': 'file',
        '.gitignore': 'file',
        'docker-compose.yml': 'file',
        'docker-compose.prod.yml': 'file',
        'Dockerfile': 'file',
        'Dockerfile.streamlit': 'file',
        'run.bat': 'file',
        'run.sh': 'file',
        'GETTING_STARTED.md': 'file',
        'PROJECT_STRUCTURE.md': 'file',
        
        # Directories
        'src': 'dir',
        'src/core': 'dir',
        'src/api': 'dir',
        'src/ui': 'dir',
        'src/utils': 'dir',
        'config': 'dir',
        'data': 'dir',
        'data/pdfs': 'dir',
        'temp_pdfs': 'dir',
        'logs': 'dir',
        'tests': 'dir',
        
        # Source files
        'src/__init__.py': 'file',
        'src/core/__init__.py': 'file',
        'src/core/config.py': 'file',
        'src/core/pdf_processor.py': 'file',
        'src/core/vector_store.py': 'file',
        'src/core/chat_engine.py': 'file',
        'src/api/__init__.py': 'file',
        'src/api/main.py': 'file',
        'src/api/routes.py': 'file',
        'src/ui/__init__.py': 'file',
        'src/ui/streamlit_app.py': 'file',
        'src/utils/__init__.py': 'file',
        'src/utils/logger.py': 'file',
        'src/utils/helpers.py': 'file',
        
        # Config files
        'config/logging.yaml': 'file',
        
        # Test files
        'tests/__init__.py': 'file',
        'tests/test_pdf_processor.py': 'file',
        'tests/test_vector_store.py': 'file',
        'tests/test_chat_engine.py': 'file',
    }
    
    print("🔍 Zenith PDF Chatbot - Project Structure Validation")
    print("=" * 60)
    
    missing_files = []
    missing_dirs = []
    found_files = 0
    found_dirs = 0
    
    for path, expected_type in expected_structure.items():
        full_path = Path(path)
        
        if expected_type == 'file':
            if full_path.is_file():
                print(f"✅ {path}")
                found_files += 1
            else:
                print(f"❌ {path} (missing file)")
                missing_files.append(path)
                
        elif expected_type == 'dir':
            if full_path.is_dir():
                print(f"📁 {path}")
                found_dirs += 1
            else:
                print(f"❌ {path} (missing directory)")
                missing_dirs.append(path)
    
    print("\n" + "=" * 60)
    print(f"📊 Summary:")
    print(f"   Files found: {found_files}/{len([p for p, t in expected_structure.items() if t == 'file'])}")
    print(f"   Directories found: {found_dirs}/{len([p for p, t in expected_structure.items() if t == 'dir'])}")
    
    if missing_files:
        print(f"\n❌ Missing files ({len(missing_files)}):")
        for file in missing_files:
            print(f"   - {file}")
    
    if missing_dirs:
        print(f"\n❌ Missing directories ({len(missing_dirs)}):")
        for dir in missing_dirs:
            print(f"   - {dir}")
    
    if not missing_files and not missing_dirs:
        print(f"\n🎉 All files and directories are present!")
        print(f"✅ Project structure is complete.")
        
        # Check file sizes to ensure they're not empty
        print(f"\n📏 File size check:")
        large_files = []
        empty_files = []
        
        for path, expected_type in expected_structure.items():
            if expected_type == 'file':
                full_path = Path(path)
                if full_path.exists():
                    size = full_path.stat().st_size
                    if size == 0:
                        empty_files.append(path)
                    elif size > 50000:  # > 50KB
                        large_files.append((path, size))
        
        if empty_files:
            print(f"   ⚠️ Empty files found: {', '.join(empty_files)}")
        else:
            print(f"   ✅ No empty files found")
        
        if large_files:
            print(f"   📋 Largest files:")
            for file, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:5]:
                print(f"      - {file}: {size:,} bytes")
        
        return True
    else:
        print(f"\n❌ Project structure is incomplete.")
        print(f"Please ensure all files and directories are created properly.")
        return False

def check_python_imports():
    """Check if critical imports work"""
    print(f"\n🐍 Python Import Validation")
    print("-" * 30)
    
    critical_imports = [
        'pathlib',
        'os', 
        'sys',
        'logging'
    ]
    
    optional_imports = [
        ('streamlit', 'Streamlit web interface'),
        ('fastapi', 'API server'),
        ('langchain', 'LangChain framework'),
        ('qdrant_client', 'Qdrant vector database'),
        ('openai', 'OpenAI API'),
        ('pypdf', 'PDF processing'),
        ('pdfplumber', 'Advanced PDF processing'),
    ]
    
    # Test critical imports
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (critical)")
    
    # Test optional imports
    missing_optional = []
    for module, description in optional_imports:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError:
            print(f"⚠️ {module} - {description} (install with: pip install -r requirements.txt)")
            missing_optional.append(module)
    
    if missing_optional:
        print(f"\n📦 To install missing packages:")
        print(f"   pip install -r requirements.txt")
    
    return len(missing_optional) == 0

def main():
    """Main validation function"""
    structure_ok = check_file_structure()
    imports_ok = check_python_imports()
    
    print(f"\n" + "=" * 60)
    if structure_ok and imports_ok:
        print(f"🎉 Zenith PDF Chatbot is ready to use!")
        print(f"")
        print(f"🚀 Next steps:")
        print(f"   1. Copy .env.example to .env")
        print(f"   2. Add your OpenAI API key to .env")
        print(f"   3. Start Qdrant: docker-compose up -d")
        print(f"   4. Run: python main.py ui")
        print(f"")
        print(f"📖 See GETTING_STARTED.md for detailed instructions")
    else:
        print(f"❌ Setup incomplete. Please fix the issues above.")
        print(f"💡 Try running: python setup.py")

if __name__ == "__main__":
    main()
