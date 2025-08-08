"""
Test MinIO Integration - Fixed Version
Run this to test if MinIO client works properly
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_minio_import():
    """Test if MinIO client can be imported"""
    try:
        from src.core.minio_client import MinIOClient
        print("✓ MinIO client import successful!")
        return True
    except ImportError as e:
        print(f"✗ MinIO client import failed: {e}")
        print("\nTo fix this:")
        print("pip install minio>=7.2.0")
        return False

def test_minio_connection():
    """Test MinIO connection with default settings"""
    try:
        from src.core.minio_client import MinIOClient
        
        # Test with default local MinIO settings
        client = MinIOClient(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        
        print("Testing MinIO connection...")
        
        if client.test_connection():
            print("✓ MinIO connection successful!")
            
            # Try to list buckets
            try:
                buckets = client.list_buckets()
                print(f"Found {len(buckets)} bucket(s):")
                
                for bucket in buckets:
                    print(f"   • {bucket['name']} (created: {bucket['creation_date_str']})")
                    
                    # Try to list PDFs in each bucket
                    try:
                        pdfs = client.list_pdf_objects(bucket['name'])
                        print(f"     Contains {len(pdfs)} PDF file(s)")
                    except Exception as e:
                        print(f"     Could not list PDFs: {e}")
                
                return True
                
            except Exception as e:
                print(f"Connected but couldn't list buckets: {e}")
                return False
        else:
            print("✗ MinIO connection failed")
            print("\nTroubleshooting:")
            print("1. Make sure MinIO server is running")
            print("2. Check if accessible at http://localhost:9001 (web console)")
            print("3. Verify credentials (default: minioadmin/minioadmin)")
            return False
            
    except Exception as e:
        print(f"✗ Error testing connection: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing MinIO Integration for Zenith")
    print("=" * 50)
    
    # Test 1: Import
    if not test_minio_import():
        return
    
    print()
    
    # Test 2: Connection
    test_minio_connection()
    
    print()
    print("Next Steps:")
    print("1. If tests pass: Run 'streamlit run minio_integration_working.py'")
    print("2. If tests fail: Check MinIO server setup and credentials")
    print("3. Visit http://localhost:8502 to use the MinIO interface")

if __name__ == "__main__":
    main()
