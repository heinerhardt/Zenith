"""
Database Security Utilities

Provides secure database path validation, SQLite connection management,
and settings sanitization to prevent path traversal, SQL injection,
and resource leak vulnerabilities.
"""

import sqlite3
import contextlib
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Generator
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Security configuration constants
DEFAULT_SQLITE_TIMEOUT = 30.0
MAX_PATH_LENGTH = 255  # Reasonable limit for database filenames
ALLOWED_DB_EXTENSIONS = {'.db', '.sqlite', '.sqlite3'}
DEFAULT_DB_DIRECTORY = 'data'

class DatabaseSecurityError(Exception):
    """Raised when database security validation fails"""
    pass

class PathTraversalError(DatabaseSecurityError):
    """Raised when path traversal attack is detected"""
    pass

class InvalidDatabasePathError(DatabaseSecurityError):
    """Raised when database path is invalid or unsafe"""
    pass

def get_project_root() -> Path:
    """
    Get the project root directory for path validation.
    
    Returns:
        Path: Absolute path to project root directory
    """
    # Start from current file and work up to find project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # Go up from src/utils/
    
    # Verify we found the right directory by checking for key files
    if not (project_root / 'src').exists() or not (project_root / 'requirements.txt').exists():
        # Fallback to environment variable or current working directory
        env_root = os.environ.get('ZENITH_PROJECT_ROOT')
        if env_root:
            project_root = Path(env_root).resolve()
        else:
            project_root = Path.cwd().resolve()
    
    return project_root

