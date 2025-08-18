#!/usr/bin/env python3
"""
Test sessions that should appear in Langfuse Sessions UI
"""

import sys
from pathlib import Path
import uuid
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_sessions_ui():
    """Create sessions that should appear in Langfuse Sessions UI"""
    
    print("Testing Sessions for Langfuse Sessions UI")
    print("=" * 50)
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        
        if not client or not client.is_enabled():
            print("Client not enabled - check .env configuration")
            return False
            
        print("Client initialized and enabled")
        
        # Create session
        session_id = f"ui_session_{uuid.uuid4().hex[:8]}"
        user_id = f"ui_user_{uuid.uuid4().hex[:6]}"
        
        print(f"Session ID: {session_id}")
        print(f"User ID: {user_id}")
        
        # 1. Initialize session (creates session_start trace with session_id)
        print("\n1. Initializing session...")
        session_result = client.trace_session(
            session_id=session_id,
            user_id=user_id,
            session_data={
                "browser": "Chrome",
                "device": "Desktop",
                "start_time": "2024-01-01T10:00:00Z"
            },
            metadata={
                "platform": "web",
                "test": True
            }
        )
        
        if session_result:
            print(f"SUCCESS: Session initialized: {session_result}")
        else:
            print("FAILED: Session not initialized")
            return False
        
        # Small delay to ensure session is processed
        time.sleep(1)
        
        # 2. Create multiple traces with the same session_id
        # This populates the session with activities
        print("\n2. Adding chat interactions to session...")
        
        for i in range(3):
            chat_trace_id = client.trace_chat_interaction(
                user_input=f"Chat message {i+1} in session",
                response=f"Response {i+1} in the session",
                provider="sessions-test",
                model="session-model",
                metadata={
                    "session_id": session_id,
                    "user_id": user_id,
                    "interaction_number": i+1
                }
            )
            
            if chat_trace_id:
                print(f"   Chat {i+1}: {chat_trace_id}")
            else:
                print(f"   FAILED: Chat {i+1}")
            
            time.sleep(0.5)  # Small delay between interactions
        
        # 3. Add document processing to session
        print("\n3. Adding document processing...")
        doc_trace_id = client.trace_document_processing(
            filename="session_document.pdf",
            chunk_count=8,
            processing_time=2.3,
            success=True,
            metadata={
                "session_id": session_id,
                "user_id": user_id
            }
        )
        
        if doc_trace_id:
            print(f"Document processing: {doc_trace_id}")
        
        # 4. Add search to session
        print("\n4. Adding search query...")
        search_trace_id = client.trace_search_query(
            query="session search test",
            results_count=5,
            retrieval_time=0.8,
            metadata={
                "session_id": session_id,
                "user_id": user_id
            }
        )
        
        if search_trace_id:
            print(f"Search query: {search_trace_id}")
        
        # 5. Update session
        print("\n5. Updating session...")
        client.update_session(
            session_id=session_id,
            session_data={
                "interactions": 3,
                "documents": 1,
                "searches": 1,
                "duration_minutes": 10
            },
            metadata={
                "completed": True
            }
        )
        
        print("\n" + "=" * 50)
        print("SESSION CREATED FOR SESSIONS UI!")
        print(f"Session ID: {session_id}")
        print(f"User ID: {user_id}")
        print("\nTO SEE IN LANGFUSE:")
        print("1. Go to Tracing -> Sessions")
        print(f"2. Look for session: {session_id}")
        print(f"3. Or filter by user: {user_id}")
        print("4. Session should show all linked traces")
        print("5. Click on session to see all activities")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Langfuse Sessions UI Test")
    print("=" * 40)
    
    success = test_sessions_ui()
    
    if success:
        print("\nSUCCESS: Session with multiple activities created!")
        print("The session should now appear in Tracing -> Sessions")
    else:
        print("\nFAILED: Check error messages above")