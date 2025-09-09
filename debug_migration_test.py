#!/usr/bin/env python3
"""
Debug script to isolate the migration system Path object error
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

print("Starting migration system debugging...")
print("=" * 50)

try:
    print("Step 1: Testing database security import...")
    from src.utils.database_security import secure_sqlite_connection
    print("✓ secure_sqlite_connection imported successfully")
    print()
    
    print("Step 2: Testing migration imports...")
    from src.database.migrations import get_migration_manager, initialize_migration_system
    print("✓ Migration system imported successfully")
    print()
    
    print("Step 3: Testing database creation...")
    from src.database.enterprise_schema import EnterpriseDatabase
    test_db_path = Path("./test_migration_debug.db")
    db = EnterpriseDatabase(test_db_path)
    print(f"✓ Database object created with path: {test_db_path} (type: {type(test_db_path)})")
    
    # Initialize the database first
    db_result = db.initialize_database()
    print(f"✓ Database initialization result: {db_result}")
    print()
    
    print("Step 4: Testing migration manager creation...")
    migration_manager = get_migration_manager(str(test_db_path))
    print(f"✓ Migration manager created")
    print(f"  - Manager type: {type(migration_manager)}")
    print(f"  - Database path: {migration_manager.database_path} (type: {type(migration_manager.database_path)})")
    print()
    
    print("Step 5: Testing migration system initialization...")
    result = initialize_migration_system(str(test_db_path))
    print(f"✓ Migration system initialization result: {result}")
    print()
    
    print("Step 6: Testing migration execution...")
    success, messages = migration_manager.migrate_up()
    print(f"✓ Migration execution - Success: {success}")
    print(f"  Messages: {messages}")
    
    print("=" * 50)
    print("🎉 All migration tests passed!")

except Exception as e:
    import traceback
    print("=" * 50)
    print("❌ MIGRATION ERROR OCCURRED:")
    print("-" * 30)
    traceback.print_exc()
    print("-" * 30)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print()
    
    # Additional debugging for Path object errors
    if "Path object" in str(e):
        print("🔍 This IS the Path object error!")
        
        # Try to identify what's being passed
        print("\nDebugging Path object issue:")
        try:
            from src.database.migrations import get_migration_manager
            print("Available in migration module:")
            import src.database.migrations as mig_mod
            print([attr for attr in dir(mig_mod) if not attr.startswith('_')])
            
            # Check what path types are being used
            test_path = Path("./test.db")
            print(f"Test Path object: {test_path} (type: {type(test_path)})")
            print(f"Test Path string: {str(test_path)} (type: {type(str(test_path))})")
            
        except Exception as debug_e:
            print(f"Debug investigation failed: {debug_e}")
    
    print("=" * 50)

finally:
    # Cleanup
    cleanup_files = [
        Path("./test_migration_debug.db"),
        Path("./test_migration_debug.db-wal"),
        Path("./test_migration_debug.db-shm"),
        Path("./test.db")
    ]
    
    for file_path in cleanup_files:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"🧹 Cleaned up {file_path}")
            except:
                print(f"⚠️ Could not clean up {file_path}")