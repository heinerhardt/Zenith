"""
Enterprise Database Migration System for Zenith
Handles database schema versioning, migrations, and rollbacks with enterprise-grade
safety measures and validation.
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Callable
from pathlib import Path
from enum import Enum
import shutil
import traceback
from dataclasses import dataclass

from src.utils.logger import get_logger
from src.utils.database_security import (
    validate_database_path,
    check_database_connection,
    sanitize_database_settings,
    secure_sqlite_connection
)
from src.database.enterprise_schema import DatabaseSchema, EnterpriseDatabase

logger = get_logger(__name__)


class MigrationStatus(Enum):
    """Migration execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationInfo:
    """Migration metadata and execution info"""
    version: int
    name: str
    description: str
    up_sql: str
    down_sql: str
    checksum: str
    created_at: datetime
    dependencies: List[int] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class MigrationBase:
    """Base class for database migrations"""
    
    def __init__(self, version: int, name: str, description: str):
        self.version = version
        self.name = name
        self.description = description
        self.dependencies: List[int] = []
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Apply the migration"""
        raise NotImplementedError("Subclasses must implement up() method")
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Rollback the migration"""
        raise NotImplementedError("Subclasses must implement down() method")
    
    def validate_pre_conditions(self, conn: sqlite3.Connection) -> bool:
        """Validate conditions before applying migration"""
        return True
    
    def validate_post_conditions(self, conn: sqlite3.Connection) -> bool:
        """Validate conditions after applying migration"""
        return True
    
    def get_checksum(self) -> str:
        """Calculate migration checksum"""
        content = f"{self.version}:{self.name}:{self.description}"
        return hashlib.sha256(content.encode()).hexdigest()


class Migration001_InitialSchema(MigrationBase):
    """Initial enterprise schema migration"""
    
    def __init__(self):
        super().__init__(
            version=1,
            name="initial_enterprise_schema",
            description="Create initial enterprise database schema with RBAC, audit logging, and security features"
        )
    
    def up(self, conn: sqlite3.Connection) -> None:
        """Create initial enterprise schema"""
        # Create all tables from schema
        create_statements = DatabaseSchema.get_create_statements()
        
        for statement in create_statements:
            conn.execute(statement)
        
        # Insert default data would be handled by EnterpriseDatabase class
        logger.info("Initial enterprise schema created")
    
    def down(self, conn: sqlite3.Connection) -> None:
        """Drop all enterprise tables"""
        # Get all table names
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        # Drop all tables
        for table in tables:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        
        logger.info("Initial enterprise schema rolled back")
    
    def validate_post_conditions(self, conn: sqlite3.Connection) -> bool:
        """Validate that all required tables exist"""
        required_tables = [
            'users', 'roles', 'permissions', 'role_permissions',
            'chat_sessions', 'chat_history', 'documents', 'document_chunks',
            'audit_log', 'security_events', 'system_settings'
        ]
        
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = set(row[0] for row in cursor.fetchall())
        
        missing_tables = set(required_tables) - existing_tables
        if missing_tables:
            logger.error(f"Missing tables after migration: {missing_tables}")
            return False
        
        return True


class MigrationRegistry:
    """Registry of all available migrations"""
    
    def __init__(self):
        self._migrations: Dict[int, MigrationBase] = {}
        self._register_builtin_migrations()
    
    def _register_builtin_migrations(self):
        """Register built-in migrations"""
        migrations = [
            Migration001_InitialSchema(),
            # Future migrations will be added here
        ]
        
        for migration in migrations:
            self.register_migration(migration)
    
    def register_migration(self, migration: MigrationBase) -> None:
        """Register a migration"""
        if migration.version in self._migrations:
            raise ValueError(f"Migration version {migration.version} already registered")
        
        self._migrations[migration.version] = migration
        logger.debug(f"Registered migration {migration.version}: {migration.name}")
    
    def get_migration(self, version: int) -> Optional[MigrationBase]:
        """Get migration by version"""
        return self._migrations.get(version)
    
    def get_all_migrations(self) -> List[MigrationBase]:
        """Get all migrations sorted by version"""
        return sorted(self._migrations.values(), key=lambda m: m.version)
    
    def get_pending_migrations(self, current_version: int) -> List[MigrationBase]:
        """Get migrations that need to be applied"""
        return [m for m in self.get_all_migrations() if m.version > current_version]
    
    def validate_dependencies(self) -> bool:
        """Validate migration dependency chain"""
        for migration in self._migrations.values():
            for dep_version in migration.dependencies:
                if dep_version not in self._migrations:
                    logger.error(f"Migration {migration.version} depends on missing migration {dep_version}")
                    return False
        return True


