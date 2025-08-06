"""
Streamlit Web Interface for Zenith PDF Chatbot
Provides an interactive web UI for PDF processing and chatbot interaction
"""

import os
import sys
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import traceback

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.core.config import config, load_config
from src.core.pdf_processor import PDFProcessor
from src.core.vector_store import VectorStore
from src.core.chat_engine import ChatEngine
from src.utils.helpers import format_file_size, format_duration, ensure_directory_exists
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Zenith PDF Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.sub-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

.info-box {
    background-color: #f0f8ff;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 1rem 0;
}

.success-box {
    background-color: #f0fff0;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #32cd32;
    margin: 1rem 0;
}

.error-box {
    background-color: #fff0f0;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ff6b6b;
    margin: 1rem 0;
}

.source-document {
    background-color: #fafafa;
    padding: 0.5rem;
    margin: 0.25rem 0;
    border-radius: 0.25rem;
    border: 1px solid #ddd;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)


class ZenithStreamlitApp:
    """Main Streamlit application class"""
    
    def __init__(self):
        """Initialize the Streamlit app"""
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        # Core components
        if 'pdf_processor' not in st.session_state:
            st.session_state.pdf_processor = None
        if 'vector_store' not in st.session_state:
            st.session_state.vector_store = None
        if 'chat_engine' not in st.session_state:
            st.session_state.chat_engine = None
        
        # Processing state
        if 'documents_processed' not in st.session_state:
            st.session_state.documents_processed = False
        if 'processing_status' not in st.session_state:
            st.session_state.processing_status = ""
        
        # Chat state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'current_sources' not in st.session_state:
            st.session_state.current_sources = []
        
        # File information
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = []
        if 'file_stats' not in st.session_state:
            st.session_state.file_stats = {}
    
    def render_sidebar(self):
        """Render the sidebar with configuration options"""
        st.sidebar.markdown("### ⚙️ Configuration")
        
        # OpenAI Configuration
        st.sidebar.markdown("#### OpenAI Settings")
        print(config.openai_api_key)
        openai_api_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            value=config.openai_api_key if config.openai_api_key != "your_openai_api_key_here" else "",
            help="Enter your OpenAI API key"
        )
        
        model_name = st.sidebar.selectbox(
            "Model",
            ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-turbo"],
            index=0,
            help="Choose the OpenAI model to use"
        )
        
        # Qdrant Configuration
        st.sidebar.markdown("#### Qdrant Settings")
        qdrant_url = st.sidebar.text_input(
            "Qdrant URL",
            value=config.qdrant_url,
            help="Qdrant server URL"
        )
        
        qdrant_port = st.sidebar.number_input(
            "Qdrant Port",
            value=config.qdrant_port,
            min_value=1,
            max_value=65535,
            help="Qdrant server port"
        )
        
        collection_name = st.sidebar.text_input(
            "Collection Name",
            value=config.qdrant_collection_name,
            help="Name for the Qdrant collection"
        )
        
        # Processing Configuration
        st.sidebar.markdown("#### Processing Settings")
        chunk_size = st.sidebar.slider(
            "Chunk Size",
            min_value=200,
            max_value=2000,
            value=config.chunk_size,
            step=100,
            help="Size of text chunks for processing"
        )
        
        chunk_overlap = st.sidebar.slider(
            "Chunk Overlap",
            min_value=0,
            max_value=500,
            value=config.chunk_overlap,
            step=50,
            help="Overlap between text chunks"
        )
        
        max_chunks = st.sidebar.slider(
            "Max Chunks per Query",
            min_value=1,
            max_value=20,
            value=config.max_chunks_per_query,
            step=1,
            help="Number of chunks to retrieve for each query"
        )
        
        # Store configuration in session state
        st.session_state.config = {
            'openai_api_key': openai_api_key,
            'model_name': model_name,
            'qdrant_url': qdrant_url,
            'qdrant_port': qdrant_port,
            'collection_name': collection_name,
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'max_chunks': max_chunks
        }
        
        # System Information
        st.sidebar.markdown("#### System Status")
        if st.sidebar.button("Check System Health"):
            self.check_system_health()
        
        # Clear data button
        if st.sidebar.button("🗑️ Clear All Data", type="secondary"):
            self.clear_all_data()
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">📚 Zenith PDF Chatbot</h1>', unsafe_allow_html=True)
        st.markdown(
            "Upload PDF documents, process them with advanced AI, and chat with your knowledge base!",
            unsafe_allow_html=True
        )
    
    def render_file_upload_section(self):
        """Render the file upload and processing section"""
        st.markdown('<h2 class="sub-header">📁 Document Processing</h2>', unsafe_allow_html=True)
        
        # Create two columns for different upload methods
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Upload PDF Files")
            uploaded_files = st.file_uploader(
                "Choose PDF files",
                type=['pdf'],
                accept_multiple_files=True,
                help="Upload one or more PDF files to process"
            )
            
            if uploaded_files:
                st.markdown("**Uploaded Files:**")
                total_size = 0
                for file in uploaded_files:
                    file_size = len(file.read())
                    file.seek(0)  # Reset file pointer
                    total_size += file_size
                    st.markdown(f"- {file.name} ({format_file_size(file_size)})")
                
                st.markdown(f"**Total Size:** {format_file_size(total_size)}")
        
        with col2:
            st.markdown("#### Or Use Directory Path")
            directory_path = st.text_input(
                "PDF Directory Path",
                placeholder="/path/to/your/pdf/directory",
                help="Enter the path to a directory containing PDF files"
            )
            
            if directory_path and Path(directory_path).exists():
                pdf_files = list(Path(directory_path).glob("**/*.pdf"))
                if pdf_files:
                    st.markdown(f"**Found {len(pdf_files)} PDF files:**")
                    for pdf_file in pdf_files[:5]:  # Show first 5
                        st.markdown(f"- {pdf_file.name}")
                    if len(pdf_files) > 5:
                        st.markdown(f"... and {len(pdf_files) - 5} more files")
                else:
                    st.warning("No PDF files found in the specified directory")
            elif directory_path:
                st.error("Directory does not exist")
        
        # Processing button
        st.markdown("---")
        
        # Validate configuration before showing process button
        config_valid = self.validate_configuration()
        
        if config_valid:
            if st.button("🚀 Process PDFs", type="primary", disabled=not (uploaded_files or directory_path)):
                if uploaded_files or directory_path:
                    self.process_pdfs(uploaded_files, directory_path)
                else:
                    st.error("Please upload files or specify a directory path")
        else:
            st.error("Please configure your OpenAI API key in the sidebar")
    
    def validate_configuration(self) -> bool:
        """Validate the current configuration"""
        if 'config' not in st.session_state:
            return False
        
        config = st.session_state.config
        
        # Check OpenAI API key
        if not config.get('openai_api_key'):
            return False
        
        return True
    
    def process_pdfs(self, uploaded_files: List, directory_path: str):
        """Process PDF files"""
        try:
            config = st.session_state.config
            
            # Initialize components
            with st.spinner("Initializing components..."):
                st.session_state.pdf_processor = PDFProcessor(
                    chunk_size=config['chunk_size'],
                    chunk_overlap=config['chunk_overlap']
                )
                
                st.session_state.vector_store = VectorStore(
                    collection_name=config['collection_name']
                )
                
                st.session_state.chat_engine = ChatEngine(
                    vector_store=st.session_state.vector_store,
                    model_name=config['model_name']
                )
            
            # Load documents
            documents = []
            
            if uploaded_files:
                with st.spinner("Loading uploaded files..."):
                    documents = st.session_state.pdf_processor.process_uploaded_files(uploaded_files)
                    st.session_state.processed_files = [f.name for f in uploaded_files]
            
            elif directory_path:
                with st.spinner("Loading files from directory..."):
                    documents = st.session_state.pdf_processor.load_pdfs_from_directory(directory_path)
                    pdf_files = list(Path(directory_path).glob("**/*.pdf"))
                    st.session_state.processed_files = [f.name for f in pdf_files]
            
            if not documents:
                st.error("No documents were loaded. Please check your files.")
                return
            
            # Split documents
            with st.spinner("Splitting documents into chunks..."):
                chunks = st.session_state.pdf_processor.split_documents(documents)
            
            # Store in vector database
            with st.spinner("Creating embeddings and storing in vector database..."):
                success = st.session_state.vector_store.add_documents(chunks)
            
            if success:
                # Setup chat engine
                with st.spinner("Setting up chat engine..."):
                    st.session_state.chat_engine.setup_conversation_chain()
                
                # Update session state
                st.session_state.documents_processed = True
                st.session_state.file_stats = {
                    'total_documents': len(documents),
                    'total_chunks': len(chunks),
                    'processed_files': st.session_state.processed_files
                }
                
                st.success(f"✅ Successfully processed {len(documents)} pages into {len(chunks)} chunks!")
                
                # Show processing summary
                self.show_processing_summary()
                
            else:
                st.error("Failed to store documents in vector database")
                
        except Exception as e:
            st.error(f"Error processing PDFs: {str(e)}")
            logger.error(f"PDF processing error: {e}")
            if st.session_state.config.get('debug_mode', False):
                st.code(traceback.format_exc())
    
    def show_processing_summary(self):
        """Show processing summary"""
        if st.session_state.file_stats:
            stats = st.session_state.file_stats
            
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown("### 📊 Processing Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Pages", stats['total_documents'])
            
            with col2:
                st.metric("Text Chunks", stats['total_chunks'])
            
            with col3:
                st.metric("Processed Files", len(stats['processed_files']))
            
            with st.expander("View processed files"):
                for filename in stats['processed_files']:
                    st.markdown(f"- {filename}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chat_section(self):
        """Render the chat interface"""
        st.markdown('<h2 class="sub-header">💬 Chat with Your Documents</h2>', unsafe_allow_html=True)
        
        if not st.session_state.documents_processed:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("📋 Please process some PDF documents first to start chatting!")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Chat interface
        self.render_chat_interface()
    
    def render_chat_interface(self):
        """Render the main chat interface"""
        # Display chat history
        self.display_chat_history()
        
        # Chat input
        user_input = st.chat_input("Ask a question about your documents...")
        
        if user_input:
            self.handle_user_input(user_input)
        
        # Chat controls
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🗑️ Clear Chat"):
                self.clear_chat_history()
        
        with col2:
            if st.button("📊 Show Sources"):
                self.show_current_sources()
        
        # Sample questions
        self.show_sample_questions()
    
    def display_chat_history(self):
        """Display the chat history"""
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(message["content"])
            
            elif message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(message["content"])
                    
                    # Show sources if available
                    if "sources" in message and message["sources"]:
                        with st.expander(f"📚 View Sources ({len(message['sources'])} documents)"):
                            for i, source in enumerate(message["sources"]):
                                st.markdown(f"**Source {i+1}:** {source.get('filename', 'Unknown')}")
                                st.markdown(f"*Page:* {source.get('page', 'Unknown')}")
                                st.markdown(f"*Content Preview:* {source.get('content', '')[:200]}...")
                                st.markdown("---")
    
    def handle_user_input(self, user_input: str):
        """Handle user input and generate response"""
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            with st.spinner("Thinking..."):
                # Get response from chat engine
                response = st.session_state.chat_engine.chat(user_input)
            
            # Add assistant response to history
            assistant_message = {
                "role": "assistant",
                "content": response["answer"],
                "sources": response.get("source_documents", [])
            }
            
            st.session_state.chat_history.append(assistant_message)
            st.session_state.current_sources = response.get("source_documents", [])
            
            # Rerun to display new messages
            st.rerun()
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            logger.error(f"Chat error: {e}")
    
    def clear_chat_history(self):
        """Clear chat history"""
        st.session_state.chat_history = []
        st.session_state.current_sources = []
        if st.session_state.chat_engine:
            st.session_state.chat_engine.clear_conversation_history()
        st.rerun()
    
    def show_current_sources(self):
        """Show current sources in sidebar"""
        if st.session_state.current_sources:
            st.sidebar.markdown("### 📚 Current Sources")
            for i, source in enumerate(st.session_state.current_sources):
                with st.sidebar.expander(f"Source {i+1}"):
                    st.markdown(f"**File:** {source.get('filename', 'Unknown')}")
                    st.markdown(f"**Page:** {source.get('page', 'Unknown')}")
                    st.markdown(f"**Content:** {source.get('content', '')[:150]}...")
    
    def show_sample_questions(self):
        """Show sample questions to help users get started"""
        st.markdown("### 💡 Sample Questions")
        
        sample_questions = [
            "What are the main topics covered in these documents?",
            "Can you summarize the key findings?",
            "What are the conclusions or recommendations?",
            "Are there any important dates or numbers mentioned?",
            "What are the main arguments presented?",
            "Can you explain the methodology used?",
            "What are the limitations mentioned?",
            "Are there any references to other studies?"
        ]
        
        # Create columns for sample questions
        cols = st.columns(2)
        
        for i, question in enumerate(sample_questions):
            col = cols[i % 2]
            if col.button(question, key=f"sample_{i}"):
                # Add question to chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })
                self.handle_user_input(question)
    
    def check_system_health(self):
        """Check system health and display status"""
        st.sidebar.markdown("**System Health Check:**")
        
        try:
            # Check vector store
            if st.session_state.vector_store:
                vector_health = st.session_state.vector_store.health_check()
                st.sidebar.markdown(f"🔵 Vector Store: {'✅ Healthy' if vector_health else '❌ Error'}")
            else:
                st.sidebar.markdown("🔵 Vector Store: ⚪ Not initialized")
            
            # Check chat engine
            if st.session_state.chat_engine:
                chat_health = st.session_state.chat_engine.health_check()
                st.sidebar.markdown(f"🤖 Chat Engine: {'✅ Healthy' if chat_health else '❌ Error'}")
            else:
                st.sidebar.markdown("🤖 Chat Engine: ⚪ Not initialized")
            
            # Check configuration
            config_valid = self.validate_configuration()
            st.sidebar.markdown(f"⚙️ Configuration: {'✅ Valid' if config_valid else '❌ Invalid'}")
            
        except Exception as e:
            st.sidebar.error(f"Health check failed: {e}")
    
    def clear_all_data(self):
        """Clear all application data"""
        try:
            # Clear vector store
            if st.session_state.vector_store:
                st.session_state.vector_store.delete_collection()
            
            # Reset session state
            st.session_state.pdf_processor = None
            st.session_state.vector_store = None
            st.session_state.chat_engine = None
            st.session_state.documents_processed = False
            st.session_state.chat_history = []
            st.session_state.current_sources = []
            st.session_state.processed_files = []
            st.session_state.file_stats = {}
            
            st.success("✅ All data cleared successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error clearing data: {e}")
    
    def run(self):
        """Run the Streamlit application"""
        # Render sidebar
        self.render_sidebar()
        
        # Render main content
        self.render_header()
        
        # Create tabs for different sections
        tab1, tab2 = st.tabs(["📁 Document Processing", "💬 Chat Interface"])
        
        with tab1:
            self.render_file_upload_section()
            
            # Show processing summary if documents are processed
            if st.session_state.documents_processed:
                self.show_processing_summary()
        
        with tab2:
            self.render_chat_section()


def main():
    """Main function to run the Streamlit app"""
    app = ZenithStreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
