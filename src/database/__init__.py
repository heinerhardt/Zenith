"""
Database Package

This package provides database functionality for the Zenith AI system,
including enterprise schema management, migrations, and security features.
"""

try:
    from .enterprise_schema import EnterpriseDatabase, UserRole
    from .migrations import get_migration_manager, initialize_migration_system
    __all__ = ['EnterpriseDatabase', 'UserRole', 'get_migration_manager', 'initialize_migration_system']
except ImportError:
    # Enterprise database features not available
    __all__ = []
