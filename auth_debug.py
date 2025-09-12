#!/usr/bin/env python3
"""
Authentication Debug Script for Zenith PDF Chatbot
Systematically debugs "Invalid username/email or password" errors
Windows Compatible Version
"""

import os
import sys
import sqlite3
from pathlib import Path
import json

# Windows compatibility - handle different path separators
def normalize_path(path_str):
    """Normalize path for Windows compatibility"""
    return Path(path_str).resolve()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_step(step, status="🔄"):
    print(f"{status} {step}")

def print_result(key, value, status="✅"):
    print(f"  {status} {key}: {value}")

def check_database_files():
    """Check if database files exist and are accessible"""
    print_header("Database Files Check")
    
    # Common database locations (Windows compatible)
    db_locations = [
        "data/zenith.db",
        "data/enterprise.db", 
        "zenith.db",
        "enterprise.db",
        "src/data/zenith.db",
        "src/data/enterprise.db",
        "data\\zenith.db",
        "data\\enterprise.db"
    ]
    
    found_databases = []
    
    for db_path in db_locations:
        full_path = normalize_path(project_root / db_path)
        if full_path.exists():
            size = full_path.stat().st_size
            print_result(f"Found: {db_path}", f"{size:,} bytes", "✅")
            found_databases.append(str(full_path))
        else:
            print_result(f"Missing: {db_path}", "Not found", "❌")
    
    if not found_databases:
        print_result("Status", "NO DATABASE FILES FOUND!", "🚨")
        return []
    
    print_result("Total databases found", len(found_databases), "✅")
    return found_databases

def check_environment_loading():
    """Check if environment variables are loading correctly"""
    print_header("Environment Variables Check")
    
    # Check .env file
    env_file = normalize_path(project_root / ".env")
    if env_file.exists():
        print_result(".env file", f"Found at {env_file}", "✅")
        print_result("Size", f"{env_file.stat().st_size} bytes", "✅")
        
        # Try different ways to load environment
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print_result("python-dotenv loading", "Attempted", "🔄")
        except ImportError:
            print_result("python-dotenv", "Not installed", "❌")
        except Exception as e:
            print_result("dotenv loading error", str(e), "❌")
        
        # Manual env file reading
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
                print_result("Manual file read", "Success", "✅")
                
                lines = [line.strip() for line in env_content.split('\n') if line.strip() and not line.startswith('#')]
                print_result("Environment lines found", len(lines), "📊")
                
                # Parse and check key variables
                env_vars = {}
                for line in lines[:10]:  # Show first 10
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
                        print_result(f"  Found: {key.strip()}", f"'{value.strip()[:20]}...'", "📋")
                
        except Exception as e:
            print_result("Manual env read error", str(e), "❌")
        
        # Check key variables in OS environment
        key_vars = [
            "FIRST_SETUP", "JWT_SECRET_KEY", "SESSION_SECRET_KEY", 
            "DEBUG_MODE", "ENABLE_AUTH"
        ]
        
        loaded_count = 0
        for var in key_vars:
            value = os.getenv(var)
            if value:
                print_result(f"OS ENV {var}", f"'{value}' (loaded)", "✅")
                loaded_count += 1
            else:
                print_result(f"OS ENV {var}", "Not in OS environment", "❌")
        
        print_result("Variables in OS environment", f"{loaded_count}/{len(key_vars)}", "📊")
        
    else:
        print_result(".env file", f"NOT FOUND at {env_file}", "🚨")
        return False
    
    return loaded_count > 0

