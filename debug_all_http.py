#!/usr/bin/env python3
"""
Debug all HTTP calls including urllib3, httpx, aiohttp etc.
"""

import sys
from pathlib import Path
import threading
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def patch_all_http_libraries():
    """Patch multiple HTTP libraries to catch all requests"""
    
    captured_requests = []
    
    # Patch requests
    try:
        import requests
        original_request = requests.request
        
        def logged_requests_request(method, url, **kwargs):
            captured_requests.append(f"REQUESTS: {method} {url}")
            print(f"🌐 REQUESTS: {method.upper()} -> {url}")
            try:
                response = original_request(method, url, **kwargs)
                print(f"   📊 Status: {response.status_code}")
                if response.status_code == 404:
                    print(f"   🚨 404 ERROR: {url}")
                return response
            except Exception as e:
                print(f"   ❌ Error: {e}")
                raise
        
        requests.request = logged_requests_request
        print("✅ Patched requests library")
    except ImportError:
        print("❌ requests not available")
    
    # Patch urllib3
    try:
        import urllib3
        original_urlopen = urllib3.poolmanager.PoolManager.urlopen
        
        def logged_urllib3_urlopen(self, method, url, **kwargs):
            full_url = f"{self.connection_pool_kw.get('scheme', 'http')}://{self.connection_pool_kw.get('host', 'unknown')}{url}"
            captured_requests.append(f"URLLIB3: {method} {full_url}")
            print(f"🌐 URLLIB3: {method.upper()} -> {full_url}")
            try:
                response = original_urlopen(self, method, url, **kwargs)
                print(f"   📊 Status: {response.status}")
                if response.status == 404:
                    print(f"   🚨 404 ERROR: {full_url}")
                return response
            except Exception as e:
                print(f"   ❌ Error: {e}")
                raise
        
        urllib3.poolmanager.PoolManager.urlopen = logged_urllib3_urlopen
        print("✅ Patched urllib3 library")
    except (ImportError, AttributeError):
        print("❌ urllib3 not available or different version")
    
    # Patch httpx if available
    try:
        import httpx
        original_httpx_request = httpx.request
        
        def logged_httpx_request(method, url, **kwargs):
            captured_requests.append(f"HTTPX: {method} {url}")
            print(f"🌐 HTTPX: {method.upper()} -> {url}")
            try:
                response = original_httpx_request(method, url, **kwargs)
                print(f"   📊 Status: {response.status_code}")
                if response.status_code == 404:
                    print(f"   🚨 404 ERROR: {url}")
                return response
            except Exception as e:
                print(f"   ❌ Error: {e}")
                raise
        
        httpx.request = logged_httpx_request
        print("✅ Patched httpx library")
    except ImportError:
        print("❌ httpx not available")
    
    # Patch socket if needed (last resort)
    try:
        import socket
        original_connect = socket.socket.connect
        
        def logged_connect(self, address):
            if isinstance(address, tuple) and len(address) == 2:
                host, port = address
                if host == 'localhost' or host == '127.0.0.1':
                    print(f"🔌 SOCKET: Connecting to {host}:{port}")
            return original_connect(self, address)
        
        socket.socket.connect = logged_connect
        print("✅ Patched socket connections")
    except:
        print("❌ Could not patch socket")
    
    return captured_requests

def test_langfuse_with_comprehensive_logging():
    """Test Langfuse with all HTTP libraries patched"""
    
    print("\n🧪 Testing Langfuse with comprehensive HTTP logging...")
    
    try:
        from langfuse import Langfuse
        
        print("📝 Creating Langfuse client...")
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        print("📝 Creating trace...")
        trace_id = client.create_trace_id()
        print(f"✅ Trace ID: {trace_id}")
        
        print("📝 Creating span...")
        with client.start_as_current_span(
            name="comprehensive-debug-span",
            input={"test": "comprehensive"},
            output={"status": "testing"}
        ) as span:
            print(f"✅ Span created: {span}")
            
            client.update_current_trace(
                name="comprehensive-debug-trace",
                metadata={"debug": "comprehensive", "purpose": "catch-404"}
            )
            print("✅ Trace updated")
        
        print("✅ Span completed")
        
        # Add a small delay to ensure data is queued
        print("⏳ Waiting 2 seconds for data to queue...")
        time.sleep(2)
        
        print("🔄 Starting flush operation...")
        print("   (Watch above for HTTP requests)")
        
        # This should trigger the 404
        client.flush()
        
        print("✅ Flush completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "404" in str(e):
            print("🚨 This is the 404 error we're trying to debug")
        
        # Show full error details
        import traceback
        print("📄 Full error trace:")
        traceback.print_exc()

def check_langfuse_internals():
    """Check Langfuse internal configuration"""
    
    print("\n🔍 Checking Langfuse Internal Configuration")
    print("=" * 50)
    
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        # Check internal attributes
        print("🔧 Checking client internals...")
        
        if hasattr(client, '_client_wrapper'):
            wrapper = client._client_wrapper
            print(f"✅ Has _client_wrapper: {type(wrapper)}")
            
            if hasattr(wrapper, 'base_url'):
                print(f"   Base URL: {wrapper.base_url}")
            if hasattr(wrapper, '_base_url'):
                print(f"   _Base URL: {wrapper._base_url}")
            if hasattr(wrapper, 'host'):
                print(f"   Host: {wrapper.host}")
        
        if hasattr(client, '_host'):
            print(f"✅ Client _host: {client._host}")
        if hasattr(client, 'host'):
            print(f"✅ Client host: {client.host}")
        if hasattr(client, '_base_url'):
            print(f"✅ Client _base_url: {client._base_url}")
        if hasattr(client, 'base_url'):
            print(f"✅ Client base_url: {client.base_url}")
            
        # Check if there's an HTTP client
        if hasattr(client, '_http_client'):
            print(f"✅ Has _http_client: {type(client._http_client)}")
        if hasattr(client, 'client'):
            print(f"✅ Has client: {type(client.client)}")
            
        print("\n🔧 Available client attributes:")
        attrs = [attr for attr in dir(client) if not attr.startswith('__')]
        for attr in attrs[:20]:  # Show first 20
            print(f"   - {attr}")
        if len(attrs) > 20:
            print(f"   ... and {len(attrs) - 20} more")
            
    except Exception as e:
        print(f"❌ Internal check failed: {e}")

if __name__ == "__main__":
    print("🕵️‍♂️ Comprehensive HTTP Debug Tool")
    print("=" * 60)
    
    # Patch all HTTP libraries
    captured = patch_all_http_libraries()
    
    # Check internals first
    check_langfuse_internals()
    
    # Run test
    test_langfuse_with_comprehensive_logging()
    
    print("\n" + "=" * 60)
    print("📊 CAPTURED REQUESTS:")
    if captured:
        for req in captured:
            print(f"  {req}")
    else:
        print("  No requests captured - may be using different HTTP method")
    
    print("\n💡 If no HTTP requests shown above:")
    print("1. Langfuse may be using internal queuing")
    print("2. May be using different HTTP library") 
    print("3. May be async requests")
    print("4. Check if flush() actually sends data or just queues it")