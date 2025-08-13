import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

st.title("🚨 Settings Stuck Fix Tool")

st.markdown("""
### Problem
Your settings save is hanging and never completes when you try to change provider settings.

### Solution
This tool will update your settings without the time-consuming validation that's causing the hang.
""")

if st.button("🔧 Load Current Settings", type="secondary"):
    try:
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_current_settings()
        
        st.write("### Current Settings:")
        st.write(f"- Ollama Enabled: **{current_settings.ollama_enabled}**")
        st.write(f"- Preferred Chat Provider: **{current_settings.preferred_chat_provider}**")
        st.write(f"- Preferred Embedding Provider: **{current_settings.preferred_embedding_provider}**")
        st.write(f"- Effective Chat Provider: **{settings_manager.get_effective_chat_provider()}**")
        st.write(f"- Effective Embedding Provider: **{settings_manager.get_effective_embedding_provider()}**")
        
        # Store in session state for modification
        st.session_state.current_settings = {
            'ollama_enabled': current_settings.ollama_enabled,
            'preferred_chat_provider': current_settings.preferred_chat_provider,
            'preferred_embedding_provider': current_settings.preferred_embedding_provider,
            'openai_api_key': current_settings.openai_api_key or "",
            'ollama_endpoint': current_settings.ollama_endpoint,
            'ollama_chat_model': current_settings.ollama_chat_model,
            'ollama_embedding_model': current_settings.ollama_embedding_model
        }
        
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Settings modification form
if 'current_settings' in st.session_state:
    st.markdown("---")
    st.markdown("### Modify Settings")
    
    with st.form("quick_settings_form"):
        st.markdown("**Provider Settings:**")
        
        # Ollama enabled
        ollama_enabled = st.checkbox(
            "Enable Ollama",
            value=st.session_state.current_settings['ollama_enabled'],
            help="Enable Ollama for local AI models"
        )
        
        # Provider selection
        col1, col2 = st.columns(2)
        
        with col1:
            chat_provider = st.selectbox(
                "Chat Provider",
                options=["openai", "ollama"],
                index=0 if st.session_state.current_settings['preferred_chat_provider'] == "openai" else 1
            )
        
        with col2:
            embedding_provider = st.selectbox(
                "Embedding Provider", 
                options=["openai", "ollama"],
                index=0 if st.session_state.current_settings['preferred_embedding_provider'] == "openai" else 1
            )
        
        st.markdown("**OpenAI Settings:**")
        openai_api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.current_settings['openai_api_key'],
            type="password",
            help="Your OpenAI API key"
        )
        
        st.markdown("**Ollama Settings:**")
        
        col1, col2 = st.columns(2)
        with col1:
            ollama_endpoint = st.text_input(
                "Ollama Endpoint",
                value=st.session_state.current_settings['ollama_endpoint']
            )
            
        with col2:
            ollama_chat_model = st.text_input(
                "Ollama Chat Model",
                value=st.session_state.current_settings['ollama_chat_model']
            )
        
        ollama_embedding_model = st.text_input(
            "Ollama Embedding Model",
            value=st.session_state.current_settings['ollama_embedding_model']
        )
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("💾 Quick Save (No Validation)", type="primary")
        
        with col2:
            normal_save = st.form_submit_button("🔄 Normal Save (With Validation)", type="secondary")
        
        if submitted:
            try:
                from core.enhanced_settings_manager import get_enhanced_settings_manager
                
                # Prepare updates
                updates = {
                    'ollama_enabled': ollama_enabled,
                    'preferred_chat_provider': chat_provider,
                    'preferred_embedding_provider': embedding_provider,
                    'ollama_endpoint': ollama_endpoint,
                    'ollama_chat_model': ollama_chat_model,
                    'ollama_embedding_model': ollama_embedding_model
                }
                
                # Add API key only if provided
                if openai_api_key.strip():
                    updates['openai_api_key'] = openai_api_key.strip()
                
                settings_manager = get_enhanced_settings_manager()
                
                with st.spinner("Saving settings (quick mode)..."):
                    success, message = settings_manager.quick_update_settings(updates)
                
                if success:
                    st.success(f"✅ {message}")
                    st.info("ℹ️ Settings saved! Use 'Force Reinitialize' in your main app to test providers.")
                    
                    # Clear session state to reload
                    if 'current_settings' in st.session_state:
                        del st.session_state.current_settings
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ Error during quick save: {e}")
        
        if normal_save:
            try:
                from core.enhanced_settings_manager import get_enhanced_settings_manager
                
                # Prepare updates
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
                
                settings_manager = get_enhanced_settings_manager()
                
                with st.spinner("Saving settings (with validation)..."):
                    success, message = settings_manager.update_settings(updates)
                
                if success:
                    st.success(f"✅ {message}")
                    
                    # Clear session state to reload
                    if 'current_settings' in st.session_state:
                        del st.session_state.current_settings
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ Error during normal save: {e}")

# Instructions
st.markdown("---")
st.markdown("### How to Use")
st.markdown("""
1. **Load Current Settings** - See what your settings are now
2. **Modify Settings** - Change the values you want to update
3. **Quick Save** - Saves immediately without validation (recommended if stuck)
4. **Normal Save** - Saves with full validation (may hang if there are issues)

**Tip:** Use **Quick Save** if your settings keep hanging, then use **Force Reinitialize** in your main app to test the providers.
""")

st.markdown("### Why This Happens")
st.info("""
Settings save can hang when the system tries to validate Ollama models by downloading them. 
This tool bypasses that validation so you can save your settings quickly.
""")
