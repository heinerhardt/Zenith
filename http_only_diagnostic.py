import streamlit as st
import os
import json
from pathlib import Path

st.title("🔍 Pure HTTP Chat Diagnostic")

st.markdown("""
### Zero-Import Diagnostic Tool
This tool uses only HTTP requests - no project imports that can cause relative import errors.
""")

# Load environment manually
@st.cache_data
def load_env():
    env_path = Path(__file__).parent / ".env"
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

if st.button("🔧 Run HTTP-Only Diagnostic", type="primary"):
    
    # Step 1: Environment Check
    st.write("### 📋 Step 1: Environment Configuration")
    
    ollama_enabled = config.get("OLLAMA_ENABLED", "False").lower() == "true"
    chat_provider = config.get("CHAT_PROVIDER", "openai")
    embedding_provider = config.get("EMBEDDING_PROVIDER", "openai")
    openai_key = config.get("OPENAI_API_KEY", "")
    ollama_endpoint = config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model = config.get("OLLAMA_CHAT_MODEL", "llama2")
    ollama_embedding_model = config.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    
    st.write(f"- **OLLAMA_ENABLED**: `{ollama_enabled}`")
    st.write(f"- **CHAT_PROVIDER**: `{chat_provider}`")
    st.write(f"- **EMBEDDING_PROVIDER**: `{embedding_provider}`")
    st.write(f"- **OpenAI API Key**: `{'✅ Set' if openai_key else '❌ Not set'}`")
    st.write(f"- **Ollama Endpoint**: `{ollama_endpoint}`")
    st.write(f"- **Ollama Chat Model**: `{ollama_chat_model}`")
    st.write(f"- **Ollama Embedding Model**: `{ollama_embedding_model}`")
    
    # Identify configuration issues
    issues = []
    if chat_provider == "ollama" and not ollama_enabled:
        issues.append("❌ Chat provider is Ollama but OLLAMA_ENABLED=False")
    if chat_provider == "openai" and not openai_key:
        issues.append("❌ Chat provider is OpenAI but no API key set")
    if embedding_provider == "ollama" and not ollama_enabled:
        issues.append("❌ Embedding provider is Ollama but OLLAMA_ENABLED=False")
    if ollama_enabled and chat_provider == "openai":
        issues.append("⚠️ Ollama is enabled but chat provider is OpenAI")
    if ollama_enabled and embedding_provider == "openai":
        issues.append("⚠️ Ollama is enabled but embedding provider is OpenAI")
    
    if issues:
        st.write("**Configuration Issues Found:**")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("✅ Configuration looks consistent")
    
    # Step 2: Test Ollama Connection (if using Ollama)
    if ollama_enabled or chat_provider == "ollama" or embedding_provider == "ollama":
        st.write("### 🦙 Step 2: Ollama Connection Test")
        
        try:
            # Use urllib instead of requests to avoid any import issues
            import urllib.request
            import urllib.error
            
            # Test Ollama health
            health_url = f"{ollama_endpoint}/api/tags"
            
            try:
                with urllib.request.urlopen(health_url, timeout=10) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        
                        st.success("✅ Ollama is running and accessible")
                        
                        # Check available models
                        models = [model['name'] for model in data.get('models', [])]
                        st.write(f"**Available Models**: {models}")
                        
                        # Check if required models exist
                        if ollama_chat_model in models:
                            st.success(f"✅ Chat model '{ollama_chat_model}' is available")
                        else:
                            st.error(f"❌ Chat model '{ollama_chat_model}' not found")
                            st.code(f"ollama pull {ollama_chat_model}")
                            st.write("☝️ Run this command to download the model")
                        
                        if ollama_embedding_model in models:
                            st.success(f"✅ Embedding model '{ollama_embedding_model}' is available")
                        else:
                            st.error(f"❌ Embedding model '{ollama_embedding_model}' not found")
                            st.code(f"ollama pull {ollama_embedding_model}")
                            st.write("☝️ Run this command to download the model")
                            
                        # Test a simple chat request
                        st.write("**Testing Chat API:**")
                        
                        chat_url = f"{ollama_endpoint}/api/generate"
                        chat_data = {
                            "model": ollama_chat_model,
                            "prompt": "Say 'test successful'",
                            "stream": False
                        }
                        
                        try:
                            req = urllib.request.Request(
                                chat_url, 
                                data=json.dumps(chat_data).encode(),
                                headers={'Content-Type': 'application/json'}
                            )
                            
                            with urllib.request.urlopen(req, timeout=15) as chat_response:
                                if chat_response.status == 200:
                                    chat_result = json.loads(chat_response.read().decode())
                                    response_text = chat_result.get('response', '')
                                    st.success(f"✅ Ollama chat test successful: {response_text[:50]}...")
                                else:
                                    st.error(f"❌ Ollama chat test failed: HTTP {chat_response.status}")
                                    
                        except Exception as chat_error:
                            st.error(f"❌ Ollama chat test failed: {chat_error}")
                            if "model" in str(chat_error).lower():
                                st.write(f"💡 The model '{ollama_chat_model}' might not be downloaded")
                    else:
                        st.error(f"❌ Ollama not responding (HTTP {response.status})")
                        
            except urllib.error.URLError as e:
                if "Connection refused" in str(e):
                    st.error(f"❌ Cannot connect to Ollama at {ollama_endpoint}")
                    st.write("**Solutions:**")
                    st.code("ollama serve")
                    st.write("☝️ Start Ollama with this command")
                else:
                    st.error(f"❌ Ollama connection error: {e}")
                    
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
                import urllib.request
                import urllib.error
                
                # Test OpenAI API
                test_data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Say 'test successful'"}],
                    "max_tokens": 10
                }
                
                req = urllib.request.Request(
                    "https://api.openai.com/v1/chat/completions",
                    data=json.dumps(test_data).encode(),
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                try:
                    with urllib.request.urlopen(req, timeout=15) as response:
                        if response.status == 200:
                            result = json.loads(response.read().decode())
                            message = result['choices'][0]['message']['content']
                            st.success(f"✅ OpenAI API test successful: {message}")
                        else:
                            st.error(f"❌ OpenAI API error: HTTP {response.status}")
                            
                except urllib.error.HTTPError as e:
                    if e.code == 401:
                        st.error("❌ OpenAI API key is invalid")
                        st.write("**Solution**: Check your API key in .env file")
                    elif e.code == 429:
                        st.warning("⚠️ OpenAI rate limit reached or insufficient credits")
                        st.write("**Solution**: Check your OpenAI account billing")
                    else:
                        error_body = e.read().decode()
                        st.error(f"❌ OpenAI API error: HTTP {e.code}")
                        st.code(error_body)
                        
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
            import urllib.request
            import urllib.error
            
            # Test Qdrant health
            health_req = urllib.request.Request(
                f"{qdrant_url}/health",
                headers={"api-key": qdrant_api_key}
            )
            
            try:
                with urllib.request.urlopen(health_req, timeout=10) as response:
                    if response.status == 200:
                        st.success("✅ Qdrant connection successful")
                        
                        # Check collection
                        collection_req = urllib.request.Request(
                            f"{qdrant_url}/collections/{collection_name}",
                            headers={"api-key": qdrant_api_key}
                        )
                        
                        try:
                            with urllib.request.urlopen(collection_req, timeout=10) as coll_response:
                                if coll_response.status == 200:
                                    collection_data = json.loads(coll_response.read().decode())
                                    vector_size = collection_data["result"]["config"]["params"]["vectors"]["size"]
                                    points_count = collection_data["result"]["points_count"]
                                    
                                    st.write(f"- **Collection**: `{collection_name}` exists")
                                    st.write(f"- **Vector dimensions**: `{vector_size}`")
                                    st.write(f"- **Documents**: `{points_count}`")
                                    
                                    # Check dimension compatibility
                                    if embedding_provider == "ollama":
                                        expected_dims = {
                                            "nomic-embed-text": 768,
                                            "mxbai-embed-large": 1024,
                                            "all-minilm": 384
                                        }
                                        expected_dim = expected_dims.get(ollama_embedding_model, 768)
                                    else:
                                        expected_dim = 1536  # OpenAI
                                    
                                    if vector_size == expected_dim:
                                        st.success(f"✅ Vector dimensions match embedding provider ({expected_dim})")
                                    else:
                                        st.error(f"❌ Vector dimension mismatch: collection has {vector_size}, provider needs {expected_dim}")
                                        st.write("**Solution**: Run the vector fix tool:")
                                        st.code("streamlit run standalone_vector_fix.py")
                                        
                        except urllib.error.HTTPError as e:
                            if e.code == 404:
                                st.info("ℹ️ Collection doesn't exist yet - will be created when you upload documents")
                            else:
                                st.warning(f"⚠️ Collection check failed: HTTP {e.code}")
                    else:
                        st.error(f"❌ Qdrant connection failed: HTTP {response.status}")
                        
            except urllib.error.URLError as e:
                st.error(f"❌ Cannot connect to Qdrant: {e}")
                
        except Exception as e:
            st.error(f"❌ Qdrant test error: {e}")
    
    # Step 5: Diagnosis Summary
    st.write("### 🎯 Step 5: Chat Engine Issue Diagnosis")
    
    st.markdown("**Most likely causes for 'chat engine initialized but sessions deleted':**")
    
    # Analyze based on findings
    if chat_provider == "ollama":
        if not ollama_enabled:
            st.error("🔥 **PRIMARY ISSUE**: Chat provider is Ollama but OLLAMA_ENABLED=False")
            st.write("**Fix**: Set `OLLAMA_ENABLED=True` in .env file")
        elif ollama_chat_model not in st.session_state.get('available_models', []):
            st.error(f"🔥 **PRIMARY ISSUE**: Ollama model '{ollama_chat_model}' not available")
            st.write(f"**Fix**: Run `ollama pull {ollama_chat_model}`")
        else:
            st.success("🦙 Ollama configuration looks correct")
    
    if chat_provider == "openai":
        if not openai_key:
            st.error("🔥 **PRIMARY ISSUE**: OpenAI selected but no API key configured")
            st.write("**Fix**: Add valid OPENAI_API_KEY to .env file")
        else:
            st.success("🤖 OpenAI configuration looks correct")
    
    st.markdown("**Next steps:**")
    st.markdown("1. 🔧 Fix any issues identified above")
    st.markdown("2. 🔄 Restart your main Streamlit app")
    st.markdown("3. 🧪 Test chat functionality")
    st.markdown("4. 📝 Check app logs for detailed error messages")

# Show configuration
st.markdown("---")
st.markdown("### 📋 Current Configuration Summary")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Provider Settings:**")
    st.write(f"- Ollama Enabled: `{config.get('OLLAMA_ENABLED', 'False')}`")
    st.write(f"- Chat Provider: `{config.get('CHAT_PROVIDER', 'openai')}`")
    st.write(f"- Embedding Provider: `{config.get('EMBEDDING_PROVIDER', 'openai')}`")

with col2:
    st.markdown("**Service Endpoints:**")
    st.write(f"- Ollama: `{config.get('OLLAMA_BASE_URL', 'Not set')}`")
    st.write(f"- OpenAI Key: `{'Set' if config.get('OPENAI_API_KEY') else 'Not set'}`")
    st.write(f"- Qdrant: `{config.get('QDRANT_URL', 'Not set')[:50]}...`")

st.markdown("### 🔧 Quick Fix Commands")
st.code("""
# Enable Ollama
echo 'OLLAMA_ENABLED=True' >> .env
echo 'CHAT_PROVIDER=ollama' >> .env
echo 'EMBEDDING_PROVIDER=ollama' >> .env

# Download Ollama models
ollama pull llama2
ollama pull nomic-embed-text

# Start Ollama
ollama serve
""")

st.info("""
💡 **Understanding the Problem**: 

"Chat engine initialized but sessions deleted" means the chat engine creates successfully, 
but when it tries to make the first request to the AI provider (OpenAI/Ollama), 
that request fails, causing the session to be cleaned up.

This diagnostic shows you exactly which provider is failing and why.
""")
