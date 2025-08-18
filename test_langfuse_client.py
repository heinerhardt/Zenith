#!/usr/bin/env python3
"""
Test the Langfuse client configuration and endpoint usage
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables first (before importing langfuse)
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"

def test_langfuse_client():
    """Test Langfuse client with correct configuration"""
    
    print("🔍 Testing Langfuse Client Configuration")
    print("=" * 50)
    
    # Test direct client initialization
    print("1️⃣ Testing direct client initialization...")
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        print("   ✅ Client created successfully")
        
        # Check client configuration
        if hasattr(client, '_client_wrapper'):
            if hasattr(client._client_wrapper, 'base_url'):
                print(f"   Base URL: {client._client_wrapper.base_url}")
            if hasattr(client._client_wrapper, '_base_url'):
                print(f"   _Base URL: {client._client_wrapper._base_url}")
        
        # List available methods
        methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
        print(f"   Available methods: {methods[:10]}...")  # Show first 10
        
        # Test trace creation
        print("\n2️⃣ Testing trace creation...")
        try:
            trace = client.trace(name="test-trace", input={"test": "data"})
            print(f"   ✅ Trace created: {trace.id}")
            
            # Test span creation
            print("\n3️⃣ Testing span creation...")
            span = trace.span(name="test-span", input={"span": "data"})
            print(f"   ✅ Span created")
            
            # End span
            span.end()
            print("   ✅ Span ended")
            
            # Test generation
            print("\n4️⃣ Testing generation...")
            generation = trace.generation(
                name="test-generation",
                model="test-model",
                input={"prompt": "test"},
                output={"response": "test response"}
            )
            print("   ✅ Generation created")
            generation.end()
            print("   ✅ Generation ended")
            
        except Exception as e:
            print(f"   ❌ Trace operations failed: {e}")
        
        # Test flush (this triggers the actual HTTP request)
        print("\n5️⃣ Testing flush (actual HTTP call)...")
        try:
            client.flush()
            print("   ✅ Flush successful - data sent to server!")
        except Exception as e:
            print(f"   ❌ Flush failed: {e}")
            print("   This is where the 404 error would occur")
            
            # Show more details about the error
            error_str = str(e)
            if "404" in error_str:
                print("   🚨 404 ERROR CONFIRMED")
                if "spans" in error_str:
                    print("   🔍 Error contains 'spans' - endpoint issue")
                    print("   🔧 Need to check Langfuse client version")
            
        return client
        
    except ImportError:
        print("   ❌ Langfuse not installed")
        print("   Run: pip install langfuse")
        return None
    except Exception as e:
        print(f"   ❌ Client creation failed: {e}")
        return None

def test_environment_config():
    """Test environment-based configuration"""
    
    print("\n" + "=" * 50)
    print("🌍 Testing Environment Configuration")
    
    try:
        from langfuse import Langfuse
        
        # This should use environment variables
        client = Langfuse()
        
        print("   ✅ Environment-based client created")
        
        # Test basic operation
        trace = client.trace(name="env-test-trace")
        print(f"   ✅ Environment trace created: {trace.id}")
        
        # Test flush
        client.flush()
        print("   ✅ Environment client flush successful")
        
    except Exception as e:
        print(f"   ❌ Environment config failed: {e}")

def test_project_integration():
    """Test with project's actual configuration"""
    
    print("\n" + "=" * 50) 
    print("🏗️ Testing Project Integration")
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        
        if client and client.is_enabled():
            print("   ✅ Project client is enabled")
            
            # Test a simple trace
            trace_id = client.trace_chat_interaction(
                user_input="test input",
                response="test response", 
                provider="test",
                model="test-model"
            )
            
            if trace_id:
                print(f"   ✅ Chat interaction traced: {trace_id}")
            else:
                print("   ❌ Chat interaction tracing failed")
                
            # Flush
            client.flush()
            print("   ✅ Project client flush successful")
            
        else:
            print("   ❌ Project client not enabled")
            
    except Exception as e:
        print(f"   ❌ Project integration failed: {e}")

if __name__ == "__main__":
    client = test_langfuse_client()
    test_environment_config()
    test_project_integration()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("If you see 404 errors above:")
    print("1. Check Langfuse server is running")
    print("2. Verify /api/public/ingestion endpoint exists")
    print("3. Update Langfuse client: pip install --upgrade langfuse")
    print("4. Check server logs for detailed errors")