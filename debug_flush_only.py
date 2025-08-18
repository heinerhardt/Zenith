#!/usr/bin/env python3
"""
Debug only the flush operation to catch the 404
"""

import requests
import sys
import json
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_flush_operation():
    """Debug just the flush operation to catch 404"""
    
    print("🔍 Debugging Flush Operation Only")
    print("=" * 50)
    
    # Store original request
    original_request = requests.request
    flush_requests = []
    
    def capture_request(method, url, **kwargs):
        """Capture and log requests during flush"""
        
        # Store this request
        request_info = {
            'method': method,
            'url': url,
            'kwargs': kwargs.copy()
        }
        flush_requests.append(request_info)
        
        print(f"\n🌐 FLUSH REQUEST: {method.upper()} -> {url}")
        
        # Show key details
        if 'headers' in kwargs:
            print(f"   📋 Content-Type: {kwargs['headers'].get('Content-Type', 'None')}")
            auth = kwargs['headers'].get('Authorization', 'None')
            if auth != 'None':
                print(f"   🔐 Auth: {auth[:20]}...")
        
        if 'json' in kwargs:
            data = kwargs['json']
            print(f"   📦 JSON payload size: {len(json.dumps(data)) if data else 0} bytes")
            
            # Show batch structure if it's the ingestion format
            if isinstance(data, dict) and 'batch' in data:
                print(f"   📊 Batch items: {len(data['batch'])}")
                for i, item in enumerate(data['batch'][:3]):  # Show first 3 items
                    print(f"       Item {i+1}: type='{item.get('type')}', id='{item.get('id', 'N/A')[:20]}...'")
            else:
                print(f"   📄 Data preview: {str(data)[:100]}...")
        
        try:
            # Make the actual request
            response = original_request(method, url, **kwargs)
            
            print(f"   📊 Response: {response.status_code}")
            
            if response.status_code == 404:
                print(f"   🚨 404 NOT FOUND - THIS IS THE ISSUE!")
                print(f"   🔍 Failed URL: {url}")
                print(f"   📄 Error response: {response.text}")
                
                # Check if it's trying wrong endpoint
                if '/spans' in url:
                    print(f"   ❌ SDK is trying to use '/spans' endpoint (doesn't exist)")
                    suggested_url = url.replace('/spans', '')
                    print(f"   💡 Should probably use: {suggested_url}")
                elif '/traces' in url and url.endswith('/traces'):
                    print(f"   ❌ SDK is trying to use '/traces' endpoint")
                    suggested_url = url.replace('/traces', '/ingestion')
                    print(f"   💡 Should use: {suggested_url}")
                else:
                    print(f"   ❓ Unknown endpoint issue")
                    
            elif response.status_code in [200, 201, 202, 207]:
                print(f"   ✅ Success!")
                print(f"   📄 Response: {response.text[:100]}...")
            else:
                print(f"   ⚠️ Error {response.status_code}: {response.text[:100]}...")
            
            return response
            
        except Exception as e:
            print(f"   💥 Request failed: {e}")
            raise
    
    # Patch requests during flush
    with patch('requests.request', side_effect=capture_request):
        with patch('requests.post', side_effect=lambda url, **kwargs: capture_request('POST', url, **kwargs)):
            try:
                from langfuse import Langfuse
                
                print("🧪 Creating Langfuse client and trace...")
                
                client = Langfuse(
                    host="http://localhost:3000",
                    public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
                    secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
                )
                
                # Create a trace that will need to be flushed
                trace_id = client.create_trace_id()
                
                with client.start_as_current_span(
                    name="flush-debug-span",
                    input={"debug": "flush-test"},
                    output={"result": "pending"}
                ) as span:
                    client.update_current_trace(
                        name="flush-debug-trace",
                        metadata={"purpose": "debug-flush-404"}
                    )
                
                print("✅ Trace and span created, now flushing...")
                print("🔄 Starting flush (watch for HTTP requests above)...")
                
                # This is where the 404 should happen
                client.flush()
                
                print("✅ Flush completed without errors!")
                
            except Exception as e:
                print(f"❌ Flush failed: {e}")
                
                if "404" in str(e):
                    print("🚨 Confirmed: 404 error during flush")
                    
    print(f"\n📊 Total requests captured: {len(flush_requests)}")
    
    # Analyze captured requests
    if flush_requests:
        print("\n🔍 REQUEST ANALYSIS:")
        for i, req in enumerate(flush_requests, 1):
            print(f"{i}. {req['method']} {req['url']}")
            
        # Look for patterns
        post_requests = [r for r in flush_requests if r['method'].upper() == 'POST']
        if post_requests:
            print(f"\nPOST requests: {len(post_requests)}")
            for req in post_requests:
                print(f"  - {req['url']}")
        
        # Check for wrong endpoints
        wrong_endpoints = [r for r in flush_requests if '/spans' in r['url'] or (r['url'].endswith('/traces'))]
        if wrong_endpoints:
            print(f"\n❌ Potentially wrong endpoints detected:")
            for req in wrong_endpoints:
                print(f"  - {req['url']}")
    
    return flush_requests

if __name__ == "__main__":
    print("🕵️ Langfuse Flush Debug Tool")
    print("=" * 60)
    
    requests = debug_flush_operation()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print("The requests above show exactly what URL is getting 404")
    print("Compare with working manual test: http://localhost:3000/api/public/ingestion")
    print("If SDK uses different URL, that's the root cause of the 404 error")