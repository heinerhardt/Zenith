#!/usr/bin/env python3
"""
Quick check for existing database at data/enterprise/zenith.db
"""

import sqlite3
import sys
from pathlib import Path

def check_specific_database():
    """Check the database at data/enterprise/zenith.db"""
    
    db_path = Path("data/enterprise/zenith.db")
    
    print(f"🔍 Checking database: {db_path.resolve()}")
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path.resolve()}")
        return
    
    print(f"✅ Database found! Size: {db_path.stat().st_size:,} bytes")
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check users specifically
        if ('users',) in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"\n👥 Users in database: {user_count}")
            
            if user_count > 0:
                cursor.execute("""
                    SELECT id, username, email, role, is_active, password_hash IS NOT NULL as has_password
                    FROM users 
                    ORDER BY id
                """)
                
                users = cursor.fetchall()
                print("📋 User details:")
                for user in users:
                    user_id, username, email, role, is_active, has_password = user
                    status = "🟢" if is_active else "🔴"
                    pwd_status = "🔑" if has_password else "❌"
                    print(f"   {status} {pwd_status} ID:{user_id} | {username} | {email} | {role}")
                
                # Get admin user password hash for testing
                cursor.execute("SELECT username, password_hash FROM users WHERE role='admin' OR username='admin'")
                admin_data = cursor.fetchone()
                if admin_data:
                    username, password_hash = admin_data
                    print(f"\n🔑 Admin user: {username}")
                    if password_hash:
                        print(f"   Password hash: {password_hash[:50]}...")
                        print(f"   Hash format: {'bcrypt' if password_hash.startswith('$2') else 'unknown'}")
                        
                        # Test common passwords
                        try:
                            import bcrypt
                            test_passwords = ["admin", "password", "123456", "zenith", "admin123"]
                            print(f"\n🧪 Testing common passwords:")
                            for pwd in test_passwords:
                                try:
                                    if bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8')):
                                        print(f"   🎯 SUCCESS: '{pwd}' works!")
                                        break
                                except:
                                    continue
                            else:
                                print(f"   ⚠️  None of the common passwords worked")
                        except ImportError:
                            print("   ❌ bcrypt not available for password testing")
                    else:
                        print("   ❌ No password hash found!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    print(f"\n🔧 Environment file check:")
    print(f"Looking for: {env_path.resolve()}")
    
    if env_path.exists():
        print(f"✅ .env file found! Size: {env_path.stat().st_size} bytes")
        
        # Show first few lines
        try:
            with open(env_path, 'r') as f:
                lines = f.read().strip().split('\n')[:10]
                print("📋 Environment variables (first 10):")
                for line in lines:
                    if '=' in line and not line.startswith('#'):
                        key = line.split('=')[0].strip()
                        print(f"   - {key}")
        except Exception as e:
            print(f"❌ Error reading .env: {e}")
    else:
        print(f"❌ .env file not found at: {env_path.resolve()}")

if __name__ == "__main__":
    print("🔍 Checking Existing Database & Environment")
    check_specific_database()
    check_env_file()
    
    print(f"\n💡 If authentication still fails:")
    print(f"   1. Note the admin username and try common passwords shown above")
    print(f"   2. Check if .env file has ENABLE_AUTH=True")
    print(f"   3. Try resetting admin password: python reset_database.py")