#!/usr/bin/env python3
"""
Simple Langfuse debug script to identify the 404 issue
"""

import requests
import json
import base64
from datetime import datetime
import os

def test_langfuse_direct():
    """Test Langfuse directly with HTTP requests"""
    
    # Configuration
    HOST = "http://localhost:3000"
    PUBLIC_KEY = "pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120"
    SECRET_KEY = "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
    
    print("🔧 Direct Langfuse HTTP Test")
    print("=" * 40)
    print(f"Host: {HOST}")
    print(f"Public Key: {PUBLIC_KEY[:20]}...")
    
    # Create proper auth header
    auth_string = f"{PUBLIC_KEY}:{SECRET_KEY}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # Test the correct endpoint
    url = f"{HOST}/api/public/ingestion"
    
    # Create minimal test data
    test_payload = {
        "batch": [
            {
                "id": "test-trace-123",
                "type": "trace-create",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "body": {
                    "id": "test-trace-123", 
                    "name": "debug-test",
                    "input": {"test": "data"},
                    "metadata": {"source": "debug"}
                }
            }
        ]
    }
    
    print(f"\n📡 Testing: {url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(url, json=test_payload, headers=headers, timeout=10)
        
        print(f"\n📊 Response:")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {response.text}")
        
        if response.status_code == 404:
            print("\n❌ 404 ERROR - Endpoint not found!")
            print("This means your Langfuse server doesn't have the ingestion endpoint")
            return False
        elif response.status_code == 401:
            print("\n🔐 401 UNAUTHORIZED - Check your keys")
            return False
        elif response.status_code in [200, 201, 202]:
            print("\n✅ SUCCESS - Ingestion working!")
            return True
        else:
            print(f"\n❓ Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n🔌 CONNECTION ERROR - Server not reachable")
        return False
    except requests.exceptions.Timeout:
        print("\n⏰ TIMEOUT - Server too slow")
        return False
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return False

def test_langfuse_client():
    """Test with actual Langfuse Python client"""
    
    print("\n" + "=" * 40)
    print("🐍 Python Client Test")
    
    try:
        from langfuse import Langfuse
        print("✅ Langfuse imported")
    except ImportError:
        print("❌ Langfuse not installed")
        print("Run: pip install langfuse")
        return False
    
    try:
        # Create client
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", 
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        print("✅ Client created")
        
        # Try to create a trace
        trace = client.trace(name="client-test", input={"test": "data"})
        print(f"✅ Trace created: {trace.id}")
        
        # Try to flush (this is where 404 usually happens)
        print("🔄 Flushing data...")
        client.flush()
        print("✅ Flush successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        
        # Check if it's the 404 error
        error_str = str(e).lower()
        if "404" in error_str:
            print("🚨 This is the 404 error!")
            if "span" in error_str:
                print("🔍 Error mentions 'span' - wrong endpoint being used")
            print("🔧 Possible fixes:")
            print("   1. Update Langfuse: pip install --upgrade langfuse")
            print("   2. Check server version compatibility")
            print("   3. Restart Langfuse server")
        
        return False

def test_server_endpoints():
    """Test what endpoints actually exist"""
    
    print("\n" + "=" * 40)
    print("🔍 Server Endpoint Discovery")
    
    HOST = "http://localhost:3000"
    
    endpoints_to_test = [
        "/",
        "/api",
        "/api/public", 
        "/api/public/ingestion",
        "/api/public/ingestion/spans",  # This should 404
        "/api/public/traces",
        "/api/health",
        "/health"
    ]
    
    for endpoint in endpoints_to_test:
        url = f"{HOST}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            status_icon = "✅" if response.status_code != 404 else "❌"
            print(f"{status_icon} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"💥 {endpoint}: {str(e)[:30]}...")

def main():
    """Run all tests"""
    
    print("🧪 Langfuse 404 Debug Suite")
    print("=" * 50)
    
    # Test 1: Direct HTTP
    http_works = test_langfuse_direct()
    
    # Test 2: Python client  
    client_works = test_langfuse_client()
    
    # Test 3: Endpoint discovery
    test_server_endpoints()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    
    if http_works and client_works:
        print("🎉 Everything working! No 404 errors.")
    elif http_works and not client_works:
        print("🔧 HTTP works but Python client fails")
        print("   → Update Langfuse client: pip install --upgrade langfuse")
    elif not http_works:
        print("🚨 Server-side issue - ingestion endpoint missing")
        print("   → Check Langfuse server setup and logs")
    else:
        print("🤔 Mixed results - need more investigation")
    
    print("\nNext steps:")
    print("1. If HTTP test fails: Fix server configuration")  
    print("2. If client test fails: Update Python client")
    print("3. Check server logs for detailed errors")

if __name__ == "__main__":
    main()