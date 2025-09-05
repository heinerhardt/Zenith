"""
Enterprise Database Schema for Zenith
Comprehensive SQLite schema with enterprise security features, audit logging,
and role-based access control following the setup specification.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from pathlib import Path
import uuid

from ..utils.logger import get_logger
from ..utils.database_security import DatabaseSecurityManager, secure_database_connection

logger = get_logger(__name__)


class UserRole(Enum):
    """User roles for RBAC system"""
    SUPER_ADMIN = "super_admin"
    ADMINISTRATOR = "administrator"
    OPERATOR = "operator"
    USER = "user"
    READ_ONLY = "read_only"


class DatabaseSchema:
    """Enterprise database schema definitions and management"""
    
    # Schema version for migrations
    CURRENT_SCHEMA_VERSION = 1
    
    @classmethod
    def get_create_statements(cls) -> List[str]:
        """Get all CREATE statements for the enterprise schema"""
        
        statements = [
            # Schema version tracking
            cls._get_schema_version_table(),
            
            # Role-based access control tables
            cls._get_roles_table(),
            cls._get_permissions_table(),
            cls._get_role_permissions_table(),
            
            # Enhanced users table
            cls._get_users_table(),
            cls._get_user_sessions_table(),
            cls._get_password_history_table(),
            
            # Chat and document management
            cls._get_chat_sessions_table(),
            cls._get_chat_history_table(),
            cls._get_documents_table(),
            cls._get_document_chunks_table(),
            
            # Configuration and settings
            cls._get_system_settings_table(),
            cls._get_user_preferences_table(),
            
            # Security and audit
            cls._get_audit_log_table(),
            cls._get_security_events_table(),
            cls._get_api_keys_table(),
            
            # Indexes for performance
            *cls._get_index_statements()
        ]
        
        return statements
    
    @classmethod
    def _get_schema_version_table(cls) -> str:
        """Schema version tracking table"""
        return """
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY,
            version INTEGER NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            checksum TEXT
        );
        """
    
    @classmethod
    def _get_roles_table(cls) -> str:
        """Roles table for RBAC"""
        return """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) UNIQUE NOT NULL,
            display_name VARCHAR(100),
            description TEXT,
            permissions JSON NOT NULL DEFAULT '[]',
            is_system_role BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_permissions_table(cls) -> str:
        """Permissions table for granular access control"""
        return """
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            display_name VARCHAR(150),
            description TEXT,
            resource VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            is_system_permission BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    
    @classmethod
    def _get_role_permissions_table(cls) -> str:
        """Role-permission junction table"""
        return """
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            granted_by INTEGER,
            UNIQUE(role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
            FOREIGN KEY (granted_by) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_users_table(cls) -> str:
        """Comprehensive users table with enterprise features"""
        return """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid VARCHAR(36) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            password_algorithm VARCHAR(20) DEFAULT 'bcrypt',
            salt VARCHAR(32),
            role_id INTEGER NOT NULL,
            full_name VARCHAR(150),
            display_name VARCHAR(100),
            avatar_url VARCHAR(500),
            timezone VARCHAR(50) DEFAULT 'UTC',
            locale VARCHAR(10) DEFAULT 'en-US',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            last_password_change DATETIME DEFAULT CURRENT_TIMESTAMP,
            password_expires_at DATETIME,
            is_active BOOLEAN DEFAULT TRUE,
            is_verified BOOLEAN DEFAULT FALSE,
            email_verified_at DATETIME,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until DATETIME,
            must_change_password BOOLEAN DEFAULT FALSE,
            two_factor_enabled BOOLEAN DEFAULT FALSE,
            two_factor_secret VARCHAR(32),
            backup_codes JSON,
            login_notification_enabled BOOLEAN DEFAULT TRUE,
            session_timeout_minutes INTEGER DEFAULT 1440,
            created_by INTEGER,
            updated_by INTEGER,
            metadata JSON DEFAULT '{}',
            FOREIGN KEY (role_id) REFERENCES roles(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_user_sessions_table(cls) -> str:
        """User sessions table for session management"""
        return """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(64) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            token_hash VARCHAR(255) NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            device_fingerprint VARCHAR(255),
            location_info JSON,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    
    @classmethod
    def _get_password_history_table(cls) -> str:
        """Password history for preventing reuse"""
        return """
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            password_algorithm VARCHAR(20) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    
    @classmethod
    def _get_chat_sessions_table(cls) -> str:
        """Chat sessions for organizing conversations"""
        return """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(36) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            title VARCHAR(200),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_message_at DATETIME,
            is_archived BOOLEAN DEFAULT FALSE,
            is_shared BOOLEAN DEFAULT FALSE,
            share_token VARCHAR(64),
            share_expires_at DATETIME,
            message_count INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            metadata JSON DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    
    @classmethod
    def _get_chat_history_table(cls) -> str:
        """Enhanced chat history with privacy controls"""
        return """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message_id VARCHAR(36) UNIQUE NOT NULL,
            parent_message_id VARCHAR(36),
            message_content TEXT NOT NULL,
            message_type ENUM('user', 'assistant', 'system') NOT NULL,
            model_name VARCHAR(100),
            provider VARCHAR(50),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            token_count INTEGER,
            processing_time_ms INTEGER,
            is_deleted BOOLEAN DEFAULT FALSE,
            deleted_at DATETIME,
            deleted_by INTEGER,
            is_edited BOOLEAN DEFAULT FALSE,
            edit_count INTEGER DEFAULT 0,
            last_edited_at DATETIME,
            feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
            feedback_comment TEXT,
            source_documents JSON,
            retrieval_context JSON,
            metadata JSON DEFAULT '{}',
            FOREIGN KEY (chat_session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (deleted_by) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_documents_table(cls) -> str:
        """Documents table for uploaded files"""
        return """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id VARCHAR(36) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            upload_status VARCHAR(20) DEFAULT 'uploaded',
            processing_status VARCHAR(20) DEFAULT 'pending',
            chunk_count INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            upload_started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            upload_completed_at DATETIME,
            processing_started_at DATETIME,
            processing_completed_at DATETIME,
            last_accessed_at DATETIME,
            access_count INTEGER DEFAULT 0,
            is_public BOOLEAN DEFAULT FALSE,
            is_archived BOOLEAN DEFAULT FALSE,
            tags JSON DEFAULT '[]',
            metadata JSON DEFAULT '{}',
            error_message TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    
    @classmethod
    def _get_document_chunks_table(cls) -> str:
        """Document chunks for vector search"""
        return """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id VARCHAR(36) UNIQUE NOT NULL,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            token_count INTEGER NOT NULL,
            page_number INTEGER,
            section_title VARCHAR(200),
            chunk_type VARCHAR(50) DEFAULT 'text',
            vector_id VARCHAR(100),
            embedding_model VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata JSON DEFAULT '{}',
            UNIQUE(document_id, chunk_index),
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        """
    
    @classmethod
    def _get_system_settings_table(cls) -> str:
        """System-wide configuration settings"""
        return """
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) UNIQUE NOT NULL,
            value TEXT,
            value_type VARCHAR(20) DEFAULT 'string',
            description TEXT,
            is_secret BOOLEAN DEFAULT FALSE,
            is_readonly BOOLEAN DEFAULT FALSE,
            validation_rule TEXT,
            category VARCHAR(50) DEFAULT 'general',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            FOREIGN KEY (updated_by) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_user_preferences_table(cls) -> str:
        """User-specific preferences and settings"""
        return """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key VARCHAR(100) NOT NULL,
            value TEXT,
            value_type VARCHAR(20) DEFAULT 'string',
            category VARCHAR(50) DEFAULT 'general',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    
    @classmethod
    def _get_audit_log_table(cls) -> str:
        """Comprehensive audit logging"""
        return """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id VARCHAR(36) UNIQUE NOT NULL,
            user_id INTEGER,
            session_id VARCHAR(64),
            event_type VARCHAR(50) NOT NULL,
            event_category VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(100),
            action VARCHAR(100) NOT NULL,
            description TEXT,
            ip_address VARCHAR(45),
            user_agent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            severity VARCHAR(20) DEFAULT 'info',
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            request_data JSON,
            response_data JSON,
            metadata JSON DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_security_events_table(cls) -> str:
        """Security-specific event logging"""
        return """
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id VARCHAR(36) UNIQUE NOT NULL,
            user_id INTEGER,
            event_type VARCHAR(50) NOT NULL,
            event_subtype VARCHAR(50),
            severity VARCHAR(20) NOT NULL,
            source_ip VARCHAR(45),
            user_agent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details JSON,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at DATETIME,
            resolved_by INTEGER,
            investigation_notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (resolved_by) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_api_keys_table(cls) -> str:
        """API keys management"""
        return """
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id VARCHAR(36) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            key_hash VARCHAR(255) NOT NULL,
            key_prefix VARCHAR(10) NOT NULL,
            scopes JSON DEFAULT '[]',
            last_used_at DATETIME,
            usage_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            revoked_at DATETIME,
            revoked_by INTEGER,
            metadata JSON DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (revoked_by) REFERENCES users(id)
        );
        """
    
    @classmethod
    def _get_index_statements(cls) -> List[str]:
        """Performance indexes for the database"""
        return [
            # Users table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid);",
            "CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);",
            
            # User sessions indexes
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);",
            
            # Chat history indexes
            "CREATE INDEX IF NOT EXISTS idx_chat_history_chat_session_id ON chat_history(chat_session_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_chat_history_message_type ON chat_history(message_type);",
            
            # Chat sessions indexes
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);",
            
            # Documents indexes
            "CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_documents_document_id ON documents(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_documents_upload_status ON documents(upload_status);",
            "CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);",
            "CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);",
            
            # Document chunks indexes
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_id ON document_chunks(chunk_id);",
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_vector_id ON document_chunks(vector_id);",
            
            # Audit log indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_event_category ON audit_log(event_category);",
            
            # Security events indexes
            "CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);",
            "CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);",
            
            # Role and permissions indexes
            "CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);",
            "CREATE INDEX IF NOT EXISTS idx_permissions_name ON permissions(name);",
            "CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);",
            "CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);",
            "CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);",
            
            # System settings indexes
            "CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);",
            "CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);",
            
            # User preferences indexes
            "CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(key);",
            "CREATE INDEX IF NOT EXISTS idx_user_preferences_category ON user_preferences(category);"
        ]


