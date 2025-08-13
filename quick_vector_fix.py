import streamlit as st
import sys
import os
from pathlib import Path

# Fix the import path issue
zenith_root = Path(__file__).parent
src_path = zenith_root / "src"

# Add both paths to handle different import scenarios
sys.path.insert(0, str(zenith_root))
sys.path.insert(0, str(src_path))

# Change working directory to Zenith root
os.chdir(zenith_root)

st.title("🔧 Vector Dimension Quick Fix")

st.markdown("""
### The Problem
Vector dimension error: `expected dim: 1536, got 1024`

Your collection was created for OpenAI (1536 dimensions) but you're using Ollama (1024 dimensions).
""")

# Simple fix button
if st.button("🔄 Fix Vector Dimensions Now", type="primary", use_container_width=True):
    try:
        # Direct approach - import what we need step by step
        st.write("🔍 Loading configuration...")
        
        # Import config directly
        sys.path.append(str(src_path / "core"))
        
        # Load environment first
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import core modules
        import requests
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        st.write("📋 Getting configuration...")
        
        # Get Qdrant connection details from environment
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "zenith_documents")
        
        st.write(f"🔌 Connecting to Qdrant: {qdrant_url}")
        
        # Connect to Qdrant
        if qdrant_api_key:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            client = QdrantClient(url=qdrant_url)
        
        # Test connection
        collections = client.get_collections()
        st.success("✅ Connected to Qdrant successfully!")
        
        # Check if collection exists
        collection_names = [col.name for col in collections.collections]
        
        if collection_name in collection_names:
            st.write(f"📊 Found collection: {collection_name}")
            
            # Get collection info
            collection_info = client.get_collection(collection_name)
            current_dim = collection_info.config.params.vectors.size
            
            st.write(f"Current collection dimensions: **{current_dim}**")
            
            # Determine correct dimension for Ollama
            ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            
            # Standard Ollama embedding dimensions
            ollama_dimensions = {
                "nomic-embed-text": 768,
                "mxbai-embed-large": 1024,
                "all-minilm": 384,
                "all-MiniLM-L6-v2": 384,
            }
            
            correct_dim = ollama_dimensions.get(ollama_model, 1024)  # Default to 1024
            
            st.write(f"Ollama model '{ollama_model}' needs: **{correct_dim}** dimensions")
            
            if current_dim != correct_dim:
                st.error(f"❌ Dimension mismatch: {current_dim} → {correct_dim}")
                
                # Ask for confirmation
                st.warning("⚠️ This will delete all documents in the collection!")
                
                if st.button("🗑️ Confirm: Delete and Recreate Collection"):
                    with st.spinner("Recreating collection..."):
                        # Delete existing collection
                        client.delete_collection(collection_name)
                        st.write("🗑️ Deleted old collection")
                        
                        # Create new collection with correct dimensions
                        client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(
                                size=correct_dim,
                                distance=Distance.COSINE
                            )
                        )
                        st.write(f"✨ Created new collection with {correct_dim} dimensions")
                        
                        # Verify new collection
                        new_info = client.get_collection(collection_name)
                        new_dim = new_info.config.params.vectors.size
                        
                        if new_dim == correct_dim:
                            st.success("🎉 Collection fixed successfully!")
                            st.balloons()
                            
                            st.markdown("### ✅ Next Steps:")
                            st.markdown("1. 🔄 **Restart your main Streamlit app**")
                            st.markdown("2. 📄 **Re-upload your PDF documents**") 
                            st.markdown("3. 🔍 **Test searches - they should work now!**")
                        else:
                            st.error(f"❌ Verification failed: got {new_dim} instead of {correct_dim}")
            else:
                st.success("✅ Collection dimensions are already correct!")
        else:
            st.warning(f"Collection '{collection_name}' does not exist. It will be created when you upload documents.")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        
        with st.expander("🔍 Show full error details"):
            import traceback
            st.code(traceback.format_exc())
        
        st.markdown("### Alternative Solutions:")
        st.markdown("1. Try running your main app and use the Admin panel")
        st.markdown("2. Check if Qdrant is running and accessible")
        st.markdown("3. Verify your .env configuration")

# Information section
st.markdown("---")
st.markdown("### 📚 Understanding Vector Dimensions")

with st.expander("Learn about embedding dimensions"):
    st.markdown("""
    **Common embedding dimensions:**
    - **OpenAI text-embedding-ada-002**: 1536 dimensions
    - **Ollama nomic-embed-text**: 768 dimensions
    - **Ollama mxbai-embed-large**: 1024 dimensions
    - **Ollama all-minilm**: 384 dimensions
    
    When you switch from OpenAI to Ollama, the vector database collection must be recreated with the new dimensions.
    """)

st.markdown("### 🔧 Manual Alternative")
with st.expander("Manual fix using Qdrant API"):
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "zenith_documents")
    
    st.code(f"""
# Using curl (if you have direct access):
curl -X DELETE "YOUR_QDRANT_URL/collections/{collection_name}"

curl -X PUT "YOUR_QDRANT_URL/collections/{collection_name}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "vectors": {{
      "size": 1024,
      "distance": "Cosine"
    }}
  }}'
    """)
