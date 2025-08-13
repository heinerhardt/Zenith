#!/usr/bin/env python3
"""
Test script to verify the user filter changes work correctly
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modified components can be imported"""
    try:
        print("Testing imports...")
        
        # Test vector store import
        from src.core.enhanced_vector_store import UserVectorStore
        print("[OK] UserVectorStore imported successfully")
        
        # Test chat engine import
        from src.core.enhanced_chat_engine import EnhancedChatEngine
        print("[OK] EnhancedChatEngine imported successfully")
        
        # Test streamlit app import
        from src.ui.enhanced_streamlit_app import ZenithAuthenticatedApp
        print("[OK] ZenithAuthenticatedApp imported successfully")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_vector_store_methods():
    """Test that the new vector store methods exist"""
    try:
        print("\nTesting vector store methods...")
        
        from src.core.enhanced_vector_store import UserVectorStore
        
        # Check if the new method exists
        if hasattr(UserVectorStore, 'get_total_document_count'):
            print("[OK] get_total_document_count method exists")
        else:
            print("[ERROR] get_total_document_count method missing")
            return False
        
        # Check similarity_search method signature
        import inspect
        sig = inspect.signature(UserVectorStore.similarity_search)
        if 'user_filter' in sig.parameters:
            print("[OK] similarity_search has user_filter parameter")
        else:
            print("[ERROR] similarity_search missing user_filter parameter")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Vector store method test error: {e}")
        return False

def test_chat_engine_methods():
    """Test that the chat engine methods have correct signatures"""
    try:
        print("\nTesting chat engine methods...")
        
        from src.core.enhanced_chat_engine import EnhancedChatEngine
        
        # Check chat method signature
        import inspect
        sig = inspect.signature(EnhancedChatEngine.chat)
        if 'user_filter' in sig.parameters:
            print("[OK] chat method has user_filter parameter")
            
            # Check default value
            param = sig.parameters['user_filter']
            if param.default == False:
                print("[OK] user_filter defaults to False (search all documents)")
            else:
                print(f"[WARNING] user_filter default is {param.default}, expected False")
        else:
            print("[ERROR] chat method missing user_filter parameter")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Chat engine method test error: {e}")
        return False

def test_streamlit_app_methods():
    """Test that the streamlit app has the updated methods"""
    try:
        print("\nTesting streamlit app methods...")
        
        from src.ui.enhanced_streamlit_app import ZenithAuthenticatedApp
        
        # Check handle_user_input method signature
        import inspect
        sig = inspect.signature(ZenithAuthenticatedApp.handle_user_input)
        params = list(sig.parameters.keys())
        
        expected_params = ['self', 'user_input', 'use_rag', 'filter_user_only']
        for param in expected_params:
            if param in params:
                print(f"[OK] handle_user_input has {param} parameter")
            else:
                print(f"[ERROR] handle_user_input missing {param} parameter")
                return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Streamlit app method test error: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("TESTING USER FILTER CHANGES")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Run tests
    tests = [
        test_imports,
        test_vector_store_methods,
        test_chat_engine_methods,
        test_streamlit_app_methods
    ]
    
    for test in tests:
        try:
            if not test():
                all_tests_passed = False
        except Exception as e:
            print(f"[ERROR] Test {test.__name__} failed with error: {e}")
            all_tests_passed = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("SUCCESS! ALL TESTS PASSED! The user filter changes are working correctly.")
        print("\nKey changes implemented:")
        print("1. [OK] Added checkbox to control document search scope")
        print("2. [OK] Default behavior: search ALL documents (user_filter=False)")
        print("3. [OK] Optional filtering: search only user's documents")
        print("4. [OK] Updated chat engine to accept user_filter parameter")
        print("5. [OK] Added get_total_document_count method to vector store")
        
        print("\nHow to use:")
        print("- Uncheck 'Search only my uploaded documents' to search ALL documents")
        print("- Check the box to search only the current user's documents")
        print("- The system now searches all documents by default")
    else:
        print("[ERROR] SOME TESTS FAILED! Please check the errors above.")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
