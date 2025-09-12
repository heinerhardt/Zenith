# 🗄️ Zenith Database Schema Analysis & Setup Plan

**Document Version:** 1.0  
**Date:** 2025-01-27  
**Status:** Implementation Ready

## 📊 Executive Summary

Zenith already has a **highly sophisticated enterprise-grade database schema** with comprehensive RBAC, audit logging, and security features. This document provides a complete analysis of the existing architecture and a development plan to consolidate and enhance the current system.

## 🏗️ Current Database Architecture

### ✅ Existing Enterprise Schema (`src/database/enterprise_schema.py`)

Your codebase contains a **production-ready database schema** with 15+ tables:

#### Core Tables Structure

```sql
-- RBAC System
roles                   -- User roles with permissions
permissions             -- Granular permission system  
role_permissions        -- Role-permission junction table

-- User Management
users                   -- Comprehensive user profiles with security features
user_sessions           -- Session management with device tracking
password_history        -- Password history for security policies

-- Chat System  
chat_sessions           -- Organized conversation management
chat_history            -- Message history with metadata and feedback

-- Document Management
documents               -- File upload and processing tracking
document_chunks         -- Vector search chunk management

-- Configuration & Settings
system_settings         -- Global system configuration
user_preferences        -- User-specific settings

-- Security & Audit
audit_log              -- Comprehensive audit trail
security_events        -- Security incident logging
api_keys               -- API key management

-- Schema Management
schema_version         -- Migration version tracking
```

#### Advanced Features

- **Role-Based Access Control (RBAC)**: Complete role and permission system
- **Security Features**: 2FA, password policies, session management, audit logging
- **Document Management**: File processing, chunking, vector integration
- **Performance Optimization**: 50+ indexes for query performance
- **Data Integrity**: Foreign keys, constraints, validation rules
- **Extensibility**: JSON fields for metadata and flexible configuration

### 🔄 Migration System (`src/database/migrations.py`)

**Robust Migration Framework:**
- ✅ Version-controlled schema changes
- ✅ Automatic backups before migrations  
- ✅ Rollback capabilities with validation
- ✅ Migration status tracking and error recovery
- ✅ Integrity checks and post-migration validation

## ❌ Identified Gaps & Issues

### 1. Configuration Management Issues

```python
# CURRENT PROBLEM: No centralized database path configuration
class Settings(BaseSettings):
    # Missing database_path field!
    # Database paths are hardcoded across components
    
# Database paths scattered across:
# - src/setup/enterprise_setup.py: "./data/enterprise/zenith.db" 
# - src/database/enterprise_schema.py: Hardcoded paths
# - Enterprise setup configs: Different default paths
```

### 2. Missing Schema Components

```sql
-- MISSING: Notifications system
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- MISSING: System health monitoring
CREATE TABLE system_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    metrics JSON DEFAULT '{}',
    last_check DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- MISSING: Enhanced file storage tracking
CREATE TABLE file_storage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id VARCHAR(36) UNIQUE NOT NULL,
    storage_type VARCHAR(50) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    metadata JSON DEFAULT '{}'
);
```

### 3. Setup Process Issues

- **Multiple Creation Paths**: `EnterpriseDatabase.initialize_database()`, migration system, setup scripts
- **Inconsistent Database Paths**: Hardcoded paths in different components
- **Missing Default Data**: No systematic default data population
- **No Health Validation**: Limited post-setup health checks

### 4. Integration Gaps

- **Environment Variable Loading**: Database path not in Settings class
- **Enterprise Setup**: Direct database calls instead of unified interface  
- **Startup Scripts**: Limited database validation
- **Error Handling**: Inconsistent error reporting across components

## 🎯 Comprehensive Development Plan

### Phase 1: Configuration Centralization

#### 1.1 Add Database Configuration to Settings

```python
# UPDATE: src/core/config.py
class Settings(BaseSettings):
    """Application configuration settings"""
    
    # ADD: Database Configuration Section
    database_path: str = Field(default="./data/enterprise/zenith.db", env="DATABASE_PATH")
    database_backup_dir: str = Field(default="./data/enterprise/backups", env="DATABASE_BACKUP_DIR")
    database_wal_mode: bool = Field(default=True, env="DATABASE_WAL_MODE")
    database_auto_backup: bool = Field(default=True, env="DATABASE_AUTO_BACKUP")
    database_max_connections: int = Field(default=10, env="DATABASE_MAX_CONNECTIONS")
    database_cache_size: int = Field(default=10000, env="DATABASE_CACHE_SIZE")
    database_foreign_keys: bool = Field(default=True, env="DATABASE_FOREIGN_KEYS")
    
    # Existing configuration...
    enable_auth: bool = Field(default=True, env="ENABLE_AUTH")
    # ... rest of settings
```

