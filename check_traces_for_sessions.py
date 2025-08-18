#!/usr/bin/env python3
"""
Check if session data appears in Traces instead of dedicated Sessions UI
"""

import sys
from pathlib import Path
import uuid
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_session_test():
    """Create a clear test session to look for in Traces"""
    
    print("Creating Test Session for Manual Verification")
    print("=" * 60)
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        
        if not client or not client.is_enabled():
            print("❌ Client not enabled")
            return None, None
            
        # Create easily identifiable session
        session_id = f"MANUAL_CHECK_SESSION_{uuid.uuid4().hex[:6].upper()}"
        user_id = f"TEST_USER_{uuid.uuid4().hex[:4].upper()}"
        
        print(f"🎯 Creating session for manual check:")
        print(f"   Session ID: {session_id}")
        print(f"   User ID: {user_id}")
        
        # 1. Create session start
        print("\n1️⃣ Creating session start...")
        session_result = client.trace_session(
            session_id=session_id,
            user_id=user_id,
            session_data={
                "test_type": "manual_verification",
                "browser": "Chrome_Test",
                "created_for": "session_debugging"
            },
            metadata={
                "manual_check": True,
                "easy_to_find": True
            }
        )
        
        if session_result:
            print(f"   ✅ Session created: {session_result}")
        else:
            print("   ❌ Session creation failed")
            return None, None
        
        time.sleep(1)
        
        # 2. Create a very obvious chat interaction
        print("\n2️⃣ Creating obvious chat interaction...")
        chat_trace_id = client.trace_chat_interaction(
            user_input="🔍 MANUAL CHECK: This is a test session trace",
            response="✅ MANUAL CHECK: This response is linked to test session",
            provider="MANUAL_TEST",
            model="TEST_MODEL_FOR_SESSION",
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "manual_check": True,
                "trace_type": "session_test"
            }
        )
        
        if chat_trace_id:
            print(f"   ✅ Chat trace: {chat_trace_id}")
        else:
            print("   ❌ Chat trace failed")
        
        time.sleep(1)
        
        # 3. Create session update event
        print("\n3️⃣ Creating session update...")
        update_success = client.update_session(
            session_id=session_id,
            session_data={
                "status": "test_completed",
                "interactions": 1,
                "test_purpose": "manual_verification"
            },
            metadata={
                "final_update": True,
                "manual_check": True
            }
        )
        
        if update_success:
            print("   ✅ Session update sent")
        else:
            print("   ❌ Session update failed")
        
        print("\n" + "=" * 60)
        print("🔍 MANUAL VERIFICATION INSTRUCTIONS:")
        print("=" * 60)
        
        print("1️⃣ CHECK TRACES TAB:")
        print(f"   • Go to Langfuse UI → Tracing → Traces")
        print(f"   • Search for: {session_id}")
        print(f"   • Should see trace named 'session_start'")
        print(f"   • Should see trace named 'chat_interaction'")
        
        print("\n2️⃣ CHECK EVENTS TAB:")
        print(f"   • Go to Langfuse UI → Tracing → Events")  
        print(f"   • Search for: {session_id}")
        print(f"   • Should see event named 'session_update'")
        
        print("\n3️⃣ CHECK SESSIONS TAB:")
        print(f"   • Go to Langfuse UI → Tracing → Sessions")
        print(f"   • Look for session: {session_id}")
        print(f"   • Or filter by user: {user_id}")
        
        print("\n4️⃣ CHECK USER FILTER:")
        print(f"   • In any tab, filter by user_id: {user_id}")
        print(f"   • Should see all traces for this user")
        
        print("\n5️⃣ CHECK SEARCH:")
        print(f"   • Use search box: MANUAL_CHECK")
        print(f"   • Should find traces with this text")
        
        print(f"\n📋 WHAT TO LOOK FOR:")
        print(f"   ✅ Traces have session_id in metadata")
        print(f"   ✅ Traces are grouped by session_id") 
        print(f"   ✅ User_id links all traces")
        print(f"   ❓ Whether Sessions UI shows anything")
        
        return session_id, user_id
        
    except Exception as e:
        print(f"❌ Test creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def verify_session_data_format():
    """Show what session data looks like for debugging"""
    
    print("\n" + "=" * 60)
    print("📊 Expected Session Data Format")
    print("=" * 60)
    
    session_id = "example_session_123"
    
    print("Session Start Trace should look like:")
    print(f"""
{{
  "id": "trace_abc123",
  "type": "trace-create", 
  "body": {{
    "id": "trace_abc123",
    "name": "session_start",
    "user_id": "user_456",
    "session_id": "{session_id}",  ← KEY FIELD
    "input": {{ "action": "session_start" }},
    "output": {{ "session_status": "started" }},
    "metadata": {{ ... }}
  }}
}}
""")
    
    print("Chat Trace should look like:")
    print(f"""
{{
  "id": "trace_def456", 
  "type": "trace-create",
  "body": {{
    "id": "trace_def456",
    "name": "chat_interaction",
    "user_id": "user_456", 
    "session_id": "{session_id}",  ← SAME SESSION_ID
    "input": "user message",
    "output": "assistant response",
    "metadata": {{ "session_id": "{session_id}" }}
  }}
}}
""")

if __name__ == "__main__":
    print("🔍 Session Manual Verification Test")
    print("=" * 70)
    
    session_id, user_id = create_session_test()
    
    if session_id and user_id:
        verify_session_data_format()
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETED")
        print(f"🎯 Session ID: {session_id}")
        print(f"👤 User ID: {user_id}")
        print("\n💡 Next Steps:")
        print("1. Check Langfuse UI using instructions above")
        print("2. Report back what you see in each tab")
        print("3. This will help determine if Sessions UI exists")
        
    else:
        print("\n❌ TEST FAILED")
        print("Could not create test session - check configuration")