import streamlit as st
import sys
import os
import importlib.util
from pathlib import Path

st.title("🔍 Standalone Chat Diagnostic")

st.markdown("""
### Import-Safe Diagnostic Tool
This tool avoids all relative import issues by using direct file imports.
""")

# Setup paths
zenith_root = Path(__file__).parent
src_path = zenith_root / "src"
os.chdir(zenith_root)

# Load environment manually
@st.cache_data
def load_env():
    env_path = zenith_root / ".env"
    config = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    config[key] = value
                    os.environ[key] = value
    except Exception as e:
        st.error(f"Could not load .env: {e}")
    return config

config = load_env()

if st.button("🔧 Run Standalone Diagnostic", type="primary"):
    
    # Step 1: Environment Check
    st.write("### 📋 Step 1: Environment Configuration")
    
    ollama_enabled = config.get("OLLAMA_ENABLED", "False").lower() == "true"
    chat_provider = config.get("CHAT_PROVIDER", "openai")
    embedding_provider = config.get("EMBEDDING_PROVIDER", "openai")
    openai_key = config.get("OPENAI_API_KEY", "")
    ollama_endpoint = config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model = config.get("OLLAMA_CHAT_MODEL", "llama2")
    
    st.write(f"- **OLLAMA_ENABLED**: `{ollama_enabled}`")
    st.write(f"- **CHAT_PROVIDER**: `{chat_provider}`")
    st.write(f"- **EMBEDDING_PROVIDER**: `{embedding_provider}`")
    st.write(f"- **OpenAI API Key**: `{'✅ Set' if openai_key else '❌ Not set'}`")
    st.write(f"- **Ollama Endpoint**: `{ollama_endpoint}`")
    st.write(f"- **Ollama Chat Model**: `{ollama_chat_model}`")
    
    # Identify configuration issues
    issues = []
    if chat_provider == "ollama" and not ollama_enabled:
        issues.append("Chat provider is Ollama but OLLAMA_ENABLED=False")
    if chat_provider == "openai" and not openai_key:
        issues.append("Chat provider is OpenAI but no API key set")
    if embedding_provider == "ollama" and not ollama_enabled:
        issues.append("Embedding provider is Ollama but OLLAMA_ENABLED=False")
    
    if issues:
        st.warning("⚠️ **Configuration Issues Found:**")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("✅ Configuration looks consistent")
    
    # Step 2: Test Ollama Connection (if using Ollama)
    if ollama_enabled or chat_provider == "ollama" or embedding_provider == "ollama":
        st.write("### 🦙 Step 2: Ollama Connection Test")
        
        try:
            import requests
            
            # Test Ollama health
            health_url = f"{ollama_endpoint}/api/tags"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                st.success("✅ Ollama is running and accessible")
                
                # Check available models
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                st.write(f"**Available Models**: {models}")
                
                # Check if required models exist
                if ollama_chat_model in models:
                    st.success(f"✅ Chat model '{ollama_chat_model}' is available")
                else:
                    st.error(f"❌ Chat model '{ollama_chat_model}' not found")
                    st.write("**Solution**: Run `ollama pull " + ollama_chat_model + "`")
                
                ollama_embedding_model = config.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
                if ollama_embedding_model in models:
                    st.success(f"✅ Embedding model '{ollama_embedding_model}' is available")
                else:
                    st.error(f"❌ Embedding model '{ollama_embedding_model}' not found")
                    st.write("**Solution**: Run `ollama pull " + ollama_embedding_model + "`")
                    
            else:
                st.error(f"❌ Ollama not responding (HTTP {response.status_code})")
                st.write("**Solution**: Start Ollama with `ollama serve`")
                
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to Ollama at {ollama_endpoint}")
            st.write("**Solutions**:")
            st.write("- Start Ollama: `ollama serve`")
            st.write("- Check if endpoint URL is correct")
            st.write("- Check firewall/network settings")
            
        except Exception as e:
            st.error(f"❌ Ollama test error: {e}")
    else:
        st.info("ℹ️ Ollama not configured - skipping Ollama tests")
    
    # Step 3: Test OpenAI (if using OpenAI)
    if chat_provider == "openai" or embedding_provider == "openai":
        st.write("### 🤖 Step 3: OpenAI Connection Test")
        
        if not openai_key:
            st.error("❌ OpenAI API key not configured")
            st.write("**Solution**: Add OPENAI_API_KEY to your .env file")
        else:
            try:
                import requests
                
                # Test OpenAI API
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }
                
                # Simple API test
                test_data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
                
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=test_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ OpenAI API key is valid and working")
                elif response.status_code == 401:
                    st.error("❌ OpenAI API key is invalid")
                    st.write("**Solution**: Check your API key in .env file")
                elif response.status_code == 429:
                    st.warning("⚠️ OpenAI rate limit reached or no credits")
                    st.write("**Solution**: Check your OpenAI account billing")
                else:
                    st.error(f"❌ OpenAI API error: HTTP {response.status_code}")
                    st.code(response.text)
                    
            except Exception as e:
                st.error(f"❌ OpenAI test error: {e}")
    else:
        st.info("ℹ️ OpenAI not configured - skipping OpenAI tests")
    
    # Step 4: Test Qdrant Connection
    st.write("### 🔍 Step 4: Qdrant Vector Database Test")
    
    qdrant_url = config.get("QDRANT_URL")
    qdrant_api_key = config.get("QDRANT_API_KEY")
    collection_name = config.get("QDRANT_COLLECTION_NAME", "zenith_documents")
    
    if not qdrant_url:
        st.error("❌ QDRANT_URL not configured")
    elif not qdrant_api_key:
        st.error("❌ QDRANT_API_KEY not configured")
    else:
        try:
            import requests
            
            headers = {"api-key": qdrant_api_key}
            
            # Test Qdrant health
            health_response = requests.get(f"{qdrant_url}/health", headers=headers, timeout=10)
            
            if health_response.status_code == 200:
                st.success("✅ Qdrant connection successful")
                
                # Check collection
                collection_response = requests.get(f"{qdrant_url}/collections/{collection_name}", headers=headers, timeout=10)
                
                if collection_response.status_code == 200:
                    collection_data = collection_response.json()
                    vector_size = collection_data["result"]["config"]["params"]["vectors"]["size"]
                    points_count = collection_data["result"]["points_count"]
                    
                    st.write(f"- **Collection**: `{collection_name}` exists")
                    st.write(f"- **Vector dimensions**: `{vector_size}`")
                    st.write(f"- **Documents**: `{points_count}`")
                    
                    # Check dimension compatibility
                    effective_embedding = embedding_provider
                    if ollama_enabled and embedding_provider == "ollama":
                        ollama_model = config.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
                        expected_dims = {
                            "nomic-embed-text": 768,
                            "mxbai-embed-large": 1024,
                            "all-minilm": 384
                        }
                        expected_dim = expected_dims.get(ollama_model, 768)
                    else:
                        expected_dim = 1536  # OpenAI
                    
                    if vector_size == expected_dim:
                        st.success(f"✅ Vector dimensions match embedding provider ({expected_dim})")
                    else:
                        st.error(f"❌ Vector dimension mismatch: collection has {vector_size}, provider needs {expected_dim}")
                        st.write("**Solution**: Run `streamlit run standalone_vector_fix.py`")
                
                elif collection_response.status_code == 404:
                    st.info("ℹ️ Collection doesn't exist yet - will be created when you upload documents")
                else:
                    st.warning(f"⚠️ Collection check failed: HTTP {collection_response.status_code}")
                    
            else:
                st.error(f"❌ Qdrant connection failed: HTTP {health_response.status_code}")
                
        except Exception as e:
            st.error(f"❌ Qdrant test error: {e}")
    
    # Step 5: Summary and Recommendations
    st.write("### 🎯 Step 5: Summary & Recommendations")
    
    st.markdown("**Based on your configuration:**")
    
    if ollama_enabled:
        st.markdown("🦙 **You're configured to use Ollama**")
        st.markdown("- Make sure Ollama is running: `ollama serve`")
        st.markdown(f"- Make sure models are available: `ollama pull {ollama_chat_model}`")
        if chat_provider != "ollama":
            st.warning(f"⚠️ Consider setting CHAT_PROVIDER=ollama in .env")
        if embedding_provider != "ollama":
            st.warning(f"⚠️ Consider setting EMBEDDING_PROVIDER=ollama in .env")
    else:
        st.markdown("🤖 **You're configured to use OpenAI**")
        if not openai_key:
            st.error("❌ You need to set OPENAI_API_KEY in .env")
        else:
            st.markdown("- API key is configured ✅")
    
    st.markdown("**Common fixes for chat issues:**")
    st.markdown("1. 🔄 **Restart your main app** after any configuration changes")
    st.markdown("2. 🔧 **Use Force Reinitialize** in admin panel to test providers")
    st.markdown("3. 📝 **Check logs** in your main app for detailed error messages")
    st.markdown("4. 🔍 **Run vector fix** if you see dimension errors")