#### 1.2 Update Environment Variables

```env
# ADD TO .env.example
# Database Configuration  
DATABASE_PATH=./data/enterprise/zenith.db
DATABASE_BACKUP_DIR=./data/enterprise/backups
DATABASE_WAL_MODE=true
DATABASE_AUTO_BACKUP=true
DATABASE_MAX_CONNECTIONS=10
DATABASE_CACHE_SIZE=10000
DATABASE_FOREIGN_KEYS=true
```

### Phase 2: Unified Database Management Interface

#### 2.1 Create Database Manager

```python
# NEW FILE: src/database/database_manager.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
import sqlite3
from datetime import datetime

from .enterprise_schema import EnterpriseDatabase, DatabaseSchema
from .migrations import MigrationManager
from ..utils.database_security import secure_sqlite_connection
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass  
class DatabaseConfig:
    """Centralized database configuration"""
    path: str = "./data/enterprise/zenith.db"
    backup_dir: str = "./data/enterprise/backups"  
    wal_mode: bool = True
    auto_backup: bool = True
    max_connections: int = 10
    foreign_keys: bool = True
    cache_size: int = 10000

class DatabaseManager:
    """Unified database management interface"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.database_path = Path(self.config.path)
        self.migration_manager = MigrationManager(self.database_path)
        self.enterprise_db = EnterpriseDatabase(self.database_path)
    
    def initialize_database(self, force: bool = False) -> bool:
        """Complete database initialization with all components"""
        try:
            logger.info(f"Initializing database at {self.database_path}")
            
            # 1. Create directory structure
            self._ensure_directories()
            
            # 2. Check if database exists
            if self._database_exists() and not force:
                logger.info("Database exists, running migrations only")
                return self._run_migrations_only()
            
            # 3. Create backup if database exists and force=True
            if self._database_exists() and force:
                backup_path = self.backup_database()
                logger.info(f"Created backup before force recreation: {backup_path}")
            
            # 4. Initialize enterprise schema
            success = self.enterprise_db.initialize_database()
            if not success:
                logger.error("Failed to initialize enterprise schema")
                return False
            
            # 5. Run any pending migrations
            migration_success = self._run_migrations_only()
            if not migration_success:
                logger.error("Failed to run database migrations")
                return False
                
            # 6. Populate default data
            self._populate_default_data()
            
            # 7. Validate database health
            health_check = self.health_check()
            if not health_check.get('healthy', False):
                logger.error(f"Database health check failed: {health_check}")
                return False
            
            logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def _ensure_directories(self):
        """Create required directory structure"""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        logs_dir = self.database_path.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
    
    def _database_exists(self) -> bool:
        """Check if database file exists and has content"""
        if not self.database_path.exists():
            return False
            
        # Check if database has tables
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                return table_count > 0
        except:
            return False
    
    def _run_migrations_only(self) -> bool:
        """Run database migrations without full initialization"""
        try:
            return self.migration_manager.migrate_up()
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def backup_database(self) -> str:
        """Create database backup with timestamp"""
        if not self._database_exists():
            raise ValueError("Cannot backup non-existent database")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"zenith_backup_{timestamp}.db"
        backup_path = Path(self.config.backup_dir) / backup_filename
        
        # Copy database file
        import shutil
        shutil.copy2(self.database_path, backup_path)
        
        logger.info(f"Database backup created: {backup_path}")
        return str(backup_path)
    
    def _populate_default_data(self):
        """Populate essential default system data"""
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                
                # System settings
                default_settings = [
                    ('FIRST_SETUP', 'False', 'First-time setup completion flag', 'setup'),
                    ('SETUP_COMPLETED', 'True', 'System setup completed', 'setup'),
                    ('SCHEMA_VERSION', str(DatabaseSchema.CURRENT_SCHEMA_VERSION), 'Current database schema version', 'system'),
                    ('BACKUP_ENABLED', str(self.config.auto_backup).lower(), 'Automatic backup enabled', 'system'),
                    ('AUDIT_LOGGING', 'true', 'Audit logging enabled', 'security'),
                    ('SESSION_TIMEOUT', '1440', 'Default session timeout in minutes', 'security'),
                    ('PASSWORD_EXPIRY_DAYS', '90', 'Password expiration period', 'security'),
                    ('MAX_LOGIN_ATTEMPTS', '5', 'Maximum failed login attempts', 'security'),
                    ('LOCKOUT_DURATION', '30', 'Account lockout duration in minutes', 'security'),
                    ('DATABASE_INITIALIZED', datetime.now().isoformat(), 'Database initialization timestamp', 'system')
                ]
                
                for key, value, description, category in default_settings:
                    conn.execute("""
                        INSERT OR REPLACE INTO system_settings (key, value, description, category, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (key, value, description, category))
                
                conn.commit()
                logger.info("Default system data populated")
                
        except Exception as e:
            logger.error(f"Failed to populate default data: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_data = {
            'healthy': False,
            'checks': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check 1: Database file exists
            db_exists = self._database_exists()
            health_data['checks'].append({
                'name': 'Database File Exists',
                'passed': db_exists,
                'details': f"Path: {self.database_path}"
            })
            
            if not db_exists:
                return health_data
            
            with secure_sqlite_connection(self.database_path) as conn:
                
                # Check 2: Schema version
                try:
                    current_version = self.migration_manager.get_current_version()
                    expected_version = DatabaseSchema.CURRENT_SCHEMA_VERSION
                    version_ok = current_version >= expected_version
                    health_data['checks'].append({
                        'name': 'Schema Version',
                        'passed': version_ok,
                        'details': f"Current: {current_version}, Expected: {expected_version}"
                    })
                except Exception as e:
                    health_data['checks'].append({
                        'name': 'Schema Version',
                        'passed': False,
                        'details': f"Error: {e}"
                    })
                
                # Check 3: Required tables exist
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = set(row[0] for row in cursor.fetchall())
                
                required_tables = {
                    'users', 'roles', 'permissions', 'role_permissions',
                    'chat_sessions', 'chat_history', 'documents', 'document_chunks',
                    'system_settings', 'audit_log', 'security_events', 'schema_version'
                }
                
                missing_tables = required_tables - existing_tables
                tables_ok = len(missing_tables) == 0
                
                health_data['checks'].append({
                    'name': 'Required Tables',
                    'passed': tables_ok,
                    'details': f"Missing: {list(missing_tables)}" if missing_tables else "All tables present"
                })
                
                # Check 4: Foreign keys enabled
                cursor = conn.execute("PRAGMA foreign_keys")
                fk_enabled = cursor.fetchone()[0] == 1
                health_data['checks'].append({
                    'name': 'Foreign Keys Enabled',
                    'passed': fk_enabled,
                    'details': "Foreign key constraints active" if fk_enabled else "Foreign keys disabled"
                })
                
                # Check 5: WAL mode (if configured)
                if self.config.wal_mode:
                    cursor = conn.execute("PRAGMA journal_mode")
                    journal_mode = cursor.fetchone()[0].upper()
                    wal_ok = journal_mode == 'WAL'
                    health_data['checks'].append({
                        'name': 'WAL Mode',
                        'passed': wal_ok,
                        'details': f"Journal mode: {journal_mode}"
                    })
                
                # Check 6: Basic data integrity
                try:
                    # Check if admin user exists
                    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
                    admin_exists = cursor.fetchone()[0] > 0
                    health_data['checks'].append({
                        'name': 'Admin User Exists',
                        'passed': admin_exists,
                        'details': "Default admin user found" if admin_exists else "No admin user"
                    })
                except Exception as e:
                    health_data['checks'].append({
                        'name': 'Admin User Check',
                        'passed': False,
                        'details': f"Error: {e}"
                    })
            
            # Overall health status
            all_passed = all(check['passed'] for check in health_data['checks'])
            critical_passed = all(
                check['passed'] for check in health_data['checks'] 
                if check['name'] in ['Database File Exists', 'Required Tables', 'Schema Version']
            )
            
            health_data['healthy'] = critical_passed
            health_data['all_checks_passed'] = all_passed
            
            return health_data
            
        except Exception as e:
            health_data['checks'].append({
                'name': 'Health Check Error',
                'passed': False,
                'details': str(e)
            })
            return health_data
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get database status summary"""
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Count records in key tables
                record_counts = {}
                for table in ['users', 'chat_sessions', 'documents', 'audit_log']:
                    if table in tables:
                        try:
                            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                            record_counts[table] = cursor.fetchone()[0]
                        except:
                            record_counts[table] = 0
                
                return {
                    'database_path': str(self.database_path),
                    'database_size_mb': self.database_path.stat().st_size / (1024 * 1024),
                    'table_count': len(tables),
                    'record_counts': record_counts,
                    'schema_version': self.migration_manager.get_current_version(),
                    'last_backup': self._get_last_backup_info()
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_last_backup_info(self) -> Optional[str]:
        """Get information about the most recent backup"""
        try:
            backup_dir = Path(self.config.backup_dir)
            if not backup_dir.exists():
                return None
                
            backup_files = list(backup_dir.glob("zenith_backup_*.db"))
            if not backup_files:
                return None
                
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            return {
                'path': str(latest_backup),
                'created': datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat(),
                'size_mb': latest_backup.stat().st_size / (1024 * 1024)
            }
        except:
            return None

# Convenience functions
def create_database_manager(config_dict: Dict[str, Any] = None) -> DatabaseManager:
    """Factory function to create DatabaseManager from config"""
    if config_dict:
        config = DatabaseConfig(**config_dict)
    else:
        # Load from application settings
        try:
            from ..core.config import config as app_config
            config = DatabaseConfig(
                path=app_config.database_path,
                backup_dir=getattr(app_config, 'database_backup_dir', './data/enterprise/backups'),
                wal_mode=getattr(app_config, 'database_wal_mode', True),
                auto_backup=getattr(app_config, 'database_auto_backup', True),
                max_connections=getattr(app_config, 'database_max_connections', 10),
                cache_size=getattr(app_config, 'database_cache_size', 10000),
                foreign_keys=getattr(app_config, 'database_foreign_keys', True)
            )
        except:
            config = DatabaseConfig()  # Use defaults
    
    return DatabaseManager(config)
```

