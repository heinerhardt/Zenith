import streamlit as st
import json
import urllib.request
import urllib.error
import subprocess
import os
from pathlib import Path

st.title("🦙 Ollama Configuration & Process Explained")

st.markdown("""
### How Ollama Works - Connection & Run Process

Let me explain how Ollama is configured and how the "run" process works.
""")

# Load current config
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

# Show current configuration
st.markdown("## 📋 Current Ollama Configuration")

ollama_endpoint = config.get("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_chat_model = config.get("OLLAMA_CHAT_MODEL", "llama2")
ollama_embedding_model = config.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

st.code(f"""
# From your .env file:
OLLAMA_BASE_URL={ollama_endpoint}
OLLAMA_CHAT_MODEL={ollama_chat_model}
OLLAMA_EMBEDDING_MODEL={ollama_embedding_model}
""")

st.markdown("## 🔧 How Ollama Connection Works")

st.markdown("""
### 1. **Ollama Server Process**
Ollama runs as a background server that listens on a port (default: 11434).

```bash
# Start the Ollama server
ollama serve
# This starts a web server at http://localhost:11434
```

### 2. **API Endpoints**
Your Zenith app connects to Ollama via HTTP API calls:

- **Health Check**: `GET /api/tags` - Lists available models
- **Chat Generation**: `POST /api/generate` - Generates responses
- **Chat Conversation**: `POST /api/chat` - Multi-turn conversations
- **Model Info**: `POST /api/show` - Get model details

### 3. **Model Loading Process**
When you make a request, Ollama:
1. **Loads the model** into memory (if not already loaded)
2. **Processes your prompt**
3. **Generates the response**
4. **Keeps model in memory** for faster subsequent requests
""")

# Check Ollama process status
if st.button("🔍 Check Ollama Process Status", type="secondary"):
    st.markdown("### Current Ollama Status")
    
    # Check if Ollama server is running
    try:
        with urllib.request.urlopen(f"{ollama_endpoint}/api/tags", timeout=5) as response:
            if response.status == 200:
                st.success("✅ Ollama server is running")
                
                data = json.loads(response.read().decode())
                models = data.get('models', [])
                
                if models:
                    st.write("**Available Models:**")
                    for model in models:
                        name = model.get('name', 'Unknown')
                        size = model.get('size', 0)
                        size_gb = size / (1024**3) if size > 0 else 0
                        modified = model.get('modified_at', 'Unknown')
                        st.write(f"- **{name}** ({size_gb:.1f} GB) - Modified: {modified[:10]}")
                else:
                    st.warning("⚠️ No models found - you need to download models")
            else:
                st.error(f"❌ Ollama server error: HTTP {response.status}")
    except Exception as e:
        st.error(f"❌ Ollama server not accessible: {e}")
        st.markdown("""
        **Possible issues:**
        1. Ollama not installed
        2. Ollama server not running (`ollama serve`)
        3. Wrong endpoint URL
        4. Firewall blocking connection
        """)

# Check what's currently loaded in memory
if st.button("🧠 Check What's Loaded in Memory", type="secondary"):
    st.markdown("### Memory Status")
    
    try:
        # Get currently running processes
        ps_data = {"name": ""}  # Empty name gets all processes
        req = urllib.request.Request(
            f"{ollama_endpoint}/api/ps",
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    ps_result = json.loads(response.read().decode())
                    models = ps_result.get('models', [])
                    
                    if models:
                        st.success("✅ Models currently loaded in memory:")
                        for model in models:
                            name = model.get('name', 'Unknown')
                            size = model.get('size', 0)
                            size_gb = size / (1024**3) if size > 0 else 0
                            st.write(f"- **{name}** ({size_gb:.1f} GB in memory)")
                    else:
                        st.info("ℹ️ No models currently loaded in memory")
                        st.write("Models are loaded on first use and stay in memory for performance")
                else:
                    st.error(f"❌ Cannot check memory status: HTTP {response.status}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                st.info("ℹ️ Memory status endpoint not available (older Ollama version)")
            else:
                st.error(f"❌ Memory check error: HTTP {e.code}")
    except Exception as e:
        st.error(f"❌ Memory check error: {e}")

st.markdown("## 🚀 Understanding 'ollama run' vs API")

st.markdown("""
### **Two Ways to Use Ollama:**

#### 1. **Command Line** (`ollama run`)
```bash
# Interactive chat in terminal
ollama run llama2
>>> Hello!
Hello! How can I help you today?

# One-shot command
ollama run llama2 "What is AI?"
```

#### 2. **HTTP API** (What Zenith uses)
```python
# What your Zenith app does:
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    "model": "llama2",
    "prompt": "What is AI?",
    "stream": False
})
```

### **Key Differences:**
- **`ollama run`**: Interactive terminal chat
- **HTTP API**: Programmatic access (what your app uses)
- **Both use the same models** and server process
""")

# Test model loading time
if st.button("⏱️ Test Model Loading Time", type="secondary"):
    st.markdown("### Model Loading Performance Test")
    
    model_to_test = ollama_chat_model
    st.write(f"Testing model: **{model_to_test}**")
    
    try:
        import time
        
        # Test small request
        test_data = {
            "model": model_to_test,
            "prompt": "Hi",
            "stream": False,
            "options": {
                "num_predict": 5
            }
        }
        
        req = urllib.request.Request(
            f"{ollama_endpoint}/api/generate",
            data=json.dumps(test_data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        start_time = time.time()
        
        with st.spinner(f"Loading and testing {model_to_test}..."):
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    total_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = json.loads(response.read().decode())
                        response_text = result.get('response', '')
                        
                        st.success(f"✅ Model loaded and responded in {total_time:.2f} seconds")
                        st.write(f"Response: *{response_text}*")
                        
                        # Performance analysis
                        if total_time > 30:
                            st.error("🔥 **VERY SLOW** - This will cause timeouts in your chat")
                            st.write("**Solutions:**")
                            st.write("1. Switch to a smaller/faster model")
                            st.write("2. Increase timeout in your app")
                            st.write("3. Check system resources (RAM/CPU)")
                        elif total_time > 10:
                            st.warning("⚠️ **SLOW** - May cause occasional timeouts")
                        else:
                            st.success("🚀 **GOOD** - Should work well in chat")
                    else:
                        st.error(f"❌ Model test failed: HTTP {response.status}")
                        
            except urllib.error.URLError as e:
                if "timed out" in str(e):
                    st.error("❌ **TIMEOUT** - Model too slow for your system")
                    st.write("🔥 **This is why your chat sessions are deleted!**")
                else:
                    st.error(f"❌ Test error: {e}")
                    
    except Exception as e:
        st.error(f"❌ Test error: {e}")

st.markdown("## 🛠️ Common Ollama Commands")

st.markdown("""
### **Essential Ollama Commands:**

```bash
# Start the server (required for API access)
ollama serve

# List available models
ollama list

# Download a model
ollama pull llama2

# Interactive chat
ollama run llama2

# Check what's running
ollama ps

# Remove a model
ollama rm llama2

# Stop the server
ollama stop
```
""")

st.markdown("## 🔧 Troubleshooting Your Issue")

st.info("""
**Your specific problem:**

1. **Ollama server is running** ✅ (connection test passes)
2. **Models are available** ✅ (you can list them)
3. **Chat generation times out** ❌ (even simple "Hi" takes >5 seconds)

**This means:**
- Your model is too large/slow for your system
- The model loading/generation process is taking too long
- Your chat app times out waiting for Ollama to respond

**Solutions:**
1. **Switch to faster model**: `ollama pull phi3:mini`
2. **Increase timeouts** in your Zenith app
3. **Check system resources** (RAM/CPU usage)
4. **Restart Ollama**: `ollama stop && ollama serve`
""")

# Quick model recommendations
st.markdown("## 🚀 Recommended Fast Models")

fast_models = [
    ("phi3:mini", "3.8B", "⚡ Very fast, good quality"),
    ("tinyllama", "1.1B", "🚀 Extremely fast, basic"),
    ("llama3.2:1b", "1B", "⚡ Fast, decent quality"),
    ("qwen2:0.5b", "0.5B", "🚀 Ultra fast, minimal")
]

for model, size, desc in fast_models:
    st.write(f"- **{model}** ({size}): {desc}")

st.code("""
# Download and test a fast model:
ollama pull phi3:mini
ollama run phi3:mini "Hello"

# If it's fast, update your .env:
OLLAMA_CHAT_MODEL=phi3:mini
""")
