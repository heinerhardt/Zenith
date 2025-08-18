#!/usr/bin/env python3
"""
Debug at socket level to see the actual HTTP request being sent
"""

import sys
import socket
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def patch_socket_send():
    """Patch socket to see raw HTTP data"""
    
    original_send = socket.socket.send
    original_sendall = socket.socket.sendall
    
    def logged_send(self, data):
        """Log raw socket send data"""
        try:
            # Try to decode as text to see HTTP request
            if isinstance(data, bytes):
                text_data = data.decode('utf-8', errors='ignore')
                if 'POST' in text_data and 'HTTP' in text_data:
                    print(f"\n📡 RAW HTTP REQUEST:")
                    print("=" * 50)
                    print(text_data[:1000])  # First 1000 chars
                    if len(text_data) > 1000:
                        print("... (truncated)")
                    print("=" * 50)
                    
                    # Extract URL from HTTP request
                    lines = text_data.split('\n')
                    for line in lines:
                        if line.startswith('POST'):
                            print(f"🎯 FOUND URL: {line}")
                            if '404' in line or '/spans' in line:
                                print("🚨 This might be the 404 issue!")
                            break
                elif 'GET' in text_data and 'HTTP' in text_data:
                    print(f"\n📡 RAW HTTP GET REQUEST:")
                    lines = text_data.split('\n')
                    for line in lines:
                        if line.startswith('GET'):
                            print(f"🎯 GET URL: {line}")
                            break
        except:
            pass
        
        return original_send(self, data)
    
    def logged_sendall(self, data):
        """Log raw socket sendall data"""
        try:
            if isinstance(data, bytes):
                text_data = data.decode('utf-8', errors='ignore')
                if 'POST' in text_data and 'HTTP' in text_data:
                    print(f"\n📡 RAW HTTP REQUEST (sendall):")
                    print("=" * 30)
                    # Just show the request line
                    lines = text_data.split('\n')
                    for line in lines[:10]:  # First 10 lines
                        print(line)
                        if line.startswith('POST'):
                            print(f"🎯 POST URL: {line}")
                    print("=" * 30)
        except:
            pass
        
        return original_sendall(self, data)
    
    socket.socket.send = logged_send  
    socket.socket.sendall = logged_sendall

def test_with_socket_logging():
    """Test Langfuse with socket-level HTTP logging"""
    
    print("🔍 Testing with Socket-Level HTTP Logging")
    print("=" * 60)
    
    patch_socket_send()
    
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        print("📝 Creating trace and span...")
        trace_id = client.create_trace_id()
        
        with client.start_as_current_span(
            name="socket-debug-span",
            input={"debug": "socket-level"},
            output={"test": "data"}
        ) as span:
            client.update_current_trace(
                name="socket-debug-trace",
                metadata={"debug": "socket", "catch_404": True}
            )
        
        print("✅ Data created, starting flush...")
        print("🔍 Watch for RAW HTTP REQUEST above...")
        
        # Flush - this should show the raw HTTP request
        client.flush()
        
        print("✅ Flush completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "404" in str(e):
            print("🚨 404 error confirmed")

def manual_test_comparison():
    """Do manual test for comparison"""
    
    print("\n" + "=" * 60)
    print("🧪 Manual Test for Comparison")
    
    import requests
    
    # Patch to see manual request too
    original_request = requests.request
    
    def log_manual_request(method, url, **kwargs):
        print(f"\n📡 MANUAL REQUEST: {method} {url}")
        response = original_request(method, url, **kwargs)
        print(f"   📊 Manual response: {response.status_code}")
        return response
    
    requests.request = log_manual_request
    
    # Manual test
    url = "http://localhost:3000/api/public/ingestion"
    test_data = {
        "batch": [
            {
                "id": "manual-test-002",
                "type": "trace-create",
                "timestamp": "2024-01-01T12:00:00Z",
                "body": {
                    "id": "manual-test-002",
                    "name": "manual-comparison",
                    "input": {"manual": "test"},
                    "metadata": {"source": "manual"}
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            url,
            json=test_data,
            auth=("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"),
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Manual test: {response.status_code}")
    except Exception as e:
        print(f"❌ Manual test failed: {e}")

def check_langfuse_queue():
    """Check if Langfuse has internal queue/batching"""
    
    print("\n" + "=" * 60)  
    print("🔍 Checking Langfuse Internal Queue")
    
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", 
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        # Check for queue-related attributes
        queue_attrs = ['_queue', '_batch', '_events', '_buffer', 'queue', 'batch', 'events']
        
        print("🔍 Looking for queue attributes:")
        for attr in queue_attrs:
            if hasattr(client, attr):
                value = getattr(client, attr)
                print(f"   ✅ {attr}: {type(value)} - {len(value) if hasattr(value, '__len__') else 'N/A'}")
            else:
                print(f"   ❌ {attr}: Not found")
        
        # Check if there are any pending items
        print("\n🔍 Checking for pending data...")
        
        # Force a simple operation
        trace_id = client.create_trace_id() 
        print(f"   Trace created: {trace_id}")
        
        # Check again
        for attr in queue_attrs:
            if hasattr(client, attr):
                value = getattr(client, attr)
                if hasattr(value, '__len__'):
                    print(f"   📊 {attr} size after trace: {len(value)}")
        
    except Exception as e:
        print(f"❌ Queue check failed: {e}")

if __name__ == "__main__":
    print("🕵️ Socket-Level HTTP Debug Tool")
    print("=" * 70)
    
    test_with_socket_logging()
    manual_test_comparison() 
    check_langfuse_queue()
    
    print("\n" + "=" * 70)
    print("📋 ANALYSIS:")
    print("1. Look for 'RAW HTTP REQUEST' above to see exact URL")
    print("2. Compare SDK URL vs manual URL")
    print("3. Check if SDK uses /spans, /traces, or wrong path")
    print("4. The working manual URL: /api/public/ingestion")