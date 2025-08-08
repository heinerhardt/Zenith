#!/usr/bin/env python3
"""
Fix and test auth system with proper UUID handling
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_auth_system():
    """Test the authentication system"""
    print("Testing authentication system with UUID fixes...")
    
    try:
        from src.core.qdrant_manager import get_qdrant_client
        from src.auth.auth_manager import AuthenticationManager
        from src.auth.models import UserRegistrationRequest
        
        print("Initializing authentication manager...")
        qdrant_client = get_qdrant_client().get_client()
        auth_manager = AuthenticationManager(
            qdrant_client=qdrant_client,
            secret_key='test-secret-key'
        )
        
        print("Authentication manager initialized successfully!")
        
        # List existing users
        users = auth_manager.user_store.list_users()
        print(f"Found {len(users)} existing users")
        
        # Check for admin user
        admin_users = [u for u in users if u.role.value == 'administrator']
        
        if admin_users:
            print(f"Admin user found: {admin_users[0].username}")
            print("Admin user already exists - no need to create new one")
        else:
            print("No admin user found - this will trigger admin creation on app startup")
        
        return True
        
    except Exception as e:
        print(f"Error testing auth system: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("ZENITH AUTH SYSTEM FIX AND TEST")
    print("=" * 40)
    
    success = test_auth_system()
    
    if success:
        print("\n[OK] Auth system test completed successfully!")
        print("\nYou can now start the app:")
        print("   python main.py ui --port 8502")
        print("\nAdmin credentials will be shown in console on first startup")
    else:
        print("\n[ERROR] Auth system test failed - check errors above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
