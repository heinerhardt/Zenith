#!/usr/bin/env python3
"""
Database Schema Analyzer and Fixer
Analyzes and fixes schema mismatches in the users table
"""

import sqlite3
import sys
from pathlib import Path

def analyze_database_schema():
    """Analyze the actual database schema"""
    db_path = "data/enterprise/zenith.db"
    
    print("🔍 Analyzing Database Schema")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        # Check users table schema
        print("👥 Users Table Schema:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        column_names = []
        for col in columns:
            col_id, name, data_type, not_null, default, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            primary = " (PRIMARY KEY)" if pk else ""
            print(f"  ✅ {name}: {data_type} {nullable}{primary}")
            column_names.append(name)
        
        # Check if we have the expected columns
        expected_columns = ['id', 'username', 'email', 'password_hash', 'role', 'is_active', 'created_at']
        missing_columns = []
        
        print(f"\n🔍 Column Compatibility Check:")
        for expected in expected_columns:
            if expected in column_names:
                print(f"  ✅ {expected}: Present")
            else:
                print(f"  ❌ {expected}: MISSING")
                missing_columns.append(expected)
        
        # Get actual user data
        print(f"\n👤 User Data Analysis:")
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  📊 Total users: {user_count}")
        
        if user_count > 0:
            # Get first user data
            cursor.execute("SELECT * FROM users LIMIT 1")
            user_data = cursor.fetchone()
            
            print(f"  📋 First user data:")
            for i, value in enumerate(user_data):
                col_name = column_names[i]
                display_value = value
                
                # Mask sensitive data
                if 'password' in col_name.lower() or 'hash' in col_name.lower():
                    if value:
                        display_value = f"{str(value)[:10]}...***"
                    else:
                        display_value = "NULL"
                
                print(f"    {col_name}: {display_value}")
        
        conn.close()
        
        return column_names, missing_columns
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        return [], []

def fix_database_schema(missing_columns):
    """Fix missing columns in the database"""
    if not missing_columns:
        print("✅ No schema fixes needed - all columns present")
        return True
    
    print(f"\n🔧 Fixing Database Schema")
    print("=" * 60)
    
    db_path = "data/enterprise/zenith.db"
    
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        # Define column additions
        column_fixes = {
            'role': 'ALTER TABLE users ADD COLUMN role TEXT DEFAULT "user"',
            'is_active': 'ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1', 
            'created_at': 'ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        for col in missing_columns:
            if col in column_fixes:
                print(f"➕ Adding column: {col}")
                try:
                    cursor.execute(column_fixes[col])
                    print(f"  ✅ Added {col} column")
                except Exception as e:
                    print(f"  ❌ Error adding {col}: {e}")
        
        # If role column was added, set admin user role
        if 'role' in missing_columns:
            print(f"🔑 Setting admin role for existing users")
            cursor.execute("UPDATE users SET role = 'admin' WHERE id = 1")
            print(f"  ✅ Set first user as admin")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database schema updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False

def test_authentication_query():
    """Test the authentication query with enterprise RBAC schema"""
    print(f"\n🧪 Testing Enterprise Authentication Query")
    print("=" * 60)
    
    db_path = "data/enterprise/zenith.db"
    
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        # First check if roles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roles'")
        roles_exists = cursor.fetchone()
        
        if roles_exists:
            print("✅ Enterprise RBAC detected - using role_id join")
            
            # Test with proper RBAC join
            cursor.execute("""
                SELECT u.id, u.username, u.email, r.name as role_name, u.is_active, u.password_hash
                FROM users u
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE u.is_active = 1
            """)
        else:
            print("⚠️ No roles table - using role_id directly")
            
            # Test without role join
            cursor.execute("""
                SELECT id, username, email, role_id, is_active, password_hash
                FROM users 
                WHERE is_active = 1
            """)
        
        users = cursor.fetchall()
        print(f"📋 Active users found: {len(users)}")
        
        if not users:
            # Check all users if no active ones
            print("⚠️ No active users - checking all users")
            
            if roles_exists:
                cursor.execute("""
                    SELECT u.id, u.username, u.email, r.name as role_name, u.is_active, u.password_hash
                    FROM users u
                    LEFT JOIN roles r ON u.role_id = r.id
                """)
            else:
                cursor.execute("SELECT id, username, email, role_id, is_active, password_hash FROM users")
            
            users = cursor.fetchall()
            print(f"📋 Total users found: {len(users)}")
        
        for user in users:
            user_id, username, email, role_info, is_active, password_hash = user
            status = "🟢" if is_active else "🔴"
            hash_status = "✅ HAS PASSWORD" if password_hash else "❌ NO PASSWORD"
            print(f"  {status} 👤 {username} | {email} | Role: {role_info} | {hash_status}")
            
            if password_hash:
                print(f"     Hash: {password_hash[:30]}...")
                
                # Test common passwords
                try:
                    import bcrypt
                    test_passwords = ["admin", "password", "123456", username, "zenith"]
                    
                    for pwd in test_passwords:
                        try:
                            if bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8')):
                                print(f"     🎯 PASSWORD FOUND: '{pwd}' works for {username}!")
                                break
                        except:
                            continue
                    else:
                        print(f"     ⚠️ Common passwords don't work - may need reset")
                        
                except ImportError:
                    print(f"     ❌ bcrypt not available for password testing")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Authentication query test failed: {e}")
        return False

def create_admin_user_if_needed():
    """Create admin user if none exists"""
    print(f"\n👤 Admin User Check")
    print("=" * 60)
    
    db_path = "data/enterprise/zenith.db"
    
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        # Check for admin users
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1")
        admin_count = cursor.fetchone()[0]
        
        if admin_count > 0:
            print(f"✅ Admin user exists ({admin_count} active admin users)")
            conn.close()
            return True
        
        print(f"⚠️ No active admin users found - checking all users")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        if total_users > 0:
            print(f"🔧 Setting existing user as admin")
            cursor.execute("UPDATE users SET role = 'admin', is_active = 1 WHERE id = 1")
            conn.commit()
            print(f"✅ Set first user as admin")
        else:
            print(f"❌ No users found - need to run enterprise setup")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking admin users: {e}")
        return False

def main():
    """Main database schema fixer"""
    print("🚀 Database Schema Analyzer & Fixer")
    
    # Step 1: Analyze current schema
    column_names, missing_columns = analyze_database_schema()
    
    if not column_names:
        print("❌ Could not analyze database")
        return
    
    # Step 2: Fix missing columns
    if missing_columns:
        fix_database_schema(missing_columns)
    
    # Step 3: Test authentication query
    test_authentication_query()
    
    # Step 4: Ensure admin user exists
    create_admin_user_if_needed()
    
    print(f"\n🎉 Schema Analysis Complete!")
    print(f"💡 Next steps:")
    print(f"   1. Try logging in with the username shown above")
    print(f"   2. If password doesn't work, run: python reset_database.py")
    print(f"   3. Or run enterprise setup: python run_interactive_setup.py")

if __name__ == "__main__":
    main()