### Phase 3: Enhanced Schema Extensions

#### 3.1 Add Missing Tables to DatabaseSchema

```python
# UPDATE: src/database/enterprise_schema.py
class DatabaseSchema:
    """Enhanced enterprise database schema"""
    
    @classmethod
    def get_create_statements(cls) -> List[str]:
        """Get all CREATE statements including new tables"""
        
        statements = [
            # Existing tables...
            cls._get_schema_version_table(),
            cls._get_roles_table(),
            cls._get_permissions_table(),
            cls._get_role_permissions_table(),
            cls._get_users_table(),
            cls._get_user_sessions_table(),
            cls._get_password_history_table(),
            cls._get_chat_sessions_table(),
            cls._get_chat_history_table(),
            cls._get_documents_table(),
            cls._get_document_chunks_table(),
            cls._get_system_settings_table(),
            cls._get_user_preferences_table(),
            cls._get_audit_log_table(),
            cls._get_security_events_table(),
            cls._get_api_keys_table(),
            
            # NEW: Additional enterprise tables
            cls._get_notifications_table(),
            cls._get_system_health_table(),
            cls._get_file_storage_table(),
            cls._get_backup_jobs_table(),
            cls._get_system_metrics_table(),
            
            # Performance indexes
            *cls._get_index_statements(),
            *cls._get_enhanced_index_statements()
        ]
        
        return statements
    
    @classmethod
    def _get_notifications_table(cls) -> str:
        """User notifications system"""
        return """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_id VARCHAR(36) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            type VARCHAR(50) NOT NULL CHECK (type IN ('info', 'warning', 'error', 'success')),
            category VARCHAR(50) DEFAULT 'general',
            priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
            is_read BOOLEAN DEFAULT FALSE,
            read_at DATETIME,
            action_url VARCHAR(500),
            action_label VARCHAR(100),
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata JSON DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    
    @classmethod
    def _get_system_health_table(cls) -> str:
        """System component health monitoring"""
        return """
        CREATE TABLE IF NOT EXISTS system_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'warning', 'error', 'unknown')),
            last_check DATETIME DEFAULT CURRENT_TIMESTAMP,
            next_check DATETIME,
            check_interval_seconds INTEGER DEFAULT 300,
            metrics JSON DEFAULT '{}',
            error_details TEXT,
            consecutive_failures INTEGER DEFAULT 0,
            max_failures INTEGER DEFAULT 3,
            alert_sent BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(component)
        );
        """
    
    @classmethod
    def _get_file_storage_table(cls) -> str:
        """Enhanced file storage tracking"""
        return """
        CREATE TABLE IF NOT EXISTS file_storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id VARCHAR(36) UNIQUE NOT NULL,
            document_id INTEGER,
            storage_type VARCHAR(50) NOT NULL DEFAULT 'local',
            storage_path VARCHAR(500) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            encryption_status VARCHAR(20) DEFAULT 'none',
            compression_type VARCHAR(20) DEFAULT 'none',
            access_permissions JSON DEFAULT '{}',
            retention_policy VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            is_archived BOOLEAN DEFAULT FALSE,
            archived_at DATETIME,
            metadata JSON DEFAULT '{}',
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
        );
        """
    
    @classmethod
    def _get_backup_jobs_table(cls) -> str:
        """Backup job tracking and management"""
        return """
        CREATE TABLE IF NOT EXISTS backup_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id VARCHAR(36) UNIQUE NOT NULL,
            backup_type VARCHAR(50) NOT NULL DEFAULT 'full',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            backup_path VARCHAR(500),
            backup_size INTEGER,
            compression_ratio REAL,
            verification_status VARCHAR(20),
            error_message TEXT,
            triggered_by VARCHAR(100),
            retention_days INTEGER DEFAULT 30,
            metadata JSON DEFAULT '{}',
            CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
        );
        """
    
    @classmethod
    def _get_system_metrics_table(cls) -> str:
        """System performance metrics"""
        return """
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name VARCHAR(100) NOT NULL,
            metric_value REAL NOT NULL,
            metric_unit VARCHAR(20),
            metric_type VARCHAR(50) NOT NULL,
            component VARCHAR(100),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            tags JSON DEFAULT '{}',
            metadata JSON DEFAULT '{}'
        );
        """
    
    @classmethod
    def _get_enhanced_index_statements(cls) -> List[str]:
        """Additional performance indexes for new tables"""
        return [
            # Notifications indexes
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires_at ON notifications(expires_at);",
            
            # System health indexes
            "CREATE INDEX IF NOT EXISTS idx_system_health_component ON system_health(component);",
            "CREATE INDEX IF NOT EXISTS idx_system_health_status ON system_health(status);",
            "CREATE INDEX IF NOT EXISTS idx_system_health_last_check ON system_health(last_check);",
            
            # File storage indexes
            "CREATE INDEX IF NOT EXISTS idx_file_storage_file_id ON file_storage(file_id);",
            "CREATE INDEX IF NOT EXISTS idx_file_storage_document_id ON file_storage(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_file_storage_file_hash ON file_storage(file_hash);",
            "CREATE INDEX IF NOT EXISTS idx_file_storage_storage_type ON file_storage(storage_type);",
            
            # Backup jobs indexes
            "CREATE INDEX IF NOT EXISTS idx_backup_jobs_job_id ON backup_jobs(job_id);",
            "CREATE INDEX IF NOT EXISTS idx_backup_jobs_status ON backup_jobs(status);",
            "CREATE INDEX IF NOT EXISTS idx_backup_jobs_started_at ON backup_jobs(started_at);",
            
            # System metrics indexes
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_component ON system_metrics(component);",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type);",
        ]
```

