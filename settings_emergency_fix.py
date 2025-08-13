import streamlit as st
import sys
import os
from pathlib import Path

# Fix import path by adding both the root and src directories
zenith_root = Path(__file__).parent
src_path = zenith_root / "src"

# Change working directory and add paths
os.chdir(zenith_root)
sys.path.insert(0, str(zenith_root))
sys.path.insert(0, str(src_path))

# Load environment manually to avoid import issues
def load_env():
    env_path = zenith_root / ".env"
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value
    except Exception as e:
        st.error(f"Could not load .env: {e}")

# Load environment first
load_env()

st.title("🚨 Settings Stuck Fix Tool")

st.markdown("""
### Problem
Your settings save hangs when changing provider settings.

### Solution  
This tool updates settings without time-consuming validation.
""")

# Check if we can import the settings manager
can_import = False
settings_manager = None

if st.button("🔧 Test Connection & Load Settings", type="primary"):
    try:
        # Try different import approaches
        import importlib.util
        
        # Method 1: Direct file import
        settings_file = src_path / "core" / "enhanced_settings_manager.py"
        
        if settings_file.exists():
            spec = importlib.util.spec_from_file_location("enhanced_settings_manager", settings_file)
            settings_module = importlib.util.module_from_spec(spec)
            
            # Add required modules to sys.modules to handle relative imports
            sys.modules['enhanced_settings_manager'] = settings_module
            
            try:
                spec.loader.exec_module(settings_module)
                
                # Get the manager
                settings_manager = settings_module.get_enhanced_settings_manager()
                current_settings = settings_manager.get_current_settings()
                
                st.success("✅ Successfully connected to settings!")
                
                st.write("### Current Settings:")
                st.write(f"- Ollama Enabled: **{current_settings.ollama_enabled}**")
                st.write(f"- Chat Provider: **{current_settings.preferred_chat_provider}**")
                st.write(f"- Embedding Provider: **{current_settings.preferred_embedding_provider}**")
                
                # Store for editing
                st.session_state.settings_loaded = True
                st.session_state.current_settings = {
                    'ollama_enabled': current_settings.ollama_enabled,
                    'preferred_chat_provider': current_settings.preferred_chat_provider,
                    'preferred_embedding_provider': current_settings.preferred_embedding_provider,
                    'openai_api_key': getattr(current_settings, 'openai_api_key', '') or "",
                    'ollama_endpoint': current_settings.ollama_endpoint,
                    'ollama_chat_model': current_settings.ollama_chat_model,
                    'ollama_embedding_model': current_settings.ollama_embedding_model
                }
                st.session_state.settings_manager = settings_manager
                
                can_import = True
                
            except Exception as import_error:
                st.error(f"❌ Import error: {import_error}")
                st.info("⚡ Trying alternative approach...")
                
                # Method 2: Direct database approach
                try:
                    import requests
                    import json
                    
                    # Get Qdrant connection details
                    qdrant_url = os.getenv("QDRANT_URL")
                    qdrant_api_key = os.getenv("QDRANT_API_KEY")
                    
                    if qdrant_url and qdrant_api_key:
                        st.info("🔌 Connecting directly to Qdrant...")
                        
                        headers = {
                            "Content-Type": "application/json",
                            "api-key": qdrant_api_key
                        }
                        
                        # Try to get settings from Qdrant
                        collection_url = f"{qdrant_url.rstrip('/')}/collections/zenith_settings"
                        
                        # Check if settings collection exists
                        response = requests.get(collection_url, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            st.success("✅ Connected to Qdrant directly!")
                            st.info("ℹ️ You can use manual settings update below")
                            st.session_state.direct_mode = True
                        else:
                            st.warning("⚠️ Could not access settings collection")
                    else:
                        st.error("❌ No Qdrant configuration found in .env")
                        
                except Exception as db_error:
                    st.error(f"❌ Database connection error: {db_error}")
        else:
            st.error("❌ Settings manager file not found")
            
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())

