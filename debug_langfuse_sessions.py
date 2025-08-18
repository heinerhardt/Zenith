#!/usr/bin/env python3
"""
Debug correct Langfuse session format for Sessions UI
"""

import sys
import requests
from pathlib import Path
import uuid
from datetime import datetime, timezone

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_correct_session_format():
    """Test different session formats to find what appears in Sessions UI"""
    
    print("Testing Correct Langfuse Session Formats")
    print("=" * 50)
    
    host = "http://localhost:3000"
    auth = ("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda")
    url = f"{host}/api/public/ingestion"
    
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    user_id = f"test_user_{uuid.uuid4().hex[:6]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    
    # Different session formats to test
    session_formats = [
        {
            "name": "Session with session_id field",
            "data": {
                "batch": [{
                    "id": str(uuid.uuid4()).replace('-', ''),
                    "type": "trace-create",
                    "timestamp": timestamp,
                    "body": {
                        "id": str(uuid.uuid4()).replace('-', ''),
                        "name": "chat_session",
                        "user_id": user_id,
                        "session_id": session_id,  # This is key for Sessions UI
                        "input": {"session_start": True},
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
        },
        {
            "name": "Multiple traces with same session_id",
            "data": {
                "batch": [
                    {
                        "id": str(uuid.uuid4()).replace('-', ''),
                        "type": "trace-create",
                        "timestamp": timestamp,
                        "body": {
                            "id": str(uuid.uuid4()).replace('-', ''),
                            "name": "session_trace_1",
                            "user_id": user_id,
                            "session_id": session_id,
                            "input": {"message": "First interaction"},
                            "output": {"response": "First response"},
                            "metadata": {"interaction": 1}
                        }
                    },
                    {
                        "id": str(uuid.uuid4()).replace('-', ''),
                        "type": "trace-create", 
                        "timestamp": timestamp,
                        "body": {
                            "id": str(uuid.uuid4()).replace('-', ''),
                            "name": "session_trace_2",
                            "user_id": user_id,
                            "session_id": session_id,
                            "input": {"message": "Second interaction"},
                            "output": {"response": "Second response"},
                            "metadata": {"interaction": 2}
                        }
                    }
                ]
            }
        }
    ]
    
    for i, test_format in enumerate(session_formats, 1):
        print(f"\n{i}. Testing: {test_format['name']}")
        
        try:
            response = requests.post(
                url,
                json=test_format['data'],
                auth=auth,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code in [200, 201, 202, 207]:
                print(f"   SUCCESS: {test_format['name']}")
            else:
                print(f"   FAILED: {test_format['name']}")
                
        except Exception as e:
            print(f"   ERROR: {e}")
    
    return session_id, user_id

def create_chat_with_session(session_id, user_id):
    """Create a chat trace with session_id to populate Sessions UI"""
    
    print(f"\nCreating chat trace with session_id: {session_id}")
    
    host = "http://localhost:3000"
    auth = ("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda")
    url = f"{host}/api/public/ingestion"
    
    trace_id = str(uuid.uuid4()).replace('-', '')
    generation_id = str(uuid.uuid4()).replace('-', '')
    timestamp = datetime.now(timezone.utc).isoformat()
    
    chat_data = {
        "batch": [
            {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "chat_interaction",
                    "user_id": user_id,
                    "session_id": session_id,  # This should make it appear in Sessions
                    "input": "Hello from session test",
                    "output": "Response from session test",
                    "metadata": {
                        "provider": "test",
                        "model": "test-model"
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
                    "name": "llm_generation",
                    "model": "test-model",
                    "input": "Hello from session test",
                    "output": "Response from session test",
                    "metadata": {
                        "provider": "test"
                    }
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            url,
            json=chat_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Chat trace status: {response.status_code}")
        print(f"Chat response: {response.text}")
        
        if response.status_code in [200, 201, 202, 207]:
            print("SUCCESS: Chat trace with session_id created!")
            return True
        else:
            print("FAILED: Chat trace not created")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Langfuse Sessions UI Debug")
    print("=" * 40)
    
    session_id, user_id = test_correct_session_format()
    
    if session_id:
        chat_created = create_chat_with_session(session_id, user_id)
        
        if chat_created:
            print(f"\nCHECK LANGFUSE UI:")
            print(f"1. Go to Tracing -> Sessions")
            print(f"2. Look for session_id: {session_id}")
            print(f"3. Look for user_id: {user_id}")
            print("4. Sessions appear when traces have session_id field")
        else:
            print("\nFAILED: Could not create session traces")
    
    print(f"\nKEY INSIGHT:")
    print("Sessions in Langfuse appear when:")
    print("1. Traces have session_id field in body")
    print("2. Multiple traces share the same session_id")
    print("3. The Sessions UI groups traces by session_id")
    print("4. No special 'session' type needed - just session_id in traces")