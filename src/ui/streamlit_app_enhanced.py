"""
Enhanced Streamlit App with MinIO Integration
Extended main Streamlit application with MinIO PDF processing capabilities
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import new MinIO components
from .pages.minio_processor import render_minio_processor_page
from .components.minio_config import render_minio_config_page
from .components.bucket_browser import render_bucket_browser_page  
from .components.batch_processor_ui import render_batch_processor_page

# Import existing components (preserve existing functionality)
from src.core.config import config
from src.core.pdf_processor import PDFProcessor
from src.core.vector_store import VectorStore
from src.core.chat_engine import ChatEngine
from src.utils.helpers import format_file_size, format_duration
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Zenith PDF Chatbot - Enhanced",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function with enhanced MinIO capabilities"""
    
    # Enhanced sidebar with MinIO options
    with st.sidebar:
        st.title("📚 Zenith PDF Chatbot")
        st.write("Enhanced with MinIO Integration")
        
        # Navigation
        st.header("🧭 Navigation")
        
        # Create page options including new MinIO pages
        page_options = {
            "🏠 Home": "home",
            "💬 Chat": "chat", 
            "📄 Document Upload": "upload",
            "🗄️ MinIO Processor": "minio_processor",
            "⚙️ MinIO Config": "minio_config",
            "📦 Browse Buckets": "bucket_browser",
            "🚀 Batch Processor": "batch_processor",
            "📊 System Status": "status"
        }
        
        selected_page = st.selectbox(
            "Select Page",
            options=list(page_options.keys()),
            key="page_selector"
        )
        
        page_key = page_options[selected_page]
        
        st.divider()
        
        # Quick MinIO status in sidebar
        render_minio_sidebar_status()
        
        st.divider()
        
        # System info
        render_system_info_sidebar()
    
    # Main content area
    if page_key == "home":
        render_home_page()
    elif page_key == "chat":
        render_chat_page()
    elif page_key == "upload":
        render_upload_page()
    elif page_key == "minio_processor":
        render_minio_processor_page()
    elif page_key == "minio_config":
        render_minio_config_page()
    elif page_key == "bucket_browser":
        render_bucket_browser_page()
    elif page_key == "batch_processor":
        render_batch_processor_page()
    elif page_key == "status":
        render_status_page()


def render_minio_sidebar_status():
    """Render MinIO status in sidebar"""
    st.subheader("🗄️ MinIO Status")
    
    client = st.session_state.get('minio_client')
    
    if not client:
        st.error("❌ Not Connected")
        if st.button("⚙️ Configure", key="sidebar_config"):
            st.session_state['page_selector'] = "⚙️ MinIO Config"
            st.rerun()
    else:
        try:
            if client.test_connection():
                st.success("✅ Connected")
                
                # Show quick stats
                try:
                    buckets = client.list_buckets()
                    st.metric("Buckets", len(buckets))
                    
                    # Count PDFs across all buckets (cached)
                    if 'total_pdfs' not in st.session_state:
                        total_pdfs = 0
                        for bucket in buckets[:3]:  # Check first 3 buckets only for performance
                            try:
                                stats = client.get_bucket_stats(bucket['name'])
                                total_pdfs += stats.get('pdf_objects', 0)
                            except:
                                pass
                        st.session_state['total_pdfs'] = total_pdfs
                    
                    st.metric("PDFs", st.session_state.get('total_pdfs', '?'))
                    
                except Exception as e:
                    st.warning("⚠️ Stats unavailable")
                
                if st.button("🔄 Refresh", key="sidebar_refresh"):
                    if 'total_pdfs' in st.session_state:
                        del st.session_state['total_pdfs']
                    st.rerun()
            else:
                st.error("❌ Connection Failed")
        except:
            st.error("❌ Error")


def render_system_info_sidebar():
    """Render system information in sidebar"""
    st.subheader("🔧 System Info")
    
    # Vector store status
    try:
        vector_store = VectorStore()
        if vector_store.health_check():
            st.success("✅ Vector Store")
        else:
            st.error("❌ Vector Store")
    except:
        st.error("❌ Vector Store")
    
    # Processing status
    processor = st.session_state.get('batch_processor')
    if processor:
        stats = processor.get_processing_stats()
        if stats['is_currently_processing']:
            st.info("🔄 Processing Active")
        else:
            st.success("✅ Ready")
    else:
        st.info("💤 Processor Idle")


