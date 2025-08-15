#!/usr/bin/env python3
"""
Simple Langfuse test to identify the correct API pattern
"""

import os

def test_langfuse_patterns():
    """Test different Langfuse import and usage patterns"""
    
    # Set environment variables (replace with your actual values)
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-test"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-test"  
    os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
    
    print("🔍 Testing Langfuse import patterns...")
    
    # Pattern 1: Class-based import
    try:
        from langfuse import Langfuse
        print("✅ Successfully imported Langfuse class")
        
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-test",
            secret_key="sk-lf-test"
        )
        
        methods = [m for m in dir(client) if not m.startswith('_')]
        print(f"   Available methods: {methods}")
        
        if hasattr(client, 'trace'):
            print("   ✅ Has 'trace' method")
        if hasattr(client, 'create_trace'):
            print("   ✅ Has 'create_trace' method")
        if hasattr(client, 'log'):
            print("   ✅ Has 'log' method")
            
    except Exception as e:
        print(f"❌ Class import failed: {e}")
    
    # Pattern 2: Global instance
    try:
        from langfuse import langfuse
        print("✅ Successfully imported global langfuse")
        
        methods = [m for m in dir(langfuse) if not m.startswith('_')]
        print(f"   Available methods: {methods}")
        
        if hasattr(langfuse, 'trace'):
            print("   ✅ Has 'trace' method")
        if hasattr(langfuse, 'create_trace'):
            print("   ✅ Has 'create_trace' method")
        if hasattr(langfuse, 'log'):
            print("   ✅ Has 'log' method")
            
    except Exception as e:
        print(f"❌ Global import failed: {e}")
    
    # Pattern 3: Decorator import
    try:
        from langfuse.decorators import observe, langfuse_context
        print("✅ Successfully imported decorators")
        print(f"   observe: {observe}")
        print(f"   langfuse_context: {langfuse_context}")
            
    except Exception as e:
        print(f"❌ Decorator import failed: {e}")
    
    # Pattern 4: Check package version and info
    try:
        import langfuse
        if hasattr(langfuse, '__version__'):
            print(f"📦 Langfuse version: {langfuse.__version__}")
        
        # Check what's in the package
        package_contents = dir(langfuse)
        print(f"📦 Package contents: {[item for item in package_contents if not item.startswith('_')]}")
        
    except Exception as e:
        print(f"❌ Package info failed: {e}")

if __name__ == "__main__":
    test_langfuse_patterns()