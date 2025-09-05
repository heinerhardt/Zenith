# Utils Module

Utility functions and security modules for the Zenith AI system.

## Module Structure

### Security Modules
- `database_security.py` - Comprehensive database security validation and protection
- `security.py` - Authentication security utilities

### General Utilities  
- `helpers.py` - General utility functions
- `logger.py` - Centralized logging configuration
- `async_helpers.py` - Asynchronous operation utilities
- `minio_helpers.py` - MinIO storage integration utilities

## Database Security Module

The `database_security.py` module provides comprehensive protection against database-related security vulnerabilities:

### Key Functions
- `validate_database_path()` - Prevents path traversal attacks on database file paths
- `secure_sqlite_connection()` - Context manager for safe SQLite connections with timeout protection
- `sanitize_database_settings()` - Validates and normalizes database configuration before storage
- `check_database_connection()` - Safe database connectivity testing with security validation

### Security Features
- **Path Traversal Protection**: Validates database paths stay within project boundaries
- **Secure File Operations**: Prevents access to system directories and files
- **Connection Safety**: Timeout protection and proper resource cleanup
- **Settings Validation**: Type checking and range validation for database settings
- **Thread Safety**: Global database operations lock for concurrent access protection

### Integration Points
- Used by `enhanced_settings_manager.py` for secure settings validation
- Integrated with `simple_chat_app.py` database configuration interface
- Provides security layer for all database path operations

### Usage Example
```python
from src.utils.database_security import validate_database_path, secure_sqlite_connection

# Validate database path
is_valid, error_msg, validated_path = validate_database_path('./data/app.db')
if is_valid:
    # Use secure connection
    with secure_sqlite_connection(validated_path) as conn:
        # Safe database operations
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
```

### Configuration
- `DEFAULT_SQLITE_TIMEOUT`: Connection timeout (30 seconds)
- `MAX_PATH_LENGTH`: Maximum database path length (255 characters)
- `ALLOWED_DB_EXTENSIONS`: Permitted database file extensions
- `DEFAULT_DB_DIRECTORY`: Default secure database directory

## Testing

Run security tests:
```bash
pytest tests/test_database_security.py -v
```