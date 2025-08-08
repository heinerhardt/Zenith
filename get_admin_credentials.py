#!/usr/bin/env python3
"""
Get admin credentials from the authentication system
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_admin_credentials():
    """Get admin user information"""
    print("Retrieving admin credentials...")
    
    try:
        from src.core.qdrant_manager import get_qdrant_client
        from src.auth.auth_manager import AuthenticationManager
        
        qdrant_client = get_qdrant_client().get_client()
        auth_manager = AuthenticationManager(
            qdrant_client=qdrant_client,
            secret_key='zenith-jwt-secret-key'  # Use the actual secret from config
        )
        
        # List all users
        users = auth_manager.user_store.list_users()
        admin_users = [u for u in users if u.role.value == 'administrator']
        
        if admin_users:
            admin = admin_users[0]
            print("\n" + "=" * 50)
            print("ADMIN USER FOUND")
            print("=" * 50)
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            print(f"Full Name: {admin.full_name or 'Not set'}")
            print(f"Created: {admin.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Last Login: {admin.last_login.strftime('%Y-%m-%d %H:%M:%S') if admin.last_login else 'Never'}")
            print(f"Active: {'Yes' if admin.is_active else 'No'}")
            print("\n" + "=" * 50)
            print("RESET PASSWORD (if needed)")
            print("=" * 50)
            
            # Generate a new password for the admin
            from src.utils.security import PasswordManager
            pm = PasswordManager()
            new_password = pm.generate_secure_password(12)
            
            print(f"New password: {new_password}")
            print("\nTo reset the password, use this new password and update the admin user.")
            print("Or you can login with the existing password if you know it.")
            
        else:
            print("No admin user found. Admin user will be created on next app startup.")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("ZENITH ADMIN CREDENTIALS")
    print("=" * 30)
    
    success = get_admin_credentials()
    
    if success:
        print("\n[INFO] If you don't know the admin password:")
        print("1. Try common passwords like 'admin', 'password', etc.")
        print("2. Or reset the database and restart the app to create a new admin")
        print("3. The app is accessible at: http://127.0.0.1:8503")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