### Phase 4: Database Creation Script

#### 4.1 Standalone Database Creation Tool

```python
# NEW FILE: scripts/create_database.py
#!/usr/bin/env python3
"""
Zenith Database Creation & Management Script
Creates and manages Zenith enterprise database with all features
"""

import sys
import argparse
import getpass
from pathlib import Path
from typing import Optional
import json

# Add src to Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from database.database_manager import DatabaseManager, DatabaseConfig
    from utils.logger import get_logger
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)

# Load environment variables
load_dotenv(project_root / ".env")

logger = get_logger(__name__)

def print_header():
    """Print script header"""
    print("🗄️  Zenith Database Creation & Management Tool")
    print("=" * 60)

def create_database(args) -> bool:
    """Create or initialize database"""
    try:
        print(f"📍 Database path: {args.path}")
        
        # Create database configuration
        config = DatabaseConfig(
            path=args.path,
            backup_dir=args.backup_dir or f"{Path(args.path).parent}/backups",
            wal_mode=args.wal_mode,
            auto_backup=args.backup,
            max_connections=args.max_connections,
            cache_size=args.cache_size,
            foreign_keys=True
        )
        
        # Initialize database manager
        db_manager = DatabaseManager(config)
        
        print("🚀 Starting database initialization...")
        
        # Create backup if requested and database exists
        if args.backup and db_manager._database_exists():
            print("📦 Creating backup...")
            backup_path = db_manager.backup_database()
            print(f"✅ Backup created: {backup_path}")
        
        # Initialize database
        print("🔨 Initializing database schema...")
        success = db_manager.initialize_database(force=args.force)
        
        if not success:
            print("❌ Database initialization failed!")
            return False
        
        print("✅ Database schema initialized successfully!")
        
        # Run health check
        print("🔍 Running health check...")
        health = db_manager.health_check()
        
        if health['healthy']:
            print("✅ Database health check passed!")
            print_health_summary(health)
        else:
            print("⚠️  Database health check found issues:")
            print_health_summary(health)
        
        # Show database status
        print("📊 Database status:")
        status = db_manager.get_status_summary()
        print_status_summary(status)
        
        return True
        
    except Exception as e:
        logger.error(f"Database creation failed: {e}")
        print(f"❌ Error: {e}")
        return False

def health_check(args) -> bool:
    """Run database health check"""
    try:
        config = DatabaseConfig(path=args.path)
        db_manager = DatabaseManager(config)
        
        print("🔍 Running comprehensive health check...")
        health = db_manager.health_check()
        
        print_health_summary(health, detailed=True)
        
        if health['healthy']:
            print("✅ Overall health: HEALTHY")
            return True
        else:
            print("❌ Overall health: UNHEALTHY")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def backup_database(args) -> bool:
    """Create database backup"""
    try:
        config = DatabaseConfig(
            path=args.path,
            backup_dir=args.backup_dir or f"{Path(args.path).parent}/backups"
        )
        db_manager = DatabaseManager(config)
        
        print("📦 Creating database backup...")
        backup_path = db_manager.backup_database()
        print(f"✅ Backup created: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def status_check(args) -> bool:
    """Show database status"""
    try:
        config = DatabaseConfig(path=args.path)
        db_manager = DatabaseManager(config)
        
        print("📊 Database Status Report")
        print("-" * 40)
        
        status = db_manager.get_status_summary()
        print_status_summary(status, detailed=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False

def print_health_summary(health: dict, detailed: bool = False):
    """Print formatted health check summary"""
    print("\n🏥 Health Check Results:")
    print("-" * 40)
    
    for check in health.get('checks', []):
        status = "✅" if check['passed'] else "❌"
        print(f"{status} {check['name']}: {check['details']}")
    
    if detailed:
        print(f"\n📅 Check timestamp: {health.get('timestamp', 'N/A')}")
        print(f"🎯 All checks passed: {health.get('all_checks_passed', False)}")

def print_status_summary(status: dict, detailed: bool = False):
    """Print formatted status summary"""
    if 'error' in status:
        print(f"❌ Status error: {status['error']}")
        return
    
    print(f"📁 Database: {status.get('database_path', 'N/A')}")
    print(f"💾 Size: {status.get('database_size_mb', 0):.2f} MB")
    print(f"📊 Tables: {status.get('table_count', 0)}")
    print(f"🔢 Schema Version: {status.get('schema_version', 'Unknown')}")
    
    if detailed and 'record_counts' in status:
        print("\n📈 Record Counts:")
        for table, count in status['record_counts'].items():
            print(f"  {table}: {count:,}")
    
    last_backup = status.get('last_backup')
    if last_backup:
        if isinstance(last_backup, dict):
            print(f"💾 Last Backup: {last_backup.get('created', 'Unknown')} ({last_backup.get('size_mb', 0):.1f} MB)")
        else:
            print(f"💾 Last Backup: {last_backup}")
    else:
        print("💾 Last Backup: None")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Zenith Database Creation & Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create --path ./data/zenith.db
  %(prog)s create --force --admin-user admin --admin-email admin@company.com
  %(prog)s health-check --path ./data/zenith.db
  %(prog)s backup --path ./data/zenith.db
  %(prog)s status --path ./data/zenith.db
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create or initialize database')
    create_parser.add_argument('--path', default='./data/enterprise/zenith.db',
                              help='Database file path')
    create_parser.add_argument('--backup-dir', 
                              help='Backup directory (default: {db_dir}/backups)')
    create_parser.add_argument('--force', action='store_true',
                              help='Force recreation if database exists')
    create_parser.add_argument('--backup', action='store_true', default=True,
                              help='Create backup before operations')
    create_parser.add_argument('--wal-mode', action='store_true', default=True,
                              help='Enable WAL mode for better concurrency')
    create_parser.add_argument('--max-connections', type=int, default=10,
                              help='Maximum database connections')
    create_parser.add_argument('--cache-size', type=int, default=10000,
                              help='SQLite cache size')
    
    # Health check command
    health_parser = subparsers.add_parser('health-check', help='Run database health check')
    health_parser.add_argument('--path', default='./data/enterprise/zenith.db',
                              help='Database file path')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--path', default='./data/enterprise/zenith.db',
                              help='Database file path')
    backup_parser.add_argument('--backup-dir',
                              help='Backup directory')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show database status')
    status_parser.add_argument('--path', default='./data/enterprise/zenith.db',
                              help='Database file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    print_header()
    
    # Execute command
    success = False
    if args.command == 'create':
        success = create_database(args)
    elif args.command == 'health-check':
        success = health_check(args)
    elif args.command == 'backup':
        success = backup_database(args)
    elif args.command == 'status':
        success = status_check(args)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Operation completed successfully!")
        return 0
    else:
        print("❌ Operation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Phase 5: Enterprise Setup Integration

#### 5.1 Update Enterprise Setup Manager

```python
# UPDATE: src/setup/enterprise_setup.py
class EnterpriseSetupManager:
    """Enhanced enterprise setup with unified database management"""
    
    async def _phase_database_setup(self, force_recreate: bool) -> SetupResult:
        """Enhanced database setup using DatabaseManager"""
        try:
            logger.info("Starting database setup phase")
            
            # Import DatabaseManager
            from ..database.database_manager import DatabaseManager, DatabaseConfig
            
            # Create database configuration from setup config
            db_config = DatabaseConfig(
                path=self.config.database_path,
                backup_dir=f"{Path(self.config.database_path).parent}/backups",
                wal_mode=self.config.enable_wal_mode,
                auto_backup=self.config.backup_before_setup,
                max_connections=10,
                cache_size=10000,
                foreign_keys=True
            )
            
            # Initialize database manager
            db_manager = DatabaseManager(db_config)
            
            # Create backup if requested
            backup_path = None
            if self.config.backup_before_setup and db_manager._database_exists():
                backup_path = db_manager.backup_database()
                logger.info(f"Created backup: {backup_path}")
            
            # Initialize database
            success = db_manager.initialize_database(force=force_recreate)
            
            if not success:
                return SetupResult(
                    phase=SetupPhase.DATABASE_SETUP,
                    status=SetupStatus.FAILED,
                    message="Database initialization failed"
                )
            
            # Run health check
            health = db_manager.health_check()
            
            # Get database status
            status = db_manager.get_status_summary()
            
            return SetupResult(
                phase=SetupPhase.DATABASE_SETUP,
                status=SetupStatus.COMPLETED,
                message="Database setup completed successfully",
                details={
                    'database_path': self.config.database_path,
                    'backup_created': backup_path,
                    'health_check': health,
                    'database_status': status
                }
            )
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return SetupResult(
                phase=SetupPhase.DATABASE_SETUP,
                status=SetupStatus.FAILED,
                message=f"Database setup error: {str(e)}"
            )
