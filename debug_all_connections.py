#!/usr/bin/env python3
"""
Debug all network connections to identify the 404 source
"""

import sys
import socket
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def patch_all_connections():
    """Patch socket connections to see ALL network activity"""
    
    original_connect = socket.socket.connect
    original_send = socket.socket.send
    original_sendall = socket.socket.sendall
    original_recv = socket.socket.recv
    
    connections = []
    
    def logged_connect(self, address):
        """Log all socket connections"""
        if isinstance(address, tuple) and len(address) == 2:
            host, port = address
            connections.append(f"{host}:{port}")
            print(f"🔌 SOCKET CONNECT: {host}:{port}")
            
            # Flag unexpected connections
            if host not in ['localhost', '127.0.0.1', '0.0.0.0'] and not host.startswith('192.168'):
                print(f"   ⚠️ External host: {host}")
            if port not in [3000, 80, 443]:
                print(f"   ⚠️ Unexpected port: {port}")
        
        return original_connect(self, address)
    
    def logged_send(self, data):
        """Log socket send data"""
        if isinstance(data, bytes):
            try:
                text = data.decode('utf-8', errors='ignore')
                if 'HTTP' in text and ('POST' in text or 'GET' in text):
                    print(f"\n📤 HTTP REQUEST SENT:")
                    print("-" * 40)
                    lines = text.split('\n')[:15]  # First 15 lines
                    for line in lines:
                        print(f"   {line}")
                        if line.startswith('POST') or line.startswith('GET'):
                            print(f"🎯 REQUEST LINE: {line}")
                            # Check for problematic endpoints
                            if '/spans' in line:
                                print("🚨 FOUND /spans ENDPOINT - This might be the 404!")
                            elif '/traces' in line and not '/api/public/ingestion' in line:
                                print("🚨 FOUND /traces ENDPOINT - This might be the 404!")
                            elif '/api/public/ingestion' in line:
                                print("✅ Correct endpoint found")
                    print("-" * 40)
            except:
                pass
        
        return original_send(self, data)
    
    def logged_sendall(self, data):
        """Log socket sendall data"""  
        if isinstance(data, bytes):
            try:
                text = data.decode('utf-8', errors='ignore')
                if 'HTTP' in text and ('POST' in text or 'GET' in text):
                    print(f"\n📤 HTTP REQUEST SENDALL:")
                    lines = text.split('\n')
                    for line in lines[:5]:  # Just first few lines
                        if line.startswith('POST') or line.startswith('GET'):
                            print(f"🎯 REQUEST: {line}")
                            break
            except:
                pass
        
        return original_sendall(self, data)
    
    def logged_recv(self, bufsize):
        """Log socket receive data"""
        data = original_recv(self, bufsize)
        
        if isinstance(data, bytes):
            try:
                text = data.decode('utf-8', errors='ignore')
                if 'HTTP' in text and ('404' in text or '200' in text or '207' in text):
                    print(f"\n📥 HTTP RESPONSE RECEIVED:")
                    lines = text.split('\n')[:10]
                    for line in lines:
                        if '404' in line or '200' in line or '207' in line:
                            print(f"🎯 RESPONSE: {line}")
                            if '404' in line:
                                print("🚨 404 RESPONSE - This is the error!")
                            break
            except:
                pass
                
        return data
    
    # Apply patches
    socket.socket.connect = logged_connect
    socket.socket.send = logged_send
    socket.socket.sendall = logged_sendall
    socket.socket.recv = logged_recv
    
    return connections

def test_langfuse_comprehensive():
    """Test Langfuse with comprehensive network monitoring"""
    
    print("🕵️ Comprehensive Network Debug")
    print("=" * 60)
    
    connections = patch_all_connections()
    
    try:
        from langfuse import Langfuse
        
        print("📝 Creating Langfuse client...")
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        print("📝 Creating trace and span...")
        trace_id = client.create_trace_id()
        
        with client.start_as_current_span(
            name="network-debug-span",
            input={"debug": "network"},
            output={"test": "comprehensive"}
        ) as span:
            client.update_current_trace(
                name="network-debug-trace",
                metadata={"debug": "network", "catch_404": True}
            )
        
        print("✅ Trace created, now flushing...")
        print("🔍 Watch for HTTP REQUEST SENT above...")
        
        # This should trigger the network activity
        client.flush()
        
        print("✅ Flush operation completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "404" in str(e):
            print("🚨 404 error confirmed - check HTTP REQUEST SENT above")
        
        # Show error details
        import traceback
        print("\n📄 Error details:")
        traceback.print_exc()
    
    print(f"\n📊 Total connections made: {len(connections)}")
    for conn in connections:
        print(f"   - {conn}")

def also_test_manual():
    """Also test manual request to compare"""
    
    print("\n" + "=" * 60)
    print("🧪 Manual Test Comparison")
    
    import requests
    
    print("📡 Manual POST to /api/public/ingestion...")
    try:
        response = requests.post(
            "http://localhost:3000/api/public/ingestion",
            json={
                "batch": [{
                    "id": "manual-network-test",
                    "type": "trace-create",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "body": {
                        "id": "manual-network-test",
                        "name": "manual-network",
                        "input": {"test": "manual"},
                        "metadata": {"source": "manual"}
                    }
                }]
            },
            auth=("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"),
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Manual test response: {response.status_code}")
        if response.status_code in [200, 207]:
            print("✅ Manual test successful")
        else:
            print(f"❌ Manual test failed: {response.text}")
    except Exception as e:
        print(f"❌ Manual test error: {e}")

if __name__ == "__main__":
    print("🔍 Comprehensive Network Connection Debug")
    print("=" * 70)
    
    test_langfuse_comprehensive()
    also_test_manual()
    
    print("\n" + "=" * 70)
    print("📋 KEY FINDINGS:")
    print("1. Look for 'HTTP REQUEST SENT' to see exact URL causing 404")
    print("2. Compare SDK request vs manual request")
    print("3. Check if SDK connects to unexpected host/port")
    print("4. Look for '/spans' or '/traces' endpoints (these cause 404)")
    print("5. Correct endpoint should be '/api/public/ingestion'")