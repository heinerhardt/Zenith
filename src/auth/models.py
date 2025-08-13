"""
User Models and Schemas for Zenith Authentication System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid
import hashlib


class UserRole(Enum):
    """User roles enumeration"""
    ADMINISTRATOR = "administrator"
    CHAT_USER = "chat_user"


@dataclass
class User:
    """User model for Zenith application"""
    id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    @classmethod
    def create_new_user(cls, username: str, email: str, password_hash: str, 
                       role: UserRole, full_name: Optional[str] = None) -> 'User':
        """Create a new user instance"""
        return cls(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            created_at=datetime.now(),
            full_name=full_name,
            preferences=cls.get_default_preferences(role)
        )
    
    @staticmethod
    def get_default_preferences(role: UserRole) -> Dict[str, Any]:
        """Get default preferences based on user role"""
        base_preferences = {
            'theme': 'light',
            'language': 'en',
            'chat_history_limit': 50,
            'file_upload_notifications': True
        }
        
        if role == UserRole.ADMINISTRATOR:
            base_preferences.update({
                'admin_notifications': True,
                'system_monitoring': True,
                'user_management_access': True
            })
        
        return base_preferences
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.now()
    
    def is_admin(self) -> bool:
        """Check if user is an administrator"""
        return self.role == UserRole.ADMINISTRATOR
    
    def is_chat_user(self) -> bool:
        """Check if user is a chat user"""
        return self.role == UserRole.CHAT_USER
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for storage"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role.value,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.preferences,
            'is_active': self.is_active,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary"""
        return cls(
            id=data['id'],
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            role=UserRole(data['role']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            preferences=data.get('preferences', {}),
            is_active=data.get('is_active', True),
            full_name=data.get('full_name'),
            avatar_url=data.get('avatar_url')
        )


@dataclass
class UserSession:
    """User session model"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    last_activity: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    @classmethod
    def create_new_session(cls, user_id: str, duration_hours: int = 24,
                          ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None) -> 'UserSession':
        """Create a new user session"""
        now = datetime.now()
        return cls(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=now,
            expires_at=now.replace(hour=now.hour + duration_hours),
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """Create session from dictionary"""
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            is_active=data.get('is_active', True),
            last_activity=datetime.fromisoformat(data['last_activity']) if data.get('last_activity') else None,
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent')
        )


@dataclass
class UserDocument:
    """User document model for tracking uploaded documents"""
    id: str
    user_id: str
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    processing_status: str = "pending"  # pending, processing, completed, failed
    chunk_count: int = 0
    source_type: str = "upload"  # upload, minio
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    @classmethod
    def create_new_document(cls, user_id: str, filename: str, original_filename: str,
                          file_size: int, source_type: str = "upload",
                          source_metadata: Optional[Dict[str, Any]] = None) -> 'UserDocument':
        """Create a new document record"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            uploaded_at=datetime.now(),
            source_type=source_type,
            source_metadata=source_metadata or {}
        )
    
    def mark_processing_started(self):
        """Mark document as processing"""
        self.processing_status = "processing"
    
    def mark_processing_completed(self, chunk_count: int):
        """Mark document as processed"""
        self.processing_status = "completed"
        self.processed_at = datetime.now()
        self.chunk_count = chunk_count
    
    def mark_processing_failed(self):
        """Mark document processing as failed"""
        self.processing_status = "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processing_status': self.processing_status,
            'chunk_count': self.chunk_count,
            'source_type': self.source_type,
            'source_metadata': self.source_metadata,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserDocument':
        """Create document from dictionary"""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            filename=data['filename'],
            original_filename=data['original_filename'],
            file_size=data['file_size'],
            uploaded_at=datetime.fromisoformat(data['uploaded_at']),
            processed_at=datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None,
            processing_status=data.get('processing_status', 'pending'),
            chunk_count=data.get('chunk_count', 0),
            source_type=data.get('source_type', 'upload'),
            source_metadata=data.get('source_metadata', {}),
            is_active=data.get('is_active', True)
        )