```

### Phase 6: Startup Script Integration

#### 6.1 Enhanced Startup Scripts

```bash
# UPDATE: start_zenith.sh
#!/bin/bash

# Add database validation
echo "🔍 Validating database..."

# Check if database exists and is healthy
if [ -f "$DATABASE_PATH" ]; then
    echo "✅ Database file found: $DATABASE_PATH"
    
    # Run health check
    python scripts/create_database.py health-check --path="$DATABASE_PATH" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Database health check passed"
    else
        echo "⚠️  Database health check failed, attempting repair..."
        python scripts/create_database.py create --path="$DATABASE_PATH" --backup
        if [ $? -ne 0 ]; then
            echo "❌ Database repair failed"
            exit 1
        fi
    fi
else
    echo "📝 Database not found, creating new database..."
    python scripts/create_database.py create --path="$DATABASE_PATH"
    if [ $? -ne 0 ]; then
        echo "❌ Database creation failed"
        exit 1
    fi
fi

echo "✅ Database validation completed"
```

```batch
REM UPDATE: start_zenith.bat
@echo off

REM Add database validation
echo 🔍 Validating database...

REM Check if database exists
if exist "%DATABASE_PATH%" (
    echo ✅ Database file found: %DATABASE_PATH%
    
    REM Run health check
    python scripts\create_database.py health-check --path="%DATABASE_PATH%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Database health check passed
    ) else (
        echo ⚠️  Database health check failed, attempting repair...
        python scripts\create_database.py create --path="%DATABASE_PATH%" --backup
        if !errorlevel! neq 0 (
            echo ❌ Database repair failed
            exit /b 1
        )
    )
) else (
    echo 📝 Database not found, creating new database...
    python scripts\create_database.py create --path="%DATABASE_PATH%"
    if !errorlevel! neq 0 (
        echo ❌ Database creation failed
        exit /b 1
    )
)

