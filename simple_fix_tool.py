import streamlit as st
import sys
import os
from pathlib import Path
import requests
import json

# Fix the import path issue
zenith_root = Path(__file__).parent
os.chdir(zenith_root)

# Load environment variables manually
def load_env():
    env_path = zenith_root / ".env"
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    env_vars[key] = value
                    os.environ[key] = value
    except Exception as e:
        st.error(f"Could not load .env file: {e}")
    return env_vars

st.title("🔧 Simple Vector Fix Tool")

# Load environment
env_vars = load_env()

# Get configuration
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
collection_name = os.getenv("QDRANT_COLLECTION_NAME", "zenith_documents")
ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

st.write("### Configuration:")
st.write(f"- Qdrant URL: `{qdrant_url}`")
st.write(f"- Collection: `{collection_name}`")
st.write(f"- Ollama Model: `{ollama_model}`")

# Dimension mapping
ollama_dimensions = {
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
    "all-MiniLM-L6-v2": 384,
}
required_dim = ollama_dimensions.get(ollama_model, 1024)

st.write(f"- Required Dimensions: `{required_dim}`")

# Initialize session state
if 'check_done' not in st.session_state:
    st.session_state.check_done = False
if 'collection_info' not in st.session_state:
    st.session_state.collection_info = None
if 'needs_fix' not in st.session_state:
    st.session_state.needs_fix = False

# Step 1: Check Collection
st.markdown("---")
st.markdown("### Step 1: Check Collection")

if st.button("🔍 Check Collection Status", type="primary"):
    headers = {"Content-Type": "application/json"}
    if qdrant_api_key:
        headers["api-key"] = qdrant_api_key
    
    try:
        collection_url = f"{qdrant_url.rstrip('/')}/collections/{collection_name}"
        
        with st.spinner("Checking collection..."):
            response = requests.get(collection_url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            st.info("ℹ️ Collection does not exist yet. It will be created when you upload documents.")
            st.session_state.check_done = True
            st.session_state.needs_fix = False
        elif response.status_code == 200:
            collection_info = response.json()
            current_dim = collection_info["result"]["config"]["params"]["vectors"]["size"]
            points_count = collection_info["result"]["points_count"]
            
            st.session_state.collection_info = {
                'current_dim': current_dim,
                'points_count': points_count,
                'required_dim': required_dim
            }
            st.session_state.check_done = True
            
            st.write(f"**Current Collection Status:**")
            st.write(f"- Current dimensions: `{current_dim}`")
            st.write(f"- Required dimensions: `{required_dim}`")
            st.write(f"- Documents stored: `{points_count}`")
            
            if current_dim != required_dim:
                st.error(f"❌ Dimension mismatch! Expected {required_dim}, got {current_dim}")
                st.session_state.needs_fix = True
            else:
                st.success("✅ Dimensions are correct!")
                st.session_state.needs_fix = False
        else:
            st.error(f"❌ Error checking collection: {response.status_code}")
            st.code(response.text)
            
    except Exception as e:
        st.error(f"❌ Connection error: {e}")

# Step 2: Fix if needed
if st.session_state.check_done and st.session_state.needs_fix:
    st.markdown("---")
    st.markdown("### Step 2: Fix Collection")
    
    info = st.session_state.collection_info
    
    st.warning(f"⚠️ **WARNING**: This will delete {info['points_count']} documents!")
    st.write("You will need to re-upload your PDF files after this fix.")
    
    # Use a unique key and clear confirmation
    confirm_delete = st.checkbox("✅ I understand that all documents will be deleted", key="confirm_checkbox")
    
    if confirm_delete:
        if st.button("🗑️ DELETE AND RECREATE COLLECTION", type="secondary", key="delete_button"):
            headers = {"Content-Type": "application/json"}
            if qdrant_api_key:
                headers["api-key"] = qdrant_api_key
            
            collection_url = f"{qdrant_url.rstrip('/')}/collections/{collection_name}"
            
            try:
                # Delete collection
                with st.spinner("Deleting old collection..."):
                    delete_response = requests.delete(collection_url, headers=headers, timeout=30)
                
                if delete_response.status_code in [200, 404]:
                    st.success("✅ Old collection deleted!")
                    
                    # Create new collection
                    with st.spinner("Creating new collection..."):
                        create_data = {
                            "vectors": {
                                "size": info['required_dim'],
                                "distance": "Cosine"
                            }
                        }
                        
                        create_response = requests.put(
                            collection_url, 
                            headers=headers, 
                            data=json.dumps(create_data),
                            timeout=30
                        )
                    
                    if create_response.status_code == 200:
                        st.success("✅ New collection created!")
                        st.balloons()
                        
                        # Reset session state
                        st.session_state.check_done = False
                        st.session_state.needs_fix = False
                        st.session_state.collection_info = None
                        
                        st.markdown("### 🎉 Fix Complete!")
                        st.markdown("**Next Steps:**")
                        st.markdown("1. 🔄 Restart your main Streamlit app")
                        st.markdown("2. 📄 Re-upload your PDF documents")
                        st.markdown("3. 🔍 Test searches")
                        
                        # Add a recheck button
                        if st.button("🔄 Verify Fix", key="verify_button"):
                            st.rerun()
                    else:
                        st.error(f"❌ Error creating collection: {create_response.status_code}")
                        st.code(create_response.text)
                else:
                    st.error(f"❌ Error deleting collection: {delete_response.status_code}")
                    st.code(delete_response.text)
                    
            except Exception as e:
                st.error(f"❌ Error during fix: {e}")

# Always show current status at the bottom
st.markdown("---")
st.markdown("### Debug Info")
with st.expander("Show session state"):
    st.json({
        "check_done": st.session_state.check_done,
        "needs_fix": st.session_state.needs_fix,
        "collection_info": st.session_state.collection_info
    })

st.markdown("### Manual Alternative")
st.markdown("If this tool doesn't work, try the command line version:")
st.code("python direct_vector_fix.py")