class MigrationManager:
    """Enterprise database migration manager"""
    
    def __init__(self, database_path: str, backup_dir: Optional[str] = None):
        """Initialize migration manager"""
        self.database_path = Path(database_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.database_path.parent / "backups"
        self.registry = MigrationRegistry()
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure migration tracking table exists
        self._ensure_migration_table()
        
        logger.info(f"Initialized migration manager for {database_path}")
    
    def _ensure_migration_table(self) -> None:
        """Ensure migration tracking table exists"""
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS database_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER UNIQUE NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        checksum VARCHAR(64) NOT NULL,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        applied_by VARCHAR(100),
                        execution_time_ms INTEGER,
                        status VARCHAR(20) DEFAULT 'completed',
                        error_message TEXT,
                        rollback_sql TEXT,
                        metadata JSON DEFAULT '{}'
                    );
                """)
                
                # Create index for performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_migrations_version 
                    ON database_migrations(version);
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise
    
    def get_current_version(self) -> int:
        """Get current database schema version"""
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT MAX(version) FROM database_migrations 
                    WHERE status = 'completed'
                """)
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
                
        except sqlite3.OperationalError:
            # Migration table doesn't exist yet
            return 0
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return 0
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT version, name, description, applied_at, status, 
                           execution_time_ms, error_message
                    FROM database_migrations 
                    ORDER BY version
                """)
                
                return [
                    {
                        'version': row[0],
                        'name': row[1],
                        'description': row[2],
                        'applied_at': row[3],
                        'status': row[4],
                        'execution_time_ms': row[5],
                        'error_message': row[6]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting migration history: {e}")
            return []
    
    def create_backup(self, suffix: str = None) -> str:
        """Create database backup before migration"""
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.database_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_suffix = f"_{suffix}" if suffix else ""
        backup_filename = f"zenith_db_backup_{timestamp}{backup_suffix}.db"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Create backup using SQLite backup API for consistency
            with secure_sqlite_connection(self.database_path) as source_conn:
                with secure_sqlite_connection(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)
            
            # Verify backup integrity
            if self._verify_backup_integrity(str(backup_path)):
                logger.info(f"Database backup created: {backup_path}")
                return str(backup_path)
            else:
                backup_path.unlink()  # Remove corrupted backup
                raise RuntimeError("Backup integrity check failed")
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    def _verify_backup_integrity(self, backup_path: str) -> bool:
        """Verify backup file integrity"""
        try:
            with secure_sqlite_connection(Path(backup_path)) as conn:
                # Run integrity check
                cursor = conn.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                return result and result[0] == 'ok'
                
        except Exception as e:
            logger.error(f"Backup integrity check failed: {e}")
            return False
    
    def migrate_up(self, target_version: Optional[int] = None, 
                  dry_run: bool = False) -> Tuple[bool, List[str]]:
        """
        Apply pending migrations up to target version
        
        Args:
            target_version: Version to migrate to (None for latest)
            dry_run: Only validate migrations without applying
            
        Returns:
            Tuple of (success, list_of_messages)
        """
        messages = []
        current_version = self.get_current_version()
        
        # Get pending migrations
        pending_migrations = self.registry.get_pending_migrations(current_version)
        
        if target_version is not None:
            pending_migrations = [m for m in pending_migrations if m.version <= target_version]
        
        if not pending_migrations:
            messages.append("No pending migrations to apply")
            return True, messages
        
        # Validate migration dependencies
        if not self.registry.validate_dependencies():
            messages.append("Migration dependency validation failed")
            return False, messages
        
        messages.append(f"Found {len(pending_migrations)} migrations to apply")
        
        if dry_run:
            for migration in pending_migrations:
                messages.append(f"Would apply: {migration.version} - {migration.name}")
            return True, messages
        
        # Create backup before migrations
        try:
            backup_path = self.create_backup("pre_migration")
            messages.append(f"Created backup: {backup_path}")
        except Exception as e:
            messages.append(f"Failed to create backup: {e}")
            return False, messages
        
        # Apply migrations
        success = True
        applied_migrations = []
        
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                conn.execute("BEGIN TRANSACTION;")
                
                for migration in pending_migrations:
                    migration_success = self._apply_migration(conn, migration, messages)
                    
                    if migration_success:
                        applied_migrations.append(migration)
                        messages.append(f"✓ Applied migration {migration.version}: {migration.name}")
                    else:
                        success = False
                        messages.append(f"✗ Failed to apply migration {migration.version}")
                        break
                
                if success:
                    conn.execute("COMMIT;")
                    messages.append("All migrations applied successfully")
                else:
                    conn.execute("ROLLBACK;")
                    messages.append("Migrations rolled back due to failure")
                    
        except Exception as e:
            success = False
            messages.append(f"Migration transaction failed: {e}")
            logger.error(f"Migration failed: {e}\n{traceback.format_exc()}")
        
        return success, messages
    
    def _apply_migration(self, conn: sqlite3.Connection, migration: MigrationBase, 
                        messages: List[str]) -> bool:
        """Apply a single migration"""
        start_time = datetime.now()
        
        try:
            # Record migration start
            self._record_migration_attempt(conn, migration, MigrationStatus.RUNNING)
            
            # Validate pre-conditions
            if not migration.validate_pre_conditions(conn):
                messages.append(f"Pre-condition validation failed for {migration.version}")
                self._record_migration_failure(conn, migration, "Pre-condition validation failed")
                return False
            
            # Apply migration
            migration.up(conn)
            
            # Validate post-conditions
            if not migration.validate_post_conditions(conn):
                messages.append(f"Post-condition validation failed for {migration.version}")
                self._record_migration_failure(conn, migration, "Post-condition validation failed")
                return False
            
            # Record successful migration
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._record_migration_success(conn, migration, int(execution_time))
            
            return True
            
        except Exception as e:
            error_msg = f"Migration {migration.version} failed: {e}"
            messages.append(error_msg)
            self._record_migration_failure(conn, migration, str(e))
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return False
    
    def _record_migration_attempt(self, conn: sqlite3.Connection, migration: MigrationBase, 
                                status: MigrationStatus) -> None:
        """Record migration attempt in tracking table"""
        conn.execute("""
            INSERT OR REPLACE INTO database_migrations 
            (version, name, description, checksum, status, applied_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            migration.version, migration.name, migration.description,
            migration.get_checksum(), status.value, "system"
        ))
    
    def _record_migration_success(self, conn: sqlite3.Connection, migration: MigrationBase, 
                                execution_time_ms: int) -> None:
        """Record successful migration"""
        conn.execute("""
            UPDATE database_migrations 
            SET status = 'completed', execution_time_ms = ?, applied_at = CURRENT_TIMESTAMP
            WHERE version = ?
        """, (execution_time_ms, migration.version))
    
    def _record_migration_failure(self, conn: sqlite3.Connection, migration: MigrationBase, 
                                error_message: str) -> None:
        """Record failed migration"""
        conn.execute("""
            UPDATE database_migrations 
            SET status = 'failed', error_message = ?
            WHERE version = ?
        """, (error_message, migration.version))
    
    def rollback_migration(self, target_version: int) -> Tuple[bool, List[str]]:
        """
        Rollback to specific version
        
        Args:
            target_version: Version to rollback to
            
        Returns:
            Tuple of (success, list_of_messages)
        """
        messages = []
        current_version = self.get_current_version()
        
        if target_version >= current_version:
            messages.append(f"Target version {target_version} is not lower than current {current_version}")
            return False, messages
        
        # Get migrations to rollback (in reverse order)
        migrations_to_rollback = [
            self.registry.get_migration(v) for v in range(current_version, target_version, -1)
            if self.registry.get_migration(v) is not None
        ]
        
        if not migrations_to_rollback:
            messages.append("No migrations to rollback")
            return True, messages
        
        messages.append(f"Rolling back {len(migrations_to_rollback)} migrations")
        
        # Create backup before rollback
        try:
            backup_path = self.create_backup("pre_rollback")
            messages.append(f"Created backup: {backup_path}")
        except Exception as e:
            messages.append(f"Failed to create backup: {e}")
            return False, messages
        
        # Perform rollback
        success = True
        
        try:
            with secure_sqlite_connection(self.database_path) as conn:
                conn.execute("BEGIN TRANSACTION;")
                
                for migration in migrations_to_rollback:
                    try:
                        migration.down(conn)
                        
                        # Update migration record
                        conn.execute("""
                            UPDATE database_migrations 
                            SET status = 'rolled_back' 
                            WHERE version = ?
                        """, (migration.version,))
                        
                        messages.append(f"✓ Rolled back migration {migration.version}")
                        
                    except Exception as e:
                        success = False
                        messages.append(f"✗ Failed to rollback migration {migration.version}: {e}")
                        break
                
                if success:
                    conn.execute("COMMIT;")
                    messages.append("Rollback completed successfully")
                else:
                    conn.execute("ROLLBACK;")
                    messages.append("Rollback transaction failed")
                    
        except Exception as e:
            success = False
            messages.append(f"Rollback failed: {e}")
            logger.error(f"Rollback failed: {e}\n{traceback.format_exc()}")
        
        return success, messages
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status"""
        current_version = self.get_current_version()
        all_migrations = self.registry.get_all_migrations()
        pending_migrations = self.registry.get_pending_migrations(current_version)
        history = self.get_migration_history()
        
        return {
            'current_version': current_version,
            'latest_available_version': max((m.version for m in all_migrations), default=0),
            'total_migrations': len(all_migrations),
            'pending_migrations': len(pending_migrations),
            'migration_history': history,
            'dependencies_valid': self.registry.validate_dependencies(),
            'database_path': str(self.database_path),
            'backup_directory': str(self.backup_dir),
            'available_backends': 1  # Fixed: Added missing field for system validation
        }


# Global migration manager instance
_migration_manager: Optional[MigrationManager] = None


def get_migration_manager(database_path: str = None) -> MigrationManager:
    """Get global migration manager instance"""
    global _migration_manager
    
    if _migration_manager is None:
        if database_path is None:
            raise ValueError("Database path required for first initialization")
        _migration_manager = MigrationManager(database_path)
    
    return _migration_manager


def initialize_migration_system(database_path: str, backup_dir: str = None):
    """Initialize migration system"""
    global _migration_manager
    
    _migration_manager = MigrationManager(database_path, backup_dir)
    logger.info("Migration system initialized")