echo ✅ Database validation completed
```

## 🎯 Implementation Priority

### ✅ Priority 1 (Critical - Week 1)
1. **Configuration Centralization**
   - Add `database_path` and related fields to Settings class
   - Update `.env.example` with database configuration variables
   - Test environment variable loading

2. **Unified DatabaseManager**
   - Create `src/database/database_manager.py`
   - Implement comprehensive initialization and health checking
   - Test database creation and validation

### ✅ Priority 2 (High - Week 2) 
1. **Database Creation Script**
   - Create `scripts/create_database.py` 
   - Implement command-line interface
   - Add health check and status commands

2. **Enterprise Setup Integration**
   - Update `EnterpriseSetupManager._phase_database_setup()`
   - Replace direct database calls with DatabaseManager
   - Test complete setup flow

### ✅ Priority 3 (Medium - Week 3)
1. **Enhanced Schema**
   - Add notifications, health monitoring, and file storage tables
   - Update DatabaseSchema with new table definitions
   - Test schema migrations

2. **Startup Script Enhancement**
   - Add database validation to startup scripts
   - Implement automatic database repair
   - Test failure scenarios

## 📚 Usage Examples

### Database Creation
```bash
# Create fresh database with default settings
python scripts/create_database.py create --path ./data/zenith.db