def render_home_page():
    """Enhanced home page with MinIO features"""
    st.title("📚 Zenith PDF Chatbot")
    st.subheader("🚀 Enhanced with MinIO Integration")
    
    st.write("""
    Welcome to Zenith PDF Chatbot with advanced MinIO integration! This enhanced version provides 
    powerful capabilities for processing and vectorizing PDF documents directly from MinIO buckets.
    """)
    
    # Feature highlights
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🆕 MinIO Features")
        st.markdown("""
        - **🗄️ MinIO Integration**: Connect to MinIO servers and browse buckets
        - **📦 Bucket Browser**: Visual interface to explore and select PDF files
        - **🚀 Batch Processing**: Process multiple PDFs simultaneously
        - **📊 Progress Tracking**: Real-time processing status and statistics  
        - **⚡ Async Processing**: Non-blocking operations for better performance
        - **🔧 Configuration Management**: Easy MinIO connection setup
        """)
    
    with col2:
        st.header("📋 Existing Features")
        st.markdown("""
        - **💬 Interactive Chat**: Chat with your documents using AI
        - **📄 Document Upload**: Upload PDFs directly through the interface  
        - **🔍 Vector Search**: Find relevant document sections quickly
        - **📊 Document Management**: Organize and track processed documents
        - **⚙️ Configurable Settings**: Customize processing parameters
        - **🔒 Secure Processing**: Safe handling of sensitive documents
        """)
    
    st.divider()
    
    # Quick start guide
    st.header("🚀 Quick Start Guide")
    
    tab1, tab2 = st.tabs(["🆕 MinIO Setup", "📄 Traditional Upload"])
    
    with tab1:
        st.markdown("""
        ### Getting Started with MinIO
        
        1. **Configure Connection**: Go to MinIO Config and enter your MinIO server details
        2. **Test Connection**: Verify your connection and view available buckets  
        3. **Browse Buckets**: Use the Bucket Browser to explore and select PDF files
        4. **Start Processing**: Use Batch Processor to process multiple PDFs at once
        5. **Chat with Documents**: Once processed, chat with your documents in the Chat page
        
        #### Benefits of MinIO Integration:
        - Process large collections of PDFs without manual uploads
        - Organize documents in buckets for better management  
        - Batch processing saves time and resources
        - Automatic cleanup of temporary files
        """)
        
        if st.button("⚙️ Configure MinIO Now", type="primary"):
            st.session_state['page_selector'] = "⚙️ MinIO Config"
            st.rerun()
    
    with tab2:
        st.markdown("""
        ### Traditional Document Upload
        
        1. **Upload PDFs**: Go to Document Upload and select your PDF files
        2. **Process Documents**: The system will extract text and create embeddings
        3. **Start Chatting**: Once processed, use the Chat page to ask questions
        4. **Manage Documents**: View and organize your processed documents
        
        #### When to Use Traditional Upload:
        - Processing individual or small numbers of PDFs
        - When you don't have a MinIO server setup
        - For quick testing and experimentation
        """)
        
        if st.button("📄 Upload Documents", type="primary"):
            st.session_state['page_selector'] = "📄 Document Upload" 
            st.rerun()
    
    st.divider()
    
    # System overview
    render_system_overview()


