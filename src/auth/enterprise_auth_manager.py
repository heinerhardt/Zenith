"""
Enterprise Authentication Manager for Zenith
Integrates with enterprise database schema, Argon2id password hashing,
RBAC system, and comprehensive audit logging.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
from enum import Enum
import secrets
import ipaddress

from .models import User, UserSession, UserRole, UserRegistrationRequest, UserLoginRequest
from ..utils.enterprise_security import (
    EnterpriseSecurityManager, get_enterprise_security_manager,
    PasswordPolicy, UserRole as EnterpriseUserRole
)
from ..utils.database_security import DatabaseSecurityManager, secure_database_connection
from ..database.enterprise_schema import EnterpriseDatabase
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationResult(Enum):
    """Authentication result codes"""
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_DISABLED = "account_disabled"
    PASSWORD_EXPIRED = "password_expired"
    MUST_CHANGE_PASSWORD = "must_change_password"
    TWO_FACTOR_REQUIRED = "two_factor_required"
    RATE_LIMITED = "rate_limited"
    SECURITY_LOCKOUT = "security_lockout"


class AuditEventType(Enum):
    """Audit event types for authentication"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    ROLE_CHANGED = "role_changed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    SESSION_EXPIRED = "session_expired"
    SECURITY_VIOLATION = "security_violation"