# Create with custom configuration
python scripts/create_database.py create --path ./data/zenith.db --wal-mode --cache-size 20000 --max-connections 20

# Force recreation with backup
python scripts/create_database.py create --path ./data/zenith.db --force --backup
```

### Health Monitoring
```bash
# Run comprehensive health check
python scripts/create_database.py health-check --path ./data/zenith.db

# Get database status
python scripts/create_database.py status --path ./data/zenith.db

# Create backup
python scripts/create_database.py backup --path ./data/zenith.db
```

### Programmatic Usage
```python
from database.database_manager import DatabaseManager, DatabaseConfig

# Create database configuration
config = DatabaseConfig(
    path="./data/zenith.db",
    wal_mode=True,
    auto_backup=True
)

# Initialize database manager
db_manager = DatabaseManager(config)

# Initialize database
success = db_manager.initialize_database()

# Run health check
health = db_manager.health_check()
print(f"Database healthy: {health['healthy']}")

# Get status
status = db_manager.get_status_summary()
print(f"Database size: {status['database_size_mb']} MB")
```

## 🔧 Configuration Reference

### Environment Variables
```env
# Database Configuration
DATABASE_PATH=./data/enterprise/zenith.db
DATABASE_BACKUP_DIR=./data/enterprise/backups  
DATABASE_WAL_MODE=true
DATABASE_AUTO_BACKUP=true
DATABASE_MAX_CONNECTIONS=10
DATABASE_CACHE_SIZE=10000
DATABASE_FOREIGN_KEYS=true
```

### Database Schema Summary
- **15+ Core Tables**: Complete enterprise feature set
- **RBAC System**: Roles, permissions, user management
- **Security**: Audit logging, session management, API keys
- **Chat System**: Sessions, history, document integration
- **Document Management**: File processing, chunking, storage
- **Configuration**: System settings, user preferences
- **Monitoring**: Health checks, metrics, notifications
- **Performance**: 50+ indexes for optimal query performance

## 📈 Conclusion

Your Zenith database architecture is already **enterprise-grade and production-ready**. This implementation plan focuses on:

1. **Consolidating** the existing robust components
2. **Centralizing** configuration management  
3. **Enhancing** monitoring and health checking
4. **Simplifying** the setup and maintenance process
5. **Adding** missing utility features

The result will be a **unified, maintainable, and highly reliable** database system that leverages your existing sophisticated schema while providing better management tools and operational excellence.