def render_system_overview():
    """Render system overview section"""
    st.header("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Document count
    try:
        vector_store = VectorStore()
        collection_info = vector_store.get_collection_info()
        doc_count = collection_info.get('vectors_count', 0) if collection_info else 0
    except:
        doc_count = '?'
    
    with col1:
        st.metric("Documents in Vector Store", doc_count)
    
    # MinIO buckets
    client = st.session_state.get('minio_client')
    bucket_count = '?'
    if client:
        try:
            buckets = client.list_buckets()
            bucket_count = len(buckets)
        except:
            pass
    
    with col2:
        st.metric("MinIO Buckets", bucket_count)
    
    # Processing jobs
    processor = st.session_state.get('batch_processor')
    job_count = '?'
    if processor:
        try:
            stats = processor.get_processing_stats()
            job_count = stats['total_jobs']
        except:
            pass
    
    with col3:
        st.metric("Processing Jobs", job_count)
    
    # Connection status
    with col4:
        if client and client.test_connection():
            st.metric("MinIO Status", "✅ Connected")
        else:
            st.metric("MinIO Status", "❌ Disconnected")


def render_chat_page():
    """Enhanced chat page (preserve existing functionality)"""
    # Import and render existing chat functionality
    # This preserves all existing chat features
    try:
        # Initialize components
        vector_store = VectorStore()
        chat_engine = ChatEngine(vector_store)
        
        st.title("💬 Chat with Documents")
        st.write("Ask questions about your processed documents")
        
        # Check if there are any documents
        collection_info = vector_store.get_collection_info()
        doc_count = collection_info.get('vectors_count', 0) if collection_info else 0
        
        if doc_count == 0:
            st.warning("No documents found in vector store. Please upload or process documents first.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Upload Documents"):
                    st.session_state['page_selector'] = "📄 Document Upload"
                    st.rerun()
            
            with col2:
                if st.button("🗄️ Process from MinIO"):
                    st.session_state['page_selector'] = "🗄️ MinIO Processor"
                    st.rerun()
            
            return
        
        # Chat interface
        st.success(f"Ready to chat! {doc_count} document chunks available.")
        
        # Chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your documents..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_engine.chat(prompt)
                    st.markdown(response)
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    except Exception as e:
        st.error(f"Error in chat interface: {str(e)}")
        logger.error(f"Chat page error: {e}")


def render_upload_page():
    """Enhanced upload page (preserve existing functionality)"""
    st.title("📄 Document Upload")
    st.write("Upload PDF documents for processing and chat")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type="pdf",
        accept_multiple_files=True,
        help="Upload PDF files to process and add to the vector store"
    )
    
    if uploaded_files:
        st.success(f"Selected {len(uploaded_files)} files")
        
        # Show file details
        for file in uploaded_files:
            st.write(f"📄 {file.name} ({format_file_size(file.size)})")
        
        if st.button("🚀 Process Files", type="primary"):
            try:
                # Initialize components
                pdf_processor = PDFProcessor()
                vector_store = VectorStore()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process files
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"Processing {file.name}...")
                    
                    # Process the uploaded file
                    documents = pdf_processor.process_uploaded_files([file])
                    chunks = pdf_processor.split_documents(documents)
                    
                    if chunks:
                        vector_store.add_documents(chunks)
                        st.success(f"✅ Processed {file.name}: {len(chunks)} chunks added")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("Processing complete!")
                st.balloons()
                
                # Offer to go to chat
                if st.button("💬 Start Chatting"):
                    st.session_state['page_selector'] = "💬 Chat"
                    st.rerun()
            
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")
                logger.error(f"Upload processing error: {e}")


def render_status_page():
    """Enhanced status page with MinIO information"""
    st.title("📊 System Status")
    st.write("Comprehensive system status and diagnostics")
    
    # System health checks
    st.header("🔍 Health Checks")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Vector Store")
        try:
            vector_store = VectorStore()
            if vector_store.health_check():
                st.success("✅ Healthy")
                
                # Show collection info
                info = vector_store.get_collection_info()
                if info:
                    st.write(f"Documents: {info.get('vectors_count', 0)}")
                    st.write(f"Status: {info.get('status', 'Unknown')}")
            else:
                st.error("❌ Unhealthy")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("MinIO Connection")
        client = st.session_state.get('minio_client')
        
        if not client:
            st.warning("⚠️ Not configured")
        else:
            try:
                if client.test_connection():
                    st.success("✅ Connected")
                    
                    # Show connection info
                    info = client.get_connection_info()
                    st.write(f"Endpoint: {info['endpoint']}")
                    st.write(f"Secure: {info['secure']}")
                else:
                    st.error("❌ Connection failed")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col3:
        st.subheader("Chat Engine")
        try:
            vector_store = VectorStore()
            chat_engine = ChatEngine(vector_store)
            if chat_engine.health_check():
                st.success("✅ Healthy")
            else:
                st.error("❌ Unhealthy")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    # Processing statistics
    st.header("📈 Processing Statistics")
    
    processor = st.session_state.get('batch_processor')
    if processor:
        stats = processor.get_processing_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", stats['total_jobs'])
        
        with col2:
            st.metric("Completed Jobs", stats['completed_jobs'])
        
        with col3:
            st.metric("Objects Processed", stats['total_objects_processed'])
        
        with col4:
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
        
        # Current processing status
        if stats['is_currently_processing']:
            st.info(f"🔄 Currently processing job: {stats['current_job_id']}")
        else:
            st.success("✅ No active processing jobs")
    
    else:
        st.info("No batch processor initialized")
    
    st.divider()
    
    # Configuration display
    st.header("⚙️ Configuration")
    
    with st.expander("View Current Configuration"):
        config_dict = {
            "OpenAI Model": config.openai_model,
            "Embedding Model": config.openai_embedding_model,
            "Chunk Size": config.chunk_size,
            "Chunk Overlap": config.chunk_overlap,
            "Qdrant URL": f"{config.qdrant_url}:{config.qdrant_port}",
            "Collection": config.qdrant_collection_name,
            "Debug Mode": config.debug_mode,
            "Log Level": config.log_level
        }
        
        st.json(config_dict)


if __name__ == "__main__":
    main()
