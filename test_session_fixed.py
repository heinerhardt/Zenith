#!/usr/bin/env python3
"""
Test the fixed session tracing that should appear in Langfuse
"""

import sys
from pathlib import Path
import uuid

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_session_visibility():
    """Test session tracing with correct format that should be visible"""
    
    print("Testing Fixed Session Tracing")
    print("=" * 50)
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        
        if not client or not client.is_enabled():
            print("Client not enabled - check .env configuration")
            return False
            
        print("Client initialized and enabled")
        
        # Generate unique identifiers
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        
        print(f"Session ID: {session_id}")
        print(f"User ID: {user_id}")
        
        # 1. Create session (will appear as a trace with name "user_session")
        print("\n1. Creating session...")
        traced_session_id = client.trace_session(
            session_id=session_id,
            user_id=user_id,
            session_data={
                "browser": "Chrome",
                "device": "Desktop",
                "start_time": "2024-01-01T10:00:00Z"
            },
            metadata={
                "platform": "web",
                "test_session": True
            }
        )
        
        if traced_session_id:
            print(f"SUCCESS: Session traced as: {traced_session_id}")
        else:
            print("FAILED: Session not traced")
            return False
        
        # 2. Add some interactions to the session
        print("\n2. Adding chat interaction to session...")
        chat_trace_id = client.trace_chat_interaction(
            user_input="Hello, I'm testing sessions",
            response="Hello! This interaction is part of your session.",
            provider="session-test",
            model="session-model",
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "interaction_number": 1
            }
        )
        
        if chat_trace_id:
            print(f"SUCCESS: Chat interaction: {chat_trace_id}")
        else:
            print("FAILED: Chat interaction not traced")
        
        # 3. Update session with activity
        print("\n3. Updating session...")
        session_updated = client.update_session(
            session_id=session_id,
            session_data={
                "interactions": 1,
                "last_activity": "2024-01-01T10:05:00Z"
            },
            metadata={
                "activity_update": True
            }
        )
        
        if session_updated:
            print("SUCCESS: Session updated")
        else:
            print("FAILED: Session update not sent")
        
        # 4. Add document processing to session
        print("\n4. Adding document processing to session...")
        doc_trace_id = client.trace_document_processing(
            filename="session_document.pdf",
            chunk_count=5,
            processing_time=1.5,
            success=True,
            metadata={
                "session_id": session_id,
                "user_id": user_id
            }
        )
        
        if doc_trace_id:
            print(f"SUCCESS: Document processing: {doc_trace_id}")
        else:
            print("FAILED: Document processing not traced")
        
        # 5. Final session update
        print("\n5. Final session update...")
        final_update = client.update_session(
            session_id=session_id,
            session_data={
                "interactions": 2,
                "documents_processed": 1,
                "session_end": "2024-01-01T10:10:00Z",
                "duration_minutes": 10
            },
            metadata={
                "session_completed": True
            }
        )
        
        if final_update:
            print("SUCCESS: Final session update sent")
        
        print("\n" + "=" * 50)
        print("RESULTS - Check Langfuse UI for:")
        print(f"1. Trace named 'user_session' with ID: {session_id}")
        print(f"2. User ID: {user_id}")
        print(f"3. Chat interaction trace: {chat_trace_id}")
        print(f"4. Document processing trace: {doc_trace_id}")
        print("5. Events named 'session_update' for session updates")
        print("\nTo find sessions in Langfuse:")
        print("- Look for traces with name 'user_session'")
        print("- Filter by user_id or session_id in metadata")
        print("- Check trace details for session_data")
        print("- Session updates appear as separate events")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Session Visibility Test")
    print("=" * 30)
    
    success = test_session_visibility()
    
    if success:
        print("\nSUCCESS: Sessions should now be visible in Langfuse!")
        print("Sessions appear as traces with name 'user_session'")
    else:
        print("\nFAILED: Check error messages above")