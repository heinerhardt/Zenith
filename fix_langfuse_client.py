#!/usr/bin/env python3
"""
Fix Langfuse client with correct API methods
"""

import os
from datetime import datetime

def test_correct_langfuse_api():
    """Test with the correct Langfuse API methods"""
    
    print("🔧 Testing Correct Langfuse API")
    print("=" * 40)
    
    try:
        from langfuse import Langfuse
        print("✅ Langfuse imported")
        
        # Create client
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        print("✅ Client created")
        
        # Check available methods
        methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
        print(f"📋 Available methods: {methods}")
        
        # Try different API patterns based on what's available
        success = False
        
        # Method 1: Modern API with create_trace
        if hasattr(client, 'create_trace'):
            print("\n🆕 Testing create_trace method...")
            try:
                trace = client.create_trace(
                    name="test-trace",
                    input={"test": "data"},
                    metadata={"source": "debug"}
                )
                print(f"✅ Trace created with create_trace: {trace.id}")
                success = True
            except Exception as e:
                print(f"❌ create_trace failed: {e}")
        
        # Method 2: Event-based API
        if hasattr(client, 'create_event') and not success:
            print("\n📅 Testing create_event method...")
            try:
                event = client.create_event(
                    name="test-event",
                    input={"test": "data"},
                    metadata={"source": "debug"}
                )
                print(f"✅ Event created: {event}")
                success = True
            except Exception as e:
                print(f"❌ create_event failed: {e}")
        
        # Method 3: Generation-based API  
        if hasattr(client, 'create_generation') and not success:
            print("\n🤖 Testing create_generation method...")
            try:
                generation = client.create_generation(
                    name="test-generation",
                    model="debug-model",
                    input={"prompt": "test"},
                    output={"response": "test response"}
                )
                print(f"✅ Generation created: {generation}")
                success = True
            except Exception as e:
                print(f"❌ create_generation failed: {e}")
        
        # Method 4: Direct ingestion
        if hasattr(client, 'ingest') and not success:
            print("\n📥 Testing ingest method...")
            try:
                result = client.ingest({
                    "type": "trace",
                    "name": "test-trace",
                    "input": {"test": "data"}
                })
                print(f"✅ Ingestion successful: {result}")
                success = True
            except Exception as e:
                print(f"❌ ingest failed: {e}")
        
        # Try flush anyway
        print("\n🔄 Testing flush...")
        try:
            client.flush()
            print("✅ Flush successful!")
        except Exception as e:
            print(f"❌ Flush failed: {e}")
        
        if success:
            print("\n🎉 Found working API method!")
        else:
            print("\n⚠️ No working API method found - may need client update")
            
        return client
        
    except ImportError:
        print("❌ Langfuse not installed")
        return None
    except Exception as e:
        print(f"❌ Client setup failed: {e}")
        return None

def update_project_integration():
    """Update the project's Langfuse integration with working methods"""
    
    print("\n" + "=" * 40)
    print("🔧 Updating Project Integration")
    
    # Test what methods actually work
    client = test_correct_langfuse_api()
    
    if not client:
        print("❌ Cannot update - client not working")
        return
    
    # Determine the best API pattern to use
    if hasattr(client, 'create_trace'):
        api_pattern = 'create_trace'
        print(f"📌 Will use: {api_pattern} API")
    elif hasattr(client, 'create_event'):
        api_pattern = 'create_event' 
        print(f"📌 Will use: {api_pattern} API")
    elif hasattr(client, 'create_generation'):
        api_pattern = 'create_generation'
        print(f"📌 Will use: {api_pattern} API")
    else:
        print("❌ No compatible API found")
        return
    
    print(f"\n✅ Recommended API pattern: {api_pattern}")
    print("Update your src/core/langfuse_integration.py to use this pattern")

def check_langfuse_version():
    """Check Langfuse version and compatibility"""
    
    print("\n" + "=" * 40)
    print("📦 Langfuse Version Check")
    
    try:
        import langfuse
        if hasattr(langfuse, '__version__'):
            print(f"Langfuse version: {langfuse.__version__}")
        else:
            print("Version not available")
            
        # Check for modern methods
        from langfuse import Langfuse
        client = Langfuse(host="http://localhost:3000", public_key="test", secret_key="test")
        
        modern_methods = ['create_trace', 'create_event', 'create_generation', 'trace']
        available_modern = [m for m in modern_methods if hasattr(client, m)]
        
        print(f"Modern methods available: {available_modern}")
        
        if not available_modern:
            print("⚠️ No modern methods found - need to upgrade:")
            print("   pip install --upgrade langfuse>=2.50.0")
        
    except Exception as e:
        print(f"❌ Version check failed: {e}")

def main():
    """Run all fixes"""
    
    print("🛠️ Langfuse Client Fix Suite")
    print("=" * 50)
    
    check_langfuse_version()
    update_project_integration()
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("1. The server is working (status 207 = success)")
    print("2. Update Langfuse client: pip install --upgrade langfuse")  
    print("3. Use the working API method shown above")
    print("4. Update your project code to use compatible methods")

if __name__ == "__main__":
    main()