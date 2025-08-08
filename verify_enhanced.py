#!/usr/bin/env python3
"""
Quick verification script to test Zenith enhanced features
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test core imports"""
    print("Testing imports...")
    
    try:
        from src.core.config import config
        print("[OK] Config import successful")
        
        from src.utils.security import PasswordManager, JWTManager
        print("[OK] Security utils import successful")
        
        from src.core.qdrant_manager import get_qdrant_client
        print("[OK] Qdrant manager import successful")
        
        from src.core.enhanced_vector_store import UserVectorStore
        print("[OK] Enhanced vector store import successful")
        
        from src.core.enhanced_chat_engine import EnhancedChatEngine
        print("[OK] Enhanced chat engine import successful")
        
        from src.auth.auth_manager import AuthenticationManager
        print("[OK] Authentication manager import successful")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_password_functionality():
    """Test password hashing"""
    print("\nTesting password functionality...")
    
    try:
        from src.utils.security import PasswordManager
        
        pm = PasswordManager()
        test_password = "TestPassword123!"
        
        # Test hashing
        hashed = pm.hash_password(test_password)
        print("[OK] Password hashing works")
        
        # Test verification
        verified = pm.verify_password(test_password, hashed)
        if verified:
            print("[OK] Password verification works")
        else:
            print("[ERROR] Password verification failed")
            return False
        
        # Test wrong password
        wrong_verified = pm.verify_password("WrongPassword", hashed)
        if not wrong_verified:
            print("[OK] Wrong password correctly rejected")
        else:
            print("[ERROR] Wrong password accepted (security issue)")
            return False
        
        return True
    except Exception as e:
        print(f"[ERROR] Password functionality error: {e}")
        return False

def test_jwt_functionality():
    """Test JWT token functionality"""
    print("\nTesting JWT functionality...")
    
    try:
        from src.utils.security import JWTManager
        
        jwt_manager = JWTManager("test-secret-key")
        test_payload = {"user_id": "test123", "username": "testuser"}
        
        # Create token
        token = jwt_manager.create_token(test_payload, expires_in_hours=1)
        print("[OK] JWT token creation works")
        
        # Verify token
        decoded = jwt_manager.verify_token(token)
        if decoded and decoded.get("user_id") == "test123":
            print("[OK] JWT token verification works")
        else:
            print("[ERROR] JWT token verification failed")
            return False
        
        return True
    except Exception as e:
        print(f"[ERROR] JWT functionality error: {e}")
        return False

def test_qdrant_connection():
    """Test Qdrant connection"""
    print("\nTesting Qdrant connection...")
    
    try:
        from src.core.qdrant_manager import get_qdrant_client
        
        qdrant_manager = get_qdrant_client()
        healthy = qdrant_manager.health_check()
        
        if healthy:
            print("[OK] Qdrant connection successful")
            
            # Test collection info
            collections = qdrant_manager.get_client().get_collections()
            print(f"[OK] Found {len(collections.collections)} collections")
            
            return True
        else:
            print("[ERROR] Qdrant connection failed")
            return False
            
    except Exception as e:
        print(f"[ERROR] Qdrant connection error: {e}")
        return False

def main():
    """Run all tests"""
    print("ZENITH ENHANCED FEATURES VERIFICATION")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Password Functionality", test_password_functionality),
        ("JWT Functionality", test_jwt_functionality),
        ("Qdrant Connection", test_qdrant_connection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"[PASS] {test_name} PASSED")
            else:
                print(f"[FAIL] {test_name} FAILED")
        except Exception as e:
            print(f"[ERROR] {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"VERIFICATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("ALL TESTS PASSED! Zenith enhanced features are working correctly.")
        print("\nYou can now:")
        print("   1. Start the app: python main.py ui --port 8502")
        print("   2. Open browser: http://127.0.0.1:8502")
        print("   3. Register a new user or use admin credentials")
        print("   4. Enjoy the enhanced features!")
    else:
        print(f"WARNING: {total - passed} tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
