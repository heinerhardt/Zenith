#!/usr/bin/env python3
"""
Create admin user for Zenith AI Chat
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.qdrant_manager import get_qdrant_client
from src.auth.auth_manager import AuthenticationManager
from src.auth.models import UserRole, UserRegistrationRequest
from src.core.config import config

def main():
    try:
        print("Creating admin user...")
        
        # Initialize Qdrant client
        qdrant_client = get_qdrant_client().get_client()
        
        # Initialize auth manager
        auth_manager = AuthenticationManager(
            qdrant_client=qdrant_client,
            secret_key=config.jwt_secret_key
        )
        
        # Create admin user
        admin_request = UserRegistrationRequest(
            username="admin",
            email="admin@zenith.ai",
            password="admin123",
            role=UserRole.ADMINISTRATOR
        )
        
        result = auth_manager.register_user(admin_request)
        
        if result and result.get("success"):
            print("Admin user created successfully!")
            print("  Username: admin")
            print("  Password: admin123")
            print("  Role: administrator")
        else:
            print(f"Failed to create admin user: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    main()