class EnterpriseDatabase:
    """Enterprise database management with migrations and security"""
    
    def __init__(self, database_path: str):
        """Initialize enterprise database manager"""
        self.database_path = Path(database_path)
        self.security_manager = DatabaseSecurityManager()
        
        # Ensure database directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized enterprise database manager for {database_path}")
    
    def initialize_database(self) -> bool:
        """Initialize database with enterprise schema"""
        try:
            with secure_database_connection(str(self.database_path)) as conn:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA cache_size=10000;")
                conn.execute("PRAGMA foreign_keys=ON;")
                
                # Create all tables
                create_statements = DatabaseSchema.get_create_statements()
                
                for statement in create_statements:
                    conn.execute(statement)
                
                # Insert initial schema version
                self._update_schema_version(conn, DatabaseSchema.CURRENT_SCHEMA_VERSION, 
                                          "Initial enterprise schema")
                
                # Create default roles
                self._create_default_roles(conn)
                
                # Create default permissions
                self._create_default_permissions(conn)
                
                conn.commit()
                
            logger.info("Enterprise database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize enterprise database: {e}")
            return False
    
    def get_current_schema_version(self) -> int:
        """Get current database schema version"""
        try:
            with secure_database_connection(str(self.database_path)) as conn:
                cursor = conn.execute(
                    "SELECT MAX(version) FROM schema_version WHERE version IS NOT NULL"
                )
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
                
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return 0
        except Exception as e:
            logger.error(f"Error getting schema version: {e}")
            return 0
    
    def _update_schema_version(self, conn: sqlite3.Connection, version: int, description: str):
        """Update schema version tracking"""
        conn.execute("""
            INSERT INTO schema_version (version, description, checksum) 
            VALUES (?, ?, ?)
        """, (version, description, self._calculate_schema_checksum()))
    
    def _calculate_schema_checksum(self) -> str:
        """Calculate checksum of current schema"""
        import hashlib
        schema_sql = ''.join(DatabaseSchema.get_create_statements())
        return hashlib.sha256(schema_sql.encode()).hexdigest()
    
    def _create_default_roles(self, conn: sqlite3.Connection):
        """Create default system roles"""
        default_roles = [
            {
                'name': UserRole.SUPER_ADMIN.value,
                'display_name': 'Super Administrator',
                'description': 'Full system access with all permissions',
                'permissions': ['*'],
                'is_system_role': True
            },
            {
                'name': UserRole.ADMINISTRATOR.value,
                'display_name': 'Administrator',
                'description': 'System administration with user management',
                'permissions': [
                    'user_management', 'system_configuration', 
                    'deployment_management', 'audit_access'
                ],
                'is_system_role': True
            },
            {
                'name': UserRole.OPERATOR.value,
                'display_name': 'Operator',
                'description': 'System monitoring and basic configuration',
                'permissions': [
                    'system_monitoring', 'basic_configuration', 
                    'chat_access', 'document_upload'
                ],
                'is_system_role': True
            },
            {
                'name': UserRole.USER.value,
                'display_name': 'User',
                'description': 'Standard user with chat and document access',
                'permissions': ['chat_access', 'document_upload', 'profile_management'],
                'is_system_role': True
            },
            {
                'name': UserRole.READ_ONLY.value,
                'display_name': 'Read Only',
                'description': 'Read-only access to chat history',
                'permissions': ['chat_read_only'],
                'is_system_role': True
            }
        ]
        
        for role in default_roles:
            conn.execute("""
                INSERT OR IGNORE INTO roles 
                (name, display_name, description, permissions, is_system_role)
                VALUES (?, ?, ?, ?, ?)
            """, (
                role['name'], role['display_name'], role['description'],
                json.dumps(role['permissions']), role['is_system_role']
            ))
    
    def _create_default_permissions(self, conn: sqlite3.Connection):
        """Create default system permissions"""
        default_permissions = [
            # User management
            ('user_create', 'Create Users', 'Create new user accounts', 'users', 'create'),
            ('user_read', 'Read Users', 'View user information', 'users', 'read'),
            ('user_update', 'Update Users', 'Modify user accounts', 'users', 'update'),
            ('user_delete', 'Delete Users', 'Remove user accounts', 'users', 'delete'),
            ('user_management', 'User Management', 'Full user management access', 'users', '*'),
            
            # System configuration
            ('system_configuration', 'System Configuration', 'Modify system settings', 'system', 'configure'),
            ('basic_configuration', 'Basic Configuration', 'Basic system settings', 'system', 'basic_config'),
            ('system_monitoring', 'System Monitoring', 'View system status and metrics', 'system', 'monitor'),
            
            # Chat and messaging
            ('chat_access', 'Chat Access', 'Access to chat functionality', 'chat', 'access'),
            ('chat_read_only', 'Chat Read Only', 'Read-only access to chat history', 'chat', 'read'),
            ('chat_delete', 'Delete Chat', 'Delete chat messages and sessions', 'chat', 'delete'),
            
            # Document management
            ('document_upload', 'Document Upload', 'Upload and process documents', 'documents', 'upload'),
            ('document_read', 'Read Documents', 'View document content', 'documents', 'read'),
            ('document_delete', 'Delete Documents', 'Remove documents', 'documents', 'delete'),
            
            # Profile and preferences
            ('profile_management', 'Profile Management', 'Manage own profile', 'profile', 'manage'),
            
            # Deployment and operations
            ('deployment_management', 'Deployment Management', 'System deployment controls', 'deployment', 'manage'),
            
            # Audit and security
            ('audit_access', 'Audit Access', 'Access to audit logs', 'audit', 'read'),
            ('security_management', 'Security Management', 'Security configuration', 'security', 'manage'),
        ]
        
        for perm in default_permissions:
            conn.execute("""
                INSERT OR IGNORE INTO permissions 
                (name, display_name, description, resource, action, is_system_permission)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, perm)
    
    def create_admin_user(self, username: str, email: str, password_hash: str, 
                         full_name: str = "System Administrator") -> Optional[str]:
        """Create admin user and return user UUID"""
        try:
            with secure_database_connection(str(self.database_path)) as conn:
                # Get admin role ID
                cursor = conn.execute(
                    "SELECT id FROM roles WHERE name = ?", 
                    (UserRole.ADMINISTRATOR.value,)
                )
                role_result = cursor.fetchone()
                if not role_result:
                    logger.error("Administrator role not found")
                    return None
                
                role_id = role_result[0]
                user_uuid = str(uuid.uuid4())
                
                # Create admin user
                conn.execute("""
                    INSERT INTO users 
                    (uuid, username, email, password_hash, password_algorithm, role_id, 
                     full_name, is_active, is_verified, email_verified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, TRUE, TRUE, CURRENT_TIMESTAMP)
                """, (user_uuid, username, email, password_hash, 'argon2id', role_id, full_name))
                
                conn.commit()
                
                logger.info(f"Created admin user: {username}")
                return user_uuid
                
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        health_status = {
            'database_accessible': False,
            'schema_version': 0,
            'table_count': 0,
            'wal_mode_enabled': False,
            'foreign_keys_enabled': False,
            'total_size_bytes': 0,
            'errors': []
        }
        
        try:
            with secure_database_connection(str(self.database_path)) as conn:
                # Basic connectivity
                health_status['database_accessible'] = True
                
                # Schema version
                health_status['schema_version'] = self.get_current_schema_version()
                
                # Table count
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                )
                health_status['table_count'] = cursor.fetchone()[0]
                
                # WAL mode check
                cursor = conn.execute("PRAGMA journal_mode")
                health_status['wal_mode_enabled'] = cursor.fetchone()[0].upper() == 'WAL'
                
                # Foreign keys check
                cursor = conn.execute("PRAGMA foreign_keys")
                health_status['foreign_keys_enabled'] = bool(cursor.fetchone()[0])
                
                # Database size
                health_status['total_size_bytes'] = self.database_path.stat().st_size
                
        except Exception as e:
            health_status['errors'].append(str(e))
            logger.error(f"Database health check failed: {e}")
        
        return health_status