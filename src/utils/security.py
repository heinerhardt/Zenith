"""
Security utilities for Zenith authentication and authorization
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
import bcrypt
from functools import wraps
import time
from collections import defaultdict

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PasswordManager:
    """Password hashing and verification manager"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Generate a secure random password"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password


class JWTManager:
    """JWT token management for user sessions"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = 'HS256'
    
    def create_token(self, payload: Dict[str, Any], expires_in_hours: int = 24) -> str:
        """Create a JWT token"""
        # Add expiration time
        payload['exp'] = datetime.utcnow() + timedelta(hours=expires_in_hours)
        payload['iat'] = datetime.utcnow()
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def refresh_token(self, token: str, extends_hours: int = 24) -> Optional[str]:
        """Refresh a token if it's still valid"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        # Remove old exp and iat
        payload.pop('exp', None)
        payload.pop('iat', None)
        
        # Create new token
        return self.create_token(payload, extends_hours)


class SessionManager:
    """Session management for user authentication"""
    
    def __init__(self, jwt_manager: JWTManager):
        self.jwt_manager = jwt_manager
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: str, username: str, role: str,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      duration_hours: int = 24) -> str:
        """Create a new user session"""
        session_id = secrets.token_urlsafe(32)
        
        # Create JWT payload
        payload = {
            'session_id': session_id,
            'user_id': user_id,
            'username': username,
            'role': role,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        # Create JWT token
        token = self.jwt_manager.create_token(payload, duration_hours)
        
        # Store session info
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'token': token
        }
        
        logger.info(f"Created session for user {username}")
        return token
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a session token"""
        payload = self.jwt_manager.verify_token(token)
        if not payload:
            return None
        
        session_id = payload.get('session_id')
        if not session_id or session_id not in self.active_sessions:
            return None
        
        # Update last activity
        self.active_sessions[session_id]['last_activity'] = datetime.utcnow()
        
        return payload
    
    def invalidate_session(self, token: str) -> bool:
        """Invalidate a session"""
        payload = self.jwt_manager.verify_token(token)
        if not payload:
            return False
        
        session_id = payload.get('session_id')
        if session_id and session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Invalidated session {session_id}")
            return True
        
        return False
    
    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a specific user"""
        sessions_to_remove = []
        
        for session_id, session_data in self.active_sessions.items():
            if session_data['user_id'] == user_id:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        logger.info(f"Invalidated {len(sessions_to_remove)} sessions for user {user_id}")
        return len(sessions_to_remove)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            # Check if session has been inactive for more than 7 days
            if (now - session_data['last_activity']).days > 7:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)


class RateLimiter:
    """Rate limiting for authentication attempts"""
    
    def __init__(self):
        self.attempts: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'count': 0, 'last_attempt': None})
        self.max_attempts = {
            'login': 5,
            'register': 3
        }
        self.lockout_duration = {
            'login': 15 * 60,  # 15 minutes
            'register': 30 * 60  # 30 minutes
        }
    
    def is_allowed(self, identifier: str, action: str) -> Tuple[bool, int]:
        """Check if an action is allowed for an identifier"""
        if action not in self.max_attempts:
            return True, 0
        
        now = time.time()
        attempt_data = self.attempts[f"{identifier}:{action}"]
        
        # Reset if enough time has passed
        if (attempt_data['last_attempt'] and 
            now - attempt_data['last_attempt'] > self.lockout_duration[action]):
            attempt_data['count'] = 0
            attempt_data['last_attempt'] = None
        
        # Check if exceeded max attempts
        if attempt_data['count'] >= self.max_attempts[action]:
            if attempt_data['last_attempt']:
                retry_after = int(self.lockout_duration[action] - (now - attempt_data['last_attempt']))
                return False, max(0, retry_after)
        
        return True, 0
    
    def record_attempt(self, identifier: str, action: str, success: bool = False):
        """Record an attempt"""
        now = time.time()
        attempt_data = self.attempts[f"{identifier}:{action}"]
        
        if success:
            # Reset on successful attempt
            attempt_data['count'] = 0
            attempt_data['last_attempt'] = None
        else:
            # Increment failed attempts
            attempt_data['count'] += 1
            attempt_data['last_attempt'] = now
    
    def clear_attempts(self, identifier: str, action: str):
        """Clear attempts for an identifier and action"""
        key = f"{identifier}:{action}"
        if key in self.attempts:
            del self.attempts[key]


class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123']
        if any(pattern in password.lower() for pattern in common_patterns):
            errors.append("Password contains common patterns")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, List[str]]:
        """Validate username"""
        errors = []
        
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if len(username) > 50:
            errors.append("Username must be less than 50 characters")
        
        if not username.replace('_', '').replace('-', '').isalnum():
            errors.append("Username can only contain letters, numbers, hyphens, and underscores")
        
        return len(errors) == 0, errors


# Streamlit decorators for authentication
def require_auth(func):
    """Decorator to require authentication for Streamlit pages"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            import streamlit as st
            if not st.session_state.get('authenticated', False):
                st.error("Authentication required")
                st.stop()
        except ImportError:
            # If streamlit is not available, skip the check
            pass
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """Decorator to require admin role for Streamlit pages"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            import streamlit as st
            if not st.session_state.get('authenticated', False):
                st.error("Authentication required")
                st.stop()
            
            user_info = st.session_state.get('user_info', {})
            if user_info.get('role') != 'administrator':
                st.error("Administrator access required")
                st.stop()
        except ImportError:
            # If streamlit is not available, skip the check
            pass
        
        return func(*args, **kwargs)
    return wrapper


# Helper functions for password operations
def hash_password(password: str) -> str:
    """Convenience function to hash password"""
    return PasswordManager.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Convenience function to verify password"""
    return PasswordManager.verify_password(password, hashed)
