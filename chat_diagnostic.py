import streamlit as st
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
os.chdir(Path(__file__).parent)

st.title("🔍 Chat Engine Diagnostic Tool")

st.markdown("""
### Problem Analysis
Chat engine initializes but then sessions get deleted, suggesting a provider failure.

Let's diagnose the issue step by step.
""")

if st.button("🔧 Run Full Diagnostic", type="primary"):
    
    # Step 1: Check environment
    st.write("### 📋 Step 1: Environment Check")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        ollama_enabled = os.getenv("OLLAMA_ENABLED", "False").lower() == "true"
        chat_provider = os.getenv("CHAT_PROVIDER", "openai")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        
        st.write(f"- OLLAMA_ENABLED: `{ollama_enabled}`")
        st.write(f"- CHAT_PROVIDER: `{chat_provider}`")
        st.write(f"- OpenAI API Key: `{'Set' if openai_key else 'Not set'}`")
        
        if chat_provider == "ollama" and not ollama_enabled:
            st.warning("⚠️ Chat provider is Ollama but OLLAMA_ENABLED=False")
        
        st.success("✅ Environment loaded")
        
    except Exception as e:
        st.error(f"❌ Environment error: {e}")
        st.stop()
    
    # Step 2: Test provider manager
    st.write("### 🔧 Step 2: Provider Manager Test")
    try:
        from core.provider_manager import get_provider_manager
        
        provider_manager = get_provider_manager()
        st.write(f"- Provider manager type: `{type(provider_manager).__name__}`")
        
        # Test getting chat provider
        try:
            chat_provider_obj = provider_manager.get_chat_provider()
            st.write(f"- Chat provider: `{type(chat_provider_obj).__name__}`")
            st.success("✅ Provider manager working")
        except Exception as provider_error:
            st.error(f"❌ Provider manager error: {provider_error}")
            st.stop()
            
    except Exception as e:
        st.error(f"❌ Provider manager import error: {e}")
        st.stop()
    
    # Step 3: Test settings manager
    st.write("### ⚙️ Step 3: Settings Manager Test")
    try:
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_current_settings()
        
        st.write(f"- Effective chat provider: `{settings_manager.get_effective_chat_provider()}`")
        st.write(f"- Effective embedding provider: `{settings_manager.get_effective_embedding_provider()}`")
        st.write(f"- Ollama enabled: `{settings_manager.is_ollama_enabled_effective()}`")
        
        st.success("✅ Settings manager working")
        
    except Exception as e:
        st.error(f"❌ Settings manager error: {e}")
        st.stop()
    
    # Step 4: Test vector store
    st.write("### 📚 Step 4: Vector Store Test")
    try:
        from core.enhanced_vector_store import UserVectorStore
        
        # Create a test vector store
        vector_store = UserVectorStore(user_id="test_user")
        
        # Test basic functionality
        stats = vector_store.get_user_stats()
        st.write(f"- Vector store stats: `{stats}`")
        
        st.success("✅ Vector store working")
        
    except Exception as e:
        st.error(f"❌ Vector store error: {e}")
        # Continue anyway, as this might work without documents
    
    # Step 5: Test chat provider directly
    st.write("### 🤖 Step 5: Direct Chat Provider Test")
    try:
        # Test the specific provider
        effective_provider = settings_manager.get_effective_chat_provider()
        
        if effective_provider == "openai":
            from core.openai_integration import OpenAIChatProvider
            
            if not current_settings.openai_api_key:
                st.error("❌ OpenAI provider selected but no API key configured")
                st.stop()
            
            provider = OpenAIChatProvider()
            st.write("- Created OpenAI provider")
            
        elif effective_provider == "ollama":
            from core.ollama_integration import OllamaChatProvider
            
            provider = OllamaChatProvider()
            st.write("- Created Ollama provider")
            
            # Test Ollama connection
            from core.ollama_integration import OllamaClient
            client = OllamaClient(current_settings.ollama_endpoint)
            
            if not client.health_check():
                st.error(f"❌ Cannot connect to Ollama at {current_settings.ollama_endpoint}")
                st.stop()
            
            st.write("✅ Ollama connection successful")
            
            # Check if chat model exists
            models = client.list_models()
            model_names = [model.name for model in models]
            
            if current_settings.ollama_chat_model not in model_names:
                st.error(f"❌ Chat model '{current_settings.ollama_chat_model}' not found")
                st.write(f"Available models: {model_names}")
                st.stop()
            
            st.write(f"✅ Chat model '{current_settings.ollama_chat_model}' available")
        
        st.success("✅ Chat provider test passed")
        
    except Exception as e:
        st.error(f"❌ Chat provider test failed: {e}")
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())
        st.stop()
    
    # Step 6: Test chat engine creation
    st.write("### 🧠 Step 6: Chat Engine Creation Test")
    try:
        from core.enhanced_chat_engine import EnhancedChatEngine
        
        # Create chat engine
        chat_engine = EnhancedChatEngine(
            user_id="test_user",
            vector_store=vector_store
        )
        
        st.write(f"- Chat engine created: `{type(chat_engine).__name__}`")
        st.write(f"- Chat provider type: `{type(chat_engine.chat_provider).__name__}`")
        
        st.success("✅ Chat engine created successfully")
        
    except Exception as e:
        st.error(f"❌ Chat engine creation failed: {e}")
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())
        st.stop()
    
    # Step 7: Test actual chat
    st.write("### 💬 Step 7: Chat Response Test")
    try:
        test_message = "Hello, can you help me?"
        
        with st.spinner("Testing chat response..."):
            response = chat_engine.chat(test_message, use_rag=False)
        
        st.write("**Test Response:**")
        st.write(f"- Answer: `{response.get('answer', 'No answer')[:100]}...`")
        st.write(f"- Error: `{response.get('error', 'None')}`")
        
        if response.get('error'):
            st.error(f"❌ Chat response error: {response['error']}")
        else:
            st.success("✅ Chat response successful!")
        
    except Exception as e:
        st.error(f"❌ Chat test failed: {e}")
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())

