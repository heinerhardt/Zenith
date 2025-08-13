import streamlit as st
import requests
import json
import os
from pathlib import Path

st.title("🔧 Standalone Vector Dimension Fix")

st.markdown("""
### No Import Issues!
This tool works directly with your Qdrant database using only standard libraries.
""")

# Load .env manually
@st.cache_data
def load_env_config():
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

# Load configuration
config = load_env_config()

# Display configuration
st.write("### 📋 Your Configuration:")
qdrant_url = config.get("QDRANT_URL", "Not found")
collection_name = config.get("QDRANT_COLLECTION_NAME", "zenith_documents")
ollama_model = config.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

st.write(f"- **Qdrant URL**: `{qdrant_url}`")
st.write(f"- **Collection**: `{collection_name}`")
st.write(f"- **Ollama Model**: `{ollama_model}`")

# Model dimension mapping
dimension_map = {
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
    "all-MiniLM-L6-v2": 384,
    "text-embedding-ada-002": 1536  # OpenAI
}

target_dimension = dimension_map.get(ollama_model, 768)
st.write(f"- **Target Dimensions**: `{target_dimension}`")

# Check if we have the needed configuration
if not config.get("QDRANT_URL") or not config.get("QDRANT_API_KEY"):
    st.error("❌ Missing Qdrant configuration in .env file!")
    st.stop()

# Set up headers for Qdrant
headers = {
    "Content-Type": "application/json",
    "api-key": config["QDRANT_API_KEY"]
}

st.markdown("---")

# Step 1: Test Connection
if st.button("🔌 Test Qdrant Connection", type="secondary"):
    try:
        with st.spinner("Testing connection..."):
            response = requests.get(f"{qdrant_url}/health", headers=headers, timeout=10)
        
        if response.status_code == 200:
            st.success("✅ Connected to Qdrant successfully!")
        else:
            st.error(f"❌ Connection failed: HTTP {response.status_code}")
            st.code(response.text)
    except Exception as e:
        st.error(f"❌ Connection error: {e}")

