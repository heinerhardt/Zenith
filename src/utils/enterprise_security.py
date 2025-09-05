"""
Enterprise Security Module for Zenith
Implements enterprise-grade security features including Argon2id password hashing,
comprehensive password policies, and enhanced authentication systems.
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List, Union
from enum import Enum
import json

# Argon2 for enterprise password hashing
from argon2 import PasswordHasher, hash_password_raw
from argon2.exceptions import VerifyMismatchError, HashingError

# Backward compatibility with existing bcrypt
import bcrypt

# Existing security utilities
from .security import JWTManager, SessionManager, RateLimiter, SecurityValidator
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PasswordHashingAlgorithm(Enum):
    """Supported password hashing algorithms"""
    BCRYPT = "bcrypt"
    ARGON2ID = "argon2id"


class PasswordPolicy:
    """Enterprise password policy configuration"""
    
    def __init__(self, 
                 min_length: int = 8,
                 max_length: int = 128,
                 require_uppercase: bool = True,
                 require_lowercase: bool = True,
                 require_numbers: bool = True,
                 require_special_chars: bool = True,
                 min_special_chars: int = 1,
                 max_age_days: Optional[int] = 90,
                 prevent_reuse_count: int = 12,
                 complexity_score_min: int = 3):
        """
        Initialize password policy
        
        Args:
            min_length: Minimum password length
            max_length: Maximum password length  
            require_uppercase: Require uppercase letters
            require_lowercase: Require lowercase letters
            require_numbers: Require numeric characters
            require_special_chars: Require special characters
            min_special_chars: Minimum number of special characters
            max_age_days: Password expiration in days (None for no expiration)
            prevent_reuse_count: Number of previous passwords to prevent reuse
            complexity_score_min: Minimum complexity score (0-5)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_special_chars = require_special_chars
        self.min_special_chars = min_special_chars
        self.max_age_days = max_age_days
        self.prevent_reuse_count = prevent_reuse_count
        self.complexity_score_min = complexity_score_min
        
        # Special characters definition
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?~`"


class EnterprisePasswordManager:
    """
    Enterprise-grade password management with Argon2id and backward compatibility
    """
    
    def __init__(self, password_policy: Optional[PasswordPolicy] = None):
        """Initialize enterprise password manager"""
        self.password_policy = password_policy or PasswordPolicy()
        
        # Argon2 configuration following OWASP recommendations
        self.argon2_hasher = PasswordHasher(
            time_cost=3,      # 3 iterations (OWASP minimum for Argon2id)
            memory_cost=65536, # 64 MB memory (OWASP recommended minimum)
            parallelism=1,     # Single thread for consistency
            hash_len=32,       # 32 byte hash length
            salt_len=16        # 16 byte salt length
        )
        
        # Algorithm version for future migration
        self.current_algorithm = PasswordHashingAlgorithm.ARGON2ID
        
        logger.info("Initialized enterprise password manager with Argon2id")
    
    def hash_password(self, password: str, 
                     algorithm: Optional[PasswordHashingAlgorithm] = None) -> str:
        """
        Hash password using specified algorithm (defaults to Argon2id)
        
        Args:
            password: Plain text password
            algorithm: Hashing algorithm to use
            
        Returns:
            Hashed password with algorithm prefix
        """
        if algorithm is None:
            algorithm = self.current_algorithm
        
        try:
            if algorithm == PasswordHashingAlgorithm.ARGON2ID:
                # Hash with Argon2id
                hashed = self.argon2_hasher.hash(password)
                return f"argon2id:{hashed}"
                
            elif algorithm == PasswordHashingAlgorithm.BCRYPT:
                # Fallback to bcrypt for backward compatibility
                salt = bcrypt.gensalt(rounds=12)  # Increased from default 10
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
                return f"bcrypt:{hashed.decode('utf-8')}"
            
            else:
                raise ValueError(f"Unsupported hashing algorithm: {algorithm}")
                
        except Exception as e:
            logger.error(f"Password hashing failed with {algorithm.value}: {e}")
            raise HashingError(f"Password hashing failed: {e}")
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash, detecting algorithm automatically
        
        Args:
            password: Plain text password
            hashed_password: Stored hash with algorithm prefix
            
        Returns:
            True if password matches hash
        """
        try:
            # Detect algorithm from prefix
            if hashed_password.startswith("argon2id:"):
                # Argon2id verification
                hash_without_prefix = hashed_password[9:]  # Remove "argon2id:" prefix
                try:
                    self.argon2_hasher.verify(hash_without_prefix, password)
                    return True
                except VerifyMismatchError:
                    return False
                    
            elif hashed_password.startswith("bcrypt:"):
                # bcrypt verification
                hash_without_prefix = hashed_password[7:]  # Remove "bcrypt:" prefix
                return bcrypt.checkpw(password.encode('utf-8'), 
                                    hash_without_prefix.encode('utf-8'))
            
            else:
                # Legacy hash without prefix - assume bcrypt for backward compatibility
                logger.warning("Password hash without algorithm prefix, assuming bcrypt")
                return bcrypt.checkpw(password.encode('utf-8'), 
                                    hashed_password.encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def needs_rehashing(self, hashed_password: str) -> bool:
        """
        Check if password hash needs to be upgraded to current algorithm
        
        Args:
            hashed_password: Stored hash with algorithm prefix
            
        Returns:
            True if hash should be upgraded
        """
        if hashed_password.startswith("argon2id:"):
            # Check if Argon2 parameters need updating
            hash_without_prefix = hashed_password[9:]
            return self.argon2_hasher.check_needs_rehash(hash_without_prefix)
            
        elif hashed_password.startswith("bcrypt:") or not hashed_password.startswith(("argon2id:", "bcrypt:")):
            # bcrypt or legacy hash - should be upgraded to Argon2id
            return True
        
        return False
    
    def validate_password_policy(self, password: str, 
                                username: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate password against enterprise policy
        
        Args:
            password: Password to validate
            username: Username for context-aware validation
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        policy = self.password_policy
        
        # Length validation
        if len(password) < policy.min_length:
            errors.append(f"Password must be at least {policy.min_length} characters long")
        
        if len(password) > policy.max_length:
            errors.append(f"Password must be no more than {policy.max_length} characters long")
        
        # Character class requirements
        if policy.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if policy.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if policy.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if policy.require_special_chars:
            special_count = sum(1 for c in password if c in policy.special_chars)
            if special_count < policy.min_special_chars:
                errors.append(f"Password must contain at least {policy.min_special_chars} special characters")
        
        # Complexity score validation
        complexity_score = self._calculate_complexity_score(password)
        if complexity_score < policy.complexity_score_min:
            errors.append(f"Password complexity score ({complexity_score}) below minimum ({policy.complexity_score_min})")
        
        # Username similarity check
        if username and self._contains_username(password, username):
            errors.append("Password must not contain username")
        
        # Common password patterns
        if self._contains_common_patterns(password):
            errors.append("Password contains common patterns or dictionary words")
        
        return len(errors) == 0, errors
    
    def generate_secure_password(self, length: int = 16, 
                                ensure_policy_compliance: bool = True) -> str:
        """
        Generate cryptographically secure password
        
        Args:
            length: Desired password length
            ensure_policy_compliance: Ensure generated password meets policy
            
        Returns:
            Secure password string
        """
        if length < self.password_policy.min_length:
            length = self.password_policy.min_length
        
        # Character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = self.password_policy.special_chars
        
        # Ensure at least one character from each required set
        password_chars = []
        
        if ensure_policy_compliance:
            if self.password_policy.require_lowercase:
                password_chars.append(secrets.choice(lowercase))
            if self.password_policy.require_uppercase:
                password_chars.append(secrets.choice(uppercase))
            if self.password_policy.require_numbers:
                password_chars.append(secrets.choice(digits))
            if self.password_policy.require_special_chars:
                for _ in range(self.password_policy.min_special_chars):
                    password_chars.append(secrets.choice(special))
        
        # Fill remaining length with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        remaining_length = length - len(password_chars)
        
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(all_chars))
        
        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password_chars)
        
        password = ''.join(password_chars)
        
        # Validate generated password
        if ensure_policy_compliance:
            is_valid, errors = self.validate_password_policy(password)
            if not is_valid:
                # Retry with different approach if validation fails
                logger.warning(f"Generated password failed validation: {errors}")
                return self.generate_secure_password(length + 2, ensure_policy_compliance)
        
        return password
    
    def _calculate_complexity_score(self, password: str) -> int:
        """Calculate password complexity score (0-5)"""
        score = 0
        
        # Length bonus
        if len(password) >= 12:
            score += 1
        
        # Character class diversity
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in self.password_policy.special_chars for c in password)
        
        score += sum([has_lower, has_upper, has_digit, has_special])
        
        return min(score, 5)
    
    def _contains_username(self, password: str, username: str) -> bool:
        """Check if password contains username (case-insensitive)"""
        if len(username) < 3:
            return False
        return username.lower() in password.lower()
    
    def _contains_common_patterns(self, password: str) -> bool:
        """Check for common password patterns"""
        password_lower = password.lower()
        
        # Common patterns and dictionary words
        common_patterns = [
            'password', 'admin', 'login', 'welcome', 'secret',
            '123456', 'qwerty', 'abc123', 'password1', 'admin123',
            '111111', '123123', 'welcome1', 'password!', 'admin!',
            'letmein', 'monkey', 'dragon', 'sunshine', 'princess',
        ]
        
        for pattern in common_patterns:
            if pattern in password_lower:
                return True
        
        # Sequential patterns
        sequences = ['123', '234', '345', '456', '567', '678', '789', '890',
                    'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij']
        
        for seq in sequences:
            if seq in password_lower or seq[::-1] in password_lower:
                return True
        
        # Repeated patterns
        if len(set(password)) < len(password) // 2:
            return True
        
        return False


class PasswordHistory:
    """Track password history to prevent reuse"""
    
    def __init__(self, max_history: int = 12):
        """Initialize password history tracker"""
        self.max_history = max_history
        self.histories: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_password(self, user_id: str, password_hash: str):
        """Add password to user's history"""
        if user_id not in self.histories:
            self.histories[user_id] = []
        
        history_entry = {
            'hash': password_hash,
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.histories[user_id].append(history_entry)
        
        # Trim history to max size
        if len(self.histories[user_id]) > self.max_history:
            self.histories[user_id] = self.histories[user_id][-self.max_history:]
    
    def is_password_reused(self, user_id: str, new_password: str, 
                          password_manager: EnterprisePasswordManager) -> bool:
        """Check if password was recently used"""
        if user_id not in self.histories:
            return False
        
        for history_entry in self.histories[user_id]:
            if password_manager.verify_password(new_password, history_entry['hash']):
                return True
        
        return False


class EnterpriseSecurityManager:
    """
    Comprehensive enterprise security manager
    Integrates password management, authentication, and security policies
    """
    
    def __init__(self, 
                 password_policy: Optional[PasswordPolicy] = None,
                 jwt_secret_key: Optional[str] = None):
        """Initialize enterprise security manager"""
        
        # Initialize components
        self.password_manager = EnterprisePasswordManager(password_policy)
        self.password_history = PasswordHistory()
        
        # JWT and session management
        if jwt_secret_key is None:
            jwt_secret_key = self._generate_jwt_secret()
        
        self.jwt_manager = JWTManager(jwt_secret_key)
        self.session_manager = SessionManager(self.jwt_manager)
        self.rate_limiter = RateLimiter()
        
        # Enhanced security validator
        self.security_validator = SecurityValidator()
        
        logger.info("Initialized enterprise security manager")
    
    def _generate_jwt_secret(self) -> str:
        """Generate secure JWT secret if not provided"""
        # In production, this should come from secure secret management
        return secrets.token_urlsafe(64)
    
    def hash_password(self, password: str, user_id: Optional[str] = None) -> str:
        """Hash password and update history if user_id provided"""
        hashed = self.password_manager.hash_password(password)
        
        if user_id:
            self.password_history.add_password(user_id, hashed)
        
        return hashed
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.password_manager.verify_password(password, hashed_password)
    
    def validate_new_password(self, password: str, user_id: str, 
                             username: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Comprehensive password validation including policy and history
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Check policy compliance
        is_valid, errors = self.password_manager.validate_password_policy(password, username)
        
        # Check password history
        if is_valid and self.password_history.is_password_reused(user_id, password, self.password_manager):
            is_valid = False
            errors.append("Password was recently used and cannot be reused")
        
        return is_valid, errors
    
    def needs_password_rehash(self, hashed_password: str) -> bool:
        """Check if stored password hash needs upgrading"""
        return self.password_manager.needs_rehashing(hashed_password)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate secure password meeting enterprise policy"""
        return self.password_manager.generate_secure_password(length)


# Global enterprise security instance
# Will be initialized by the application setup
_enterprise_security_manager: Optional[EnterpriseSecurityManager] = None


def get_enterprise_security_manager() -> EnterpriseSecurityManager:
    """Get global enterprise security manager instance"""
    global _enterprise_security_manager
    
    if _enterprise_security_manager is None:
        _enterprise_security_manager = EnterpriseSecurityManager()
    
    return _enterprise_security_manager


def initialize_enterprise_security(password_policy: Optional[PasswordPolicy] = None,
                                 jwt_secret_key: Optional[str] = None):
    """Initialize enterprise security with custom configuration"""
    global _enterprise_security_manager
    
    _enterprise_security_manager = EnterpriseSecurityManager(
        password_policy=password_policy,
        jwt_secret_key=jwt_secret_key
    )
    
    logger.info("Enterprise security system initialized")


# Convenience functions for backward compatibility
def enterprise_hash_password(password: str, user_id: Optional[str] = None) -> str:
    """Hash password using enterprise security manager"""
    return get_enterprise_security_manager().hash_password(password, user_id)


def enterprise_verify_password(password: str, hashed_password: str) -> bool:
    """Verify password using enterprise security manager"""
    return get_enterprise_security_manager().verify_password(password, hashed_password)