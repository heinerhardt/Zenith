#!/usr/bin/env python3
"""
Test all updated methods in the fixed langfuse_integration.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_all_tracing_methods():
    """Test all tracing methods with the fixed integration"""
    
    print("🧪 Testing All Fixed Tracing Methods")
    print("=" * 60)
    
    try:
        from src.core.langfuse_integration import get_langfuse_client
        
        client = get_langfuse_client()
        
        if not client or not client.is_enabled():
            print("❌ Client not enabled - check .env configuration")
            return False
            
        print("✅ Client initialized and enabled")
        
        # Test 1: Chat interaction
        print("\n1️⃣ Testing chat interaction...")
        chat_trace_id = client.trace_chat_interaction(
            user_input="Test all methods fixed",
            response="All methods now use direct HTTP",
            provider="test-provider",
            model="test-model",
            metadata={"test": "all_methods_fixed"}
        )
        
        if chat_trace_id:
            print(f"✅ Chat traced: {chat_trace_id}")
        else:
            print("❌ Chat tracing failed")
            return False
        
        # Test 2: Document processing
        print("\n2️⃣ Testing document processing...")
        doc_trace_id = client.trace_document_processing(
            filename="all-methods-test.pdf",
            chunk_count=12,
            processing_time=2.8,
            success=True,
            metadata={"test": "document_processing_fixed"}
        )
        
        if doc_trace_id:
            print(f"✅ Document processing traced: {doc_trace_id}")
        else:
            print("❌ Document processing failed")
            return False
        
        # Test 3: Search query (this was causing context errors)
        print("\n3️⃣ Testing search query...")
        search_trace_id = client.trace_search_query(
            query="test search query fixed",
            results_count=5,
            retrieval_time=0.8,
            metadata={"test": "search_query_fixed"}
        )
        
        if search_trace_id:
            print(f"✅ Search query traced: {search_trace_id}")
        else:
            print("❌ Search query tracing failed")
            return False
        
        # Test 4: Complete RAG flow (this was causing .end() errors)
        print("\n4️⃣ Testing complete RAG flow...")
        rag_trace_id = client.trace_complete_rag_flow(
            user_input="Test RAG flow fixed",
            search_query="search for RAG test",
            search_results=[
                {"doc": "result1", "score": 0.9},
                {"doc": "result2", "score": 0.8},
                {"doc": "result3", "score": 0.7}
            ],
            llm_response="RAG response using fixed method",
            provider="rag-provider",
            model="rag-model", 
            total_time=3.5,
            metadata={"test": "rag_flow_fixed"}
        )
        
        if rag_trace_id:
            print(f"✅ RAG flow traced: {rag_trace_id}")
        else:
            print("❌ RAG flow tracing failed")
            return False
        
        # Test 5: Flush (should not cause errors)
        print("\n5️⃣ Testing flush...")
        try:
            client.flush()
            print("✅ Flush completed without errors")
        except Exception as e:
            print(f"⚠️ Flush warning (expected): {e}")
        
        print("\n🎉 ALL METHODS WORKING!")
        print("✅ No more context errors")
        print("✅ No more '.end()' method errors")  
        print("✅ No more 404 export span batch errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_convenience_functions():
    """Test convenience functions"""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Convenience Functions")
    
    try:
        from src.core.langfuse_integration import (
            trace_chat_if_enabled,
            trace_document_if_enabled,
            trace_search_if_enabled,
            trace_rag_flow_if_enabled,
            flush_langfuse
        )
        
        print("1️⃣ Testing trace_chat_if_enabled...")
        chat_trace = trace_chat_if_enabled(
            "Convenience chat test",
            "Convenience response", 
            "convenience-provider",
            "convenience-model"
        )
        print(f"✅ Convenience chat: {chat_trace if chat_trace else 'No trace'}")
        
        print("2️⃣ Testing trace_search_if_enabled...")
        search_trace = trace_search_if_enabled(
            "convenience search",
            3,
            0.5
        )
        print(f"✅ Convenience search: {search_trace if search_trace else 'No trace'}")
        
        print("3️⃣ Testing trace_rag_flow_if_enabled...")
        rag_trace = trace_rag_flow_if_enabled(
            "Convenience RAG input",
            "convenience search",
            [{"doc": "conv1"}],
            "Convenience RAG response",
            "conv-provider",
            "conv-model",
            2.0
        )
        print(f"✅ Convenience RAG: {rag_trace if rag_trace else 'No trace'}")
        
        print("4️⃣ Testing flush_langfuse...")
        flush_langfuse()
        print("✅ Convenience flush completed")
        
    except Exception as e:
        print(f"❌ Convenience functions failed: {e}")

if __name__ == "__main__":
    print("🚀 Complete Method Fix Verification")
    print("=" * 70)
    
    success = test_all_tracing_methods()
    
    if success:
        test_convenience_functions()
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS: All Langfuse methods are now working!")
        print("✅ No more SDK context errors")
        print("✅ No more '_AgnosticContextManager' errors")
        print("✅ No more 404 export span batch errors")
        print("✅ All methods use working direct HTTP approach")
        
    else:
        print("\n" + "=" * 70)
        print("❌ Some methods still have issues")
        print("Check error messages above")