class EnterpriseUserStore:
    """Enterprise user data storage using SQLite database"""
    
    def __init__(self, database_path: str):
        """Initialize enterprise user store"""
        self.database_path = database_path
        self.security_manager = DatabaseSecurityManager()
        
        logger.info(f"Initialized enterprise user store with database: {database_path}")
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a new user and return user UUID"""
        try:
            with secure_database_connection(self.database_path) as conn:
                user_uuid = str(uuid.uuid4())
                
                conn.execute("""
                    INSERT INTO users 
                    (uuid, username, email, password_hash, password_algorithm, role_id, 
                     full_name, display_name, timezone, locale, is_active, is_verified,
                     must_change_password, created_by, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_uuid, user_data['username'], user_data['email'],
                    user_data['password_hash'], user_data.get('password_algorithm', 'argon2id'),
                    user_data['role_id'], user_data.get('full_name'),
                    user_data.get('display_name'), user_data.get('timezone', 'UTC'),
                    user_data.get('locale', 'en-US'), user_data.get('is_active', True),
                    user_data.get('is_verified', False), user_data.get('must_change_password', False),
                    user_data.get('created_by'), json.dumps(user_data.get('metadata', {}))
                ))
                
                conn.commit()
                logger.info(f"Created user: {user_data['username']} ({user_uuid})")
                return user_uuid
                
        except Exception as e:
            logger.error(f"Failed to create user {user_data.get('username')}: {e}")
            return None
    
    def get_user_by_id(self, user_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get user by ID (UUID or integer)"""
        try:
            with secure_database_connection(self.database_path) as conn:
                # Try by UUID first, then by integer ID
                if isinstance(user_id, str):
                    cursor = conn.execute("""
                        SELECT u.*, r.name as role_name, r.permissions 
                        FROM users u 
                        JOIN roles r ON u.role_id = r.id 
                        WHERE u.uuid = ? OR u.id = ?
                    """, (user_id, user_id))
                else:
                    cursor = conn.execute("""
                        SELECT u.*, r.name as role_name, r.permissions 
                        FROM users u 
                        JOIN roles r ON u.role_id = r.id 
                        WHERE u.id = ?
                    """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_user_dict(row)
                
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT u.*, r.name as role_name, r.permissions 
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    WHERE u.username = ? AND u.is_active = TRUE
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_user_dict(row)
                
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
        
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT u.*, r.name as role_name, r.permissions 
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    WHERE u.email = ? AND u.is_active = TRUE
                """, (email,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_user_dict(row)
                
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
        
        return None
    
    def update_user(self, user_uuid: str, updates: Dict[str, Any]) -> bool:
        """Update user information"""
        try:
            with secure_database_connection(self.database_path) as conn:
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for field, value in updates.items():
                    if field in ['username', 'email', 'password_hash', 'password_algorithm',
                               'full_name', 'display_name', 'timezone', 'locale', 'is_active',
                               'is_verified', 'last_login', 'last_password_change', 'password_expires_at',
                               'failed_login_attempts', 'locked_until', 'must_change_password',
                               'two_factor_enabled', 'updated_by']:
                        set_clauses.append(f"{field} = ?")
                        values.append(value)
                    elif field == 'metadata':
                        set_clauses.append("metadata = ?")
                        values.append(json.dumps(value))
                
                if not set_clauses:
                    return True
                
                # Add updated_at timestamp
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.append(user_uuid)
                
                query = f"""
                    UPDATE users 
                    SET {', '.join(set_clauses)}
                    WHERE uuid = ?
                """
                
                cursor = conn.execute(query, values)
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Updated user: {user_uuid}")
                
                return success
                
        except Exception as e:
            logger.error(f"Failed to update user {user_uuid}: {e}")
            return False
    
    def update_login_attempt(self, username: str, success: bool, ip_address: str = None) -> None:
        """Update login attempt tracking"""
        try:
            with secure_database_connection(self.database_path) as conn:
                if success:
                    # Reset failed attempts on successful login
                    conn.execute("""
                        UPDATE users 
                        SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                        WHERE username = ?
                    """, (username,))
                else:
                    # Increment failed attempts
                    conn.execute("""
                        UPDATE users 
                        SET failed_login_attempts = failed_login_attempts + 1
                        WHERE username = ?
                    """, (username,))
                    
                    # Check if account should be locked
                    cursor = conn.execute("""
                        SELECT failed_login_attempts FROM users WHERE username = ?
                    """, (username,))
                    
                    row = cursor.fetchone()
                    if row and row[0] >= 5:  # Lock after 5 failed attempts
                        lockout_time = datetime.now() + timedelta(minutes=30)
                        conn.execute("""
                            UPDATE users 
                            SET locked_until = ?
                            WHERE username = ?
                        """, (lockout_time, username))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update login attempt for {username}: {e}")
    
    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT locked_until FROM users 
                    WHERE username = ? AND locked_until > CURRENT_TIMESTAMP
                """, (username,))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error checking account lock for {username}: {e}")
            return False
    
    def get_role_id(self, role_name: str) -> Optional[int]:
        """Get role ID by name"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
                row = cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            logger.error(f"Error getting role ID for {role_name}: {e}")
            return None
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List users with pagination"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT u.*, r.name as role_name, r.permissions 
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    ORDER BY u.created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                return [self._row_to_user_dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def _row_to_user_dict(self, row) -> Dict[str, Any]:
        """Convert database row to user dictionary"""
        return {
            'id': row[0],
            'uuid': row[1],
            'username': row[2],
            'email': row[3],
            'password_hash': row[4],
            'password_algorithm': row[5],
            'salt': row[6],
            'role_id': row[7],
            'full_name': row[8],
            'display_name': row[9],
            'avatar_url': row[10],
            'timezone': row[11],
            'locale': row[12],
            'created_at': row[13],
            'updated_at': row[14],
            'last_login': row[15],
            'last_password_change': row[16],
            'password_expires_at': row[17],
            'is_active': bool(row[18]),
            'is_verified': bool(row[19]),
            'email_verified_at': row[20],
            'failed_login_attempts': row[21],
            'locked_until': row[22],
            'must_change_password': bool(row[23]),
            'two_factor_enabled': bool(row[24]),
            'role_name': row[-2],
            'permissions': json.loads(row[-1]) if row[-1] else []
        }


class EnterpriseAuditLogger:
    """Audit logging for authentication events"""
    
    def __init__(self, database_path: str):
        """Initialize audit logger"""
        self.database_path = database_path
    
    def log_auth_event(self, event_type: AuditEventType, user_id: Optional[str] = None,
                      username: Optional[str] = None, ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None, success: bool = True,
                      details: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None):
        """Log authentication event"""
        try:
            with secure_database_connection(self.database_path) as conn:
                event_id = str(uuid.uuid4())
                
                conn.execute("""
                    INSERT INTO audit_log 
                    (event_id, user_id, event_type, event_category, action, description,
                     ip_address, user_agent, success, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id, user_id, event_type.value, 'authentication',
                    event_type.value, f"Authentication event: {event_type.value}",
                    ip_address, user_agent, success, error_message,
                    json.dumps(details or {})
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log audit event {event_type}: {e}")
    
    def log_security_event(self, event_type: str, severity: str, user_id: Optional[str] = None,
                          ip_address: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log security event"""
        try:
            with secure_database_connection(self.database_path) as conn:
                event_id = str(uuid.uuid4())
                
                conn.execute("""
                    INSERT INTO security_events 
                    (event_id, user_id, event_type, severity, source_ip, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event_id, user_id, event_type, severity, ip_address,
                    json.dumps(details or {})
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log security event {event_type}: {e}")


class EnterpriseAuthenticationManager:
    """Enterprise authentication manager with full security features"""
    
    def __init__(self, database_path: str, password_policy: Optional[PasswordPolicy] = None):
        """Initialize enterprise authentication manager"""
        self.database_path = database_path
        self.user_store = EnterpriseUserStore(database_path)
        self.audit_logger = EnterpriseAuditLogger(database_path)
        
        # Initialize enterprise security
        self.security_manager = get_enterprise_security_manager()
        if password_policy:
            self.security_manager.password_manager.password_policy = password_policy
        
        # Rate limiting tracking
        self.rate_limit_attempts = {}
        self.rate_limit_window = timedelta(minutes=15)
        self.max_attempts_per_window = 5
        
        logger.info("Initialized enterprise authentication manager")
    
    def register_user(self, registration: UserRegistrationRequest,
                     ip_address: Optional[str] = None, created_by: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Register a new user with enterprise validation"""
        
        # Rate limiting check
        if ip_address and self._is_rate_limited(ip_address, 'register'):
            self.audit_logger.log_auth_event(
                AuditEventType.LOGIN_FAILURE, username=registration.username,
                ip_address=ip_address, success=False, error_message="Rate limited"
            )
            return False, "Too many registration attempts. Please try again later.", None
        
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
        
        # Validate password with enterprise policy
        is_valid, password_errors = self.security_manager.validate_new_password(
            registration.password, "new_user", registration.username
        )
        if not is_valid:
            return False, "; ".join(password_errors), None
        
        # Get role ID
        role_id = self.user_store.get_role_id(registration.role.value if hasattr(registration.role, 'value') else str(registration.role))
        if not role_id:
            return False, "Invalid role specified", None
        
        try:
            # Hash password with enterprise security
            password_hash = self.security_manager.hash_password(registration.password, "new_user")
            
            # Create user data
            user_data = {
                'username': registration.username,
                'email': registration.email,
                'password_hash': password_hash,
                'password_algorithm': 'argon2id',
                'role_id': role_id,
                'full_name': getattr(registration, 'full_name', None),
                'display_name': getattr(registration, 'display_name', registration.username),
                'is_active': True,
                'is_verified': False,
                'must_change_password': False,
                'created_by': created_by,
                'metadata': {}
            }
            
            user_uuid = self.user_store.create_user(user_data)
            if user_uuid:
                # Log successful registration
                self.audit_logger.log_auth_event(
                    AuditEventType.LOGIN_SUCCESS, user_id=user_uuid, 
                    username=registration.username, ip_address=ip_address,
                    details={'action': 'user_registration'}
                )
                
                logger.info(f"Registered new user: {registration.username}")
                return True, "User registered successfully", user_uuid
            else:
                return False, "Failed to create user account", None
                
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            return False, "Registration failed due to system error", None
    
    def authenticate_user(self, login_request: UserLoginRequest,
                         ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[AuthenticationResult, str, Optional[Dict[str, Any]]]:
        """Authenticate user with comprehensive security checks"""
        
        # Rate limiting check
        if ip_address and self._is_rate_limited(ip_address, 'login'):
            self.audit_logger.log_auth_event(
                AuditEventType.LOGIN_FAILURE, username=login_request.username_or_email,
                ip_address=ip_address, success=False, error_message="Rate limited"
            )
            return AuthenticationResult.RATE_LIMITED, "Too many login attempts. Please try again later.", None
        
        # Validate login data
        validation_errors = login_request.validate()
        if validation_errors:
            return AuthenticationResult.INVALID_CREDENTIALS, "; ".join(validation_errors), None
        
        # Find user by username or email
        user = self.user_store.get_user_by_username(login_request.username_or_email)
        if not user:
            user = self.user_store.get_user_by_email(login_request.username_or_email)
        
        if not user:
            self._record_failed_login(login_request.username_or_email, ip_address, "User not found")
            return AuthenticationResult.INVALID_CREDENTIALS, "Invalid username/email or password", None
        
        username = user['username']
        user_uuid = user['uuid']
        
        # Check if account is locked
        if self.user_store.is_account_locked(username):
            self.audit_logger.log_security_event(
                "login_attempt_locked_account", "warning", user_uuid, ip_address,
                {'username': username, 'attempt_ip': ip_address}
            )
            return AuthenticationResult.ACCOUNT_LOCKED, "Account is temporarily locked", None
        
        # Check if account is active
        if not user['is_active']:
            self.audit_logger.log_security_event(
                "login_attempt_disabled_account", "warning", user_uuid, ip_address,
                {'username': username}
            )
            return AuthenticationResult.ACCOUNT_DISABLED, "Account is disabled", None
        
        # Verify password
        if not self.security_manager.verify_password(login_request.password, user['password_hash']):
            self._record_failed_login(username, ip_address, "Invalid password", user_uuid)
            return AuthenticationResult.INVALID_CREDENTIALS, "Invalid username/email or password", None
        
        # Check if password needs to be changed
        if user['must_change_password']:
            return AuthenticationResult.MUST_CHANGE_PASSWORD, "Password must be changed", {'user_uuid': user_uuid}
        
        # Check password expiration
        if user['password_expires_at'] and datetime.fromisoformat(user['password_expires_at'].replace('Z', '+00:00')) < datetime.now():
            return AuthenticationResult.PASSWORD_EXPIRED, "Password has expired", {'user_uuid': user_uuid}
        
        # Check if password hash needs upgrading
        if self.security_manager.needs_password_rehash(user['password_hash']):
            # Upgrade password hash in background
            try:
                new_hash = self.security_manager.hash_password(login_request.password, user_uuid)
                self.user_store.update_user(user_uuid, {
                    'password_hash': new_hash,
                    'password_algorithm': 'argon2id'
                })
                logger.info(f"Upgraded password hash for user: {username}")
            except Exception as e:
                logger.warning(f"Failed to upgrade password hash for {username}: {e}")
        
        # Record successful login
        self.user_store.update_login_attempt(username, True, ip_address)
        
        # Create session token
        try:
            session_data = self._create_user_session(user, ip_address, user_agent)
            
            # Log successful authentication
            self.audit_logger.log_auth_event(
                AuditEventType.LOGIN_SUCCESS, user_id=user_uuid, username=username,
                ip_address=ip_address, user_agent=user_agent,
                details={'session_id': session_data['session_id']}
            )
            
            # Clear rate limiting on successful login
            if ip_address:
                self._clear_rate_limit(ip_address, 'login')
            
            logger.info(f"User authenticated successfully: {username}")
            return AuthenticationResult.SUCCESS, "Authentication successful", session_data
            
        except Exception as e:
            logger.error(f"Failed to create session for {username}: {e}")
            return AuthenticationResult.INVALID_CREDENTIALS, "Authentication failed", None
    
    def _record_failed_login(self, username: str, ip_address: Optional[str], reason: str, user_uuid: Optional[str] = None):
        """Record failed login attempt"""
        self.user_store.update_login_attempt(username, False, ip_address)
        
        self.audit_logger.log_auth_event(
            AuditEventType.LOGIN_FAILURE, user_id=user_uuid, username=username,
            ip_address=ip_address, success=False, error_message=reason
        )
        
        # Update rate limiting
        if ip_address:
            self._record_rate_limit_attempt(ip_address, 'login')
    
    def _create_user_session(self, user: Dict[str, Any], ip_address: Optional[str], user_agent: Optional[str]) -> Dict[str, Any]:
        """Create user session with enterprise security"""
        session_id = secrets.token_urlsafe(32)
        token = self.security_manager.session_manager.create_session(
            user_id=user['uuid'],
            username=user['username'],
            role=user['role_name'],
            ip_address=ip_address,
            user_agent=user_agent,
            duration_hours=24
        )
        
        # Store session in database
        with secure_database_connection(self.database_path) as conn:
            conn.execute("""
                INSERT INTO user_sessions 
                (session_id, user_id, token_hash, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id, user['id'], 
                hashlib.sha256(token.encode()).hexdigest(),
                ip_address, user_agent,
                datetime.now() + timedelta(hours=24)
            ))
            conn.commit()
        
        return {
            'token': token,
            'session_id': session_id,
            'user': {
                'uuid': user['uuid'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role_name'],
                'permissions': user['permissions']
            }
        }
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate user session token"""
        return self.security_manager.session_manager.validate_session(token)
    
    def logout_user(self, token: str) -> bool:
        """Logout user and invalidate session"""
        payload = self.validate_session(token)
        if payload:
            self.audit_logger.log_auth_event(
                AuditEventType.LOGOUT, user_id=payload.get('user_id'),
                username=payload.get('username')
            )
        
        return self.security_manager.session_manager.invalidate_session(token)
    
    def change_password(self, user_uuid: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password with enterprise validation"""
        user = self.user_store.get_user_by_id(user_uuid)
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.security_manager.verify_password(old_password, user['password_hash']):
            self.audit_logger.log_security_event(
                "password_change_invalid_old", "warning", user_uuid,
                details={'username': user['username']}
            )
            return False, "Current password is incorrect"
        
        # Validate new password with enterprise policy
        is_valid, errors = self.security_manager.validate_new_password(
            new_password, user_uuid, user['username']
        )
        if not is_valid:
            return False, "; ".join(errors)
        
        try:
            # Hash new password
            new_hash = self.security_manager.hash_password(new_password, user_uuid)
            
            # Update password
            success = self.user_store.update_user(user_uuid, {
                'password_hash': new_hash,
                'password_algorithm': 'argon2id',
                'last_password_change': datetime.now(),
                'must_change_password': False
            })
            
            if success:
                # Invalidate all user sessions
                self.security_manager.session_manager.invalidate_all_user_sessions(user_uuid)
                
                # Log password change
                self.audit_logger.log_auth_event(
                    AuditEventType.PASSWORD_CHANGE, user_id=user_uuid,
                    username=user['username']
                )
                
                logger.info(f"Password changed for user: {user['username']}")
                return True, "Password changed successfully"
            else:
                return False, "Failed to update password"
                
        except Exception as e:
            logger.error(f"Password change failed for {user['username']}: {e}")
            return False, "Password change failed"
    
    def _is_rate_limited(self, ip_address: str, action: str) -> bool:
        """Check if IP is rate limited for action"""
        key = f"{ip_address}:{action}"
        now = datetime.now()
        
        if key in self.rate_limit_attempts:
            attempts = self.rate_limit_attempts[key]
            # Remove old attempts outside window
            attempts[:] = [attempt for attempt in attempts if now - attempt < self.rate_limit_window]
            
            return len(attempts) >= self.max_attempts_per_window
        
        return False
    
    def _record_rate_limit_attempt(self, ip_address: str, action: str):
        """Record rate limit attempt"""
        key = f"{ip_address}:{action}"
        now = datetime.now()
        
        if key not in self.rate_limit_attempts:
            self.rate_limit_attempts[key] = []
        
        self.rate_limit_attempts[key].append(now)
    
    def _clear_rate_limit(self, ip_address: str, action: str):
        """Clear rate limit for IP and action"""
        key = f"{ip_address}:{action}"
        if key in self.rate_limit_attempts:
            del self.rate_limit_attempts[key]


# Global enterprise auth manager instance
_enterprise_auth_manager: Optional[EnterpriseAuthenticationManager] = None


def get_enterprise_auth_manager(database_path: str = None) -> EnterpriseAuthenticationManager:
    """Get global enterprise authentication manager instance"""
    global _enterprise_auth_manager
    
    if _enterprise_auth_manager is None:
        if database_path is None:
            raise ValueError("Database path required for first initialization")
        _enterprise_auth_manager = EnterpriseAuthenticationManager(database_path)
    
    return _enterprise_auth_manager


def initialize_enterprise_auth(database_path: str, password_policy: Optional[PasswordPolicy] = None):
    """Initialize enterprise authentication system"""
    global _enterprise_auth_manager
    
    _enterprise_auth_manager = EnterpriseAuthenticationManager(database_path, password_policy)
    logger.info("Enterprise authentication system initialized")