import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

st.title("🔧 Zenith Settings Reset Tool")

if st.button("🔄 Force Reset Settings to .env", type="primary"):
    try:
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        from core.config import config
        
        st.write("### Current .env Configuration:")
        st.write(f"- OLLAMA_ENABLED: **{config.ollama_enabled}**")
        st.write(f"- CHAT_PROVIDER: **{config.chat_provider}**")
        st.write(f"- EMBEDDING_PROVIDER: **{config.embedding_provider}**")
        
        settings_manager = get_enhanced_settings_manager()
        
        st.write("### Before Reset:")
        current = settings_manager.get_current_settings()
        st.write(f"- ollama_enabled: **{current.ollama_enabled}**")
        st.write(f"- preferred_chat_provider: **{current.preferred_chat_provider}**")
        st.write(f"- preferred_embedding_provider: **{current.preferred_embedding_provider}**")
        
        with st.spinner("Resetting settings..."):
            success = settings_manager.force_reset_to_env_settings()
        
        if success:
            st.success("✅ Settings reset successfully!")
            
            st.write("### After Reset:")
            current = settings_manager.get_current_settings()
            st.write(f"- ollama_enabled: **{current.ollama_enabled}**")
            st.write(f"- preferred_chat_provider: **{current.preferred_chat_provider}**")
            st.write(f"- preferred_embedding_provider: **{current.preferred_embedding_provider}**")
            
            st.write("### Effective Providers:")
            st.write(f"- Chat: **{settings_manager.get_effective_chat_provider()}**")
            st.write(f"- Embedding: **{settings_manager.get_effective_embedding_provider()}**")
            st.write(f"- Ollama Enabled: **{settings_manager.is_ollama_enabled_effective()}**")
            
            with st.spinner("Reinitializing providers..."):
                reinit_success, message = settings_manager.force_reinitialize_providers()
            
            if reinit_success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
        else:
            st.error("❌ Failed to reset settings")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.code(str(e))

st.markdown("---")
st.markdown("**Instructions:**")
st.markdown("1. Click the button above to force reset all settings")
st.markdown("2. This will make settings match your .env file")
st.markdown("3. Restart your main Streamlit app after reset")
