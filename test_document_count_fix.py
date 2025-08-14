#!/usr/bin/env python3
"""
Test script to verify the get_total_document_count fix
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_total_document_count():
    """Test the get_total_document_count method"""
    try:
        print("Testing get_total_document_count method...")
        
        # Import the vector store
        from src.core.enhanced_vector_store import UserVectorStore
        
        # Create a test instance (this will use default user_id if none provided)
        vector_store = UserVectorStore(user_id="test_user")
        
        # Try to get total document count
        try:
            total_count = vector_store.get_total_document_count()
            print(f"[OK] Total document count retrieved: {total_count}")
            return True
        except Exception as e:
            print(f"[ERROR] get_total_document_count failed: {e}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test setup failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("TESTING get_total_document_count FIX")
    print("=" * 50)
    
    success = test_total_document_count()
    
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] get_total_document_count method is working!")
    else:
        print("[ERROR] get_total_document_count method still has issues.")
        return 1
    
    print("=" * 50)
    return 0

if __name__ == "__main__":
    exit(main())
