#!/usr/bin/env python3
"""
Debug session format and test what Langfuse accepts
"""

import sys
import requests
from pathlib import Path
import uuid
from datetime import datetime, timezone

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_session_formats():
    """Test different session formats to see what Langfuse accepts"""
    
    print("🔍 Testing Session Formats for Langfuse")
    print("=" * 60)
    
    host = "http://localhost:3000"
    auth = ("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda")
    url = f"{host}/api/public/ingestion"
    
    session_id = f"test_session_{uuid.uuid4().hex[:12]}"
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Test different session formats
    session_formats = [
        {
            "name": "Session as Event",
            "data": {
                "batch": [{
                    "id": session_id,
                    "type": "event-create",
                    "timestamp": timestamp,
                    "body": {
                        "id": session_id,
                        "name": "session_start",
                        "input": {"user_id": user_id},
                        "output": {"session_created": True},
                        "metadata": {
                            "session_id": session_id,
                            "user_id": user_id,
                            "session_type": "web",
                            "browser": "Chrome"
                        }
                    }
                }]
            }
        },
        {
            "name": "Session as Trace",
            "data": {
                "batch": [{
                    "id": session_id,
                    "type": "trace-create", 
                    "timestamp": timestamp,
                    "body": {
                        "id": session_id,
                        "name": "user_session",
                        "user_id": user_id,
                        "session_id": session_id,
                        "input": {"session_start": True},
                        "output": {"session_status": "active"},
                        "metadata": {
                            "session_data": {
                                "browser": "Chrome",
                                "device": "Desktop"
                            },
                            "session_type": "web"
                        }
                    }
                }]
            }
        },
        {
            "name": "Session as Span",
            "data": {
                "batch": [{
                    "id": session_id,
                    "type": "span-create",
                    "timestamp": timestamp,
                    "body": {
                        "id": session_id,
                        "trace_id": session_id,  # Use session_id as trace_id
                        "name": "session_span",
                        "input": {"user_id": user_id},
                        "output": {"session_active": True},
                        "metadata": {
                            "session_data": {
                                "browser": "Chrome",
                                "device": "Desktop"
                            }
                        }
                    }
                }]
            }
        }
    ]
    
    for i, format_test in enumerate(session_formats, 1):
        print(f"\n{i}️⃣ Testing: {format_test['name']}")
        
        try:
            response = requests.post(
                url,
                json=format_test['data'],
                auth=auth,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code in [200, 201, 202, 207]:
                print(f"   ✅ {format_test['name']} - SUCCESS!")
            else:
                print(f"   ❌ {format_test['name']} - Failed")
                
        except Exception as e:
            print(f"   ❌ {format_test['name']} - Error: {e}")
    
    return session_id, user_id

def test_session_with_linked_traces(session_id, user_id):
    """Test creating traces linked to a session"""
    
    print(f"\n" + "=" * 60)
    print("🔗 Testing Session with Linked Traces")
    
    host = "http://localhost:3000"
    auth = ("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda")
    url = f"{host}/api/public/ingestion"
    
    # Create a chat trace linked to the session
    trace_id = str(uuid.uuid4()).replace('-', '')
    generation_id = str(uuid.uuid4()).replace('-', '')
    timestamp = datetime.now(timezone.utc).isoformat()
    
    linked_data = {
        "batch": [
            {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "session_chat",
                    "user_id": user_id,
                    "session_id": session_id,  # Link to session
                    "input": "Hello from session",
                    "output": "Response within session",
                    "metadata": {
                        "session_id": session_id,
                        "user_id": user_id,
                        "linked_to_session": True
                    }
                }
            },
            {
                "id": generation_id,
                "type": "generation-create",
                "timestamp": timestamp,
                "body": {
                    "id": generation_id,
                    "trace_id": trace_id,
                    "name": "session_generation",
                    "model": "session-model",
                    "input": "Hello from session",
                    "output": "Response within session",
                    "metadata": {
                        "session_id": session_id,
                        "user_id": user_id,
                        "provider": "session-test"
                    }
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            url,
            json=linked_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Linked traces status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201, 202, 207]:
            print("✅ Traces linked to session successfully!")
        else:
            print("❌ Failed to link traces to session")
            
    except Exception as e:
        print(f"❌ Error linking traces: {e}")

def check_langfuse_session_support():
    """Check if Langfuse supports sessions in UI"""
    
    print(f"\n" + "=" * 60)
    print("🔍 Checking Langfuse Session Support")
    
    print("""
📋 Langfuse Session Analysis:

1. Sessions might not appear as separate entities in Langfuse UI
2. Sessions are typically represented through:
   - Traces with session_id in metadata
   - User_id grouping in traces
   - Session context in trace metadata

3. To see sessions in Langfuse:
   - Look for traces grouped by user_id
   - Filter by session_id in metadata
   - Check trace details for session information

4. Sessions might be visible in:
   - Analytics/Dashboard view
   - User activity view  
   - Trace filtering by session_id
""")

if __name__ == "__main__":
    print("🔍 Langfuse Session Format Debug")
    print("=" * 70)
    
    session_id, user_id = test_session_formats()
    
    if session_id:
        test_session_with_linked_traces(session_id, user_id)
    
    check_langfuse_session_support()
    
    print("\n" + "=" * 70)
    print("📋 RESULTS:")
    print("1. Check which session format worked (status 207)")
    print("2. Sessions might not appear as separate UI elements")
    print("3. Look for traces with session_id in metadata")
    print("4. Sessions are often implicit through trace grouping")
    print(f"\n🔍 Check Langfuse UI for:")
    print(f"   - User ID: {user_id}")
    print(f"   - Session ID: {session_id}")
    print("   - Traces with session metadata")