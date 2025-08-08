                st.success("✅ MinIO connected and ready")
                info = client.get_connection_info()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Endpoint", info['endpoint'])
                with col2:
                    st.metric("Status", "Connected")
            else:
                st.error("❌ Connection lost")
        except:
            st.error("❌ Connection error")
    else:
        st.info("⚠️ Not connected - configure above")
    
    # Quick setup guide
    with st.expander("📖 Quick Setup Guide"):
        st.markdown("""
        ### Local MinIO Setup (for testing):
        
        1. **Download MinIO server** (if you don't have it):
           - Windows: Download from https://min.io/download
           - Or use Docker: `docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"`
        
        2. **Start MinIO server**:
           - Run the MinIO executable
           - Default credentials: `minioadmin` / `minioadmin`
           - Web console: http://localhost:9001
        
        3. **Create buckets and upload PDFs**:
           - Access web console at http://localhost:9001
           - Create a bucket (e.g., "documents")
           - Upload some PDF files
        
        4. **Configure connection above**:
           - Endpoint: `localhost:9000`
           - Access Key: `minioadmin`
           - Secret Key: `minioadmin`
        """)


def render_minio_processor_page():
    """MinIO PDF Processor Page - PATCH VERSION"""
    st.title("🗄️ MinIO PDF Processor")
    st.write("Process PDF documents from MinIO buckets into your knowledge base.")
    
    # Check MinIO connection
    client = st.session_state.get('minio_client')
    
    if not client:
        st.warning("⚠️ MinIO not connected")
        st.info("Please configure MinIO connection first.")
        if st.button("⚙️ Go to MinIO Configuration"):
            # You may need to adjust this based on your navigation
            st.info("Navigate to 'MinIO Config' page to set up connection.")
        return
    
    # Test connection
    try:
        if not client.test_connection():
            st.error("❌ MinIO connection lost")
            if st.button("🔧 Reconfigure"):
                st.info("Navigate to 'MinIO Config' page to fix connection.")
            return
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        return
    
    st.success("✅ MinIO connected")
    
    # Load buckets
    try:
        with st.spinner("Loading buckets..."):
            buckets = client.list_buckets()
        
        if not buckets:
            st.warning("❌ No buckets found")
            st.info("Create buckets and upload PDFs using the MinIO web console.")
            return
        
        # Bucket selection
        st.header("📦 Select Bucket")
        bucket_names = [bucket['name'] for bucket in buckets]
        selected_bucket = st.selectbox("Choose bucket:", bucket_names)
        
        if selected_bucket:
            # Load PDFs from bucket
            with st.spinner(f"Scanning {selected_bucket} for PDFs..."):
                pdf_objects = client.list_pdf_objects(selected_bucket)
            
            if not pdf_objects:
                st.warning(f"❌ No PDF files found in bucket '{selected_bucket}'")
                st.info("Upload PDF files to this bucket using the MinIO web console.")
                return
            
            # Show PDF files
            st.success(f"✅ Found {len(pdf_objects)} PDF files")
            
            # File preview
            with st.expander(f"📄 PDF Files ({len(pdf_objects)})"):
                for pdf in pdf_objects[:15]:  # Show first 15
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📄 {pdf['name']}")
                    with col2:
                        st.write(pdf['size_str'])
                    with col3:
                        st.write(pdf['last_modified_str'][:10])
                
                if len(pdf_objects) > 15:
                    st.write(f"... and {len(pdf_objects) - 15} more files")
            
            # Processing settings
            st.header("⚙️ Processing Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_files = st.number_input(
                    "Max files to process",
                    min_value=1,
                    max_value=len(pdf_objects),
                    value=min(5, len(pdf_objects)),
                    help="Limit processing for testing"
                )
                
                batch_size = st.slider(
                    "Batch size",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Files to process simultaneously"
                )
            
            with col2:
                # Show estimates
                files_to_process = pdf_objects[:max_files]
                total_size = sum(f.get('size', 0) for f in files_to_process)
                total_mb = total_size / (1024 * 1024)
                
                st.metric("Files to process", max_files)
                st.metric("Total size", f"{total_mb:.1f} MB")
                
                # Time estimate (rough)
                est_time = total_mb * 3  # ~3 seconds per MB
                st.metric("Est. time", f"{est_time:.0f}s")
            
            # Process button
            st.divider()
            
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                process_minio_pdfs(client, selected_bucket, files_to_process)
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def process_minio_pdfs(client, bucket_name, pdf_objects):
    """Process PDFs from MinIO - PATCH VERSION"""
    st.header("🔄 Processing PDFs...")
    
    # Initialize processing components
    try:
        pdf_processor = st.session_state.pdf_processor
        vector_store = st.session_state.vector_store
    except:
        st.error("❌ Processing components not initialized")
        return
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = st.container()
    
    processed_count = 0
    failed_count = 0
    total_chunks = 0
    
    # Create temp directory
    temp_dir = Path("temp_minio_pdfs")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        for i, pdf_obj in enumerate(pdf_objects):
            object_name = pdf_obj['name']
            
            status_text.text(f"📥 Processing {i+1}/{len(pdf_objects)}: {object_name}")
            
            try:
                # Download PDF
                local_path = client.download_object(bucket_name, object_name)
                
                # Process PDF
                documents = pdf_processor.load_pdf(local_path)
                
                # Add MinIO source metadata
                for doc in documents:
                    doc.metadata.update({
                        'source': f"minio://{bucket_name}/{object_name}",
                        'minio_bucket': bucket_name,
                        'minio_object': object_name,
                        'file_size': pdf_obj.get('size', 0)
                    })
                
                # Create chunks and add to vector store
                chunks = pdf_processor.split_documents(documents)
                if chunks:
                    vector_store.add_documents(chunks)
                    total_chunks += len(chunks)
                
                # Success
                with results:
                    st.success(f"✅ {object_name}: {len(documents)} pages → {len(chunks)} chunks")
                
                processed_count += 1
                
                # Update processing state
                st.session_state.documents_processed = True
                st.session_state.processed_files.append(object_name)
                
                # Cleanup temp file
                if local_path and local_path.exists():
                    local_path.unlink()
            
            except Exception as e:
                with results:
                    st.error(f"❌ {object_name}: {str(e)}")
                failed_count += 1
            
            # Update progress
            progress_bar.progress((i + 1) / len(pdf_objects))
        
        # Final results
        status_text.text("🎉 Processing complete!")
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Successful", processed_count)
        with col2:
            st.metric("❌ Failed", failed_count)
        with col3:
            st.metric("📄 Total chunks", total_chunks)
        
        if processed_count > 0:
            st.balloons()
            st.success(f"🎉 Successfully processed {processed_count} PDFs! Added {total_chunks} chunks to knowledge base.")
            
            st.info("💬 You can now chat with these documents using the Chat tab!")
            
            # Update session state for the main app
            if 'file_stats' not in st.session_state:
                st.session_state.file_stats = {}
            
            st.session_state.file_stats['minio_processed'] = {
                'count': processed_count,
                'chunks': total_chunks,
                'source': f'MinIO bucket: {bucket_name}'
            }
    
    except Exception as e:
        st.error(f"❌ Processing error: {e}")
    
    finally:
        # Cleanup
        try:
            for temp_file in temp_dir.glob("*.pdf"):
                temp_file.unlink()
            temp_dir.rmdir()
        except:
            pass


