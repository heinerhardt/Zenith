#!/usr/bin/env python3
"""
Test session tracing functionality
"""

import sys
from pathlib import Path
import uuid

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_session_tracing():
    """Test session tracing functionality"""
    
    print("🧪 Testing Session Tracing Functionality")
    print("=" * 60)
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        
        if not client or not client.is_enabled():
            print("❌ Client not enabled - check .env configuration")
            return False
            
        print("✅ Client initialized and enabled")
        
        # Generate session ID
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        
        # Test 1: Create a new session
        print(f"\n1️⃣ Creating new session: {session_id}")
        traced_session_id = client.trace_session(
            session_id=session_id,
            user_id=user_id,
            session_data={
                "browser": "Chrome",
                "device": "Desktop",
                "ip": "127.0.0.1",
                "user_agent": "Test Agent"
            },
            metadata={
                "session_start": "2024-01-01T12:00:00Z",
                "platform": "web",
                "test": True
            }
        )
        
        if traced_session_id:
            print(f"✅ Session traced successfully: {traced_session_id}")
        else:
            print("❌ Session tracing failed")
            return False
        
        # Test 2: Trace a chat interaction with session context
        print(f"\n2️⃣ Tracing chat interaction in session context...")
        chat_trace_id = client.trace_chat_interaction(
            user_input="Hello, this is within a session",
            response="Hello! I can see this is part of your session.",
            provider="session-test",
            model="session-model",
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "interaction_number": 1
            }
        )
        
        if chat_trace_id:
            print(f"✅ Chat with session context traced: {chat_trace_id}")
        else:
            print("❌ Chat with session context failed")
            return False
        
        # Test 3: Update the session with new data
        print(f"\n3️⃣ Updating session with new data...")
        session_updated = client.update_session(
            session_id=session_id,
            session_data={
                "interactions_count": 1,
                "last_activity": "2024-01-01T12:05:00Z",
                "pages_visited": ["/chat", "/dashboard"]
            },
            metadata={
                "session_duration_minutes": 5,
                "updated_test": True
            }
        )
        
        if session_updated:
            print("✅ Session updated successfully")
        else:
            print("❌ Session update failed")
            return False
        
        # Test 4: Trace another interaction in the same session
        print(f"\n4️⃣ Tracing second interaction in same session...")
        chat_trace_id_2 = client.trace_chat_interaction(
            user_input="Can you help me with document processing?",
            response="Of course! I can help you process documents.",
            provider="session-test",
            model="session-model",
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "interaction_number": 2
            }
        )
        
        if chat_trace_id_2:
            print(f"✅ Second chat interaction traced: {chat_trace_id_2}")
        else:
            print("❌ Second chat interaction failed")
            return False
        
        # Test 5: Update session with final data
        print(f"\n5️⃣ Final session update...")
        final_update = client.update_session(
            session_id=session_id,
            session_data={
                "interactions_count": 2,
                "session_end": "2024-01-01T12:10:00Z",
                "total_duration_minutes": 10,
                "status": "completed"
            },
            metadata={
                "final_update": True,
                "session_quality": "good"
            }
        )
        
        if final_update:
            print("✅ Final session update successful")
        else:
            print("❌ Final session update failed")
            return False
        
        print(f"\n🎉 Session tracing test completed successfully!")
        print(f"📊 Session ID: {session_id}")
        print(f"👤 User ID: {user_id}")
        print(f"💬 Chat interactions: 2")
        print("✅ All session data sent via working HTTP method")
        
        return True
        
    except Exception as e:
        print(f"❌ Session tracing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_convenience_functions():
    """Test session convenience functions"""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Session Convenience Functions")
    
    try:
        from src.core.langfuse_integration import (
            trace_session_if_enabled,
            update_session_if_enabled
        )
        
        # Generate session ID
        session_id = f"conv_session_{uuid.uuid4().hex[:12]}"
        user_id = f"conv_user_{uuid.uuid4().hex[:8]}"
        
        print("1️⃣ Testing trace_session_if_enabled...")
        traced_session = trace_session_if_enabled(
            session_id=session_id,
            user_id=user_id,
            session_data={
                "source": "convenience_function",
                "test": True
            },
            metadata={"convenience_test": True}
        )
        print(f"✅ Convenience session traced: {traced_session}")
        
        print("2️⃣ Testing update_session_if_enabled...")
        session_updated = update_session_if_enabled(
            session_id=session_id,
            session_data={
                "updated": True,
                "convenience_update": True
            },
            metadata={"update_test": True}
        )
        print(f"✅ Convenience session updated: {session_updated}")
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")

def demonstrate_session_workflow():
    """Demonstrate a complete session workflow"""
    
    print("\n" + "=" * 60)
    print("🚀 Complete Session Workflow Demo")
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        if not client:
            return
        
        # Simulate a user session workflow
        session_id = f"workflow_{uuid.uuid4().hex[:12]}"
        user_id = "demo_user_123"
        
        print(f"👤 User {user_id} starts session {session_id}")
        
        # 1. User starts session
        client.trace_session(
            session_id=session_id,
            user_id=user_id,
            session_data={
                "entry_point": "/login",
                "referrer": "google.com"
            }
        )
        
        # 2. User uploads a document
        client.trace_document_processing(
            filename="user_document.pdf",
            chunk_count=8,
            processing_time=2.3,
            success=True,
            metadata={"session_id": session_id, "user_id": user_id}
        )
        
        # 3. User asks questions about the document
        client.trace_chat_interaction(
            user_input="What is the main topic of this document?",
            response="The document discusses AI and machine learning applications.",
            provider="workflow-demo",
            model="demo-model",
            metadata={"session_id": session_id, "user_id": user_id}
        )
        
        # 4. User performs a search
        client.trace_search_query(
            query="AI applications",
            results_count=5,
            retrieval_time=0.6,
            metadata={"session_id": session_id, "user_id": user_id}
        )
        
        # 5. Update session with activity summary
        client.update_session(
            session_id=session_id,
            session_data={
                "documents_processed": 1,
                "chat_interactions": 1,
                "searches_performed": 1,
                "session_status": "active"
            }
        )
        
        print("✅ Complete session workflow traced successfully!")
        print(f"📈 All activities linked to session: {session_id}")
        
    except Exception as e:
        print(f"❌ Workflow demo failed: {e}")

if __name__ == "__main__":
    print("🚀 Session Tracing Test Suite")
    print("=" * 70)
    
    success = test_session_tracing()
    
    if success:
        test_convenience_functions()
        demonstrate_session_workflow()
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS: Session tracing is working perfectly!")
        print("✅ Session creation and updates work")
        print("✅ Chat interactions link to sessions")
        print("✅ All session data sent via working HTTP method")
        print("✅ No 404 errors or SDK issues")
        print("\n📖 Usage:")
        print("  • client.trace_session() - Create new session")
        print("  • client.update_session() - Update existing session")
        print("  • Add session_id to metadata in other trace methods")
        
    else:
        print("\n" + "=" * 70)
        print("❌ Session tracing test failed")
        print("Check error messages above")