# Settings form if we have settings loaded
if st.session_state.get('settings_loaded', False):
    st.markdown("---")
    st.markdown("### 🛠️ Modify Settings")
    
    with st.form("settings_form"):
        current = st.session_state.current_settings
        
        # Provider settings
        st.markdown("**🤖 Provider Settings:**")
        
        ollama_enabled = st.checkbox(
            "Enable Ollama",
            value=current['ollama_enabled'],
            help="Enable Ollama for local AI models"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            chat_provider = st.selectbox(
                "Chat Provider",
                options=["openai", "ollama"],
                index=0 if current['preferred_chat_provider'] == "openai" else 1
            )
        
        with col2:
            embedding_provider = st.selectbox(
                "Embedding Provider",
                options=["openai", "ollama"], 
                index=0 if current['preferred_embedding_provider'] == "openai" else 1
            )
        
        # API Keys
        st.markdown("**🔑 API Configuration:**")
        openai_api_key = st.text_input(
            "OpenAI API Key",
            value=current['openai_api_key'],
            type="password"
        )
        
        # Ollama settings
        st.markdown("**🦙 Ollama Configuration:**")
        col1, col2 = st.columns(2)
        
        with col1:
            ollama_endpoint = st.text_input(
                "Ollama Endpoint",
                value=current['ollama_endpoint']
            )
            
        with col2:
            ollama_chat_model = st.text_input(
                "Chat Model",
                value=current['ollama_chat_model']
            )
        
        ollama_embedding_model = st.text_input(
            "Embedding Model",
            value=current['ollama_embedding_model']
        )
        
        # Save button
        if st.form_submit_button("💾 SAVE SETTINGS (NO VALIDATION)", type="primary", use_container_width=True):
            try:
                settings_manager = st.session_state.settings_manager
                
                updates = {
                    'ollama_enabled': ollama_enabled,
                    'preferred_chat_provider': chat_provider,
                    'preferred_embedding_provider': embedding_provider,
                    'ollama_endpoint': ollama_endpoint,
                    'ollama_chat_model': ollama_chat_model,
                    'ollama_embedding_model': ollama_embedding_model
                }
                
                if openai_api_key.strip():
                    updates['openai_api_key'] = openai_api_key.strip()
                
                with st.spinner("Saving settings (bypassing validation)..."):
                    # Use quick update to avoid hanging
                    success, message = settings_manager.quick_update_settings(updates)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    
                    st.markdown("### 🎉 Settings Saved!")
                    st.markdown("**Next steps:**")
                    st.markdown("1. 🔄 Restart your main Streamlit app")
                    st.markdown("2. 🧪 Use 'Force Reinitialize' to test providers")
                    st.markdown("3. 🔍 Check that searches work correctly")
                    
                    # Clear to reload
                    for key in ['settings_loaded', 'current_settings', 'settings_manager']:
                        if key in st.session_state:
                            del st.session_state[key]
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ Save error: {e}")

# Manual mode for direct Qdrant access
elif st.session_state.get('direct_mode', False):
    st.markdown("---")
    st.markdown("### 🔧 Manual Settings Update")
    st.info("Using direct Qdrant access mode")
    
    with st.form("manual_settings"):
        st.markdown("**Configure your preferred settings:**")
        
        manual_ollama = st.checkbox("Enable Ollama", value=True)
        manual_chat = st.selectbox("Chat Provider", ["ollama", "openai"])
        manual_embedding = st.selectbox("Embedding Provider", ["ollama", "openai"])
        
        if st.form_submit_button("💾 Apply Manual Settings"):
            st.success("✅ Manual settings noted!")
            st.markdown(f"**Your choices:**")
            st.markdown(f"- Ollama: {manual_ollama}")
            st.markdown(f"- Chat: {manual_chat}")
            st.markdown(f"- Embedding: {manual_embedding}")
            
            st.info("ℹ️ Restart your main app and use the Admin panel to apply these settings")

# Fallback instructions
if not st.session_state.get('settings_loaded', False) and not st.session_state.get('direct_mode', False):
    st.markdown("---")
    st.markdown("### 🔄 Alternative Solutions")
    
    st.markdown("**If the connection fails, try these alternatives:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📝 Manual .env Edit:**")
        st.code("""
# Edit your .env file directly:
OLLAMA_ENABLED=True
CHAT_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
        """)
    
    with col2:
        st.markdown("**🔄 Reset Scripts:**")
        st.code("""
# Run these scripts:
python direct_vector_fix.py
streamlit run qdrant_cloud_fix.py
        """)

st.markdown("---")
st.markdown("### 💡 Why Settings Hang")
st.info("""
Settings save can hang when the system tries to:
- Download/validate Ollama models
- Test network connections to providers
- Perform time-consuming health checks

This tool bypasses those checks so you can save settings immediately.
""")
