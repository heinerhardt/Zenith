#!/usr/bin/env python3
"""
Simple session test to debug why sessions don't appear
"""

import sys
import requests
from pathlib import Path
import uuid
from datetime import datetime, timezone

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_simple_session():
    """Test simple session format"""
    
    print("Testing Session Formats for Langfuse")
    print("=" * 50)
    
    host = "http://localhost:3000"
    auth = ("pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120", "sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda")
    url = f"{host}/api/public/ingestion"
    
    session_id = f"debug_session_{uuid.uuid4().hex[:8]}"
    user_id = f"debug_user_{uuid.uuid4().hex[:6]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    
    # Test 1: Session as trace (most likely to work)
    print("\nTesting session as trace...")
    
    session_data = {
        "batch": [{
            "id": session_id,
            "type": "trace-create", 
            "timestamp": timestamp,
            "body": {
                "id": session_id,
                "name": "user_session",
                "user_id": user_id,
                "session_id": session_id,
                "input": {"session_start": True, "user_id": user_id},
                "output": {"session_status": "active"},
                "metadata": {
                    "session_type": "web",
                    "browser": "Chrome",
                    "device": "Desktop",
                    "is_session": True
                }
            }
        }]
    }
    
    try:
        response = requests.post(
            url,
            json=session_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201, 202, 207]:
            print("SUCCESS: Session trace created!")
            
            # Now create a chat trace linked to this session
            print("\nCreating chat linked to session...")
            
            chat_trace_id = str(uuid.uuid4()).replace('-', '')
            generation_id = str(uuid.uuid4()).replace('-', '')
            
            chat_data = {
                "batch": [
                    {
                        "id": chat_trace_id,
                        "type": "trace-create",
                        "timestamp": timestamp,
                        "body": {
                            "id": chat_trace_id,
                            "name": "session_chat",
                            "user_id": user_id,
                            "session_id": session_id,
                            "input": "Hello, this chat is linked to a session",
                            "output": "Response within the session context",
                            "metadata": {
                                "session_id": session_id,
                                "user_id": user_id,
                                "interaction_type": "chat",
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
                            "trace_id": chat_trace_id,
                            "name": "session_chat_generation",
                            "model": "session-model",
                            "input": "Hello, this chat is linked to a session",
                            "output": "Response within the session context",
                            "metadata": {
                                "session_id": session_id,
                                "user_id": user_id,
                                "provider": "session-test"
                            }
                        }
                    }
                ]
            }
            
            chat_response = requests.post(
                url,
                json=chat_data,
                auth=auth,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Chat status: {chat_response.status_code}")
            print(f"Chat response: {chat_response.text}")
            
            return session_id, user_id
            
        else:
            print("FAILED: Session trace not created")
            return None, None
            
    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == "__main__":
    print("Simple Session Test")
    print("=" * 30)
    
    session_id, user_id = test_simple_session()
    
    if session_id:
        print(f"\nSUCCESS! Check Langfuse UI for:")
        print(f"- Session trace: {session_id}")
        print(f"- User ID: {user_id}")
        print(f"- Look for traces with name 'user_session'")
        print(f"- Filter by user_id or session_id in metadata")
    else:
        print("\nFAILED: Could not create session")