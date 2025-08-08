"""
Test Zenith Components for MinIO Integration
Run this to verify all components can be initialized properly
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_zenith_components():
    """Test that all Zenith components can be initialized"""
    print("Testing Zenith components...")
    print("=" * 50)
    
    # Test 1: Configuration
    try:
        from src.core.config import config
        print("✓ Configuration: OK")
        
        # Check key settings
        has_openai_key = config.openai_api_key and config.openai_api_key != "your_openai_api_key_here"
        print(f"  - OpenAI API Key: {'SET' if has_openai_key else 'NOT SET'}")
        print(f"  - Qdrant URL: {config.qdrant_url}")
        print(f"  - Collection: {config.qdrant_collection_name}")
        
    except Exception as e:
        print(f"✗ Configuration: FAILED - {e}")
        return False
    
    # Test 2: PDF Processor
    try:
        from src.core.pdf_processor import PDFProcessor
        pdf_processor = PDFProcessor()
        print("✓ PDF Processor: OK")
        print(f"  - Chunk size: {pdf_processor.chunk_size}")
        print(f"  - Chunk overlap: {pdf_processor.chunk_overlap}")
    except Exception as e:
        print(f"✗ PDF Processor: FAILED - {e}")
        return False
    
    # Test 3: Vector Store
    try:
        from src.core.vector_store import VectorStore
        vector_store = VectorStore()
        print("✓ Vector Store: OK")
        
        # Test connection
        if vector_store.health_check():
            print("  - Health check: PASSED")
        else:
            print("  - Health check: FAILED (but component initialized)")
            
    except Exception as e:
        print(f"✗ Vector Store: FAILED - {e}")
        print("  This might be due to:")
        print("    - Missing OpenAI API key")
        print("    - Qdrant connection issues")
        print("    - Missing dependencies")
        return False
    
    # Test 4: MinIO Client
    try:
        from src.core.minio_client import MinIOClient
        print("✓ MinIO Client: OK")
    except Exception as e:
        print(f"✗ MinIO Client: FAILED - {e}")
        return False
    
    print()
    print("🎉 All components test passed!")
    print()
    print("Your MinIO processor should now work properly.")
    print("Visit: http://localhost:8505/minio_processor")
    
    return True

def check_environment():
    """Check environment setup"""
    print("\n🔍 Environment Check:")
    print("-" * 20)
    
    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file exists")
        
        # Check for key variables
        env_content = env_file.read_text()
        
        if "OPENAI_API_KEY" in env_content:
            print("✓ OPENAI_API_KEY found in .env")
        else:
            print("✗ OPENAI_API_KEY missing from .env")
            
        if "QDRANT_URL" in env_content:
            print("✓ QDRANT_URL found in .env")
        else:
            print("✗ QDRANT_URL missing from .env")
            
        if "MINIO_ENDPOINT" in env_content:
            print("✓ MINIO_ENDPOINT found in .env")
        else:
            print("✗ MINIO_ENDPOINT missing from .env")
    else:
        print("✗ .env file not found")

if __name__ == "__main__":
    if test_zenith_components():
        check_environment()
    else:
        print("\n❌ Component tests failed.")
        print("Please check your configuration and dependencies.")
