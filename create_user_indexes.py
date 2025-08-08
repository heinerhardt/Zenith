#!/usr/bin/env python3
"""
Create necessary indexes for the user collection
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_user_indexes():
    """Create necessary indexes for user collection"""
    print("Creating user collection indexes...")
    
    try:
        from src.core.qdrant_manager import get_qdrant_client
        from qdrant_client.http import models
        
        qdrant_manager = get_qdrant_client()
        collection_name = "zenith_users"
        
        # Check if collection exists
        if not qdrant_manager.collection_exists(collection_name):
            print(f"Collection {collection_name} does not exist")
            return False
        
        # Create indexes
        indexes_to_create = ["type", "username", "email"]
        
        for field_name in indexes_to_create:
            try:
                qdrant_manager.get_client().create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=models.KeywordIndexParams(
                        type="keyword",
                        is_tenant=False
                    )
                )
                print(f"[OK] Created index for field: {field_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"[OK] Index for {field_name} already exists")
                else:
                    print(f"[WARNING] Could not create index for {field_name}: {e}")
        
        print("\n[SUCCESS] User collection indexes created/verified")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating indexes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("ZENITH USER COLLECTION INDEX CREATION")
    print("=" * 40)
    
    success = create_user_indexes()
    
    if success:
        print("\n[INFO] Indexes are ready. You can now use the login system.")
        print("[INFO] Try logging in with: admin / Admin123!")
    else:
        print("\n[ERROR] Index creation failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
