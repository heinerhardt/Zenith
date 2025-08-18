#!/usr/bin/env python3
"""
Debug Langfuse configuration and force immediate sending
"""

import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_langfuse_configuration():
    """Debug Langfuse client configuration"""
    
    print("🔧 Langfuse Configuration Debug")
    print("=" * 50)
    
    try:
        from langfuse import Langfuse
        
        # Create client with debug info
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda",
            # Try to enable debug mode if available
            debug=True if hasattr(Langfuse, 'debug') else None
        )
        
        print(f"✅ Client created")
        
        # Check all attributes
        print("\n🔍 Client attributes:")
        attrs = [attr for attr in dir(client) if not attr.startswith('__')]
        
        config_attrs = [attr for attr in attrs if 'config' in attr.lower() or 'host' in attr.lower() or 'url' in attr.lower()]
        for attr in config_attrs:
            try:
                value = getattr(client, attr)
                print(f"   🔧 {attr}: {value}")
            except:
                print(f"   ❌ {attr}: Error accessing")
        
        # Check for batching/queue settings
        queue_attrs = [attr for attr in attrs if 'batch' in attr.lower() or 'queue' in attr.lower() or 'flush' in attr.lower()]
        print(f"\n🔍 Queue/batch related attributes:")
        for attr in queue_attrs:
            try:
                value = getattr(client, attr)
                print(f"   📊 {attr}: {value}")
            except:
                print(f"   ❌ {attr}: Error accessing")
                
        # Check for HTTP client
        http_attrs = [attr for attr in attrs if 'client' in attr.lower() or 'http' in attr.lower()]
        print(f"\n🔍 HTTP client attributes:")
        for attr in http_attrs:
            try:
                value = getattr(client, attr)
                print(f"   🌐 {attr}: {type(value)} - {value}")
            except:
                print(f"   ❌ {attr}: Error accessing")
        
        return client
        
    except Exception as e:
        print(f"❌ Configuration debug failed: {e}")
        return None

def test_immediate_sending():
    """Try to force immediate sending"""
    
    print("\n" + "=" * 50)
    print("🚀 Testing Immediate Sending")
    
    try:
        from langfuse import Langfuse
        
        # Try different initialization patterns
        clients_to_test = []
        
        # Standard client
        client1 = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        clients_to_test.append(("Standard", client1))
        
        # Try with different host formats
        client2 = Langfuse(
            host="http://127.0.0.1:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        clients_to_test.append(("127.0.0.1", client2))
        
        # Try environment variables
        import os
        os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        
        client3 = Langfuse()  # Should use env vars
        clients_to_test.append(("Environment", client3))
        
        for name, client in clients_to_test:
            print(f"\n🧪 Testing {name} client:")
            
            try:
                # Create simple event
                event = client.create_event(
                    name=f"immediate-test-{name.lower()}",
                    input={"client": name},
                    output={"test": "immediate"},
                    metadata={"immediate": True}
                )
                print(f"   ✅ Event created: {event}")
                
                # Try multiple flush methods
                flush_methods = ['flush', 'shutdown', 'close']
                for method_name in flush_methods:
                    if hasattr(client, method_name):
                        print(f"   🔄 Trying {method_name}()...")
                        method = getattr(client, method_name)
                        method()
                        print(f"   ✅ {method_name}() completed")
                        
                        # Wait a bit to see if async request happens
                        time.sleep(1)
                        
                print(f"   ✅ {name} client test completed")
                
            except Exception as e:
                print(f"   ❌ {name} client failed: {e}")
                if "404" in str(e):
                    print(f"   🚨 404 error in {name} client")
                
    except Exception as e:
        print(f"❌ Immediate sending test failed: {e}")

def test_direct_api_call():
    """Test direct API call using langfuse internals"""
    
    print("\n" + "=" * 50)
    print("🔧 Testing Direct API Call")
    
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        # Check if client has direct API access
        if hasattr(client, 'api'):
            print("✅ Client has 'api' attribute")
            api = client.api
            print(f"   API type: {type(api)}")
            
            # Check API methods
            api_methods = [method for method in dir(api) if not method.startswith('_')]
            print(f"   API methods: {api_methods[:10]}...")  # First 10
            
            # Try to find ingestion method
            ingestion_methods = [method for method in api_methods if 'ingest' in method.lower() or 'batch' in method.lower()]
            if ingestion_methods:
                print(f"   🎯 Ingestion methods: {ingestion_methods}")
                
                # Try to use direct ingestion
                for method_name in ingestion_methods:
                    try:
                        method = getattr(api, method_name)
                        print(f"   🧪 Trying {method_name}...")
                        
                        # Create test data
                        test_batch = [{
                            "id": "direct-api-test",
                            "type": "trace-create",
                            "timestamp": "2024-01-01T12:00:00Z",
                            "body": {
                                "id": "direct-api-test",
                                "name": "direct-api",
                                "input": {"direct": "api"},
                                "metadata": {"method": "direct"}
                            }
                        }]
                        
                        # Try to call the method
                        result = method({"batch": test_batch})
                        print(f"   ✅ {method_name} result: {result}")
                        
                    except Exception as e:
                        print(f"   ❌ {method_name} failed: {e}")
                        if "404" in str(e):
                            print(f"   🚨 404 in direct API call!")
            else:
                print("   ❓ No ingestion methods found in API")
        else:
            print("❌ Client has no 'api' attribute")
            
        # Check for other potential direct methods
        direct_methods = [method for method in dir(client) if 'send' in method.lower() or 'post' in method.lower() or 'ingest' in method.lower()]
        if direct_methods:
            print(f"🔍 Direct methods on client: {direct_methods}")
        
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")

if __name__ == "__main__":
    print("🔧 Langfuse Configuration & Force Send Debug")
    print("=" * 70)
    
    client = debug_langfuse_configuration()
    test_immediate_sending()
    test_direct_api_call()
    
    print("\n" + "=" * 70)
    print("📋 SUMMARY:")
    print("1. Check client configuration above")
    print("2. Look for 404 errors in immediate sending tests")
    print("3. If direct API works, we can bypass the flush issue")
    print("4. The manual endpoint works, so server is fine")