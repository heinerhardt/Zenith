"""
Working MinIO Integration for Zenith PDF Chatbot
Standalone interface to test MinIO functionality
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Page configuration
st.set_page_config(
    page_title="MinIO PDF Processor - Zenith",
    page_icon="🗄️",
    layout="wide"
)

# Check MinIO availability
try:
    from src.core.minio_client import MinIOClient
    MINIO_AVAILABLE = True
except ImportError as e:
    MINIO_AVAILABLE = False
    MINIO_ERROR = str(e)

def render_minio_config():
    """MinIO Configuration Interface"""
    st.title("⚙️ MinIO Configuration")
    st.write("Configure your MinIO server connection.")
    
    if not MINIO_AVAILABLE:
        st.error("❌ MinIO library not available")
        st.error(f"Error: {MINIO_ERROR}")
        
        st.info("**To fix this issue:**")
        st.code("pip install minio>=7.2.0")
        
        st.info("**Then restart this application:**")
        st.code("streamlit run minio_integration_working.py")
        
        with st.expander("📖 Full Installation Instructions"):
            st.markdown("""
            ### Installation Steps:
            
            1. **Open terminal/command prompt**
            2. **Navigate to your project directory:**
               ```bash
               cd C:\\Zenith
               ```
            
            3. **Activate your virtual environment (if using one):**
               ```bash
               # Windows
               venv\\Scripts\\activate
               
               # Or if using conda
               conda activate your-env-name
               ```
            
            4. **Install MinIO:**
               ```bash
               pip install minio>=7.2.0
               ```
            
            5. **Restart this application:**
               ```bash
               streamlit run minio_integration_working.py
               ```
            """)
        return
    
    # MinIO configuration form
    st.header("🔧 Server Configuration")
    
    with st.form("minio_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            endpoint = st.text_input(
                "MinIO Endpoint",
                value=st.session_state.get('minio_endpoint', 'localhost:9000'),
                help="MinIO server address (e.g., localhost:9000)"
            )
            
            access_key = st.text_input(
                "Access Key",
                value=st.session_state.get('minio_access_key', 'minioadmin'),
                help="MinIO access key (default: minioadmin)"
            )
            
            secure = st.checkbox(
                "Use HTTPS",
                value=st.session_state.get('minio_secure', False),
                help="Enable for secure connections (usually False for local testing)"
            )
        
        with col2:
            secret_key = st.text_input(
                "Secret Key",
                value=st.session_state.get('minio_secret_key', 'minioadmin'),
                type="password",
                help="MinIO secret key (default: minioadmin)"
            )
            
            region = st.text_input(
                "Region",
                value=st.session_state.get('minio_region', 'us-east-1'),
                help="MinIO region (usually us-east-1)"
            )
        
        # Form buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            save_and_test = st.form_submit_button("💾 Save & Test", type="primary")
        
        with col2:
            test_only = st.form_submit_button("🔍 Test Connection")
        
        with col3:
            clear_config = st.form_submit_button("🧹 Clear Config")
        
        # Handle form actions
        if clear_config:
            # Clear session state
            keys_to_clear = ['minio_endpoint', 'minio_access_key', 'minio_secret_key', 
                           'minio_secure', 'minio_region', 'minio_client']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Configuration cleared!")
            st.rerun()
        
        if save_and_test or test_only:
            if not access_key or not secret_key:
                st.error("❌ Access key and secret key are required")
            else:
                # Save configuration if requested
                if save_and_test:
                    st.session_state['minio_endpoint'] = endpoint
                    st.session_state['minio_access_key'] = access_key
                    st.session_state['minio_secret_key'] = secret_key
                    st.session_state['minio_secure'] = secure
                    st.session_state['minio_region'] = region
                
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
                            
                            # Store client in session state
                            st.session_state['minio_client'] = client
                            
                            # Show bucket information
                            try:
                                buckets = client.list_buckets()
                                if buckets:
                                    st.info(f"Found {len(buckets)} bucket(s)")
                                    
                                    with st.expander("📦 Available Buckets"):
                                        for bucket in buckets:
                                            st.write(f"• **{bucket['name']}** - Created: {bucket['creation_date_str']}")
                                else:
                                    st.warning("No buckets found. Create buckets using MinIO web console.")
                            
                            except Exception as e:
                                st.warning(f"Connected successfully, but couldn't list buckets: {e}")
                        else:
                            st.error("❌ Connection test failed")
                    
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                        
                        # Show troubleshooting tips
                        with st.expander("🔧 Troubleshooting Tips"):
                            st.markdown("""
                            **Common issues:**
                            
                            1. **MinIO server not running**
                               - Start MinIO server first
                               - Check if accessible at http://localhost:9001
                            
                            2. **Wrong endpoint format**
                               - Use `localhost:9000` (not `http://localhost:9000`)
                               - Remove protocol prefix
                            
                            3. **Incorrect credentials**
                               - Default MinIO credentials: `minioadmin` / `minioadmin`
                               - Check your MinIO server configuration
                            
                            4. **Network/firewall issues**
                               - Check if port 9000 is accessible
                               - Verify firewall settings
                            """)
    
    # Connection Status
    st.divider()
    st.header("📊 Connection Status")
    
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
    
    # Setup guide
    with st.expander("📖 MinIO Setup Guide"):
        st.markdown("""
        ### Local MinIO Setup (for testing):
        
        **Option 1: Download MinIO Binary**
        1. Download from: https://min.io/download
        2. Run MinIO server:
           ```bash
           # Windows
           minio.exe server C:\\data --console-address ":9001"
           
           # Linux/Mac
           ./minio server /data --console-address ":9001"
           ```
        3. Access web console: http://localhost:9001
        4. Default credentials: `minioadmin` / `minioadmin`
        
        **Option 2: Docker (easier)**
        ```bash
        docker run -p 9000:9000 -p 9001:9001 \\
          minio/minio server /data --console-address ":9001"
        ```
        
        **After starting MinIO:**
        1. Open web console: http://localhost:9001
        2. Login with: `minioadmin` / `minioadmin`
        3. Create a bucket (e.g., "documents")
        4. Upload some PDF files
        5. Return here to configure connection
        """)


def render_minio_processor():
    """MinIO PDF Processor Interface"""
    st.title("🗄️ MinIO PDF Processor")
    st.write("Process PDF documents from MinIO buckets.")
    
    if not MINIO_AVAILABLE:
        st.error("❌ MinIO library not available - please install it first")
        st.info("Go to the 'Configuration' tab for installation instructions")
        return
    
    # Check MinIO connection
    client = st.session_state.get('minio_client')
    
    if not client:
        st.warning("⚠️ MinIO not connected")
        st.info("Please configure MinIO connection in the 'Configuration' tab first.")
        return
    
    # Test connection
    try:
        if not client.test_connection():
            st.error("❌ MinIO connection lost")
            st.info("Please reconfigure connection in the 'Configuration' tab.")
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
            st.info("Create buckets and upload PDFs using MinIO web console at http://localhost:9001")
            return
        
        # Bucket selection
        st.header("📦 Select Bucket")
        bucket_names = [bucket['name'] for bucket in buckets]
        selected_bucket = st.selectbox("Choose bucket to process:", bucket_names)
        
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
                st.info("Upload PDF files to this bucket using MinIO web console.")
                return
            
            # Display found PDFs
            st.success(f"✅ Found **{len(pdf_objects)}** PDF files")
            
            # PDF file preview
            with st.expander(f"📄 PDF Files Preview ({len(pdf_objects)} files)"):
                # Show table of PDFs
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
            st.header("⚙️ Processing Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_files = st.number_input(
                    "Max files to process",
                    min_value=1,
                    max_value=len(pdf_objects),
                    value=min(5, len(pdf_objects)),
                    help="Limit processing for testing (start small)"
                )
                
                batch_size = st.slider(
                    "Processing batch size",
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
                estimated_time = total_mb * 2  # ~2 seconds per MB
                st.metric("Estimated time", f"{estimated_time:.0f} seconds")
            
            # Action buttons
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    process_pdfs_simple(client, selected_bucket, files_to_process)
            
            with col2:
                if st.button("📊 Analyze Bucket", use_container_width=True):
                    analyze_bucket_simple(client, selected_bucket, pdf_objects)
            
            with col3:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading bucket information: {e}")


def process_pdfs_simple(client, bucket_name, pdf_objects):
    """Simple PDF processing function"""
    st.header("🔄 Processing PDFs...")
    
    # Check if we have the required processors
    try:
        from src.core.pdf_processor import PDFProcessor
        from src.core.vector_store import VectorStore
        
        pdf_processor = PDFProcessor()
        vector_store = VectorStore()
        
    except ImportError as e:
        st.error(f"❌ Required components not available: {e}")
        st.info("Make sure your Zenith application is properly configured.")
        return
    except Exception as e:
        st.error(f"❌ Error initializing processors: {e}")
        return
    
    # Processing progress tracking
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
                        'last_modified': pdf_obj.get('last_modified_str', '')
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
            st.info("💬 You can now use these documents in your main Zenith chat application!")
    
    except Exception as e:
        st.error(f"❌ Processing error: {e}")
    
    finally:
        # Cleanup temp directory
        try:
            for temp_file in temp_dir.glob("*.pdf"):
                temp_file.unlink()
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
        except Exception:
            pass


def analyze_bucket_simple(client, bucket_name, pdf_objects):
    """Simple bucket analysis"""
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
    st.subheader("📅 Recently Modified Files (Top 10)")
    
    sorted_files = sorted(pdf_objects, key=lambda x: x.get('last_modified', ''), reverse=True)
    
    for i, obj in enumerate(sorted_files[:10]):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📄 {obj['name']}")
        with col2:
            st.write(obj['size_str'])
        with col3:
            st.write(obj.get('last_modified_str', 'Unknown')[:10])


def main():
    """Main application"""
    st.title("🗄️ MinIO PDF Processor for Zenith")
    st.write("Process PDF documents from MinIO buckets into your Zenith knowledge base.")
    
    # Create tabs
    tab1, tab2 = st.tabs(["⚙️ Configuration", "🚀 PDF Processor"])
    
    with tab1:
        render_minio_config()
    
    with tab2:
        render_minio_processor()
    
    # Footer
    st.divider()
    st.markdown("**Need help?** Check the Configuration tab for setup instructions.")


if __name__ == "__main__":
    main()
