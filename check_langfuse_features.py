#!/usr/bin/env python3
"""
Check Langfuse features and version to see if Sessions are supported
"""

import sys
import requests
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_langfuse_version():
    """Check Langfuse version and available features"""
    
    print("Checking Langfuse Server Features")
    print("=" * 50)
    
    host = "http://localhost:3000"
    
    # Try to get version/health info
    endpoints_to_check = [
        "/api/health",
        "/api/version", 
        "/api/public/version",
        "/health",
        "/.well-known/version",
        "/api/public/health"
    ]
    
    print("Checking server endpoints...")
    for endpoint in endpoints_to_check:
        url = f"{host}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            print(f"{endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"  Content: {response.text[:200]}")
        except Exception as e:
            print(f"{endpoint}: Error - {str(e)[:50]}")
    
    # Check main page for version info
    print(f"\nChecking main page...")
    try:
        response = requests.get(host, timeout=10)
        if response.status_code == 200:
            print("Main page accessible")
            # Look for version in HTML
            if "version" in response.text.lower():
                lines = response.text.split('\n')
                for line in lines:
                    if 'version' in line.lower():
                        print(f"Version info: {line.strip()[:100]}")
                        break
        else:
            print(f"Main page status: {response.status_code}")
    except Exception as e:
        print(f"Main page error: {e}")

def test_sessions_directly():
    """Test sessions with minimal data to see if they work at all"""
    
    print(f"\n" + "=" * 50)
    print("Testing Sessions with Minimal Data")
    
    import uuid
    from datetime import datetime, timezone
    
    host = "http://localhost:3000"
    auth = ("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda")
    url = f"{host}/api/public/ingestion"
    
    session_id = f"minimal_session_{uuid.uuid4().hex[:6]}"
    user_id = f"minimal_user_{uuid.uuid4().hex[:4]}"
    trace_id = str(uuid.uuid4()).replace('-', '')
    timestamp = datetime.now(timezone.utc).isoformat()
    
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    print(f"Trace ID: {trace_id}")
    
    # Minimal trace with session_id
    minimal_data = {
        "batch": [{
            "id": trace_id,
            "type": "trace-create",
            "timestamp": timestamp,
            "body": {
                "id": trace_id,
                "name": "minimal_test",
                "user_id": user_id,
                "session_id": session_id,
                "input": {"test": "minimal"},
                "output": {"result": "minimal"},
                "metadata": {"minimal_test": True}
            }
        }]
    }
    
    try:
        response = requests.post(
            url,
            json=minimal_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201, 202, 207]:
            print("SUCCESS: Minimal trace with session_id sent")
            return True
        else:
            print("FAILED: Could not send minimal trace")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def check_traces_for_session():
    """Check if any traces exist and if they have session information"""
    
    print(f"\n" + "=" * 50)
    print("Checking Existing Traces")
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        if not client:
            print("Cannot get Langfuse client")
            return
            
        print(f"Client host: {client.host}")
        print(f"Client ingestion URL: {client.ingestion_url}")
        
        # Check if we can see client internals
        if hasattr(client, 'client') and client.client:
            print("SDK client available")
            
            # Try to get some data (this might not work but worth trying)
            try:
                # Some Langfuse versions have different methods
                methods_to_try = ['get_traces', 'get_sessions', 'list_traces']
                for method in methods_to_try:
                    if hasattr(client.client, method):
                        print(f"SDK has method: {method}")
            except Exception as e:
                print(f"SDK method check failed: {e}")
        else:
            print("No SDK client available")
            
    except Exception as e:
        print(f"Error checking client: {e}")

def analyze_langfuse_ui():
    """Analyze what might be wrong with Sessions UI"""
    
    print(f"\n" + "=" * 50)
    print("Langfuse Sessions Analysis")
    
    print("""
Possible reasons Sessions don't appear:

1. LANGFUSE VERSION:
   - Sessions UI might not be available in your Langfuse version
   - Need Langfuse v2.0+ for Sessions UI
   - Self-hosted versions might have different features

2. CONFIGURATION:
   - Sessions feature might be disabled
   - Database might not support sessions
   - UI might not be built with Sessions support

3. DATA STRUCTURE:
   - session_id field might not be processed correctly
   - Need minimum number of traces per session
   - Time window requirements for session grouping

4. UI REFRESH:
   - Sessions might take time to appear
   - UI might need manual refresh
   - Caching issues

RECOMMENDATIONS:
1. Check Langfuse documentation for your version
2. Look at Traces tab - search for your session_id
3. Check if traces have session_id in metadata
4. Try the official Langfuse Python SDK examples
""")

if __name__ == "__main__":
    print("Langfuse Features & Sessions Checker")
    print("=" * 60)
    
    check_langfuse_version()
    
    success = test_sessions_directly()
    
    check_traces_for_session()
    
    analyze_langfuse_ui()
    
    if success:
        print(f"\n" + "=" * 60)
        print("RESULTS:")
        print("✅ Basic trace with session_id was sent successfully")
        print("❓ If Sessions UI still empty, it might be:")
        print("   - Langfuse version doesn't support Sessions UI")
        print("   - Feature not enabled in your instance")
        print("   - Need to check Traces tab instead")
        print("\n💡 TRY THIS:")
        print("1. Go to Tracing -> Traces")
        print("2. Search for your session_id in the search box")
        print("3. Look at trace details for session information")
        print("4. Sessions might be implicit rather than explicit UI")
    else:
        print(f"\n" + "=" * 60)
        print("❌ Could not send basic trace - check connection")