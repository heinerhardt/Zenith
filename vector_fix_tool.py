import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

st.title("🔧 Zenith Vector Dimension Fix Tool")

st.markdown("### Vector Dimension Mismatch Error")
st.error("Your Qdrant collection expects 1536 dimensions (OpenAI) but got 1024 dimensions (Ollama)")

if st.button("🔍 Analyze Current Configuration", type="primary"):
    try:
        from core.config import config
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_current_settings()
        
        st.write("### Current Configuration:")
        st.write(f"- Ollama enabled: **{current_settings.ollama_enabled}**")
        st.write(f"- Ollama embedding model: **{current_settings.ollama_embedding_model}**")
        st.write(f"- Effective embedding provider: **{settings_manager.get_effective_embedding_provider()}**")
        st.write(f"- Collection name: **{config.qdrant_collection_name}**")
        
        # Test embedding dimensions
        try:
            from core.enhanced_vector_store import get_embedding_provider
            
            provider = get_embedding_provider(settings_manager.get_effective_embedding_provider())
            test_embedding = provider.embed_text("test")
            actual_dimension = len(test_embedding)
            expected_dimension = provider.get_dimension()
            
            st.write("### Embedding Test:")
            st.write(f"- Provider: **{type(provider).__name__}**")
            st.write(f"- Expected dimension: **{expected_dimension}**")
            st.write(f"- Actual dimension: **{actual_dimension}**")
            
            if actual_dimension != expected_dimension:
                st.warning(f"⚠️ Dimension mismatch! Expected {expected_dimension}, got {actual_dimension}")
            else:
                st.success("✅ Dimensions match!")
                
        except Exception as e:
            st.error(f"❌ Error testing embeddings: {e}")
            
        # Check collection info
        try:
            from core.qdrant_manager import get_qdrant_client
            
            qdrant = get_qdrant_client()
            collection_info = qdrant.get_collection(config.qdrant_collection_name)
            
            st.write("### Current Collection Info:")
            st.write(f"- Vector size: **{collection_info.config.params.vectors.size}**")
            st.write(f"- Distance: **{collection_info.config.params.vectors.distance}**")
            st.write(f"- Points count: **{collection_info.points_count}**")
            
        except Exception as e:
            st.error(f"❌ Error getting collection info: {e}")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Fix Collection (Recreate)", type="secondary"):
        try:
            from core.enhanced_vector_store import EnhancedVectorStore
            from core.enhanced_settings_manager import get_enhanced_settings_manager
            
            settings_manager = get_enhanced_settings_manager()
            
            with st.spinner("Recreating collection with correct dimensions..."):
                vector_store = EnhancedVectorStore()
                success = vector_store.create_collection(force_recreate=True)
                
            if success:
                st.success("✅ Collection recreated successfully!")
                st.warning("⚠️ Note: All previously uploaded documents will need to be re-uploaded")
            else:
                st.error("❌ Failed to recreate collection")
                
        except Exception as e:
            st.error(f"❌ Error: {e}")

with col2:
    if st.button("📊 Update Dimension Map", type="secondary"):
        st.info("This will update the dimension mapping for your Ollama model")
        
        # Show current model and let user update dimensions
        try:
            from core.enhanced_settings_manager import get_enhanced_settings_manager
            
            settings_manager = get_enhanced_settings_manager()
            current_settings = settings_manager.get_current_settings()
            
            st.write(f"Current model: **{current_settings.ollama_embedding_model}**")
            
            new_dimension = st.number_input(
                "Enter the correct dimension for your model:",
                min_value=1,
                max_value=2048,
                value=1024,
                help="Common values: 384, 768, 1024, 1536"
            )
            
            if st.button("Update Dimension Mapping"):
                st.code(f"""
# Add this to src/core/enhanced_vector_store.py in get_dimension() method:
"{current_settings.ollama_embedding_model}": {new_dimension},
                """)
                st.info("Manual update required - copy the code above")
                
        except Exception as e:
            st.error(f"❌ Error: {e}")

st.markdown("---")
st.markdown("### Quick Solutions:")
st.markdown("1. **Recreate Collection**: Easiest fix, but you'll lose existing documents")
st.markdown("2. **Update Dimension Map**: Fix the dimension detection for your model")
st.markdown("3. **Switch Models**: Use a model with known dimensions (like nomic-embed-text)")
st.markdown("4. **Backup & Restore**: Export documents, recreate collection, re-import")
