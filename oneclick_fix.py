import streamlit as st
import os
import requests
import json
from pathlib import Path

# Load environment
def load_env():
    env_path = Path(__file__).parent / ".env"
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value
    except Exception:
        pass

load_env()

st.title("🔧 One-Click Vector Fix")

st.markdown("""
**Problem:** Vector dimension error when searching documents.

**Solution:** This tool will automatically fix your collection dimensions.
""")

# Configuration
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
collection_name = os.getenv("QDRANT_COLLECTION_NAME", "zenith_documents")
ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Show config
with st.expander("Show Configuration"):
    st.write(f"Qdrant URL: {qdrant_url}")
    st.write(f"Collection: {collection_name}")
    st.write(f"Ollama Model: {ollama_model}")

# Dimension mapping
dimensions = {
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
}
target_dim = dimensions.get(ollama_model, 1024)

st.write(f"**Target dimensions for {ollama_model}: {target_dim}**")

# Main action
st.markdown("---")

if st.button("🔄 FIX VECTOR DIMENSIONS NOW", type="primary", use_container_width=True):
    
    # Set up headers
    headers = {"Content-Type": "application/json"}
    if qdrant_api_key:
        headers["api-key"] = qdrant_api_key
    
    collection_url = f"{qdrant_url.rstrip('/')}/collections/{collection_name}"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Check connection
        status_text.text("🔌 Testing Qdrant connection...")
        progress_bar.progress(10)
        
        health_response = requests.get(f"{qdrant_url.rstrip('/')}/health", headers=headers, timeout=10)
        if health_response.status_code != 200:
            st.error("❌ Cannot connect to Qdrant")
            st.stop()
        
        # Step 2: Check collection
        status_text.text("📊 Checking current collection...")
        progress_bar.progress(25)
        
        collection_response = requests.get(collection_url, headers=headers, timeout=10)
        
        if collection_response.status_code == 404:
            st.info("ℹ️ Collection doesn't exist yet - will be created when you upload documents")
            st.stop()
        elif collection_response.status_code != 200:
            st.error(f"❌ Error accessing collection: {collection_response.status_code}")
            st.stop()
        
        # Step 3: Analyze dimensions
        status_text.text("🔍 Analyzing dimensions...")
        progress_bar.progress(40)
        
        collection_info = collection_response.json()
        current_dim = collection_info["result"]["config"]["params"]["vectors"]["size"]
        points_count = collection_info["result"]["points_count"]
        
        st.write(f"📊 **Current Status:**")
        st.write(f"- Collection dimensions: {current_dim}")
        st.write(f"- Target dimensions: {target_dim}")
        st.write(f"- Documents in collection: {points_count}")
        
        if current_dim == target_dim:
            st.success("✅ Dimensions are already correct!")
            st.stop()
        
        # Step 4: Show warning and get permission
        st.warning(f"⚠️ **WILL DELETE {points_count} DOCUMENTS**")
        
        # Step 5: Delete collection
        status_text.text("🗑️ Deleting old collection...")
        progress_bar.progress(60)
        
        delete_response = requests.delete(collection_url, headers=headers, timeout=30)
        if delete_response.status_code not in [200, 404]:
            st.error(f"❌ Failed to delete collection: {delete_response.status_code}")
            st.stop()
        
        # Step 6: Create new collection
        status_text.text("✨ Creating new collection...")
        progress_bar.progress(80)
        
        create_data = {
            "vectors": {
                "size": target_dim,
                "distance": "Cosine"
            }
        }
        
        create_response = requests.put(
            collection_url,
            headers=headers,
            data=json.dumps(create_data),
            timeout=30
        )
        
        if create_response.status_code != 200:
            st.error(f"❌ Failed to create collection: {create_response.status_code}")
            st.code(create_response.text)
            st.stop()
        
        # Step 7: Verify
        status_text.text("✅ Verifying fix...")
        progress_bar.progress(100)
        
        verify_response = requests.get(collection_url, headers=headers, timeout=10)
        if verify_response.status_code == 200:
            verify_info = verify_response.json()
            new_dim = verify_info["result"]["config"]["params"]["vectors"]["size"]
            
            if new_dim == target_dim:
                status_text.text("🎉 Fix completed successfully!")
                st.success(f"✅ Collection recreated with {new_dim} dimensions!")
                st.balloons()
                
                st.markdown("### ✅ Next Steps:")
                st.markdown("1. 🔄 **Restart your main Streamlit app**")
                st.markdown("2. 📄 **Re-upload your PDF documents**")
                st.markdown("3. 🔍 **Test document searches**")
            else:
                st.error(f"❌ Verification failed: got {new_dim} instead of {target_dim}")
        else:
            st.error("❌ Could not verify the fix")
    
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to Qdrant at {qdrant_url}")
        st.error("Make sure Qdrant is running and the URL is correct")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())

# Alternative options
st.markdown("---")
st.markdown("### Alternative Solutions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Command Line Fix:**")
    st.code("python direct_vector_fix.py")

with col2:
    st.markdown("**Manual Qdrant API:**")
    if st.button("Show API Commands"):
        st.code(f"""
# Delete collection
curl -X DELETE "{qdrant_url}/collections/{collection_name}"

# Create new collection  
curl -X PUT "{qdrant_url}/collections/{collection_name}" \\
  -H "Content-Type: application/json" \\
  -d '{{"vectors": {{"size": {target_dim}, "distance": "Cosine"}}}}'
        """)
