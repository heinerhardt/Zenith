import streamlit as st
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

st.title("🦙 Ollama Timeout Diagnostic")

st.markdown("""
### Ollama Chat Timeout Issue
Your Ollama connection test passed, but chat generation is timing out.
Let's diagnose what's happening.
""")

# Load .env
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
    except Exception as e:
        st.error(f"Could not load .env: {e}")
    return config

config = load_env()

ollama_endpoint = config.get("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_chat_model = config.get("OLLAMA_CHAT_MODEL", "llama2")

st.write(f"**Ollama Endpoint**: `{ollama_endpoint}`")
st.write(f"**Chat Model**: `{ollama_chat_model}`")

if st.button("🔍 Diagnose Ollama Timeout", type="primary"):
    
    # Step 1: Basic connection test
    st.write("### Step 1: Basic Connection Test")
    try:
        start_time = time.time()
        with urllib.request.urlopen(f"{ollama_endpoint}/api/tags", timeout=5) as response:
            connection_time = time.time() - start_time
            if response.status == 200:
                st.success(f"✅ Connection successful ({connection_time:.2f}s)")
                data = json.loads(response.read().decode())
                models = [model['name'] for model in data.get('models', [])]
                st.write(f"Available models: {models}")
                
                if ollama_chat_model not in models:
                    st.error(f"❌ Model '{ollama_chat_model}' not found!")
                    st.write("**Solution**: Download the model:")
                    st.code(f"ollama pull {ollama_chat_model}")
                    st.stop()
            else:
                st.error(f"❌ Connection failed: HTTP {response.status}")
                st.stop()
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        st.stop()
    
    # Step 2: Test model loading
    st.write("### Step 2: Model Loading Test")
    try:
        # Test if model is loaded
        show_data = {"name": ollama_chat_model}
        req = urllib.request.Request(
            f"{ollama_endpoint}/api/show",
            data=json.dumps(show_data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=10) as response:
            load_time = time.time() - start_time
            if response.status == 200:
                st.success(f"✅ Model info retrieved ({load_time:.2f}s)")
                model_info = json.loads(response.read().decode())
                
                # Show model details
                if 'details' in model_info:
                    details = model_info['details']
                    st.write(f"- **Family**: {details.get('family', 'Unknown')}")
                    st.write(f"- **Format**: {details.get('format', 'Unknown')}")
                    st.write(f"- **Parameter size**: {details.get('parameter_size', 'Unknown')}")
                    
                    # Check if it's a large model
                    param_size = details.get('parameter_size', '')
                    if '70B' in param_size or '65B' in param_size:
                        st.warning("⚠️ This is a very large model - generation may be slow")
                    elif '13B' in param_size or '30B' in param_size:
                        st.info("ℹ️ This is a medium-large model - generation may take time")
            else:
                st.error(f"❌ Model info failed: HTTP {response.status}")
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            st.error(f"❌ Model '{ollama_chat_model}' not found on server")
            st.write("**Solution**:")
            st.code(f"ollama pull {ollama_chat_model}")
        else:
            st.error(f"❌ Model info error: HTTP {e.code}")
    except Exception as e:
        st.error(f"❌ Model info error: {e}")
    
    # Step 3: Progressive timeout tests
    st.write("### Step 3: Progressive Chat Tests")
    
    test_prompts = [
        ("Very Short", "Hi", 5),
        ("Short", "Say hello", 15),
        ("Medium", "Tell me about yourself in one sentence", 30),
        ("Standard", "What is artificial intelligence?", 60)
    ]
    
    for test_name, prompt, timeout in test_prompts:
        st.write(f"**{test_name} Test** (timeout: {timeout}s)")
        
        try:
            chat_data = {
                "model": ollama_chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 50,  # Limit response length
                    "temperature": 0.1,  # Lower randomness for faster generation
                    "top_p": 0.9
                }
            }
            
            req = urllib.request.Request(
                f"{ollama_endpoint}/api/generate",
                data=json.dumps(chat_data).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=timeout) as response:
                generation_time = time.time() - start_time
                
                if response.status == 200:
                    result = json.loads(response.read().decode())
                    response_text = result.get('response', '')
                    
                    st.success(f"✅ {test_name} test passed ({generation_time:.2f}s)")
                    st.write(f"Response: *{response_text[:100]}...*")
                    
                    # Performance analysis
                    if generation_time > 30:
                        st.warning(f"⚠️ Slow generation ({generation_time:.1f}s) - this could cause timeouts")
                    elif generation_time > 10:
                        st.info(f"ℹ️ Moderate generation time ({generation_time:.1f}s)")
                    
                else:
                    st.error(f"❌ {test_name} test failed: HTTP {response.status}")
                    break
                    
        except urllib.error.URLError as e:
            if "timed out" in str(e):
                st.error(f"❌ {test_name} test timed out after {timeout}s")
                st.write("🔥 **This is likely your chat session issue!**")
                break
            else:
                st.error(f"❌ {test_name} test error: {e}")
                break
        except Exception as e:
            st.error(f"❌ {test_name} test error: {e}")
            break
    
    # Step 4: Performance recommendations
    st.write("### Step 4: Performance Analysis")
    
    st.markdown("**Common causes of Ollama timeouts:**")
    st.markdown("""
    1. **🐌 Slow hardware** - Model too large for your system
    2. **🧠 Insufficient RAM** - Model can't load fully into memory
    3. **🔥 CPU overload** - System resources maxed out
    4. **📡 Network issues** - If using remote Ollama instance
    5. **⚙️ Wrong model configuration** - Model parameters causing slowness
    """)
    
    # System recommendations based on model
    if '70B' in ollama_chat_model or '65B' in ollama_chat_model:
        st.error("🔥 **70B+ models require significant resources**")
        st.write("**Recommended alternatives:**")
        st.code("""
# Try smaller, faster models:
ollama pull llama2:7b-chat
ollama pull mistral:7b
ollama pull phi3:mini
        """)
    elif '13B' in ollama_chat_model or '30B' in ollama_chat_model:
        st.warning("⚠️ **Medium models can be slow on modest hardware**")
        st.write("**Consider trying:**")
        st.code("ollama pull llama2:7b-chat")
    else:
        st.info("ℹ️ **Model size looks reasonable for most systems**")

# Quick fixes section
st.markdown("---")
st.markdown("### 🔧 Quick Fixes for Ollama Timeouts")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Model Solutions:**")
    if st.button("Switch to Fast Model"):
        st.code("""
# Download a fast 7B model:
ollama pull llama2:7b-chat

# Update your .env:
OLLAMA_CHAT_MODEL=llama2:7b-chat
        """)
        
    if st.button("Optimize Current Model"):
        st.code("""
# Pull with specific tag for efficiency:
ollama pull """ + ollama_chat_model + """:q4_0

# Or try the instruct variant:
ollama pull """ + ollama_chat_model + """:instruct
        """)

with col2:
    st.markdown("**System Solutions:**")
    if st.button("Check System Resources"):
        st.code("""
# Check memory usage:
ollama ps

# Check system memory:
free -h  # Linux/Mac
wmic OS get TotalVisibleMemorySize  # Windows

# Restart Ollama:
ollama stop
ollama serve
        """)
        
    if st.button("Timeout Workarounds"):
        st.info("""
        **In your main app:**
        1. Increase chat timeout to 60-120 seconds
        2. Add loading messages for users
        3. Use streaming responses
        4. Implement retry logic
        """)

# Model recommendations
st.markdown("---")
st.markdown("### 🚀 Recommended Fast Models")

fast_models = [
    ("phi3:mini", "3.8B", "⚡ Fastest - Great for chat"),
    ("llama2:7b-chat", "7B", "🔥 Fast - Good balance"),
    ("mistral:7b", "7B", "✨ Fast - High quality"),
    ("codellama:7b", "7B", "💻 Fast - Code focused")
]

for model, size, desc in fast_models:
    st.write(f"- **{model}** ({size}): {desc}")

st.code("""
# Try the fastest option:
ollama pull phi3:mini

# Update .env:
OLLAMA_CHAT_MODEL=phi3:mini
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
""")

st.markdown("### 💡 Understanding the Timeout Issue")
st.info("""
**Why this causes "sessions deleted":**

1. Chat engine initializes successfully ✅
2. User sends first message ✅  
3. Ollama takes too long to respond ⏱️
4. Request times out after 30-60 seconds ❌
5. Chat engine throws error ❌
6. Session gets cleaned up/deleted 🗑️

**The fix**: Use a faster model or increase timeout settings in your app.
""")
