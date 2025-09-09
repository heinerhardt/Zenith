#!/usr/bin/env python3
"""
Windows Test Script for Admin User Creation Fix
Tests the UNIQUE constraint error fix for admin user creation
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("🔧 TESTING ADMIN USER CREATION FIX (Windows)")
print("=" * 60)

def cleanup_test_files():
    """Clean up test database files"""
    test_files = [
        "test_admin_windows.db",
        "test_admin_windows.db-wal", 
        "test_admin_windows.db-shm"
    ]
    
    for file in test_files:
        try:
            if Path(file).exists():
                Path(file).unlink()
                print(f"🧹 Cleaned up {file}")
        except Exception as e:
            print(f"⚠️ Could not clean up {file}: {e}")

def test_admin_creation():
    """Test admin user creation with UNIQUE constraint fix"""
    test_db_path = "test_admin_windows.db"
    
    try:
        print("\nStep 1: Importing required modules...")
        try:
            from src.database.enterprise_schema import EnterpriseDatabase
            print("✅ Enterprise database module imported")
        except ImportError as e:
            print(f"❌ Failed to import enterprise database: {e}")
            return False
            
        try:
            # Create a minimal logger to avoid loguru dependency
            import logging
            logging.basicConfig(level=logging.INFO)
            print("✅ Logging configured")
        except Exception as e:
            print(f"⚠️ Logging setup warning: {e}")
        
        print(f"\nStep 2: Initializing test database: {test_db_path}")
        enterprise_db = EnterpriseDatabase(test_db_path)
        
        # Initialize database
        init_result = enterprise_db.initialize_database()
        if not init_result:
            print("❌ Failed to initialize enterprise database")
            return False
        print("✅ Database initialized successfully")
        
        print("\nStep 3: Testing first admin user creation...")
        admin_uuid_1 = enterprise_db.create_admin_user(
            username="admin",
            email="admin@zenith.local",
            password_hash="test_hash_12345",  # Mock password hash
            full_name="Test Administrator",
            force_recreate=False
        )
        
        if admin_uuid_1:
            print(f"✅ First admin created successfully - UUID: {admin_uuid_1}")
        else:
            print("❌ Failed to create first admin user")
            return False
            
        print("\nStep 4: Testing duplicate admin creation (should handle gracefully)...")
        admin_uuid_2 = enterprise_db.create_admin_user(
            username="admin",  # Same username
            email="admin@zenith.local",  # Same email - this used to cause UNIQUE constraint error
            password_hash="test_hash_67890",  # Different password
            full_name="Test Administrator Updated",
            force_recreate=False  # Should return existing without error
        )
        
        if admin_uuid_2:
            print(f"✅ Duplicate admin handled successfully - UUID: {admin_uuid_2}")
        else:
            print("❌ Failed to handle duplicate admin user")
            return False
            
        print("\nStep 5: Verifying UUIDs match (should be same user)...")
        if admin_uuid_1 == admin_uuid_2:
            print("✅ UUIDs match - existing user returned correctly")
            print("✅ UNIQUE constraint error FIX VERIFIED!")
        else:
            print(f"❌ UUIDs don't match: {admin_uuid_1} != {admin_uuid_2}")
            return False
            
        print("\nStep 6: Testing force recreate functionality...")
        admin_uuid_3 = enterprise_db.create_admin_user(
            username="admin",
            email="admin@zenith.local", 
            password_hash="test_hash_force_update",
            full_name="Force Updated Administrator",
            force_recreate=True  # Should update existing user
        )
        
        if admin_uuid_3 and admin_uuid_3 == admin_uuid_1:
            print(f"✅ Force recreate successful - UUID: {admin_uuid_3}")
            print("✅ Same UUID returned after update")
        else:
            print("❌ Force recreate failed or returned different UUID")
            return False
            
        print("\nStep 7: Testing different admin user creation...")
        admin_uuid_4 = enterprise_db.create_admin_user(
            username="admin2",  # Different username
            email="admin2@zenith.local",  # Different email
            password_hash="test_hash_second_admin",
            full_name="Second Administrator",
            force_recreate=False
        )
        
        if admin_uuid_4 and admin_uuid_4 != admin_uuid_1:
            print(f"✅ Second admin created successfully - UUID: {admin_uuid_4}")
            print("✅ Multiple admins supported")
        else:
            print("❌ Failed to create second admin user")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        print("\nFull traceback:")
        print("-" * 40)
        traceback.print_exc()
        print("-" * 40)
        return False

def main():
    """Main test execution"""
    try:
        # Clean up any existing test files
        cleanup_test_files()
        
        # Run the test
        success = test_admin_creation()
        
        # Clean up test files
        cleanup_test_files()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Admin user creation UNIQUE constraint error is FIXED")
            print("✅ Existing user detection works properly")
            print("✅ Force recreate functionality works")
            print("✅ Multiple admin users are supported")
            print("\n🚀 The enterprise setup should now complete successfully!")
        else:
            print("❌ TESTS FAILED!")
            print("⚠️ The UNIQUE constraint fix may not be working properly")
            print("⚠️ Check the error messages above for details")
            
        print("=" * 60)
        
        input("\nPress Enter to exit...")
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        cleanup_test_files()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error in main: {e}")
        cleanup_test_files()
        return 1

if __name__ == "__main__":
    sys.exit(main())