"""
Simple MinIO Integration Script
Add this to your existing Streamlit app to enable MinIO functionality
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Check if MinIO is available
try:
    from src.core.minio_client import MinIOClient
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

def render_minio_tabs():
    """Add MinIO tabs to your existing Streamlit app"""
    
    if not MINIO_AVAILABLE:
        st.error("❌ MinIO not available")
        st.info("Install MinIO: pip install minio>=7.2.0")
        return
    
    # Create MinIO tabs
    minio_tab1, minio_tab2 = st.tabs(["⚙️ MinIO Config", "🗄️ Process PDFs"])
    
    with minio_tab1:
        render_minio_config()
    
    with minio_tab2:
        render_minio_processor()

def render_minio_config():
    """MinIO Configuration Interface"""
    st.header("⚙️ MinIO Configuration")
    
    with st.form("minio_config"):
        col1, col2 = st.columns(2)
        
        with col1:
            endpoint = st.text_input("Endpoint", value="10.16.100.2:9000")
            access_key = st.text_input("Access Key", value="minioadmin")
        
        with col2:
            secret_key = st.text_input("Secret Key", value="minioadmin", type="password")
            secure = st.checkbox("Use HTTPS", value=False)
        
        if st.form_submit_button("💾 Save & Test", type="primary"):
            if access_key and secret_key:
                try:
                    client = MinIOClient(endpoint, access_key, secret_key, secure)
                    if client.test_connection():
                        st.success("✅ Connected!")
                        st.session_state['minio_client'] = client
                        
                        buckets = client.list_buckets()
                        st.info(f"Found {len(buckets)} buckets")
                        
                        for bucket in buckets:
                            st.write(f"📦 {bucket['name']}")
                    else:
                        st.error("❌ Connection failed")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Credentials required")

def render_minio_processor():
    """MinIO PDF Processor Interface"""
    st.header("🗄️ Process PDFs from MinIO")
    
    client = st.session_state.get('minio_client')
    if not client:
        st.warning("⚠️ Configure MinIO connection first")
        return
    
    try:
        buckets = client.list_buckets()
        if not buckets:
            st.warning("No buckets found")
            return
        
        selected_bucket = st.selectbox("Select Bucket", [b['name'] for b in buckets])
        
        if selected_bucket:
            pdf_objects = client.list_pdf_objects(selected_bucket)
            st.success(f"Found {len(pdf_objects)} PDFs")
            
            if pdf_objects and st.button("🚀 Process All PDFs", type="primary"):
                process_pdfs_from_minio(client, selected_bucket, pdf_objects)
                
    except Exception as e:
        st.error(f"Error: {e}")

def process_pdfs_from_minio(client, bucket_name, pdf_objects):
    """Process PDFs from MinIO bucket"""
    
    # Import your existing processors
    try:
        # Get processors from session state (your existing app pattern)
        pdf_processor = st.session_state.get('pdf_processor')
        vector_store = st.session_state.get('vector_store')
        
        if not pdf_processor or not vector_store:
            st.error("❌ PDF processor or vector store not initialized")
            return
        
    except Exception as e:
        st.error(f"❌ Error accessing processors: {e}")
        return
    
    progress = st.progress(0)
    processed = 0
    total_chunks = 0
    
    for i, pdf in enumerate(pdf_objects):
        st.write(f"Processing: {pdf['name']}")
        
        try:
            # Download from MinIO
            local_path = client.download_object(bucket_name, pdf['name'])
            
            # Process with your existing processor
            docs = pdf_processor.load_pdf(local_path)
            
            # Add MinIO metadata
            for doc in docs:
                doc.metadata.update({
                    'source': f"minio://{bucket_name}/{pdf['name']}",
                    'minio_bucket': bucket_name,
                    'minio_object': pdf['name']
                })
            
            # Split and add to vector store
            chunks = pdf_processor.split_documents(docs)
            vector_store.add_documents(chunks)
            
            st.success(f"✅ {pdf['name']}: {len(chunks)} chunks")
            processed += 1
            total_chunks += len(chunks)
            
            # Cleanup
            if local_path.exists():
                local_path.unlink()
                
        except Exception as e:
            st.error(f"❌ {pdf['name']}: {e}")
        
        progress.progress((i + 1) / len(pdf_objects))
    
    st.balloons()
    st.success(f"🎉 Processed {processed} PDFs! Added {total_chunks} chunks to knowledge base.")
    
    # Update your app's session state
    st.session_state.documents_processed = True

# Integration instructions for your existing app
"""
INTEGRATION INSTRUCTIONS:

To add MinIO functionality to your existing Streamlit app:

1. Add this import at the top of your streamlit_app.py:
   from minio_simple_integration import render_minio_tabs, MINIO_AVAILABLE

2. In your main interface, add MinIO tabs after your existing tabs:
   
   # Your existing tabs
   tab1, tab2 = st.tabs(["📁 Upload", "💬 Chat"])
   
   # Add MinIO tabs if available
   if MINIO_AVAILABLE:
       st.divider()
       st.subheader("🗄️ MinIO Integration")
       render_minio_tabs()

3. That's it! Your app will now have MinIO functionality.
"""

if __name__ == "__main__":
    st.set_page_config(page_title="MinIO Integration Test", layout="wide")
    st.title("MinIO Integration Test")
    
    render_minio_tabs()