def validate_database_path(path: str, project_root: Optional[Path] = None) -> Tuple[bool, str, Optional[Path]]:
    """
    Validate and normalize database path within project boundaries.
    
    Prevents path traversal attacks by ensuring database files remain within
    the project directory structure.
    
    Args:
        path: User-provided database path
        project_root: Project root directory (auto-detected if None)
        
    Returns:
        Tuple of (is_valid, error_message, normalized_path)
        - is_valid: True if path is safe to use
        - error_message: Human-readable error description if invalid
        - normalized_path: Absolute, normalized path if valid
        
    Raises:
        PathTraversalError: If path traversal attack detected
        InvalidDatabasePathError: If path is invalid for other reasons
    """
    if not path or not isinstance(path, str):
        return False, "Database path cannot be empty", None
    
    if len(path) > MAX_PATH_LENGTH:
        return False, f"Database path too long (max {MAX_PATH_LENGTH} characters)", None
    
    # Get project root for boundary checking
    if project_root is None:
        project_root = get_project_root()
    
    try:
        # Convert to Path object and resolve to absolute path
        user_path = Path(path).expanduser()
        
        # Check for obviously malicious patterns before resolving
        path_str = str(user_path)
        if '..' in path_str or path_str.startswith('/'):
            if not path_str.startswith(str(project_root)):
                raise PathTraversalError(f"Database path outside project directory: {path}")
        
        # Resolve to absolute path to handle relative paths and symlinks
        try:
            if user_path.is_absolute():
                abs_path = user_path.resolve()
            else:
                # For relative paths, resolve relative to the project root
                abs_path = (project_root / user_path).resolve()
        except (OSError, RuntimeError) as e:
            return False, f"Invalid path: {str(e)}", None
        
        # Ensure the resolved path is within project boundaries
        try:
            # This will raise ValueError if abs_path is not relative to project_root
            abs_path.relative_to(project_root)
        except ValueError:
            raise PathTraversalError(f"Database path outside project directory: {abs_path}")
        
        # Validate file extension
        if abs_path.suffix.lower() not in ALLOWED_DB_EXTENSIONS:
            return False, f"Invalid extension. Allowed: {', '.join(ALLOWED_DB_EXTENSIONS)}", None
        
        # Ensure the path is within the data directory by default
        data_dir = project_root / DEFAULT_DB_DIRECTORY
        try:
            abs_path.relative_to(data_dir)
        except ValueError:
            # Allow other locations within project root, but warn
            logger.warning(f"Database path outside standard data directory: {abs_path}")
        
        # Additional security checks
        if abs_path.name.startswith('.'):
            return False, "Hidden files not allowed", None
            
        # Check for forbidden path components (only check paths within project root)
        forbidden_components = {'..', '.', 'etc', 'bin', 'usr', 'var', 'sys', 'proc', 'tmp', 'temp'}
        # Windows reserved names
        windows_reserved = {'con', 'aux', 'prn', 'nul', 'com1', 'com2', 'com3', 'com4', 
                           'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 
                           'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
        
        # Only check path components that are within the project directory
        try:
            relative_path = abs_path.relative_to(project_root)
            relative_components = set(relative_path.parts)
            # Check for forbidden components in directory names
            if forbidden_components & relative_components:
                dangerous = forbidden_components & relative_components
                return False, f"Database path contains forbidden components: {', '.join(dangerous)}", None
            # Check for Windows reserved names (case insensitive) in directory names and filename
            relative_components_lower = set(p.lower() for p in relative_path.parts)
            filename_stem_lower = abs_path.stem.lower()
            # Check directory names
            if windows_reserved & relative_components_lower:
                dangerous = windows_reserved & relative_components_lower
                return False, f"Database path contains forbidden components: {', '.join(dangerous)}", None
            # Check filename stem (without extension)
            if filename_stem_lower in windows_reserved:
                return False, f"Database path contains forbidden components: {filename_stem_lower}", None
            # Check filename stem against regular forbidden components
            if filename_stem_lower in {'tmp', 'temp'}:
                return False, f"Database path contains forbidden components: {filename_stem_lower}", None
        except ValueError:
            # Path is outside project root - this will be caught by the boundary check above
            pass
        
        return True, None, abs_path
        
    except PathTraversalError as e:
        return False, str(e), None
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False, f"Path validation failed: {str(e)}", None

@contextlib.contextmanager
def secure_sqlite_connection(
    db_path: Path, 
    timeout: float = DEFAULT_SQLITE_TIMEOUT,
    read_only: bool = False
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for secure SQLite connections with proper cleanup and timeout.
    
    Ensures connections are properly closed even if exceptions occur, and provides
    timeout protection against resource exhaustion attacks.
    
    Args:
        db_path: Validated database path
        timeout: Connection timeout in seconds
        read_only: Whether to open in read-only mode
        
    Yields:
        sqlite3.Connection: Database connection object
        
    Raises:
        DatabaseSecurityError: If connection fails or path is invalid
        sqlite3.Error: For database-specific errors
    """
    if not isinstance(db_path, Path):
        raise InvalidDatabasePathError("Database path must be a Path object")
    
    if not db_path.exists() and read_only:
        raise DatabaseSecurityError(f"Database file does not exist: {db_path}")
    
    connection = None
    start_time = time.time()
    
    try:
        # Create parent directory if it doesn't exist (securely)
        if not read_only:
            parent_dir = db_path.parent
            if not parent_dir.exists():
                # Validate parent directory is also within project bounds
                project_root = get_project_root()
                try:
                    parent_dir.relative_to(project_root)
                except ValueError:
                    raise PathTraversalError(f"Database directory outside project: {parent_dir}")
                
                # Create directory with secure permissions
                parent_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
                logger.info(f"Created database directory: {parent_dir}")
        
        # Open connection with timeout and security settings
        connection_uri = f"file:{db_path}"
        if read_only:
            connection_uri += "?mode=ro"
        
        connection = sqlite3.connect(
            connection_uri, 
            timeout=timeout,
            uri=True,
            check_same_thread=False  # Allow connection to be used across threads
        )
        
        # Configure connection security settings
        connection.execute("PRAGMA foreign_keys = ON")  # Enforce foreign key constraints
        connection.execute("PRAGMA journal_mode = WAL")  # Use Write-Ahead Logging for better concurrency
        connection.execute("PRAGMA synchronous = FULL")  # Ensure data integrity
        connection.execute("PRAGMA temp_store = MEMORY")  # Store temp data in memory for security
        connection.execute("PRAGMA secure_delete = ON")  # Overwrite deleted data
        
        # Set row factory for easier data access
        connection.row_factory = sqlite3.Row
        
        logger.debug(f"Opened secure SQLite connection to {db_path} in {time.time() - start_time:.3f}s")
        
        yield connection
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error for {db_path}: {e}")
        raise  # Re-raise sqlite3.Error directly for test compatibility
    except Exception as e:
        logger.error(f"Unexpected error opening {db_path}: {e}")
        raise DatabaseSecurityError(f"Failed to open database connection: {str(e)}") from e
    finally:
        if connection:
            try:
                connection.close()
                logger.debug(f"Closed SQLite connection to {db_path}")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")

def sanitize_database_settings(settings: Dict[str, Any], project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Sanitize database configuration settings before saving.
    
    Validates and normalizes all database-related settings to prevent
    security vulnerabilities.
    
    Args:
        settings: Raw settings dictionary from user input
        project_root: Project root directory for path validation
        
    Returns:
        Dict[str, Any]: Sanitized settings dictionary
        
    Raises:
        DatabaseSecurityError: If settings contain security vulnerabilities
    """
    sanitized = {}
    
    for key, value in settings.items():
        if key == 'sqlite_db_path':
            # Validate database path
            if value:
                is_valid, error_msg, validated_path = validate_database_path(str(value), project_root)
                if not is_valid:
                    raise ValueError(f"Invalid database path: {error_msg}")
                sanitized[key] = str(validated_path)
            else:
                sanitized[key] = value
                
        elif key == 'sqlite_auto_backup':
            # Ensure boolean with string coercion
            if isinstance(value, str):
                sanitized[key] = value.lower() in ('true', '1', 'yes', 'on')
            else:
                sanitized[key] = bool(value) if value is not None else True
            
        elif key == 'sqlite_backup_retention_days':
            # Validate retention days
            if value is not None:
                try:
                    days = int(value)
                    if days < 1 or days > 365:
                        raise ValueError("Backup retention days must be between 1 and 365")
                    sanitized[key] = days
                except TypeError as e:
                    raise ValueError(f"Invalid backup retention days: {e}")
                except ValueError:
                    raise  # Re-raise ValueError directly for test compatibility
            else:
                sanitized[key] = 30  # Default
                
        elif key == 'sqlite_auto_vacuum':
            # Ensure boolean with string coercion
            if isinstance(value, str):
                sanitized[key] = value.lower() in ('true', '1', 'yes', 'on')
            else:
                sanitized[key] = bool(value) if value is not None else True
            
        elif key == 'sqlite_wal_mode':
            # Ensure boolean with string coercion
            if isinstance(value, str):
                sanitized[key] = value.lower() in ('true', '1', 'yes', 'on')
            else:
                sanitized[key] = bool(value) if value is not None else True
            
        else:
            # Pass through other settings unchanged
            sanitized[key] = value
    
    return sanitized

def check_database_connection(db_path: str, project_root: Optional[Path] = None, timeout: float = 5.0) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Test database connection and return connection info.
    
    Safely tests database connectivity without exposing sensitive information.
    
    Args:
        db_path: Database path string to validate and test
        project_root: Project root directory for validation
        timeout: Connection timeout in seconds
        
    Returns:
        Tuple of (success, message, info_dict)
        - success: True if connection successful
        - message: Human-readable status message
        - info_dict: Database information (version, file size, etc.)
    """
    info = {}
    created_directory = False
    
    try:
        # First validate the path
        is_valid, error_msg, validated_path = validate_database_path(db_path, project_root)
        if not is_valid:
            return False, f"❌ Invalid database path error: {error_msg}", {}
        
        # Check if we need to create the directory
        parent_dir = validated_path.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            created_directory = True
            info['created_directory'] = True
        else:
            info['created_directory'] = False
        
        # Test connection (allow creation for testing)
        with secure_sqlite_connection(validated_path, timeout=timeout, read_only=False) as conn:
            # Get SQLite version
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            info['version'] = version
            info['sqlite_version'] = version  # Keep both for compatibility
            
            # Get database file size
            if validated_path.exists():
                info['file_size_bytes'] = validated_path.stat().st_size
            else:
                info['file_size_bytes'] = 0
            
            # Get table count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            info['table_count'] = cursor.fetchone()[0]
            
            # Get pragma info
            cursor.execute("PRAGMA journal_mode")
            info['journal_mode'] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA foreign_keys")
            info['foreign_keys'] = bool(cursor.fetchone()[0])
            
            return True, f"✅ Connection successful - SQLite {version}", info
            
    except DatabaseSecurityError as e:
        logger.warning(f"Database security error during connection test: {e}")
        return False, f"❌ Security error: {str(e)}", info
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False, f"❌ Connection failed: {str(e)}", info

# Thread-safe database operations lock
_db_operations_lock = threading.Lock()

def get_database_operations_lock() -> threading.Lock:
    """
    Get the global database operations lock for thread safety.
    
    Returns:
        threading.Lock: Global lock for database operations
    """
    return _db_operations_lock