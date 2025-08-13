import streamlit as st
import requests
import json
import os
from pathlib import Path

st.title("🔧 Qdrant Cloud Vector Fix")

# Load environment manually
env_path = Path(__file__).parent / ".env"
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

# Configuration from your .env
qdrant_url = "https://ff544b2f-9868-490a-806a-f499c01c3b2b.us-east4-0.gcp.cloud.qdrant.io"
qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.k1rigQDkZo9G4gIkWcmIBnDt96Er6rhV7nETUvQOcm8"
collection_name = "zenith_documents"
ollama_model = "nomic-embed-text"

st.markdown(f"""
### Your Configuration:
- **Qdrant**: Cloud instance (Qdrant Cloud)
- **Collection**: `{collection_name}`
- **Model**: `{ollama_model}`
- **Required dimensions**: `768` (for nomic-embed-text)
""")

headers = {
    "Content-Type": "application/json",
    "api-key": qdrant_api_key
}

# Test connection first
if st.button("🔌 Test Connection", type="secondary"):
    try:
        response = requests.get(f"{qdrant_url}/health", headers=headers, timeout=10)
        if response.status_code == 200:
            st.success("✅ Connected to Qdrant Cloud successfully!")
        else:
            st.error(f"❌ Connection failed: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Connection error: {e}")

# Check collection status
if st.button("📊 Check Collection", type="secondary"):
    try:
        collection_url = f"{qdrant_url}/collections/{collection_name}"
        response = requests.get(collection_url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            st.info("ℹ️ Collection doesn't exist yet")
        elif response.status_code == 200:
            data = response.json()
            current_dim = data["result"]["config"]["params"]["vectors"]["size"]
            points_count = data["result"]["points_count"]
            
            st.write(f"**Collection Status:**")
            st.write(f"- Current dimensions: `{current_dim}`")
            st.write(f"- Required dimensions: `768`")
            st.write(f"- Documents: `{points_count}`")
            
            if current_dim != 768:
                st.error(f"❌ Dimension mismatch: {current_dim} → 768")
                st.session_state.needs_fix = True
                st.session_state.points_count = points_count
            else:
                st.success("✅ Dimensions are correct!")
        else:
            st.error(f"❌ Error: {response.status_code}")
            st.code(response.text)
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Fix button
st.markdown("---")
if st.session_state.get('needs_fix', False):
    points_count = st.session_state.get('points_count', 0)
    
    st.warning(f"⚠️ **This will delete {points_count} documents!**")
    
    confirm = st.checkbox("I understand all documents will be deleted")
    
    if confirm and st.button("🔄 FIX COLLECTION NOW", type="primary"):
        collection_url = f"{qdrant_url}/collections/{collection_name}"
        
        progress = st.progress(0)
        status = st.empty()
        
        try:
            # Delete
            status.text("🗑️ Deleting collection...")
            progress.progress(33)
            
            delete_resp = requests.delete(collection_url, headers=headers, timeout=30)
            
            if delete_resp.status_code in [200, 404]:
                status.text("✨ Creating new collection...")
                progress.progress(66)
                
                # Create with 768 dimensions for nomic-embed-text
                create_data = {
                    "vectors": {
                        "size": 768,
                        "distance": "Cosine"
                    }
                }
                
                create_resp = requests.put(
                    collection_url,
                    headers=headers,
                    json=create_data,
                    timeout=30
                )
                
                if create_resp.status_code == 200:
                    status.text("✅ Verifying...")
                    progress.progress(100)
                    
                    # Verify
                    verify_resp = requests.get(collection_url, headers=headers)
                    if verify_resp.status_code == 200:
                        verify_data = verify_resp.json()
                        new_dim = verify_data["result"]["config"]["params"]["vectors"]["size"]
                        
                        if new_dim == 768:
                            st.success("🎉 Collection fixed successfully!")
                            st.balloons()
                            
                            # Clear session state
                            if 'needs_fix' in st.session_state:
                                del st.session_state.needs_fix
                            
                            st.markdown("### ✅ Next Steps:")
                            st.markdown("1. Restart your Streamlit app")
                            st.markdown("2. Re-upload your PDF documents")
                            st.markdown("3. Test document searches")
                        else:
                            st.error(f"❌ Verification failed: got {new_dim}")
                else:
                    st.error(f"❌ Create failed: {create_resp.status_code}")
                    st.code(create_resp.text)
            else:
                st.error(f"❌ Delete failed: {delete_resp.status_code}")
                
        except Exception as e:
            st.error(f"❌ Error during fix: {e}")

# Manual commands
st.markdown("---")
st.markdown("### Manual Fix Commands")
st.markdown("If the button doesn't work, you can use these curl commands:")

st.code(f"""
# Delete collection
curl -X DELETE "{qdrant_url}/collections/{collection_name}" \\
  -H "api-key: {qdrant_api_key}"

# Create new collection with 768 dimensions
curl -X PUT "{qdrant_url}/collections/{collection_name}" \\
  -H "Content-Type: application/json" \\
  -H "api-key: {qdrant_api_key}" \\
  -d '{{"vectors": {{"size": 768, "distance": "Cosine"}}}}'
""")

st.markdown("### Why 768 dimensions?")
st.info("The `nomic-embed-text` model produces 768-dimensional vectors, but your collection was created for OpenAI's 1536 dimensions.")