# Manual provider test
st.markdown("---")
st.markdown("### 🧪 Manual Provider Tests")

col1, col2 = st.columns(2)

with col1:
    if st.button("Test OpenAI Provider"):
        try:
            from core.openai_integration import OpenAIChatProvider
            provider = OpenAIChatProvider()
            
            # Simple test
            from core.enhanced_chat_engine import ChatMessage
            from datetime import datetime
            
            test_msg = ChatMessage(
                role="user",
                content="Say 'test successful'",
                timestamp=datetime.now(),
                user_id="test"
            )
            
            response = provider.chat([test_msg], "You are a helpful assistant.")
            st.success(f"✅ OpenAI Response: {response[:50]}...")
            
        except Exception as e:
            st.error(f"❌ OpenAI test failed: {e}")

with col2:
    if st.button("Test Ollama Provider"):
        try:
            from core.ollama_integration import OllamaChatProvider
            provider = OllamaChatProvider()
            
            # Simple test
            from core.enhanced_chat_engine import ChatMessage
            from datetime import datetime
            
            test_msg = ChatMessage(
                role="user",
                content="Say 'test successful'",
                timestamp=datetime.now(),
                user_id="test"
            )
            
            response = provider.chat([test_msg], "You are a helpful assistant.")
            st.success(f"✅ Ollama Response: {response[:50]}...")
            
        except Exception as e:
            st.error(f"❌ Ollama test failed: {e}")

st.markdown("---")
st.markdown("### 💡 Common Issues")

st.markdown("""
**If tests fail, check:**

1. **Provider Settings**: Make sure your effective provider matches your configuration
2. **API Keys**: OpenAI requires a valid API key
3. **Ollama Connection**: Ollama must be running and accessible
4. **Model Availability**: Required models must be downloaded in Ollama
5. **Vector Dimensions**: Collection dimensions must match embedding provider
6. **Network Issues**: Check connectivity to providers
""")

st.markdown("### 🔧 Quick Fixes")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Reset Settings"):
        st.info("Run: `streamlit run settings_emergency_fix.py`")

with col2:
    if st.button("Fix Vector Dimensions"):
        st.info("Run: `streamlit run standalone_vector_fix.py`")

with col3:
    if st.button("Force Reinitialize"):
        st.info("Use the admin panel 'Force Reinitialize' button")
