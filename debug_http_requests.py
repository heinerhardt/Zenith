#!/usr/bin/env python3
"""
Debug HTTP requests made by Langfuse SDK to identify 404 source
"""

import requests
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_langfuse_http():
    """Monitor all HTTP requests made by Langfuse"""
    
    print("🕵️ Debugging Langfuse HTTP Requests")
    print("=" * 50)
    
    # Store original request method
    original_request = requests.request
    
    def logged_request(method, url, **kwargs):
        """Log all HTTP requests"""
        print(f"\n🌐 HTTP {method.upper()} -> {url}")
        
        # Show headers (without full auth details)
        if 'headers' in kwargs:
            headers = kwargs['headers'].copy()
            if 'Authorization' in headers:
                headers['Authorization'] = f"{headers['Authorization'][:20]}..."
            print(f"   📋 Headers: {headers}")
        
        # Show data preview
        if 'json' in kwargs:
            data_str = str(kwargs['json'])
            print(f"   📦 JSON data: {data_str[:200]}..." if len(data_str) > 200 else f"   📦 JSON data: {data_str}")
        elif 'data' in kwargs:
            data_str = str(kwargs['data'])
            print(f"   📦 Data: {data_str[:200]}..." if len(data_str) > 200 else f"   📦 Data: {data_str}")
        
        try:
            # Make the actual request
            response = original_request(method, url, **kwargs)
            
            # Log response
            status_icon = "✅" if 200 <= response.status_code < 300 else "❌"
            print(f"   {status_icon} Response: {response.status_code}")
            
            if response.status_code == 404:
                print(f"   🚨 404 NOT FOUND!")
                print(f"   🔍 URL breakdown:")
                print(f"       Full URL: {url}")
                if '?' in url:
                    base_url, params = url.split('?', 1)
                    print(f"       Base: {base_url}")
                    print(f"       Params: {params}")
                print(f"   📄 Response body: {response.text[:300]}...")
            elif response.status_code >= 400:
                print(f"   ⚠️ Error response: {response.text[:100]}...")
            else:
                print(f"   📊 Success!")
                if response.text and len(response.text) < 200:
                    print(f"   📄 Response: {response.text}")
            
            return response
            
        except Exception as e:
            print(f"   💥 Request failed: {e}")
            raise
    
    # Patch requests to log all calls
    with patch('requests.request', side_effect=logged_request):
        # Also patch requests.post, requests.get, etc.
        with patch('requests.post', side_effect=lambda url, **kwargs: logged_request('POST', url, **kwargs)):
            with patch('requests.get', side_effect=lambda url, **kwargs: logged_request('GET', url, **kwargs)):
                test_langfuse_with_logging()

def test_langfuse_with_logging():
    """Test Langfuse operations with HTTP logging"""
    
    print("🧪 Testing Langfuse with HTTP monitoring...")
    
    try:
        from langfuse import Langfuse
        
        # Create client
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        print("✅ Client created")
        
        # Create trace and span (this should work)
        print("\n📝 Creating trace and span...")
        trace_id = client.create_trace_id()
        print(f"✅ Trace ID: {trace_id}")
        
        with client.start_as_current_span(
            name="debug-span",
            input={"test": "data"},
            output={"result": "success"}
        ) as span:
            print(f"✅ Span created: {span}")
            
            # Update trace within context
            client.update_current_trace(
                name="debug-trace",
                metadata={"debug": True}
            )
            print("✅ Trace updated")
        
        print("✅ Span completed")
        
        # Now flush - this is where 404 should happen
        print("\n🔄 Flushing data (this is where 404 occurs)...")
        client.flush()
        print("✅ Flush completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "404" in str(e):
            print("🚨 This is the 404 error we're debugging!")

def test_manual_endpoint_check():
    """Manually test the endpoints Langfuse should be using"""
    
    print("\n" + "=" * 50)
    print("🔍 Manual Endpoint Testing")
    
    host = "http://localhost:3000"
    auth = ("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda")
    
    # Test the ingestion endpoint with minimal data
    url = f"{host}/api/public/ingestion"
    
    test_data = {
        "batch": [
            {
                "id": "test-trace-001",
                "type": "trace-create",
                "timestamp": "2024-01-01T12:00:00Z",
                "body": {
                    "id": "test-trace-001",
                    "name": "manual-test",
                    "input": {"test": "manual"},
                    "metadata": {"source": "manual_test"}
                }
            }
        ]
    }
    
    print(f"📡 Testing POST {url}")
    try:
        response = requests.post(
            url,
            json=test_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 Response: {response.status_code}")
        print(f"📄 Body: {response.text[:300]}...")
        
        if response.status_code == 404:
            print("🚨 Manual test also gets 404 - server configuration issue!")
        elif response.status_code in [200, 201, 202, 207]:
            print("✅ Manual test works - SDK might be using wrong endpoint")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Manual test failed: {e}")

if __name__ == "__main__":
    print("🔍 Langfuse 404 HTTP Debug Tool")
    print("=" * 60)
    
    # Test with HTTP monitoring
    debug_langfuse_http()
    
    # Test manual endpoint
    test_manual_endpoint_check()
    
    print("\n" + "=" * 60)
    print("📋 ANALYSIS:")
    print("Look at the HTTP requests above to see:")
    print("1. What exact URL is getting 404")
    print("2. What data is being sent") 
    print("3. Whether it's a server or client issue")
    print("4. Compare SDK requests vs manual requests")