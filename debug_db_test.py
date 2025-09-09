#!/usr/bin/env python3
"""
Debug script to isolate the secure_database_connection error
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

print("Starting database connection debugging...")
print("=" * 50)

try:
    print("Step 1: Testing database security import...")
    from src.utils.database_security import secure_sqlite_connection
    print("✓ secure_sqlite_connection imported successfully")
    
    # List all functions in the module
    import src.utils.database_security as db_sec
    print("Available functions:", [f for f in dir(db_sec) if not f.startswith('_')])
    print()
    
    print("Step 2: Testing enterprise schema import...")
    from src.database.enterprise_schema import EnterpriseDatabase
    print("✓ EnterpriseDatabase imported successfully")
    print()
    
    print("Step 3: Creating database object...")
    db = EnterpriseDatabase("./test_debug.db")
    print("✓ Database object created successfully")
    print()
    
    print("Step 4: Testing database initialization...")
    result = db.initialize_database()
    print(f"✓ Database initialization result: {result}")
    print()
    
    if result:
        print("Step 5: Testing health check...")
        health = db.health_check()
        print(f"✓ Health check result: {health}")
    
    print("=" * 50)
    print("🎉 All tests passed! No secure_database_connection error found.")

except Exception as e:
    import traceback
    print("=" * 50)
    print("❌ ERROR OCCURRED:")
    print("-" * 30)
    traceback.print_exc()
    print("-" * 30)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print()
    
    # Additional debugging info
    if "secure_database_connection" in str(e):
        print("🔍 This IS the secure_database_connection error!")
        print("Let's check what's in the current namespace:")
        print("Globals containing 'secure':", [k for k in globals() if 'secure' in k.lower()])
        
        # Check the specific module
        try:
            import src.utils.database_security as db_sec
            print("Database security module contents:", [f for f in dir(db_sec) if 'secure' in f.lower()])
        except:
            print("Could not import database_security module")
    
    print("=" * 50)

finally:
    # Cleanup
    test_db_path = Path("./test_debug.db")
    if test_db_path.exists():
        try:
            test_db_path.unlink()
            print("🧹 Cleaned up test database file")
        except:
            print("⚠️ Could not clean up test database file")