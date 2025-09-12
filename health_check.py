#!/usr/bin/env python3
"""
Zenith Health Check Script
Comprehensive system diagnostics for authentication and database issues
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import bcrypt

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def check_environment():
    """Check environment variables and configuration"""
    print_header("ENVIRONMENT CHECK")
    
    # Check .env file
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"✓ .env file found: {env_file}")
        with open(env_file, 'r') as f:
            env_content = f.read()
            print(f"  Size: {len(env_content)} bytes")
    else:
        print(f"✗ .env file not found: {env_file}")
    
    # Check key environment variables
    env_vars = [
        'FIRST_SETUP', 'DATABASE_PATH', 'QDRANT_URL', 'QDRANT_PORT',
        'OPENAI_API_KEY', 'APP_PORT', 'DEBUG_MODE', 'LOG_LEVEL'
    ]
    
    print("\nEnvironment Variables:")
    for var in env_vars:
        value = os.getenv(var, 'NOT SET')
        if 'API_KEY' in var or 'PASSWORD' in var:
            display_value = '[HIDDEN]' if value != 'NOT SET' else 'NOT SET'
        else:
            display_value = value
        print(f"  {var}: {display_value}")

def check_database_files():
    """Check database files and permissions"""
    print_header("DATABASE FILES CHECK")
    
    # Common database locations
    db_paths = [
        project_root / "data" / "zenith.db",
        project_root / "zenith.db",
        Path(os.getenv('DATABASE_PATH', 'data/zenith.db')),
    ]
    
    for db_path in db_paths:
        if db_path.exists():
            print(f"✓ Database found: {db_path}")
            stat = db_path.stat()
            print(f"  Size: {stat.st_size} bytes")
            print(f"  Modified: {datetime.fromtimestamp(stat.st_mtime)}")
            print(f"  Readable: {os.access(db_path, os.R_OK)}")
            print(f"  Writable: {os.access(db_path, os.W_OK)}")
            return db_path
        else:
            print(f"✗ Database not found: {db_path}")
    
    return None

def check_database_schema(db_path):
    """Check database schema and structure"""
    print_header("DATABASE SCHEMA CHECK")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables found: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check specific tables
        expected_tables = ['users', 'system_settings', 'chat_sessions']
        missing_tables = []
        
        for table_name in expected_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                missing_tables.append(table_name)
        
        if missing_tables:
            print(f"\n✗ Missing expected tables: {missing_tables}")
        else:
            print(f"\n✓ All expected tables present")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database schema check failed: {e}")
        return False

def check_users_table(db_path):
    """Check users table and authentication data"""
    print_header("USERS TABLE CHECK")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("✗ Users table does not exist")
            conn.close()
            return False
        
        # Get table schema
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("Users table schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\nTotal users: {user_count}")
        
        if user_count > 0:
            # Show user details (without passwords)
            cursor.execute("SELECT id, username, email, created_at, is_admin FROM users")
            users = cursor.fetchall()
            print("\nUser accounts:")
            for user in users:
                print(f"  ID: {user[0]}")
                print(f"    Username: {user[1]}")
                print(f"    Email: {user[2]}")
                print(f"    Created: {user[3]}")
                print(f"    Admin: {user[4]}")
                print()
            
            # Check password hashes
            cursor.execute("SELECT username, password_hash FROM users")
            password_data = cursor.fetchall()
            print("Password hash validation:")
            for username, hash_val in password_data:
                if hash_val:
                    # Check if it's a bcrypt hash
                    is_bcrypt = hash_val.startswith('$2b$') or hash_val.startswith('$2a$') or hash_val.startswith('$2y$')
                    print(f"  {username}: {'✓ Valid bcrypt hash' if is_bcrypt else '✗ Invalid hash format'}")
                else:
                    print(f"  {username}: ✗ No password hash")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Users table check failed: {e}")
        return False

def check_system_settings(db_path):
    """Check system settings and setup state"""
    print_header("SYSTEM SETTINGS CHECK")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if system_settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'")
        if not cursor.fetchone():
            print("✗ System_settings table does not exist")
            conn.close()
            return False
        
        # Get all settings
        cursor.execute("SELECT key, value FROM system_settings")
        settings = cursor.fetchall()
        print(f"System settings ({len(settings)} entries):")
        
        important_settings = ['FIRST_SETUP', 'SETUP_COMPLETED', 'ADMIN_PASSWORD_SET']
        for key, value in settings:
            if any(important in key for important in important_settings):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: [value present]")
        
        # Check FIRST_SETUP specifically
        cursor.execute("SELECT value FROM system_settings WHERE key='FIRST_SETUP'")
        first_setup = cursor.fetchone()
        if first_setup:
            print(f"\n✓ FIRST_SETUP flag: {first_setup[0]}")
        else:
            print(f"\n✗ FIRST_SETUP flag not found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ System settings check failed: {e}")
        return False

def check_authentication_config():
    """Check authentication configuration"""
    print_header("AUTHENTICATION CONFIG CHECK")
    
    try:
        # Try to import auth manager
        from src.auth.auth_manager import AuthManager
        from src.core.config import config
        
        print("✓ Auth manager import successful")
        print(f"  JWT Secret Key: {'[SET]' if hasattr(config, 'jwt_secret_key') and config.jwt_secret_key else '[NOT SET]'}")
        print(f"  JWT Expiry: {getattr(config, 'jwt_expiry_hours', 'NOT SET')} hours")
        
        # Try to create auth manager instance
        auth_manager = AuthManager()
        print("✓ Auth manager initialization successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Authentication config check failed: {e}")
        return False

def test_password_verification(db_path):
    """Test password verification for existing users"""
    print_header("PASSWORD VERIFICATION TEST")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, password_hash FROM users LIMIT 3")
        users = cursor.fetchall()
        
        if not users:
            print("No users found for password testing")
            conn.close()
            return
        
        print("Testing password hash verification (with sample passwords):")
        test_passwords = ['admin', 'password', '123456', 'admin123', 'zenith']
        
        for username, stored_hash in users:
            print(f"\nUser: {username}")
            if not stored_hash:
                print("  ✗ No password hash stored")
                continue
                
            # Test common passwords
            found_match = False
            for test_pass in test_passwords:
                try:
                    if bcrypt.checkpw(test_pass.encode('utf-8'), stored_hash.encode('utf-8')):
                        print(f"  ✓ Password matches: '{test_pass}'")
                        found_match = True
                        break
                except Exception as e:
                    continue
            
            if not found_match:
                print(f"  ? Password not in common list (this is normal for security)")
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Password verification test failed: {e}")

def check_logs():
    """Check application logs"""
    print_header("LOGS CHECK")
    
    log_paths = [
        project_root / "data" / "logs" / "startup.log",
        project_root / "logs" / "app.log",
        project_root / "zenith.log",
    ]
    
    for log_path in log_paths:
        if log_path.exists():
            print(f"✓ Log file found: {log_path}")
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    print(f"  Lines: {len(lines)}")
                    if lines:
                        print(f"  Last entry: {lines[-1].strip()}")
            except Exception as e:
                print(f"  Error reading log: {e}")
        else:
            print(f"✗ Log file not found: {log_path}")

def check_enterprise_setup():
    """Check enterprise setup markers"""
    print_header("ENTERPRISE SETUP CHECK")
    
    enterprise_marker = project_root / ".enterprise_configured"
    if enterprise_marker.exists():
        print(f"✓ Enterprise setup marker found: {enterprise_marker}")
        stat = enterprise_marker.stat()
        print(f"  Created: {datetime.fromtimestamp(stat.st_mtime)}")
    else:
        print(f"✗ Enterprise setup marker not found: {enterprise_marker}")
    
    # Check setup scripts
    setup_scripts = [
        project_root / "start_zenith.sh",
        project_root / "start_zenith.bat",
        project_root / "run_interactive_setup.py"
    ]
    
    for script in setup_scripts:
        if script.exists():
            print(f"✓ Setup script found: {script.name}")
        else:
            print(f"✗ Setup script missing: {script.name}")

def main():
    """Run all health checks"""
    print("ZENITH HEALTH CHECK")
    print(f"Timestamp: {datetime.now()}")
    print(f"Project root: {project_root}")
    
    # Run all checks
    check_environment()
    
    db_path = check_database_files()
    if db_path:
        check_database_schema(db_path)
        check_users_table(db_path)
        check_system_settings(db_path)
        test_password_verification(db_path)
    
    check_authentication_config()
    check_logs()
    check_enterprise_setup()
    
    print_header("HEALTH CHECK COMPLETE")
    print("If you're seeing authentication errors, check:")
    print("1. User accounts exist in the database")
    print("2. Password hashes are properly formatted")
    print("3. FIRST_SETUP flag is set correctly")
    print("4. Authentication configuration is loaded")
    print("\nTo reset authentication, run: python reset_database.py")

if __name__ == "__main__":
    main()