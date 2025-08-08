"""
Simple MinIO Integration for Existing Streamlit App
Add this to your existing streamlit_app.py
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def render_minio_config_simple():
    """Simple MinIO configuration page"""
    st.title("⚙️ MinIO Configuration")
    st.write("Configure your MinIO server connection.")
    
    # Check if MinIO is available
    try:
        from src.core.minio_client import MinIOClient
    except ImportError as e:
        st.error("❌ MinIO integration not available.")
        st.error(f"Error: {e}")
        st.info("To enable MinIO integration, install the required dependencies:")
        st.code("pip install minio>=7.2.0")
        
        with st.expander("Installation Instructions"):
            st.markdown("""
            ### Install MinIO Dependencies
            
            Run this command in your terminal:
            ```bash
            pip install minio>=7.2.0
            ```
            
            Then restart your Streamlit application.
            """)
        return
    
    # Configuration form
    with st.form("minio_config"):
        st.subheader("MinIO Server Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            endpoint = st.text_input(
                "Endpoint",
                value="localhost:9000",
                help="MinIO server endpoint (host:port)"
            )
            
            access_key = st.text_input(
                "Access Key",
                help="MinIO access key"
            )
            
            secure = st.checkbox(
                "Use HTTPS",
                value=False,
                help="Enable for secure connections"
            )
        
        with col2:
            secret_key = st.text_input(
                "Secret Key",
                type="password",
                help="MinIO secret key"
            )
            
            region = st.text_input(
                "Region",
                value="us-east-1",
                help="MinIO region"
            )
        
        submitted = st.form_submit_button("💾 Save & Test Connection", type="primary")
        
        if submitted:
            if not access_key or not secret_key:
                st.error("❌ Access key and secret key are required")
            else:
                # Test connection
                with st.spinner("Testing connection..."):
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
                            
                            # Save to session state
                            st.session_state['minio_client'] = client
                            st.session_state['minio_connected'] = True
                            
                            # Show bucket info
                            try:
                                buckets = client.list_buckets()
                                st.info(f"Found {len(buckets)} buckets")
                                
                                if buckets:
                                    st.write("**Available Buckets:**")
                                    for bucket in buckets:
                                        st.write(f"📦 {bucket['name']} (created: {bucket['creation_date_str']})")
                            
                            except Exception as e:
                                st.warning(f"Connected, but couldn't list buckets: {e}")
                        else:
                            st.error("❌ Connection failed")
                    
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")


def render_minio_processor_simple():
    """Simple MinIO PDF processor"""
    st.title("🗄️ MinIO PDF Processor")
    st.write("Process PDF files from MinIO buckets.")
    
    # Check MinIO connection
    client = st.session_state.get('minio_client')
    
    if not client:
        st.warning("⚠️ MinIO not connected. Please configure MinIO connection first.")
        if st.button("⚙️ Go to MinIO Configuration"):
            st.switch_page("MinIO Config")
        return
    
    # Test connection
    if not client.test_connection():
        st.error("❌ MinIO connection lost. Please reconfigure.")
        if st.button("⚙️ Reconfigure MinIO"):
            st.switch_page("MinIO Config")
        return
    
    st.success("✅ MinIO connected")
    
    # Bucket selection
    try:
        buckets = client.list_buckets()
        
        if not buckets:
            st.warning("No buckets found")
            return
        
        bucket_names = [bucket['name'] for bucket in buckets]
        selected_bucket = st.selectbox("Select Bucket", bucket_names)
        
        if selected_bucket:
            st.subheader(f"📦 Processing PDFs from bucket: {selected_bucket}")
            
            # Get PDF objects
            with st.spinner("Loading PDF files..."):
                pdf_objects = client.list_pdf_objects(selected_bucket)
            
            if not pdf_objects:
                st.info("No PDF files found in this bucket")
                return
            
            st.success(f"Found {len(pdf_objects)} PDF files")
            
            # Show PDF list
            with st.expander(f"PDF Files ({len(pdf_objects)})"):
                for pdf in pdf_objects[:10]:  # Show first 10
                    st.write(f"📄 {pdf['name']} ({pdf['size_str']})")
                
                if len(pdf_objects) > 10:
                    st.write(f"... and {len(pdf_objects) - 10} more files")
            
            # Simple processing
            if st.button("🚀 Process All PDFs", type="primary"):
                process_pdfs_simple(client, selected_bucket, pdf_objects)
    
    except Exception as e:
        st.error(f"Error loading buckets: {e}")


def process_pdfs_simple(client, bucket_name, pdf_objects):
    """Simple PDF processing function"""
    from src.core.pdf_processor import PDFProcessor
    from src.core.vector_store import VectorStore
    
    # Initialize components
    pdf_processor = PDFProcessor()
    vector_store = VectorStore()
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    processed_count = 0
    failed_count = 0
    temp_dir = Path("temp_pdfs")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        for i, pdf_obj in enumerate(pdf_objects):
            object_name = pdf_obj['name']
            status_text.text(f"Processing {object_name}...")
            
            try:
                # Download PDF
                local_path = client.download_object(bucket_name, object_name)
                
                # Process PDF
                documents = pdf_processor.load_pdf(local_path)
                
                # Add MinIO metadata
                for doc in documents:
                    doc.metadata.update({
                        'minio_bucket': bucket_name,
                        'minio_object': object_name,
                        'source': f"minio://{bucket_name}/{object_name}"
                    })
                
                # Split and add to vector store
                chunks = pdf_processor.split_documents(documents)
                if chunks:
                    vector_store.add_documents(chunks)
                
                with results_container:
                    st.success(f"✅ {object_name}: {len(chunks)} chunks added")
                
                processed_count += 1
                
                # Cleanup
                if local_path.exists():
                    local_path.unlink()
            
            except Exception as e:
                with results_container:
                    st.error(f"❌ Failed to process {object_name}: {e}")
                failed_count += 1
            
            # Update progress
            progress_bar.progress((i + 1) / len(pdf_objects))
        
        # Final status
        status_text.text("Processing complete!")
        
        st.balloons()
        st.success(f"🎉 Processing complete! {processed_count} PDFs processed successfully, {failed_count} failed.")
        
        if st.button("💬 Start Chatting with Documents"):
            st.switch_page("Chat")
    
    except Exception as e:
        st.error(f"Processing error: {e}")
    
    finally:
        # Cleanup temp directory
        try:
            for file in temp_dir.glob("*.pdf"):
                file.unlink()
        except:
            pass


# Add these functions to your existing streamlit_app.py navigation
def add_minio_pages_to_existing_app():
    """
    Add this code to your existing streamlit_app.py file
    
    In your page navigation section, add:
    """
    
    # Example integration with existing app structure
    page_options = {
        # ... your existing pages ...
        "⚙️ MinIO Config": render_minio_config_simple,
        "🗄️ MinIO Processor": render_minio_processor_simple,
        # ... rest of your pages ...
    }
    
    # In your main function, add the page handlers:
    selected_page = st.selectbox("Select Page", list(page_options.keys()))
    
    if selected_page in page_options:
        page_options[selected_page]()


if __name__ == "__main__":
    # Test the MinIO config page
    render_minio_config_simple()
    client = st.session_state.get('minio_client')
    
    if client:
        try:
            if client.test_connection():
                st.success("✅ MinIO is connected and ready!")
                
                # Show quick stats
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
    """MinIO PDF Processor Page - Add this to your existing app"""
    st.title("🗄️ MinIO PDF Processor")
    st.write("Process PDF files directly from MinIO buckets.")
    
    # Check MinIO connection
    client = st.session_state.get('minio_client')
    
    if not client:
        st.warning("⚠️ MinIO not connected. Please configure MinIO connection first.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚙️ Configure MinIO", type="primary"):
                st.info("Navigate to 'MinIO Config' page to set up your connection.")
        
        with col2:
            if st.button("📖 View Setup Guide"):
                with st.expander("MinIO Setup Guide", expanded=True):
                    st.markdown("""
                    ### Quick Setup Steps:
                    
                    1. **Install MinIO**: Download and start MinIO server
                    2. **Get Credentials**: Note your access key and secret key
                    3. **Configure Connection**: Go to MinIO Config page
                    4. **Test Connection**: Verify your settings work
                    5. **Process PDFs**: Return here to process documents
                    
                    ### Example MinIO Setup (Local):
                    ```bash
                    # Download MinIO
                    wget https://dl.min.io/server/minio/release/linux-amd64/minio
                    chmod +x minio
                    
                    # Start MinIO server
                    ./minio server /data --console-address ":9001"
                    ```
                    
                    Default credentials: `minioadmin` / `minioadmin`
                    """)
        return
    
    # Test connection
    try:
        if not client.test_connection():
            st.error("❌ MinIO connection lost. Please reconfigure.")
            if st.button("⚙️ Reconfigure MinIO"):
                st.info("Navigate to 'MinIO Config' page to fix your connection.")
            return
    except Exception as e:
        st.error(f"❌ MinIO connection error: {e}")
        return
    
    st.success("✅ MinIO connected successfully!")
    
    # Main processing interface
    st.header("📦 Select Bucket and Process PDFs")
    
    try:
        # Get buckets
        with st.spinner("Loading buckets..."):
            buckets = client.list_buckets()
        
        if not buckets:
            st.warning("No buckets found in your MinIO server.")
            st.info("Create some buckets and upload PDF files to get started.")
            return
        
        # Bucket selection
        bucket_names = [bucket['name'] for bucket in buckets]
        selected_bucket = st.selectbox(
            "Choose a bucket to process:",
            bucket_names,
            key="bucket_selector"
        )
        
        if selected_bucket:
            # Show bucket info
            bucket_info = next((b for b in buckets if b['name'] == selected_bucket), None)
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📦 **Bucket:** {selected_bucket}")
            with col2:
                if bucket_info:
                    st.info(f"📅 **Created:** {bucket_info['creation_date_str']}")
            
            # Get PDF files
            with st.spinner(f"Scanning bucket '{selected_bucket}' for PDF files..."):
                pdf_objects = client.list_pdf_objects(selected_bucket)
            
            if not pdf_objects:
                st.warning(f"No PDF files found in bucket '{selected_bucket}'")
                st.info("Upload some PDF files to this bucket and try again.")
                return
            
            # Show PDF files found
            st.success(f"Found **{len(pdf_objects)}** PDF files in bucket '{selected_bucket}'")
            
            # File preview
            with st.expander(f"📄 PDF Files Preview ({len(pdf_objects)} files)"):
                # Show first 20 files
                display_count = min(20, len(pdf_objects))
                
                for i, pdf in enumerate(pdf_objects[:display_count]):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📄 {pdf['name']}")
                    with col2:
                        st.write(pdf['size_str'])
                    with col3:
                        st.write(pdf['last_modified_str'][:10])  # Date only
                
                if len(pdf_objects) > display_count:
                    st.write(f"... and {len(pdf_objects) - display_count} more files")
            
            # Processing options
            st.header("🚀 Processing Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Processing settings
                st.subheader("⚙️ Settings")
                
                batch_size = st.slider(
                    "Batch Size",
                    min_value=1,
                    max_value=20,
                    value=5,
                    help="Number of PDFs to process simultaneously"
                )
                
                max_files = st.number_input(
                    "Max Files to Process",
                    min_value=1,
                    max_value=len(pdf_objects),
                    value=min(10, len(pdf_objects)),
                    help="Limit processing to first N files (for testing)"
                )
            
            with col2:
                # Processing statistics
                st.subheader("📊 Estimates")
                
                total_size = sum(obj.get('size', 0) for obj in pdf_objects[:max_files])
                total_size_mb = total_size / (1024 * 1024)
                
                st.metric("Files to Process", max_files)
                st.metric("Total Size", f"{total_size_mb:.1f} MB")
                
                # Rough time estimate (2 seconds per MB)
                estimated_time = total_size_mb * 2
                st.metric("Est. Time", f"{estimated_time:.1f} seconds")
            
            # Process button
            st.divider()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    process_pdfs_from_minio(client, selected_bucket, pdf_objects[:max_files], batch_size)
            
            with col2:
                if st.button("📊 Analyze Bucket", use_container_width=True):
                    analyze_bucket_contents(client, selected_bucket, pdf_objects)
            
            with col3:
                if st.button("🔄 Refresh Bucket", use_container_width=True):
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error loading bucket information: {e}")


def process_pdfs_from_minio(client, bucket_name, pdf_objects, batch_size):
    """Process PDFs from MinIO bucket"""
    st.header("🔄 Processing PDFs...")
    
    # Initialize components
    try:
        from src.core.pdf_processor import PDFProcessor
        from src.core.vector_store import VectorStore
        
        pdf_processor = PDFProcessor()
        vector_store = VectorStore()
        
    except Exception as e:
        st.error(f"Error initializing processors: {e}")
        return
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_container = st.container()
    results_container = st.container()
    
    # Processing counters
    processed_count = 0
    failed_count = 0
    total_chunks = 0
    
    # Create temp directory
    temp_dir = Path("temp_pdfs")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Process files in batches
        for i in range(0, len(pdf_objects), batch_size):
            batch = pdf_objects[i:i + batch_size]
            
            with status_container:
                st.write(f"Processing batch {i//batch_size + 1} ({len(batch)} files)...")
            
            # Process each file in the batch
            for j, pdf_obj in enumerate(batch):
                object_name = pdf_obj['name']
                current_file = i + j + 1
                
                with status_container:
                    st.write(f"📄 Processing {current_file}/{len(pdf_objects)}: {object_name}")
                
                try:
                    # Download PDF
                    local_path = client.download_object(bucket_name, object_name)
                    
                    # Process PDF
                    documents = pdf_processor.load_pdf(local_path)
                    
                    # Add MinIO metadata
                    for doc in documents:
                        doc.metadata.update({
                            'minio_bucket': bucket_name,
                            'minio_object': object_name,
                            'source': f"minio://{bucket_name}/{object_name}",
                            'file_size': pdf_obj.get('size', 0),
                            'last_modified': pdf_obj.get('last_modified_str', '')
                        })
                    
                    # Split into chunks
                    chunks = pdf_processor.split_documents(documents)
                    
                    # Add to vector store
                    if chunks:
                        vector_store.add_documents(chunks)
                        total_chunks += len(chunks)
                    
                    with results_container:
                        st.success(f"✅ {object_name}: {len(documents)} pages → {len(chunks)} chunks")
                    
                    processed_count += 1
                    
                    # Cleanup temp file
                    if local_path.exists():
                        local_path.unlink()
                
                except Exception as e:
                    with results_container:
                        st.error(f"❌ Failed to process {object_name}: {str(e)}")
                    failed_count += 1
                
                # Update progress
                progress_bar.progress(current_file / len(pdf_objects))
        
        # Final results
        with status_container:
            st.write("🎉 Processing Complete!")
        
        # Success metrics
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
            st.success(f"🎉 Successfully processed {processed_count} PDFs and added {total_chunks} chunks to the knowledge base!")
            
            # Offer to go to chat
            if st.button("💬 Start Chatting with Your Documents", type="primary"):
                st.info("Navigate to the Chat tab to start asking questions about your processed documents!")
        
    except Exception as e:
        st.error(f"Processing error: {e}")
    
    finally:
        # Cleanup temp directory
        try:
            for temp_file in temp_dir.glob("*.pdf"):
                temp_file.unlink()
        except:
            pass


def analyze_bucket_contents(client, bucket_name, pdf_objects):
    """Analyze bucket contents and show statistics"""
    st.header(f"📊 Bucket Analysis: {bucket_name}")
    
    if not pdf_objects:
        st.info("No PDF files to analyze")
        return
    
    # Calculate statistics
    total_files = len(pdf_objects)
    total_size = sum(obj.get('size', 0) for obj in pdf_objects)
    total_size_mb = total_size / (1024 * 1024)
    
    # Size distribution
    size_ranges = {'Small (<1MB)': 0, 'Medium (1-10MB)': 0, 'Large (10-100MB)': 0, 'Very Large (>100MB)': 0}
    
    for obj in pdf_objects:
        size_mb = obj.get('size', 0) / (1024 * 1024)
        if size_mb < 1:
            size_ranges['Small (<1MB)'] += 1
        elif size_mb < 10:
            size_ranges['Medium (1-10MB)'] += 1
        elif size_mb < 100:
            size_ranges['Large (10-100MB)'] += 1
        else:
            size_ranges['Very Large (>100MB)'] += 1
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total PDFs", total_files)
    with col2:
        st.metric("Total Size", f"{total_size_mb:.1f} MB")
    with col3:
        avg_size = total_size_mb / total_files if total_files > 0 else 0
        st.metric("Avg Size", f"{avg_size:.1f} MB")
    with col4:
        largest = max(pdf_objects, key=lambda x: x.get('size', 0))
        largest_size = largest.get('size', 0) / (1024 * 1024)
        st.metric("Largest File", f"{largest_size:.1f} MB")
    
    # Size distribution chart
    st.subheader("📈 File Size Distribution")
    
    size_data = []
    for size_range, count in size_ranges.items():
        if count > 0:
            size_data.append({'Size Range': size_range, 'Count': count})
    
    if size_data:
        import pandas as pd
        df = pd.DataFrame(size_data)
        st.bar_chart(df.set_index('Size Range'))
    
    # Recent files
    st.subheader("📅 Recently Modified Files")
    
    # Sort by modification time
    sorted_files = sorted(pdf_objects, key=lambda x: x.get('last_modified', ''), reverse=True)
    
    for i, obj in enumerate(sorted_files[:10]):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📄 {obj['name']}")
        with col2:
            st.write(obj['size_str'])
        with col3:
            st.write(obj['last_modified_str'][:10] if obj.get('last_modified_str') else 'Unknown')


# Instructions for integration
def integration_instructions():
    """
    INTEGRATION INSTRUCTIONS:
    
    To add MinIO functionality to your existing streamlit_app.py:
    
    1. Add the import at the top:
       try:
           from src.core.minio_client import MinIOClient
           MINIO_AVAILABLE = True
       except ImportError:
           MINIO_AVAILABLE = False
    
    2. Add these functions to your existing app file:
       - render_minio_config()
       - render_minio_processor()
       - process_pdfs_from_minio()
       - analyze_bucket_contents()
    
    3. Add MinIO pages to your navigation (find your page selection logic):
       
       # Add to your existing page options
       if MINIO_AVAILABLE:
           page_options.update({
               "⚙️ MinIO Config": render_minio_config,
               "🗄️ MinIO Processor": render_minio_processor,
           })
    
    4. Add the page handlers in your main app logic:
       elif selected_page == "⚙️ MinIO Config":
           render_minio_config()
       elif selected_page == "🗄️ MinIO Processor":
           render_minio_processor()
    
    That's it! Your app will now have MinIO capabilities while preserving all existing functionality.
    """
    pass


if __name__ == "__main__":
    st.title("MinIO Integration Components")
    st.write("These are the MinIO integration components to add to your existing Streamlit app.")
    
    tab1, tab2 = st.tabs(["MinIO Config", "MinIO Processor"])
    
    with tab1:
        render_minio_config()
    
    with tab2:
        render_minio_processor()
