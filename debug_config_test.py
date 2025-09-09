#!/usr/bin/env python3
"""
Debug script to isolate the configuration setup Path object error
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

print("Starting configuration setup debugging...")
print("=" * 50)

try:
    print("Step 1: Testing basic imports...")
    from src.core.enhanced_configuration_manager import (
        initialize_configuration_management, 
        get_config_manager,
        EnhancedConfigurationManager,
        DatabaseConfigurationStore
    )
    print("✓ Configuration manager imports successful")
    print()
    
    print("Step 2: Testing direct DatabaseConfigurationStore creation...")
    db_path = "./test_config_debug.db"
    print(f"Creating store with path: {db_path} (type: {type(db_path)})")
    store = DatabaseConfigurationStore(db_path)
    print("✓ DatabaseConfigurationStore created successfully")
    print()
    
    print("Step 3: Testing initialize_configuration_management...")
    print(f"Initializing with path: {db_path}")
    initialize_configuration_management(db_path, "development")
    print("✓ Configuration management initialized")
    print()
    
    print("Step 4: Getting config manager...")
    config_manager = get_config_manager()
    print("✓ Config manager obtained")
    print(f"  - Manager type: {type(config_manager)}")
    print(f"  - Database path: {config_manager.database_path} (type: {type(config_manager.database_path)})")
    print()
    
    print("Step 5: Testing configuration operations...")
    print("Setting test configuration...")
    result = config_manager.set_config("test.key", "test_value", changed_by="debug")
    print(f"✓ Set config result: {result}")
    print()
    
    print("Getting test configuration...")
    value = config_manager.get_config("test.key")
    print(f"✓ Get config result: {value}")
    print()
    
    print("Step 6: Testing health check...")
    health = config_manager.health_check()
    print(f"✓ Health check result: {health}")
    
    print("=" * 50)
    print("🎉 All configuration tests passed!")

except Exception as e:
    import traceback
    print("=" * 50)
    print("❌ CONFIGURATION ERROR OCCURRED:")
    print("-" * 30)
    traceback.print_exc()
    print("-" * 30)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print()
    
    # Additional debugging for Path object errors
    if "Path object" in str(e):
        print("🔍 This IS the Path object error!")
        
        print("\nDebugging Path object issue:")
        try:
            print("Testing Path conversion...")
            test_path = Path("./test.db")
            print(f"Path object: {test_path} (type: {type(test_path)})")
            print(f"String conversion: {str(test_path)} (type: {type(str(test_path))})")
            
            from src.utils.database_security import secure_sqlite_connection
            print("Testing secure_sqlite_connection requirements...")
            
        except Exception as debug_e:
            print(f"Debug investigation failed: {debug_e}")
    
    print("=" * 50)

finally:
    # Cleanup
    cleanup_files = [
        Path("./test_config_debug.db"),
        Path("./test_config_debug.db-wal"),
        Path("./test_config_debug.db-shm")
    ]
    
    for file_path in cleanup_files:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"🧹 Cleaned up {file_path}")
            except:
                print(f"⚠️ Could not clean up {file_path}")