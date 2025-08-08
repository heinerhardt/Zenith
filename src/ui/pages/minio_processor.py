"""
Working MinIO Processor Page for Streamlit
Simple, functional MinIO integration
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Page configuration
st.set_page_config(
    page_title="MinIO PDF Processor - Zenith",
    page_icon="🗄️",
    layout="wide"
)

# Check if MinIO is available
try:
    from src.core.minio_client import MinIOClient
    MINIO_AVAILABLE = True
except ImportError as e:
    MINIO_AVAILABLE = False
    MINIO_ERROR = str(e)

def main():
    """Main MinIO processor page"""
    st.title("🗄️ MinIO PDF Processor")
    st.write("Process PDF documents from MinIO buckets into your Zenith knowledge base.")
    
    # System status check
    st.sidebar.header("🔧 System Status")
    
    # Check MinIO availability
    if not MINIO_AVAILABLE:
        st.sidebar.error("❌ MinIO not available")
        st.error("❌ MinIO integration not available")
        st.error(f"Import error: {MINIO_ERROR}")
        
        st.info("**To fix this:**")
        st.code("pip install minio>=7.2.0")
        
        st.info("**Then restart the Streamlit application**")
        return
    else:
        st.sidebar.success("✅ MinIO available")
    
    # Check other components
    try:
        from src.core.config import config
        st.sidebar.success("✅ Configuration loaded")
        
        # Show key config values (safely)
        with st.sidebar.expander("📋 Config Status"):
            st.write(f"OpenAI API Key: {'✅ Set' if config.openai_api_key and config.openai_api_key != 'your_openai_api_key_here' else '❌ Not set'}")
            st.write(f"Qdrant URL: {config.qdrant_url}")
            st.write(f"Collection: {config.qdrant_collection_name}")
    except Exception as e:
        st.sidebar.error("❌ Configuration error")
        st.sidebar.write(str(e))
    
    # Check PDF processor
    try:
        from src.core.pdf_processor import PDFProcessor
        st.sidebar.success("✅ PDF Processor available")
    except Exception as e:
        st.sidebar.error("❌ PDF Processor error")
        st.sidebar.write(str(e))
    
    # Check vector store
    try:
        from src.core.vector_store import VectorStore
        st.sidebar.success("✅ Vector Store available")
    except Exception as e:
        st.sidebar.error("❌ Vector Store error")
        st.sidebar.write(str(e))
    
    # Create tabs for MinIO functionality
    tab1, tab2 = st.tabs(["⚙️ Configuration", "🚀 Process PDFs"])
    
    with tab1:
        render_minio_config()
    
    with tab2:
        render_minio_processor()

def render_minio_config():
    """MinIO Configuration Interface"""
    st.header("⚙️ MinIO Configuration")
    st.write("Configure your MinIO server connection.")
    
    with st.form("minio_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            endpoint = st.text_input(
                "MinIO Endpoint",
                value=st.session_state.get('minio_endpoint', '10.16.100.2:9000'),
                help="Your MinIO server endpoint"
            )
            
            access_key = st.text_input(
                "Access Key",
                value=st.session_state.get('minio_access_key', 'minioadmin'),
                help="MinIO access key"
            )
            
            secure = st.checkbox(
                "Use HTTPS",
                value=st.session_state.get('minio_secure', False),
                help="Enable for secure connections"
            )
        
        with col2:
            secret_key = st.text_input(
                "Secret Key",
                value=st.session_state.get('minio_secret_key', 'minioadmin'),
                type="password",
                help="MinIO secret key"
            )
            
            region = st.text_input(
                "Region",
                value=st.session_state.get('minio_region', 'us-east-1'),
                help="MinIO region"
            )
        
        # Form buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            save_and_test = st.form_submit_button("💾 Save & Test Connection", type="primary")
        
        with col2:
            test_only = st.form_submit_button("🔍 Test Connection Only")
        
        with col3:
            clear_config = st.form_submit_button("🧹 Clear Configuration")
        
        # Handle form actions
        if clear_config:
            # Clear all MinIO session state
            keys_to_clear = ['minio_endpoint', 'minio_access_key', 'minio_secret_key', 
                           'minio_secure', 'minio_region', 'minio_client']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✅ Configuration cleared!")
            st.rerun()
        
        if save_and_test or test_only:
            if not access_key or not secret_key:
                st.error("❌ Access key and secret key are required!")
            else:
                # Save configuration if requested
                if save_and_test:
                    st.session_state['minio_endpoint'] = endpoint
                    st.session_state['minio_access_key'] = access_key
                    st.session_state['minio_secret_key'] = secret_key
                    st.session_state['minio_secure'] = secure
                    st.session_state['minio_region'] = region
                    st.success("✅ Configuration saved!")
                
                # Test connection
                with st.spinner("Testing MinIO connection..."):
                    try:
                        client = MinIOClient(
                            endpoint=endpoint,
                            access_key=access_key,
                            secret_key=secret_key,
                            secure=secure,
                            region=region
                        )
                        
                        if client.test_connection():
                            st.success("✅ Connection successful!")
                            st.session_state['minio_client'] = client
                            
                            # Show buckets
                            try:
                                buckets = client.list_buckets()
                                if buckets:
                                    st.info(f"Found {len(buckets)} bucket(s)")
                                    
                                    with st.expander("📦 Available Buckets"):
                                        for bucket in buckets:
                                            st.write(f"• **{bucket['name']}** - Created: {bucket['creation_date_str']}")
                                else:
                                    st.warning("No buckets found. Create buckets using MinIO console.")
                            except Exception as e:
                                st.warning(f"Connected, but couldn't list buckets: {e}")
                        else:
                            st.error("❌ Connection test failed!")
                            
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                        
                        with st.expander("🔧 Troubleshooting"):
                            st.markdown("""
                            **Common Issues:**
                            
                            1. **MinIO server not running**
                               - Check if your MinIO server is accessible
                               - Try accessing the web console
                            
                            2. **Network connectivity**
                               - Verify the endpoint address is correct
                               - Check firewall and network settings
                            
                            3. **Authentication**
                               - Verify access key and secret key
                               - Check user permissions in MinIO
                            """)
    
    # Connection Status
    st.divider()
    st.header("📊 Current Connection Status")
    
    client = st.session_state.get('minio_client')
    if client:
        try:
            if client.test_connection():
                st.success("✅ MinIO is connected and ready!")
                
                info = client.get_connection_info()
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Endpoint", info['endpoint'])
                with col2:
                    st.metric("Secure", "Yes" if info['secure'] else "No")
                with col3:
                    st.metric("Status", "Connected")
            else:
                st.error("❌ Connection lost - please reconfigure")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")
    else:
        st.info("⚠️ No MinIO connection configured")

def render_minio_processor():
    """MinIO PDF Processor Interface"""
    st.header("🚀 Process PDFs from MinIO")
    
    # Check MinIO connection
    client = st.session_state.get('minio_client')
    
    if not client:
        st.warning("⚠️ MinIO not connected")
        st.info("Please configure MinIO connection in the Configuration tab first.")
        return
    
    # Test connection
    try:
        if not client.test_connection():
            st.error("❌ MinIO connection lost")
            st.info("Please reconfigure connection in the Configuration tab.")
            return
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        return
    
    st.success("✅ MinIO connected successfully!")
    
    # Load and display buckets
    try:
        with st.spinner("Loading buckets..."):
            buckets = client.list_buckets()
        
        if not buckets:
            st.warning("❌ No buckets found")
            st.info("Create buckets and upload PDFs using MinIO console.")
            return
        
        # Bucket selection
        st.subheader("📦 Select Bucket")
        bucket_names = [bucket['name'] for bucket in buckets]
        selected_bucket = st.selectbox(
            "Choose bucket to process:",
            bucket_names,
            key="bucket_selector"
        )
        
        if selected_bucket:
            # Show bucket info
            bucket_info = next((b for b in buckets if b['name'] == selected_bucket), None)
            if bucket_info:
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"📦 **Bucket:** {selected_bucket}")
                with col2:
                    st.info(f"📅 **Created:** {bucket_info['creation_date_str']}")
            
            # Load PDF files from bucket
            with st.spinner(f"Scanning bucket '{selected_bucket}' for PDF files..."):
                pdf_objects = client.list_pdf_objects(selected_bucket)
            
            if not pdf_objects:
                st.warning(f"❌ No PDF files found in bucket '{selected_bucket}'")
                st.info("Upload PDF files to this bucket using MinIO console.")
                return
            
            # Display found PDFs
            st.success(f"✅ Found **{len(pdf_objects)}** PDF files")
            
            # PDF file preview
            with st.expander(f"📄 PDF Files Preview ({len(pdf_objects)} files)"):
                for i, pdf in enumerate(pdf_objects[:20]):  # Show first 20
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📄 {pdf['name']}")
                    with col2:
                        st.write(pdf['size_str'])
                    with col3:
                        st.write(pdf['last_modified_str'][:10])  # Date only
                
                if len(pdf_objects) > 20:
                    st.write(f"... and {len(pdf_objects) - 20} more files")
            
            # Processing options
            st.subheader("⚙️ Processing Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_files = st.number_input(
                    "Max files to process",
                    min_value=1,
                    max_value=len(pdf_objects),
                    value=min(10, len(pdf_objects)),
                    help="Start with a small number for testing"
                )
                
                batch_size = st.slider(
                    "Batch size",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Number of files to process simultaneously"
                )
            
            with col2:
                # Show processing estimates
                files_to_process = pdf_objects[:max_files]
                total_size = sum(obj.get('size', 0) for obj in files_to_process)
                total_mb = total_size / (1024 * 1024)
                
                st.metric("Files to process", max_files)
                st.metric("Total size", f"{total_mb:.1f} MB")
                
                # Rough time estimate
                estimated_time = max_files * 30  # ~30 seconds per file
                st.metric("Estimated time", f"{estimated_time} seconds")
            
            # Action buttons
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    process_pdfs_from_minio(client, selected_bucket, files_to_process)
            
            with col2:
                if st.button("📊 Analyze Bucket", use_container_width=True):
                    analyze_bucket_contents(client, selected_bucket, pdf_objects)
            
            with col3:
                if st.button("🔄 Refresh Bucket", use_container_width=True):
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading bucket information: {e}")

def process_pdfs_from_minio(client, bucket_name, pdf_objects):
    """Process PDFs from MinIO bucket"""
    st.header("🔄 Processing PDFs...")
    
    # Initialize processing components
    try:
        from src.core.pdf_processor import PDFProcessor
        from src.core.vector_store import VectorStore
        
        # Initialize components directly (don't rely on session state)
        pdf_processor = PDFProcessor()
        vector_store = VectorStore()
        
        st.info("✅ PDF processor and vector store initialized successfully")
        
    except ImportError as e:
        st.error(f"❌ Required components not available: {e}")
        st.info("Make sure your Zenith application dependencies are installed.")
        return
    except Exception as e:
        st.error(f"❌ Error initializing processors: {e}")
        st.error("This might be due to missing configuration (OpenAI API key, Qdrant connection, etc.)")
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common issues:**
            
            1. **Missing OpenAI API Key**
               - Check your .env file has OPENAI_API_KEY set
               - Verify the API key is valid
            
            2. **Qdrant Connection Issues**
               - Check QDRANT_URL and QDRANT_API_KEY in .env
               - Verify Qdrant server is accessible
            
            3. **Missing Dependencies**
               - Run: pip install langchain openai qdrant-client
            """)
        return
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.container()
    results_container = st.container()
    
    processed_count = 0
    failed_count = 0
    total_chunks = 0
    
    # Create temp directory
    temp_dir = Path("temp_minio_pdfs")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        for i, pdf_obj in enumerate(pdf_objects):
            object_name = pdf_obj['name']
            
            with status_container:
                st.write(f"📥 Processing {i+1}/{len(pdf_objects)}: {object_name}")
            
            try:
                # Download PDF from MinIO
                local_path = client.download_object(bucket_name, object_name)
                
                # Process PDF
                documents = pdf_processor.load_pdf(local_path)
                
                # Add MinIO source metadata
                for doc in documents:
                    doc.metadata.update({
                        'source': f"minio://{bucket_name}/{object_name}",
                        'minio_bucket': bucket_name,
                        'minio_object': object_name,
                        'file_size': pdf_obj.get('size', 0),
                        'last_modified': pdf_obj.get('last_modified_str', ''),
                        'processed_via': 'minio_processor_page'
                    })
                
                # Split documents into chunks
                chunks = pdf_processor.split_documents(documents)
                
                # Add to vector store
                if chunks:
                    vector_store.add_documents(chunks)
                    total_chunks += len(chunks)
                
                # Show success
                with results_container:
                    st.success(f"✅ {object_name}: {len(documents)} pages → {len(chunks)} chunks")
                
                processed_count += 1
                
                # Cleanup temp file
                if local_path and local_path.exists():
                    local_path.unlink()
            
            except Exception as e:
                with results_container:
                    st.error(f"❌ Failed to process {object_name}: {str(e)}")
                failed_count += 1
                
                # Log detailed error for debugging
                import traceback
                error_details = traceback.format_exc()
                with st.expander(f"Error details for {object_name}"):
                    st.code(error_details)
            
            # Update progress
            progress_bar.progress((i + 1) / len(pdf_objects))
        
        # Final status
        with status_container:
            st.write("🎉 Processing complete!")
        
        # Show results summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("✅ Processed", processed_count)
        with col2:
            st.metric("❌ Failed", failed_count)
        with col3:
            st.metric("📄 Total Chunks", total_chunks)
        with col4:
            success_rate = (processed_count / len(pdf_objects)) * 100 if pdf_objects else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        if processed_count > 0:
            st.balloons()
            st.success(f"🎉 Successfully processed {processed_count} PDFs and created {total_chunks} text chunks!")
            st.info("💬 You can now chat with these documents in your main Zenith application!")
            
            # Show link to main app
            st.markdown("**Next Steps:**")
            st.markdown("1. Go to your [main Zenith app](http://localhost:8505)")
            st.markdown("2. Use the 'Chat Interface' tab")
            st.markdown("3. Ask questions about your processed documents")
    
    except Exception as e:
        st.error(f"❌ Processing error: {e}")
        
        # Show detailed error information
        import traceback
        error_details = traceback.format_exc()
        with st.expander("Detailed Error Information"):
            st.code(error_details)
    
    finally:
        # Cleanup temp directory
        try:
            for temp_file in temp_dir.glob("*.pdf"):
                temp_file.unlink()
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
        except Exception:
            pass