def test_database_connections(db_paths):
    """Test database connections and look for users"""
    print_header("Database Connection & Users Check")
    
    for db_path in db_paths:
        print(f"\n🔍 Testing database: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Check if users table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users';
            """)
            
            users_table = cursor.fetchone()
            if not users_table:
                print_result("Users table", "NOT FOUND", "❌")
                
                # Show available tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print_result("Available tables", [t[0] for t in tables], "📋")
                
                conn.close()
                continue
            
            print_result("Users table", "Found", "✅")
            
            # Get user count
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print_result("Total users", user_count, "📊")
            
            if user_count > 0:
                # Get user details
                cursor.execute("""
                    SELECT id, username, email, role, is_active, created_at 
                    FROM users 
                    LIMIT 5
                """)
                
                users = cursor.fetchall()
                print(f"  📋 Users in database:")
                for user in users:
                    user_id, username, email, role, is_active, created_at = user
                    status = "🟢" if is_active else "🔴"
                    print(f"     {status} ID:{user_id} | {username} | {email} | {role} | {created_at}")
                
                # Check for admin user specifically
                cursor.execute("""
                    SELECT username, email, role, is_active, password_hash 
                    FROM users 
                    WHERE role = 'admin' OR username = 'admin'
                """)
                
                admin_users = cursor.fetchall()
                if admin_users:
                    print_result("Admin users found", len(admin_users), "✅")
                    for admin in admin_users:
                        username, email, role, is_active, password_hash = admin
                        hash_status = "✅" if password_hash else "❌ NO HASH"
                        print(f"     🔑 Admin: {username} | {email} | Active: {is_active} | Password: {hash_status}")
                else:
                    print_result("Admin users", "NONE FOUND", "🚨")
            
            conn.close()
            
        except sqlite3.Error as e:
            print_result("Database error", str(e), "🚨")
        except Exception as e:
            print_result("Connection error", str(e), "🚨")

def test_password_verification(db_paths):
    """Test password hashing and verification"""
    print_header("Password Verification Test")
    
    # Try to import bcrypt
    try:
        import bcrypt
        print_result("bcrypt import", "Success", "✅")
    except ImportError:
        print_result("bcrypt import", "FAILED - not installed", "🚨")
        return
    
    for db_path in db_paths:
        print(f"\n🔍 Testing passwords in: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Get users with their password hashes
            cursor.execute("""
                SELECT username, email, password_hash 
                FROM users 
                WHERE password_hash IS NOT NULL
                LIMIT 3
            """)
            
            users = cursor.fetchall()
            if not users:
                print_result("Users with passwords", "NONE FOUND", "❌")
                conn.close()
                continue
            
            print_result("Users with password hashes", len(users), "✅")
            
            for username, email, password_hash in users:
                print(f"  👤 Testing user: {username}")
                
                if not password_hash:
                    print_result(f"  Password hash for {username}", "EMPTY", "❌")
                    continue
                
                # Check if hash looks like bcrypt
                if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
                    print_result(f"  Hash format for {username}", "bcrypt format ✅", "✅")
                    print(f"     Hash: {password_hash[:30]}...")
                    
                    # Test with common passwords
                    test_passwords = ["admin", "password", "123456", "zenith", username, "admin123"]
                    
                    found_password = False
                    for test_pass in test_passwords:
                        try:
                            if bcrypt.checkpw(test_pass.encode('utf-8'), password_hash.encode('utf-8')):
                                print_result(f"  🎯 PASSWORD FOUND", f"'{test_pass}' works for {username}", "🎉")
                                found_password = True
                                break
                        except Exception as e:
                            print_result(f"  bcrypt error", str(e), "❌")
                            continue
                    
                    if not found_password:
                        print_result(f"  Password test for {username}", "No common passwords work", "⚠️")
                        print("     Try logging in with a password you remember setting")
                        
                else:
                    print_result(f"  Hash format for {username}", "Not bcrypt format", "❌")
                    print(f"     Hash preview: {password_hash[:50]}...")
            
            conn.close()
            
        except Exception as e:
            print_result("Password test error", str(e), "🚨")

def test_auth_imports():
    """Test authentication imports and configuration"""
    print_header("Authentication System Check")
    
    try:
        # Try to import config
        from src.core.config import config
        print_result("Config import", "Success", "✅")
        print_result("Auth enabled", getattr(config, 'enable_auth', 'Not set'), "📊")
        print_result("JWT secret set", bool(getattr(config, 'jwt_secret_key', None)), "📊")
        print_result("Session duration", f"{getattr(config, 'session_duration_hours', 'Not set')}h", "📊")
    except Exception as e:
        print_result("Config import error", str(e), "❌")
    
    # Try to import auth managers
    try:
        from src.auth.auth_manager import AuthManager
        print_result("AuthManager import", "Success", "✅")
    except Exception as e:
        print_result("AuthManager import error", str(e), "❌")
        
    try:
        from src.auth.enterprise_auth_manager import EnterpriseAuthManager
        print_result("EnterpriseAuthManager import", "Success", "✅")
    except Exception as e:
        print_result("EnterpriseAuthManager import", str(e), "❌")

def main():
    print("🚀 Starting Zenith Authentication Debug (Windows Compatible)")
    print(f"📁 Project root: {project_root}")
    print(f"🖥️  Platform: {os.name} ({sys.platform})")
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Step 1: Check database files
    databases = check_database_files()
    
    # Step 2: Check environment loading
    env_loaded = check_environment_loading()
    
    # Step 3: Test database connections and users
    if databases:
        test_database_connections(databases)
        test_password_verification(databases)
    
    # Step 4: Test auth imports
    test_auth_imports()
    
    # Summary and recommendations
    print_header("Debug Summary & Recommendations")
    print_result("Database files found", len(databases), "📊")
    print_result("Environment loading", "Working" if env_loaded else "Failed", "📊")
    
    print("\n💡 Troubleshooting Guide:")
    
    if not databases:
        print("🚨 NO DATABASE - Run enterprise setup first:")
        print("   python run_interactive_setup.py")
        print("   OR: ./start_zenith.sh --mode=setup")
        
    elif not env_loaded:
        print("🚨 ENVIRONMENT VARIABLES NOT LOADING:")
        print("   1. Check if .env file has correct format")
        print("   2. Restart your application/IDE")
        print("   3. Try manual environment loading")
        
    else:
        print("✅ DATABASE & ENVIRONMENT OK - Check password verification results above")
        print("💡 If password verification failed:")
        print("   1. Try the passwords shown above")
        print("   2. Reset admin password: python reset_database.py")
        print("   3. Run setup again: python run_interactive_setup.py")

if __name__ == "__main__":
    main()