# Quick fix buttons
st.markdown("---")
st.markdown("### 🛠️ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔧 Fix Settings"):
        st.info("Run: `streamlit run settings_emergency_fix.py`")

with col2:
    if st.button("🔍 Fix Vector Dimensions"):
        st.info("Run: `streamlit run standalone_vector_fix.py`")

with col3:
    if st.button("📋 Show Manual Steps"):
        st.info("""
        **Manual troubleshooting:**
        1. Check if Ollama is running: `ollama list`
        2. Pull required models: `ollama pull llama2`
        3. Test OpenAI key in browser/curl
        4. Restart main Streamlit app
        """)

# Configuration summary
st.markdown("---")
st.markdown("### 📋 Your Current Configuration")

with st.expander("Show full configuration"):
    for key, value in config.items():
        if 'API_KEY' in key or 'SECRET' in key:
            display_value = f"{value[:10]}..." if value else "Not set"
        else:
            display_value = value
        st.write(f"**{key}**: `{display_value}`")

st.markdown("### 💡 Understanding the Issue")
st.info("""
**"Chat engine initialized but no return"** typically means:

1. **Provider fails during first request** - The engine creates successfully but the AI provider (OpenAI/Ollama) fails when trying to generate a response
2. **Configuration mismatch** - Settings say use Ollama but it's not running, or OpenAI but no API key
3. **Network/timeout issues** - Provider is unreachable or takes too long to respond
4. **Model not available** - Ollama model not downloaded, or OpenAI model not accessible

The diagnostic above should identify which specific issue you're experiencing.
""")