# Step 2: Check Collection
if st.button("📊 Check Collection Dimensions", type="secondary"):
    try:
        collection_url = f"{qdrant_url}/collections/{collection_name}"
        
        with st.spinner("Checking collection..."):
            response = requests.get(collection_url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            st.info("ℹ️ Collection doesn't exist yet. It will be created when you upload documents.")
        elif response.status_code == 200:
            data = response.json()
            current_dim = data["result"]["config"]["params"]["vectors"]["size"]
            points_count = data["result"]["points_count"]
            
            st.write("### 📊 Collection Status:")
            st.write(f"- **Current dimensions**: `{current_dim}`")
            st.write(f"- **Target dimensions**: `{target_dimension}`")
            st.write(f"- **Documents stored**: `{points_count}`")
            
            if current_dim == target_dimension:
                st.success("✅ Dimensions are already correct!")
            else:
                st.error(f"❌ Dimension mismatch detected!")
                st.write(f"**Fix needed**: {current_dim} → {target_dimension}")
                
                # Store the mismatch info
                st.session_state.dimension_mismatch = True
                st.session_state.current_dim = current_dim
                st.session_state.target_dim = target_dimension
                st.session_state.points_count = points_count
        else:
            st.error(f"❌ Error checking collection: HTTP {response.status_code}")
            st.code(response.text)
            
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Step 3: Fix Dimensions (if mismatch detected)
if st.session_state.get('dimension_mismatch', False):
    st.markdown("---")
    st.markdown("### 🔧 Fix Dimension Mismatch")
    
    current_dim = st.session_state.get('current_dim', 0)
    target_dim = st.session_state.get('target_dim', 0)
    points_count = st.session_state.get('points_count', 0)
    
    st.warning(f"⚠️ **This will delete {points_count} documents!**")
    st.write("You will need to re-upload your PDF files after this fix.")
    
    # Confirmation
    confirm = st.checkbox(f"✅ I understand that {points_count} documents will be deleted")
    
    if confirm:
        if st.button("🔄 FIX DIMENSIONS NOW", type="primary", use_container_width=True):
            collection_url = f"{qdrant_url}/collections/{collection_name}"
            
            try:
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Delete collection
                status_text.text("🗑️ Deleting old collection...")
                progress_bar.progress(25)
                
                delete_response = requests.delete(collection_url, headers=headers, timeout=30)
                
                if delete_response.status_code in [200, 404]:
                    status_text.text("✨ Creating new collection...")
                    progress_bar.progress(50)
                    
                    # Step 2: Create new collection
                    create_data = {
                        "vectors": {
                            "size": target_dim,
                            "distance": "Cosine"
                        }
                    }
                    
                    create_response = requests.put(
                        collection_url,
                        headers=headers,
                        json=create_data,
                        timeout=30
                    )
                    
                    if create_response.status_code == 200:
                        status_text.text("🔍 Verifying fix...")
                        progress_bar.progress(75)
                        
                        # Step 3: Verify
                        verify_response = requests.get(collection_url, headers=headers, timeout=10)
                        
                        if verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            new_dim = verify_data["result"]["config"]["params"]["vectors"]["size"]
                            
                            progress_bar.progress(100)
                            status_text.text("✅ Fix completed!")
                            
                            if new_dim == target_dim:
                                st.success(f"🎉 Collection fixed successfully!")
                                st.balloons()
                                
                                # Clear session state
                                if 'dimension_mismatch' in st.session_state:
                                    del st.session_state.dimension_mismatch
                                
                                st.markdown("### ✅ Next Steps:")
                                st.markdown("1. 🔄 **Restart your Streamlit app**")
                                st.markdown("2. 📄 **Re-upload your PDF documents**")
                                st.markdown("3. 🔍 **Test document searches**")
                            else:
                                st.error(f"❌ Verification failed: expected {target_dim}, got {new_dim}")
                        else:
                            st.error("❌ Could not verify the fix")
                    else:
                        st.error(f"❌ Failed to create collection: {create_response.status_code}")
                        st.code(create_response.text)
                else:
                    st.error(f"❌ Failed to delete collection: {delete_response.status_code}")
                    st.code(delete_response.text)
                    
            except Exception as e:
                st.error(f"❌ Error during fix: {e}")

# Manual commands section
st.markdown("---")
st.markdown("### 🛠️ Manual Fix Commands")
st.markdown("If the buttons don't work, you can use these curl commands:")

manual_commands = f"""
# Delete collection
curl -X DELETE "{qdrant_url}/collections/{collection_name}" \\
  -H "api-key: {config.get('QDRANT_API_KEY', 'YOUR_API_KEY')}"

# Create new collection with {target_dimension} dimensions
curl -X PUT "{qdrant_url}/collections/{collection_name}" \\
  -H "Content-Type: application/json" \\
  -H "api-key: {config.get('QDRANT_API_KEY', 'YOUR_API_KEY')}" \\
  -d '{{"vectors": {{"size": {target_dimension}, "distance": "Cosine"}}}}'
"""

st.code(manual_commands)

# Information section
st.markdown("---")
st.markdown("### 📚 Understanding the Problem")

with st.expander("Why do dimension mismatches happen?"):
    st.markdown(f"""
    **Vector dimensions** depend on the embedding model you're using:
    
    - **OpenAI text-embedding-ada-002**: 1536 dimensions
    - **Ollama nomic-embed-text**: 768 dimensions
    - **Ollama mxbai-embed-large**: 1024 dimensions
    - **Ollama all-minilm**: 384 dimensions
    
    **Your current setup:**
    - Model: `{ollama_model}`
    - Expected dimensions: `{target_dimension}`
    
    When you switch from OpenAI to Ollama (or between different Ollama models), 
    the vector database collection must be recreated with the new dimensions.
    
    **This tool fixes the mismatch by:**
    1. Deleting the old collection (with wrong dimensions)
    2. Creating a new collection (with correct dimensions)
    3. Verifying the fix worked
    """)

st.markdown("### 🔄 After the Fix")
st.info("""
**Remember**: After fixing dimensions, you'll need to:
1. Restart your main Streamlit application
2. Re-upload all your PDF documents (they were deleted)
3. The documents will be embedded with the correct dimensions
4. Document searches should work without errors
""")