# ==================== INTEGRATION WITH EXISTING APP ====================
# 
# INSTRUCTIONS: Add this code to your existing navigation/page handling section
#
# 1. Find your page selection code (probably near the end of your class or main function)
# 2. Add MinIO pages to your page options
# 3. Add the page handlers
#
# Example integration:

def integrate_minio_with_existing_app():
    """
    INTEGRATION EXAMPLE - Modify your existing page navigation like this:
    
    # In your existing page navigation section, add:
    
    # Add MinIO pages if available
    if MINIO_AVAILABLE:
        # Add to your existing tab or page structure
        tab_minio_config, tab_minio_processor = st.tabs(["MinIO Config", "MinIO Processor"])
        
        with tab_minio_config:
            render_minio_config_page()
        
        with tab_minio_processor:
            render_minio_processor_page()
    
    # OR if using selectbox navigation:
    
    page_options = ["Home", "Upload", "Chat"]  # your existing pages
    
    if MINIO_AVAILABLE:
        page_options.extend(["MinIO Config", "MinIO Processor"])
    
    selected_page = st.selectbox("Select Page", page_options)
    
    if selected_page == "MinIO Config":
        render_minio_config_page()
    elif selected_page == "MinIO Processor":
        render_minio_processor_page()
    # ... your existing page handlers ...
    """
    pass


# ==================== SIMPLE STANDALONE VERSION ====================
# If you want to test MinIO functionality separately, uncomment this:

def main_minio_standalone():
    """Standalone MinIO interface for testing"""
    st.set_page_config(page_title="MinIO PDF Processor", page_icon="🗄️", layout="wide")
    
    st.title("🗄️ MinIO PDF Processor")
    st.write("Standalone MinIO interface for testing")
    
    # Simple tab navigation
    tab1, tab2 = st.tabs(["⚙️ Configuration", "🚀 Processor"])
    
    with tab1:
        render_minio_config_page()
    
    with tab2:
        render_minio_processor_page()


# ==================== END OF PATCH ====================

# To use the standalone version, run this file directly:
if __name__ == "__main__":
    # Uncomment this line to run standalone MinIO interface:
    # main_minio_standalone()
    
    # Keep your existing main execution here
    pass
