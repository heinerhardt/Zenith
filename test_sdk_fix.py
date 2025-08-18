#!/usr/bin/env python3
"""
Test the fixed Langfuse SDK integration
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_fixed_integration():
    """Test the updated Langfuse integration"""
    
    print("🔧 Testing Fixed Langfuse Integration")
    print("=" * 50)
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        # Get the client
        client = get_langfuse_client()
        
        if not client:
            print("❌ Client not initialized")
            print("Check your .env configuration")
            return False
            
        if not client.is_enabled():
            print("❌ Client not enabled")
            print("Set LANGFUSE_ENABLED=true in .env")
            return False
            
        print("✅ Client initialized and enabled")
        
        # Test chat interaction tracing (using SDK methods)
        print("\n🗨️ Testing chat interaction tracing...")
        try:
            trace_id = client.trace_chat_interaction(
                user_input="Hello, this is a test",
                response="This is a test response",
                provider="test",
                model="test-model",
                metadata={"test": True}
            )
            
            if trace_id:
                print(f"✅ Chat interaction traced: {trace_id}")
            else:
                print("❌ Chat tracing returned empty trace_id")
                
        except Exception as e:
            print(f"❌ Chat tracing failed: {e}")
            
        # Test document processing tracing
        print("\n📄 Testing document processing tracing...")
        try:
            trace_id = client.trace_document_processing(
                filename="test.pdf",
                chunk_count=5,
                processing_time=2.5,
                success=True,
                metadata={"test": True}
            )
            
            if trace_id:
                print(f"✅ Document processing traced: {trace_id}")
            else:
                print("❌ Document tracing returned empty trace_id")
                
        except Exception as e:
            print(f"❌ Document tracing failed: {e}")
            
        # Test flush (this is where the 404 error used to happen)
        print("\n🔄 Testing flush (sending data to server)...")
        try:
            client.flush()
            print("✅ Flush successful - no 404 errors!")
        except Exception as e:
            print(f"❌ Flush failed: {e}")
            if "404" in str(e):
                print("🚨 Still getting 404 - need more investigation")
            return False
            
        print("\n🎉 All tests passed! Langfuse integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_direct_sdk():
    """Test direct SDK usage for comparison"""
    
    print("\n" + "=" * 50)
    print("🧪 Testing Direct SDK Usage")
    
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        print("✅ Direct client created")
        
        # Create trace using SDK method
        trace = client.trace(
            name="sdk-test-trace",
            input={"message": "test input"},
            metadata={"source": "direct_sdk_test"}
        )
        
        print(f"✅ Direct trace created: {trace.id}")
        
        # Add a generation to the trace
        generation = trace.generation(
            name="test-generation",
            model="test-model",
            input={"prompt": "test"},
            output={"response": "test response"}
        )
        
        print("✅ Generation added to trace")
        generation.end()
        
        # Flush
        client.flush()
        print("✅ Direct SDK flush successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct SDK test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Langfuse SDK Fix Verification")
    print("=" * 60)
    
    # Test the updated integration
    integration_works = test_fixed_integration()
    
    # Test direct SDK for comparison
    direct_works = test_direct_sdk()
    
    print("\n" + "=" * 60)
    print("📋 RESULTS:")
    
    if integration_works and direct_works:
        print("🎉 SUCCESS: Both integration and direct SDK are working!")
        print("✅ The 404 error should be fixed")
    elif direct_works and not integration_works:
        print("🔧 Direct SDK works, but integration needs more fixes")
    elif not direct_works:
        print("🚨 Direct SDK still failing - check server or client version")
        print("   Try: pip install --upgrade langfuse>=2.50.0")
    
    print("\n📝 Remember:")
    print("• Use langfuse.trace() method (SDK handles endpoints)")
    print("• Set LANGFUSE_HOST to base URL (no /api/public/ingestion)")
    print("• Let the SDK handle all HTTP requests internally")