def analyze_bucket_contents(client, bucket_name, pdf_objects):
    """Analyze bucket contents"""
    st.header(f"📊 Bucket Analysis: {bucket_name}")
    
    if not pdf_objects:
        st.info("No PDF files to analyze")
        return
    
    # Basic statistics
    total_files = len(pdf_objects)
    total_size = sum(obj.get('size', 0) for obj in pdf_objects)
    total_mb = total_size / (1024 * 1024)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total PDFs", total_files)
    with col2:
        st.metric("Total Size", f"{total_mb:.1f} MB")
    with col3:
        avg_size = total_mb / total_files if total_files > 0 else 0
        st.metric("Average Size", f"{avg_size:.1f} MB")
    with col4:
        largest = max(pdf_objects, key=lambda x: x.get('size', 0))
        largest_mb = largest.get('size', 0) / (1024 * 1024)
        st.metric("Largest File", f"{largest_mb:.1f} MB")
    
    # Recent files
    st.subheader("📅 Recently Modified Files")
    
    sorted_files = sorted(pdf_objects, key=lambda x: x.get('last_modified', ''), reverse=True)
    
    for i, obj in enumerate(sorted_files[:10]):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📄 {obj['name']}")
        with col2:
            st.write(obj['size_str'])
        with col3:
            st.write(obj.get('last_modified_str', 'Unknown')[:10])

# Run the main function
if __name__ == "__main__":
    main()
else:
    # This is executed when the page is loaded as a Streamlit page
    main()
