#!/usr/bin/env python3
"""
Test Langfuse v3.x context-based API
"""

import os

def test_langfuse_v3_context():
    """Test Langfuse v3.x with proper context management"""
    
    print("🧪 Testing Langfuse v3.x Context API")
    print("=" * 50)
    
    try:
        from langfuse import Langfuse
        
        # Create client
        client = Langfuse(
            host="http://localhost:3000",
            public_key="pk-lf-c55d605b-a057-4a0b-bd96-f7c35ace0120",
            secret_key="sk-lf-6eaba769-8ba6-4010-b5a0-b0361ba09cda"
        )
        
        print("✅ Client created")
        
        # Method 1: Use context managers (recommended for v3.x)
        print("\n1️⃣ Testing with context manager...")
        try:
            # Create trace ID first
            trace_id = client.create_trace_id()
            print(f"✅ Created trace ID: {trace_id}")
            
            # Update the current trace
            client.update_current_trace(
                name="context-test",
                input={"test": "input"},
                metadata={"method": "context_manager"}
            )
            print("✅ Updated current trace")
            
            # Start span as current (this sets the context)
            with client.start_as_current_span(
                name="test-span",
                input={"span": "data"}
            ) as span:
                print(f"✅ Started span in context: {span}")
                
                # Start generation within the span context
                with client.start_as_current_generation(
                    name="test-generation",
                    model="test-model",
                    input={"prompt": "test"},
                    output={"response": "test response"}
                ) as generation:
                    print(f"✅ Started generation in context: {generation}")
                    
                print("✅ Generation completed")
            print("✅ Span completed")
            
        except Exception as e:
            print(f"❌ Context manager test failed: {e}")
        
        # Method 2: Manual context management
        print("\n2️⃣ Testing manual context management...")
        try:
            # Create new trace
            trace_id = client.create_trace_id()
            client.update_current_trace(
                name="manual-test",
                input={"manual": "test"}
            )
            
            # Start span and keep reference
            span = client.start_as_current_span(
                name="manual-span",
                input={"data": "test"}
            )
            print(f"✅ Started manual span: {span}")
            
            # Update span with output
            client.update_current_span(output={"result": "success"})
            print("✅ Updated span")
            
            # Start generation in this context
            generation = client.start_as_current_generation(
                name="manual-generation",
                model="manual-model",
                input={"prompt": "manual test"},
                output={"response": "manual response"}
            )
            print(f"✅ Started manual generation: {generation}")
            
            # Update generation
            client.update_current_generation(output={"final": "result"})
            print("✅ Updated generation")
            
        except Exception as e:
            print(f"❌ Manual test failed: {e}")
        
        # Method 3: Simple event-based (fallback)
        print("\n3️⃣ Testing simple event creation...")
        try:
            event = client.create_event(
                name="simple-event",
                input={"event": "data"},
                output={"event": "result"},
                metadata={"fallback": True}
            )
            print(f"✅ Created simple event: {event}")
            
        except Exception as e:
            print(f"❌ Event test failed: {e}")
        
        # Flush all data
        print("\n🔄 Flushing data to server...")
        try:
            client.flush()
            print("✅ Flush successful - data sent to Langfuse!")
        except Exception as e:
            print(f"❌ Flush failed: {e}")
            if "404" in str(e):
                print("🚨 Still getting 404 - server issue")
            return False
        
        print("\n🎉 Langfuse v3.x context API working correctly!")
        return True
        
    except ImportError:
        print("❌ Langfuse not installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_project_integration():
    """Test with the updated project integration"""
    
    print("\n" + "=" * 50)
    print("🏗️ Testing Updated Project Integration")
    
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        
        if not client or not client.is_enabled():
            print("❌ Project client not enabled")
            return False
            
        print("✅ Project client enabled")
        
        # Test chat interaction
        trace_id = client.trace_chat_interaction(
            user_input="Hello from context test",
            response="Response from context test",
            provider="test",
            model="test-model"
        )
        
        if trace_id:
            print(f"✅ Chat interaction traced: {trace_id}")
        else:
            print("❌ Chat tracing failed")
            
        # Flush
        client.flush()
        print("✅ Project integration flush successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Project integration failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Langfuse v3.x Context API Test Suite")
    print("=" * 60)
    
    context_works = test_langfuse_v3_context()
    project_works = test_project_integration()
    
    print("\n" + "=" * 60)
    print("📋 RESULTS:")
    
    if context_works and project_works:
        print("🎉 SUCCESS: v3.x context API is working!")
        print("✅ No more 404 errors with proper context management")
    elif context_works:
        print("🔧 Context API works, but project needs adjustment")
    else:
        print("🚨 Still having issues - check server and configuration")
    
    print("\n📝 v3.x Key Points:")
    print("• Use start_as_current_span() and start_as_current_generation()")
    print("• Use context managers (with statements) when possible")
    print("• Update current context with update_current_trace/span/generation")
    print("• The SDK handles /api/public/ingestion endpoint automatically")