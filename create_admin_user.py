#!/usr/bin/env python3
"""
Script to create the first admin user for Zenith Three-Panel Interface
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.qdrant_manager import get_qdrant_client
from src.auth.auth_manager import AuthenticationManager
from src.auth.models import UserRegistrationRequest, UserRole
from src.core.config import config

def main():
    """Create admin user"""
    print("Creating admin user for Zenith Three-Panel Interface...")
    
    try:
        # Initialize Qdrant client
        qdrant_client = get_qdrant_client().get_client()
        
        # Initialize auth manager
        auth_manager = AuthenticationManager(
            qdrant_client=qdrant_client,
            secret_key=config.jwt_secret_key
        )
        
        # Check if any users exist
        users = auth_manager.user_store.list_users()
        user_count = len(users)
        print(f"Current user count: {user_count}")
        
        if user_count > 0:
            print("Users already exist. Admin user may already be created.")
            for user in users:
                print(f"- {user.email} ({user.role.value})")
            return
        
        # Create admin user
        admin_request = UserRegistrationRequest(
            username="admin",
            email="admin@zenith.ai",
            password="admin123",
            role=UserRole.ADMINISTRATOR.value
        )
        
        success, message, user = auth_manager.register_user(
            admin_request,
            ip_address="127.0.0.1"
        )
        
        if success:
            print("Admin user created successfully!")
            print(f"   Username: admin")
            print(f"   Email: admin@zenith.ai") 
            print(f"   Password: admin123")
            print(f"   Role: {user.role.value}")
            print("\nYou can now login to the three-panel interface.")
        else:
            print(f"Failed to create admin user: {message}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()