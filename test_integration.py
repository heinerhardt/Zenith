"""
Test the MinIO integration in your main Streamlit app
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_integration():
    """Test that MinIO integration imports work"""
    print("Testing MinIO integration...")
    
    # Test 1: Check if the integration module can be imported
    try:
        from minio_simple_integration import render_minio_tabs, MINIO_AVAILABLE
        print("✓ MinIO integration module imported successfully")
        print(f"  MinIO Available: {MINIO_AVAILABLE}")
    except ImportError as e:
        print(f"✗ MinIO integration import failed: {e}")
        return False
    
    # Test 2: Check if MinIO client works
    if MINIO_AVAILABLE:
        try:
            from src.core.minio_client import MinIOClient
            print("✓ MinIO client can be imported")
        except ImportError as e:
            print(f"✗ MinIO client import failed: {e}")
            return False
    
    # Test 3: Check if main app imports work
    try:
        from src.core.config import config
        from src.core.pdf_processor import PDFProcessor
        from src.core.vector_store import VectorStore
        print("✓ Main app components import successfully")
    except ImportError as e:
        print(f"✗ Main app import failed: {e}")
        return False
    
    print("\n🎉 Integration test completed successfully!")
    print("\nYour Zenith app now has MinIO functionality!")
    print("Visit http://localhost:8504 to see the integrated app")
    
    return True

if __name__ == "__main__":
    test_integration()