@dataclass
class SystemSettings:
    """System settings model"""
    id: str = "system_settings"
    
    # Model Configuration
    openai_api_key: Optional[str] = None
    openai_chat_model: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-ada-002"
    
    # Ollama Configuration
    ollama_enabled: bool = False
    ollama_endpoint: str = "http://localhost:11434"
    ollama_chat_model: str = "llama2"
    ollama_embedding_model: str = "nomic-embed-text"
    
    # Model Selection (Admin settings override .env)
    preferred_chat_provider: str = "openai"
    preferred_embedding_provider: str = "openai"
    
    # Langsmith Configuration
    langsmith_enabled: bool = False
    langsmith_api_key: Optional[str] = None
    langsmith_project_name: str = "zenith-pdf-chatbot"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_tracing_enabled: bool = True
    langsmith_evaluation_enabled: bool = False
    
    # Qdrant Configuration
    qdrant_mode: str = "cloud"  # local or cloud
    qdrant_cloud_url: Optional[str] = None
    qdrant_cloud_api_key: Optional[str] = None
    qdrant_local_host: str = "localhost"
    qdrant_local_port: int = 6333
    qdrant_collection_name: str = "zenith_documents"
    
    # Processing Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_query: int = 5
    max_file_size_mb: int = 50
    
    # MinIO Configuration
    minio_enabled: bool = False
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    minio_secure: bool = False
    
    def get_effective_chat_provider(self) -> str:
        """
        Get the effective chat provider with priority logic:
        1. If Ollama is enabled in settings, use Ollama
        2. Otherwise, use the preferred setting
        """
        if self.ollama_enabled:
            return "ollama"
        return self.preferred_chat_provider
    
    def get_effective_embedding_provider(self) -> str:
        """
        Get the effective embedding provider with priority logic:
        1. If Ollama is enabled in settings, use Ollama
        2. Otherwise, use the preferred setting
        """
        if self.ollama_enabled:
            return "ollama"
        return self.preferred_embedding_provider
    
    def is_ollama_enabled(self) -> bool:
        """Check if Ollama is enabled in settings"""
        return self.ollama_enabled
    
    def is_langsmith_enabled(self) -> bool:
        """Check if Langsmith is enabled in settings"""
        return self.langsmith_enabled
    
    # System Configuration
    allow_user_registration: bool = True
    require_admin_approval: bool = False
    session_duration_hours: int = 24
    max_users: int = 100
    
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemSettings':
        """Create settings from dictionary"""
        # Handle datetime fields
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)


# Validation schemas
class UserRegistrationRequest:
    """User registration request validation"""
    
    def __init__(self, username: str, email: str, password: str, 
                 full_name: Optional[str] = None, role: str = "chat_user"):
        self.username = username.strip()
        self.email = email.strip().lower()
        self.password = password
        self.full_name = full_name.strip() if full_name else None
        self.role = UserRole(role)
    
    def validate(self) -> List[str]:
        """Validate registration request"""
        errors = []
        
        # Username validation
        if not self.username or len(self.username) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if not self.username.replace('_', '').replace('-', '').isalnum():
            errors.append("Username can only contain letters, numbers, hyphens, and underscores")
        
        # Email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            errors.append("Invalid email address format")
        
        # Password validation
        if not self.password or len(self.password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in self.password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in self.password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in self.password):
            errors.append("Password must contain at least one number")
        
        return errors


class UserLoginRequest:
    """User login request validation"""
    
    def __init__(self, username_or_email: str, password: str):
        self.username_or_email = username_or_email.strip().lower()
        self.password = password
    
    def validate(self) -> List[str]:
        """Validate login request"""
        errors = []
        
        if not self.username_or_email:
            errors.append("Username or email is required")
        
        if not self.password:
            errors.append("Password is required")
        
        return errors
