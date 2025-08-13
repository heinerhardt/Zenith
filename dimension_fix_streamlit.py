import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

st.title("🔧 Vector Dimension Fix Tool")

st.markdown("""
### The Problem
Your Qdrant collection was created for OpenAI embeddings (1536 dimensions) but you're now using Ollama embeddings (1024 dimensions).

This causes the error: `Vector dimension error: expected dim: 1536, got 1024`
""")

if st.button("🔍 Check Current Status", type="primary"):
    try:
        # Import after setting up the path
        from core.enhanced_vector_store import EnhancedVectorStore
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        from core.config import config
        
        # Get current settings
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_current_settings()
        
        st.write("### Current Configuration:")
        st.write(f"- Effective embedding provider: **{settings_manager.get_effective_embedding_provider()}**")
        st.write(f"- Ollama embedding model: **{current_settings.ollama_embedding_model}**")
        st.write(f"- Collection name: **{config.qdrant_collection_name}**")
        
        # Test current embedding provider
        with st.spinner("Testing embedding provider..."):
            from core.enhanced_vector_store import get_embedding_provider
            
            provider = get_embedding_provider(settings_manager.get_effective_embedding_provider())
            test_embedding = provider.embed_text("test")
            actual_dimension = len(test_embedding)
            expected_dimension = provider.get_dimension()
            
            st.write("### Embedding Test Results:")
            st.write(f"- Provider: **{type(provider).__name__}**")
            st.write(f"- Model: **{getattr(provider, 'model_name', 'N/A')}**")
            st.write(f"- Expected dimension: **{expected_dimension}**")
            st.write(f"- Actual dimension: **{actual_dimension}**")
            
            if actual_dimension != expected_dimension:
                st.warning(f"⚠️ Dimension mapping issue! Expected {expected_dimension}, got {actual_dimension}")
            else:
                st.success("✅ Embedding dimensions are consistent!")
        
        # Check collection status
        with st.spinner("Checking collection status..."):
            vector_store = EnhancedVectorStore()
            compatible, message, collection_dim, provider_dim = vector_store.check_dimension_compatibility()
            
            st.write("### Collection Status:")
            st.write(f"- Status: **{message}**")
            if collection_dim > 0 and provider_dim > 0:
                st.write(f"- Collection expects: **{collection_dim} dimensions**")
                st.write(f"- Provider produces: **{provider_dim} dimensions**")
                
                if compatible:
                    st.success("✅ Collection and provider dimensions match!")
                else:
                    st.error("❌ Dimension mismatch detected!")
                    
                    if st.button("🔄 Fix Dimension Mismatch", type="secondary"):
                        with st.spinner("Recreating collection with correct dimensions..."):
                            success, fix_message = vector_store.fix_dimension_mismatch()
                            
                        if success:
                            st.success(f"✅ {fix_message}")
                            st.balloons()
                            
                            st.markdown("### ✅ Next Steps:")
                            st.markdown("1. 🔄 **Restart your main Streamlit app**")
                            st.markdown("2. 📄 **Re-upload your PDF documents**")
                            st.markdown("3. 🔍 **Test searches - they should work now!**")
                        else:
                            st.error(f"❌ {fix_message}")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())

st.markdown("---")

st.markdown("### Manual Alternative")
st.markdown("If the automated fix doesn't work, you can manually recreate the collection:")

st.code("""
# In your Python environment:
from src.core.enhanced_vector_store import EnhancedVectorStore

vector_store = EnhancedVectorStore()
success = vector_store.create_collection(force_recreate=True)
print(f"Collection recreated: {success}")
""")

st.markdown("### Understanding the Issue")
with st.expander("📚 Learn more about vector dimensions"):
    st.markdown("""
    **Vector dimensions** depend on the embedding model:
    
    - **OpenAI text-embedding-ada-002**: 1536 dimensions
    - **Ollama nomic-embed-text**: 768 dimensions  
    - **Ollama mxbai-embed-large**: 1024 dimensions
    - **Ollama all-minilm**: 384 dimensions
    
    When you switch embedding providers, the collection must be recreated with the new dimensions.
    
    **Why this happened**: You originally used OpenAI embeddings, then switched to Ollama, but the collection still expects OpenAI dimensions.
    """)

st.warning("⚠️ **Important**: Recreating the collection will delete all existing documents. You'll need to re-upload your PDFs.")
