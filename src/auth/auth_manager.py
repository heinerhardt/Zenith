"""
Authentication Manager for Zenith
Handles user authentication, registration, and session management
"""

import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json

from .models import User, UserSession, UserRole, UserRegistrationRequest, UserLoginRequest
from src.utils.security import (
    PasswordManager, JWTManager, SessionManager, RateLimiter,
    SecurityValidator, hash_password, verify_password
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserStore:
    """User data storage interface using Qdrant"""
    
    def __init__(self, qdrant_client):
        self.qdrant_client = qdrant_client
        self.collection_name = "zenith_users"
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the users collection exists in Qdrant"""
        try:
            from qdrant_client.http import models
            
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection for users
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # Small vector size for user data
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created users collection: {self.collection_name}")
                
                # Create index for filtering by type
                try:
                    self.qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="type",
                        field_schema=models.KeywordIndexParams(
                            type="keyword",
                            is_tenant=False
                        )
                    )
                    logger.info(f"Created type index for collection: {self.collection_name}")
                except Exception as e:
                    logger.warning(f"Could not create type index: {e}")
                
                # Create index for username
                try:
                    self.qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="username",
                        field_schema=models.KeywordIndexParams(
                            type="keyword",
                            is_tenant=False
                        )
                    )
                    logger.info(f"Created username index for collection: {self.collection_name}")
                except Exception as e:
                    logger.warning(f"Could not create username index: {e}")
                
                # Create index for email
                try:
                    self.qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="email",
                        field_schema=models.KeywordIndexParams(
                            type="keyword",
                            is_tenant=False
                        )
                    )
                    logger.info(f"Created email index for collection: {self.collection_name}")
                except Exception as e:
                    logger.warning(f"Could not create email index: {e}")
                    
        except Exception as e:
            logger.error(f"Error ensuring users collection exists: {e}")
            raise
    
    def store_user(self, user: User) -> bool:
        """Store user in Qdrant"""
        try:
            from qdrant_client.http import models
            import uuid
            
            # Create a simple vector for the user (using username hash)
            vector = self._create_user_vector(user.username)
            
            # Convert user ID to UUID if it's a string
            if isinstance(user.id, str):
                try:
                    point_id = str(uuid.UUID(user.id))
                except ValueError:
                    # If it's not a valid UUID, generate a new one
                    point_id = str(uuid.uuid4())
                    user.id = point_id
            else:
                point_id = str(user.id)
            
            # Store user data
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            **user.to_dict(),
                            'type': 'user'
                        }
                    )
                ]
            )
            
            logger.info(f"Stored user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing user {user.username}: {e}")
            return False
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            # Convert to proper UUID format if needed
            import uuid
            try:
                point_id = str(uuid.UUID(user_id))
            except ValueError:
                point_id = user_id
                
            result = self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            
            if result and len(result) > 0:
                user_data = result[0].payload
                if user_data.get('type') == 'user':
                    return User.from_dict(user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            from qdrant_client.http import models
            
            # Search for user with matching username
            result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="username",
                            match=models.MatchValue(value=username)
                        ),
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value="user")
                        )
                    ]
                ),
                limit=1
            )
            
            if result and result[0] and len(result[0]) > 0:
                user_data = result[0][0].payload
                return User.from_dict(user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            from qdrant_client.http import models
            
            result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="email",
                            match=models.MatchValue(value=email)
                        ),
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value="user")
                        )
                    ]
                ),
                limit=1
            )
            
            if result and result[0] and len(result[0]) > 0:
                user_data = result[0][0].payload
                return User.from_dict(user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def update_user(self, user: User) -> bool:
        """Update user information"""
        return self.store_user(user)  # Upsert will update existing user
    
    def list_users(self, limit: int = 100) -> List[User]:
        """List all users"""
        try:
            from qdrant_client.http import models
            
            # First try without filter to see if there are any points
            result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True
            )
            
            users = []
            if result and result[0]:
                for point in result[0]:
                    try:
                        # Check if this is a user type
                        payload = point.payload
                        if payload.get('type') == 'user':
                            user = User.from_dict(payload)
                            users.append(user)
                    except Exception as e:
                        logger.warning(f"Error parsing user data: {e}")
            
            return users
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        try:
            # Convert to proper UUID format if needed
            import uuid
            try:
                point_id = str(uuid.UUID(user_id))
            except ValueError:
                point_id = user_id
                
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            logger.info(f"Deleted user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def _create_user_vector(self, username: str) -> List[float]:
        """Create a simple vector for user storage"""
        import hashlib
        
        # Create a deterministic vector based on username
        hash_obj = hashlib.sha256(username.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 384-dimensional vector
        vector = []
        for i in range(384):
            byte_index = i % len(hash_bytes)
            vector.append((hash_bytes[byte_index] - 128) / 128.0)
        
        return vector


class AuthenticationManager:
    """Main authentication manager"""
    
    def __init__(self, qdrant_client, secret_key: Optional[str] = None):
        """Initialize authentication manager"""
        self.user_store = UserStore(qdrant_client)
        self.password_manager = PasswordManager()
        self.jwt_manager = JWTManager(secret_key)
        self.session_manager = SessionManager(self.jwt_manager)
        self.rate_limiter = RateLimiter()
        
        # Ensure admin user exists
        self._ensure_admin_user()
    
    def _ensure_admin_user(self):
        """Ensure at least one admin user exists"""
        try:
            users = self.user_store.list_users()
            admin_users = [u for u in users if u.role == UserRole.ADMINISTRATOR]
            
            if not admin_users:
                # Create default admin user
                admin_password = self.password_manager.generate_secure_password()
                admin_user = User.create_new_user(
                    username="admin",
                    email="admin@zenith.local",
                    password_hash=self.password_manager.hash_password(admin_password),
                    role=UserRole.ADMINISTRATOR,
                    full_name="System Administrator"
                )
                
                if self.user_store.store_user(admin_user):
                    logger.info(f"Created default admin user with password: {admin_password}")
                    print(f"DEFAULT ADMIN CREDENTIALS:")
                    print(f"Username: admin")
                    print(f"Password: {admin_password}")
                    print("Please change the password after first login!")
                
        except Exception as e:
            logger.error(f"Error ensuring admin user: {e}")
    
    def register_user(self, registration: UserRegistrationRequest, 
                     ip_address: str = None) -> Tuple[bool, str, Optional[User]]:
        """Register a new user"""
        
        # Rate limiting
        if ip_address:
            allowed, retry_after = self.rate_limiter.is_allowed(ip_address, 'register')
            if not allowed:
                return False, f"Too many registration attempts. Try again in {retry_after} seconds.", None
        
        # Validate registration data
        validation_errors = registration.validate()
        if validation_errors:
            return False, "; ".join(validation_errors), None
        
        # Check if username already exists
        existing_user = self.user_store.get_user_by_username(registration.username)
        if existing_user:
            return False, "Username already exists", None
        
        # Check if email already exists
        existing_email = self.user_store.get_user_by_email(registration.email)
        if existing_email:
            return False, "Email already registered", None
        
        # Create new user
        try:
            password_hash = self.password_manager.hash_password(registration.password)
            user = User.create_new_user(
                username=registration.username,
                email=registration.email,
                password_hash=password_hash,
                role=registration.role,
                full_name=registration.full_name
            )
            
            if self.user_store.store_user(user):
                logger.info(f"Registered new user: {user.username}")
                return True, "User registered successfully", user
            else:
                return False, "Failed to store user data", None
                
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False, "Registration failed", None
    
    def login_user(self, login_request: UserLoginRequest, 
                  ip_address: str = None, user_agent: str = None) -> Tuple[bool, str, Optional[str]]:
        """Authenticate user and create session"""
        
        # Rate limiting
        if ip_address:
            allowed, retry_after = self.rate_limiter.is_allowed(ip_address, 'login')
            if not allowed:
                return False, f"Too many login attempts. Try again in {retry_after} seconds.", None
        
        # Validate login data
        validation_errors = login_request.validate()
        if validation_errors:
            return False, "; ".join(validation_errors), None
        
        # Find user by username or email
        user = self.user_store.get_user_by_username(login_request.username_or_email)
        if not user:
            user = self.user_store.get_user_by_email(login_request.username_or_email)
        
        if not user:
            return False, "Invalid username/email or password", None
        
        # Check if user is active
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Verify password
        if not self.password_manager.verify_password(login_request.password, user.password_hash):
            return False, "Invalid username/email or password", None
        
        # Update last login
        user.update_last_login()
        self.user_store.update_user(user)
        
        # Create session
        try:
            token = self.session_manager.create_session(
                user_id=user.id,
                username=user.username,
                role=user.role.value,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Clear rate limiting on successful login
            if ip_address:
                self.rate_limiter.clear_attempts(ip_address, 'login')
            
            logger.info(f"User logged in: {user.username}")
            return True, "Login successful", token
            
        except Exception as e:
            logger.error(f"Error creating session for {user.username}: {e}")
            return False, "Login failed", None
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate user session token"""
        return self.session_manager.validate_session(token)
    
    def logout_user(self, token: str) -> bool:
        """Logout user and invalidate session"""
        return self.session_manager.invalidate_session(token)
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from session token"""
        payload = self.validate_session(token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if user_id:
            return self.user_store.get_user_by_id(user_id)
        
        return None
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.password_manager.verify_password(old_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters long"
        
        # Update password
        try:
            user.password_hash = self.password_manager.hash_password(new_password)
            if self.user_store.update_user(user):
                # Invalidate all user sessions to force re-login
                self.session_manager.invalidate_all_user_sessions(user_id)
                logger.info(f"Password changed for user: {user.username}")
                return True, "Password changed successfully"
            else:
                return False, "Failed to update password"
                
        except Exception as e:
            logger.error(f"Error changing password for {user.username}: {e}")
            return False, "Password change failed"
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        user = self.user_store.get_user_by_id(user_id)
        if not user:
            return False
        
        # Update preferences
        user.preferences.update(preferences)
        return self.user_store.update_user(user)
    
    def is_user_admin(self, token: str) -> bool:
        """Check if current user is administrator"""
        payload = self.validate_session(token)
        if not payload:
            return False
        
        return payload.get('role') == 'administrator'
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        return self.session_manager.cleanup_expired_sessions()


# Streamlit session management helpers
def init_auth_session():
    """Initialize authentication session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_token' not in st.session_state:
        st.session_state.user_token = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = None

def get_current_user_from_session(auth_manager: AuthenticationManager) -> Optional[User]:
    """Get current user from Streamlit session"""
    if not st.session_state.get('authenticated') or not st.session_state.get('user_token'):
        return None
    
    return auth_manager.get_current_user(st.session_state.user_token)

def require_authentication(auth_manager: AuthenticationManager) -> Optional[User]:
    """Require authentication for current page"""
    user = get_current_user_from_session(auth_manager)
    if not user:
        st.error("Authentication required")
        st.stop()
    return user

def require_admin(auth_manager: AuthenticationManager) -> Optional[User]:
    """Require admin authentication for current page"""
    user = require_authentication(auth_manager)
    if not user.is_admin():
        st.error("Administrator access required")
        st.stop()
    return user

def logout_user_session():
    """Logout user from Streamlit session"""
    st.session_state.authenticated = False
    st.session_state.user_token = None
    st.session_state.user_info = None
    st.rerun()
