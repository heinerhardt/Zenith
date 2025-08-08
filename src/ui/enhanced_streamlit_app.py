"""
Enhanced Streamlit Web Interface for Zenith PDF Chatbot
Includes authentication, role-based access, and improved features
"""

import os
import sys
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import traceback
import uuid

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.core.config import config
from src.core.qdrant_manager import get_qdrant_client
from src.core.enhanced_vector_store import UserVectorStore
from src.core.enhanced_chat_engine import EnhancedChatEngine
from src.core.pdf_processor import PDFProcessor
from src.core.settings_manager import get_settings_manager
from src.core.chat_history import get_chat_history_manager, ChatSession, ChatMessage
from src.auth.auth_manager import (
    AuthenticationManager, init_auth_session, get_current_user_from_session,
    require_authentication, require_admin, logout_user_session
)
from src.auth.models import UserRole, UserRegistrationRequest, UserLoginRequest
from src.utils.helpers import format_file_size, format_duration
from src.utils.logger import get_logger
from datetime import datetime

# Initialize logger
logger = get_logger(__name__)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

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

.user-info {
    background-color: #f8f9fa;
    padding: 0.5rem 1rem;
    border-radius: 0.25rem;
    border: 1px solid #dee2e6;
    margin-bottom: 1rem;
}

.admin-panel {
    background-color: #fff3cd;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ffc107;
    margin: 1rem 0;
}

.file-upload-area {
    border: 2px dashed #ccc;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    background-color: #fafafa;
}
</style>
""", unsafe_allow_html=True)


class ZenithAuthenticatedApp:
    """Main Streamlit application with authentication"""
    
    def __init__(self):
        """Initialize the application"""
        self.initialize_session_state()
        self.initialize_auth()
        
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        # Authentication state
        init_auth_session()
        
        # Core components
        if 'pdf_processor' not in st.session_state:
            st.session_state.pdf_processor = None
        if 'vector_store' not in st.session_state:
            st.session_state.vector_store = None
        if 'chat_engine' not in st.session_state:
            st.session_state.chat_engine = None
        
        # Chat history components
        if 'chat_history_manager' not in st.session_state:
            st.session_state.chat_history_manager = get_chat_history_manager()
        if 'current_session' not in st.session_state:
            st.session_state.current_session = None
        
        # Processing state
        if 'documents_processed' not in st.session_state:
            st.session_state.documents_processed = False
        
        # Chat state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # File information
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = []
        if 'file_stats' not in st.session_state:
            st.session_state.file_stats = {}
        
        # Admin panel state
        if 'show_admin_panel' not in st.session_state:
            st.session_state.show_admin_panel = False
    
    def initialize_auth(self):
        """Initialize authentication manager"""
        if 'auth_manager' not in st.session_state or st.session_state.auth_manager is None:
            try:
                qdrant_client = get_qdrant_client().get_client()
                st.session_state.auth_manager = AuthenticationManager(
                    qdrant_client=qdrant_client,
                    secret_key=config.jwt_secret_key
                )
                logger.info("Authentication manager initialized successfully")
            except Exception as e:
                st.error(f"Failed to initialize authentication: {e}")
                logger.error(f"Authentication initialization error: {e}")
                # Create a fallback error state
                st.session_state.auth_manager = None
                st.stop()
    
    def render_login_page(self):
        """Render login/registration page"""
        # Hide sidebar on login page
        st.markdown("""
        <style>
        .css-1d391kg {display: none}
        .css-1rs6os {display: none}
        .css-17eq0hr {display: none}
        [data-testid="stSidebar"] {display: none}
        .stSidebar {display: none}
        section[data-testid="stSidebar"] {display: none}
        </style>
        """, unsafe_allow_html=True)
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<h1 class="main-header">📚 Zenith PDF Chatbot</h1>', unsafe_allow_html=True)
            st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">Secure Authentication Required</p>', unsafe_allow_html=True)
            
            # Create tabs for login and registration
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
            
            with tab1:
                self.render_login_form()
            
            with tab2:
                self.render_registration_form()
    
    def render_login_form(self):
        """Render login form"""
        st.markdown("### 🔐 Login to Your Account")
        
        # Check if auth manager is properly initialized
        if not st.session_state.get('auth_manager'):
            st.error("Authentication system not initialized. Please refresh the page.")
            if st.button("Refresh Page"):
                st.rerun()
            return
        
        with st.form("login_form"):
            username_or_email = st.text_input(
                "Username or Email",
                placeholder="Enter your username or email address"
            )
            password = st.text_input(
                "Password", 
                type="password",
                placeholder="Enter your password"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button("🔐 Login", use_container_width=True, type="primary")
            
            if submit_button:
                if username_or_email and password:
                    # Attempt login
                    login_request = UserLoginRequest(username_or_email, password)
                    
                    # Get client IP (simplified)
                    ip_address = "127.0.0.1"  # In production, get real IP
                    user_agent = "Streamlit App"
                    
                    try:
                        success, message, token = st.session_state.auth_manager.login_user(
                            login_request, ip_address, user_agent
                        )
                        
                        if success:
                            # Store session information
                            st.session_state.authenticated = True
                            st.session_state.user_token = token
                            
                            # Get user info
                            user = st.session_state.auth_manager.get_current_user(token)
                            if user:
                                st.session_state.user_info = {
                                    'id': user.id,
                                    'username': user.username,
                                    'email': user.email,
                                    'role': user.role.value,
                                    'full_name': user.full_name
                                }
                            
                            st.success("✅ Login successful! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Login error: {str(e)}")
                        logger.error(f"Login error: {e}")
                else:
                    st.error("⚠️ Please enter both username/email and password")
    
    def render_registration_form(self):
        """Render registration form"""
        st.markdown("### Create New Account")
        
        # Check if auth manager is properly initialized
        if not st.session_state.get('auth_manager'):
            st.error("Authentication system not initialized. Please refresh the page.")
            return
        
        # Check if registration is allowed
        try:
            settings_manager = get_settings_manager()
            settings = settings_manager.get_settings()
            
            if not settings.allow_user_registration:
                st.warning("User registration is currently disabled. Please contact an administrator.")
                return
        except Exception as e:
            st.warning("Could not check registration settings. Registration may be disabled.")
            return
        
        with st.form("registration_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            full_name = st.text_input("Full Name (Optional)")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # Role selection (default to chat user)
            role = st.selectbox(
                "Account Type",
                options=["chat_user"],
                format_func=lambda x: "Chat User" if x == "chat_user" else x,
                help="Chat users can upload files and chat with documents"
            )
            
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                # Validate inputs
                if not all([username, email, password]):
                    st.error("Please fill in all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long")
                else:
                    # Attempt registration
                    registration = UserRegistrationRequest(
                        username=username,
                        email=email,
                        password=password,
                        full_name=full_name if full_name else None,
                        role=role
                    )
                    
                    ip_address = "127.0.0.1"  # In production, get real IP
                    
                    try:
                        success, message, user = st.session_state.auth_manager.register_user(
                            registration, ip_address
                        )
                        
                        if success:
                            st.success("Registration successful! You can now login.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Registration error: {str(e)}")
                        logger.error(f"Registration error: {e}")
    
    def render_user_header(self):
        """Render user information header"""
        if st.session_state.get('authenticated') and st.session_state.get('user_info'):
            user_info = st.session_state.user_info
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f'<div class="user-info">'
                          f'👤 Welcome, {user_info.get("full_name") or user_info.get("username")} '
                          f'({user_info.get("role", "").replace("_", " ").title()})'
                          f'</div>', unsafe_allow_html=True)
            
            with col2:
                if st.button("🚪 Logout"):
                    self.logout_user()
            
            with col3:
                if user_info.get("role") == "administrator" and st.button("⚙️ Admin"):
                    st.session_state.show_admin_panel = True
                    st.rerun()
    
    def logout_user(self):
        """Logout current user"""
        try:
            if st.session_state.get('user_token'):
                st.session_state.auth_manager.logout_user(st.session_state.user_token)
            
            logout_user_session()
            st.success("Logged out successfully")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Logout error: {e}")
    
    def render_chat_interface(self):
        """Render the main chat interface"""
        st.markdown('<h1 class="main-header">📚 Zenith PDF Chatbot</h1>', unsafe_allow_html=True)
        
        # Initialize user components if needed
        if not st.session_state.vector_store:
            user_id = st.session_state.user_info.get('id')
            st.session_state.vector_store = UserVectorStore(user_id=user_id)
            st.session_state.chat_engine = EnhancedChatEngine(
                user_id=user_id,
                vector_store=st.session_state.vector_store
            )
        
        # Render sidebar with chat history
        self.render_sidebar_info()
        
        # Create tabs for file upload and chat
        tab1, tab2 = st.tabs(["📁 Upload Documents", "💬 Chat"])
        
        with tab1:
            self.render_file_upload_interface()
        
        with tab2:
            self.render_chat_tab()
    
    def render_sidebar_info(self):
        """Render sidebar information"""
        st.sidebar.markdown("### 📚 Zenith PDF Chatbot")
        
        # Chat History Section
        self.render_chat_history_sidebar()
        
        # Simple document info (only if documents are processed)
        if st.session_state.documents_processed and st.session_state.file_stats:
            st.sidebar.markdown("### 📄 Document Info")
            stats = st.session_state.file_stats
            st.sidebar.markdown(f"**Files:** {len(stats.get('processed_files', []))}")
            st.sidebar.markdown(f"**Pages:** {stats.get('total_documents', 0)}")
            st.sidebar.markdown(f"**Chunks:** {stats.get('total_chunks', 0)}")
        
        # Optional: Show document statistics for admin users only
        user_info = st.session_state.get('user_info', {})
        if user_info.get('role') == 'administrator':
            if st.sidebar.checkbox("Show Advanced Stats", value=False):
                if st.session_state.chat_engine:
                    stats = st.session_state.chat_engine.get_user_document_stats()
                    st.sidebar.markdown("### 📊 Document Statistics")
                    st.sidebar.json(stats)
    
    def render_chat_history_sidebar(self):
        """Render chat history in sidebar"""
        st.sidebar.markdown("### 💬 Chat History")
        
        user_id = st.session_state.user_info.get('id')
        if not user_id:
            return
        
        # New Chat button
        if st.sidebar.button("🆕 New Chat", use_container_width=True, type="primary"):
            self.start_new_chat_session()
        
        # Get recent sessions
        try:
            recent_sessions = st.session_state.chat_history_manager.get_user_sessions(user_id, limit=5)
            
            if recent_sessions:
                st.sidebar.markdown("**Recent Sessions:**")
                
                for i, session in enumerate(recent_sessions):
                    # Create a shortened title for display
                    display_title = session.title
                    if len(display_title) > 25:
                        display_title = display_title[:22] + "..."
                    
                    # Show message count and date
                    msg_count = session.get_message_count()
                    date_str = session.updated_at.strftime("%m/%d")
                    
                    # Check if this is the current session
                    is_current = (st.session_state.current_session and 
                                st.session_state.current_session.session_id == session.session_id)
                    
                    # Container for each session
                    with st.sidebar.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            button_type = "primary" if is_current else "secondary"
                            if st.button(
                                f"💬 {display_title}",
                                key=f"session_{session.session_id}",
                                use_container_width=True,
                                type=button_type,
                                help=f"{msg_count} messages, last: {date_str}"
                            ):
                                self.load_chat_session(session.session_id)
                        
                        with col2:
                            if st.button("🗑️", 
                                       key=f"delete_{session.session_id}", 
                                       help="Delete session",
                                       type="secondary"):
                                if st.session_state.chat_history_manager.delete_session(session.session_id, user_id):
                                    # If we deleted the current session, start a new one
                                    if is_current:
                                        st.session_state.current_session = None
                                        self.start_new_chat_session()
                                    else:
                                        st.rerun()
                        
                        # Show small session info
                        st.sidebar.caption(f"📝 {msg_count} msgs • 📅 {date_str}")
                        
                        if i < len(recent_sessions) - 1:
                            st.sidebar.markdown("---")
            else:
                st.sidebar.info("💭 No chat history yet.\nClick 'New Chat' to start!")
                
        except Exception as e:
            st.sidebar.error(f"Error loading chat history: {str(e)}")
    
    def start_new_chat_session(self):
        """Start a new chat session"""
        user_id = st.session_state.user_info.get('id')
        if not user_id:
            return
        
        # Create new session
        context = None
        if st.session_state.documents_processed and st.session_state.file_stats:
            files = st.session_state.file_stats.get('processed_files', [])
            if files:
                context = f"Documents: {', '.join(files[:3])}"
                if len(files) > 3:
                    context += f" and {len(files) - 3} more"
        
        session = st.session_state.chat_history_manager.create_session(
            user_id=user_id,
            title=f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            document_context=context
        )
        
        st.session_state.current_session = session
        st.session_state.chat_history = []  # Clear current chat display
        
        # Clean up old sessions (keep only 5 most recent)
        st.session_state.chat_history_manager.cleanup_old_sessions(user_id, keep_count=5)
        
        st.rerun()
    
    def load_chat_session(self, session_id: str):
        """Load an existing chat session"""
        user_id = st.session_state.user_info.get('id')
        if not user_id:
            return
        
        session = st.session_state.chat_history_manager.get_session(session_id, user_id)
        if session:
            st.session_state.current_session = session
            
            # Convert session messages to chat history format
            st.session_state.chat_history = []
            for msg in session.messages:
                st.session_state.chat_history.append({
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp
                })
            
            st.rerun()
    
    def add_message_to_current_session(self, role: str, content: str):
        """Add a message to the current session"""
        user_id = st.session_state.user_info.get('id')
        if not user_id:
            return
        
        # Ensure we have a current session
        if not st.session_state.current_session:
            self.start_new_chat_session()
        
        # Add message to session
        if st.session_state.current_session:
            success = st.session_state.chat_history_manager.add_message_to_session(
                st.session_state.current_session.session_id,
                user_id,
                role,
                content
            )
            
            if success:
                # Update local session object
                st.session_state.current_session.add_message(role, content)
                
                # Update chat display
                st.session_state.chat_history.append({
                    'role': role,
                    'content': content,
                    'timestamp': datetime.now()
                })
    
    def render_file_upload_interface(self):
        """Render file upload interface for chat users"""
        st.markdown("### Upload Your PDF Documents")
        
        # File upload with drag and drop
        st.markdown('<div class="file-upload-area">', unsafe_allow_html=True)
        st.markdown("#### Drag and Drop PDF Files")
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDF files to analyze",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            st.markdown("**Uploaded Files:**")
            total_size = 0
            
            for file in uploaded_files:
                file_size = len(file.read())
                file.seek(0)  # Reset file pointer
                total_size += file_size
                st.markdown(f"- {file.name} ({format_file_size(file_size)})")
            
            st.markdown(f"**Total Size:** {format_file_size(total_size)}")
            
            # Process files button
            if st.button("🚀 Process Documents", type="primary"):
                self.process_user_documents(uploaded_files)
        
        # Show user's processed documents
        self.show_user_documents()
    
    def process_user_documents(self, uploaded_files: List):
        """Process uploaded documents for the current user"""
        try:
            user_id = st.session_state.user_info.get('id')
            
            # Initialize PDF processor
            if not st.session_state.pdf_processor:
                st.session_state.pdf_processor = PDFProcessor()
            
            with st.spinner("Processing your documents..."):
                # Load documents
                documents = st.session_state.pdf_processor.process_uploaded_files(uploaded_files)
                
                if not documents:
                    st.error("No documents were loaded. Please check your files.")
                    return
                
                # Split documents
                chunks = st.session_state.pdf_processor.split_documents(documents)
                
                # Generate unique document ID for this upload
                document_id = str(uuid.uuid4())
                
                # Store in user's vector store
                success = st.session_state.vector_store.add_documents(chunks, document_id)
                
                if success:
                    # Update processed files info
                    st.session_state.processed_files.extend([f.name for f in uploaded_files])
                    st.session_state.file_stats = {
                        'total_documents': len(documents),
                        'total_chunks': len(chunks),
                        'document_id': document_id
                    }
                    
                    st.success(f"✅ Successfully processed {len(documents)} pages into {len(chunks)} chunks!")
                    
                    # Show processing summary
                    self.show_processing_summary()
                else:
                    st.error("Failed to store documents in vector database")
                    
        except Exception as e:
            st.error(f"Error processing documents: {str(e)}")
            logger.error(f"Document processing error: {e}")
    
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
                st.metric("Processed Files", len(st.session_state.processed_files))
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def show_user_documents(self):
        """Show user's processed documents"""
        try:
            if st.session_state.vector_store:
                user_stats = st.session_state.vector_store.get_user_stats()
                
                if user_stats.get('total_documents', 0) > 0:
                    st.markdown("### 📄 Your Documents")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Documents", user_stats['total_documents'])
                    with col2:
                        st.metric("Total Chunks", user_stats['total_chunks'])
                    
                    # Delete documents option
                    if st.button("🗑️ Clear All Documents", type="secondary"):
                        if st.session_state.vector_store.delete_user_documents():
                            st.success("All documents deleted successfully")
                            st.session_state.processed_files = []
                            st.session_state.file_stats = {}
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to delete documents")
                else:
                    st.info("No documents uploaded yet. Use the upload area above to get started!")
        except Exception as e:
            logger.error(f"Error showing user documents: {e}")
    
    def render_chat_tab(self):
        """Render the chat tab"""
        st.markdown("### 💬 Chat with Your Documents")
        
        # Check if user has documents or allow general chat
        user_stats = {}
        if st.session_state.vector_store:
            user_stats = st.session_state.vector_store.get_user_stats()
        
        has_documents = user_stats.get('total_documents', 0) > 0
        
        if not has_documents:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("🤖 You can chat with me even without uploading documents! "
                       "I can help with general questions, and when you upload PDFs, "
                       "I'll be able to answer questions about their content too.")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Display chat history
        self.display_chat_history()
        
        # Chat input
        user_input = st.chat_input("Ask me anything...")
        
        if user_input:
            self.handle_user_input(user_input, has_documents)
        
        # Chat controls
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🗑️ Clear Chat"):
                self.clear_chat_history()
        
        with col2:
            if has_documents and st.button("📊 Document Stats"):
                self.show_document_stats()
    
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
                    if message.get("sources") and len(message["sources"]) > 0:
                        with st.expander(f"📚 View Sources ({len(message['sources'])} documents)"):
                            for i, source in enumerate(message["sources"]):
                                st.markdown(f"**Source {i+1}:** {source.get('filename', 'Unknown')}")
                                st.markdown(f"*Content:* {source.get('content', '')}")
                                st.markdown("---")
    
    def handle_user_input(self, user_input: str, has_documents: bool):
        """Handle user input and generate response"""
        # Add user message to chat history and session
        self.add_message_to_current_session("user", user_input)
        
        try:
            with st.spinner("Thinking..."):
                # Get response from chat engine
                if st.session_state.chat_engine:
                    # Use RAG if user has documents, otherwise general chat
                    response = st.session_state.chat_engine.chat(
                        user_input, 
                        use_rag=has_documents
                    )
                else:
                    # Fallback to basic response
                    response = {
                        "answer": "I'm sorry, but the chat system is not properly initialized. Please try refreshing the page.",
                        "source_documents": []
                    }
                
                # Add assistant response to chat history and session
                assistant_message = {
                    "role": "assistant",
                    "content": response.get("answer", "I couldn't generate a response."),
                    "sources": []
                }
                
                # Process source documents
                if response.get("source_documents"):
                    for doc in response["source_documents"]:
                        source_info = {
                            "content": doc.page_content[:200] + "...",
                            "filename": doc.metadata.get("filename", "Unknown file"),
                            "page": doc.metadata.get("page", "Unknown page")
                        }
                        assistant_message["sources"].append(source_info)
                
                # Add to session and display
                self.add_message_to_current_session("assistant", assistant_message["content"])
                
        except Exception as e:
            error_message = f"Sorry, I encountered an error: {str(e)}"
            self.add_message_to_current_session("assistant", error_message)
            logger.error(f"Error in chat: {e}")
        
        # Force refresh to show new messages
        st.rerun()
    
    def clear_chat_history(self):
        """Clear current chat history and start new session"""
        st.session_state.chat_history = []
        st.session_state.current_session = None
        if st.session_state.chat_engine:
            st.session_state.chat_engine.clear_conversation_history()
        self.start_new_chat_session()
        st.rerun()
    
    def show_document_stats(self):
        """Show document statistics"""
        if st.session_state.chat_engine:
            stats = st.session_state.chat_engine.get_user_document_stats()
            
            st.sidebar.markdown("### 📊 Document Statistics")
            st.sidebar.json(stats)
    
    def run(self):
        """Run the main application"""
        # Ensure auth is properly initialized before anything else
        self.initialize_auth()
        
        # Check authentication
        if not st.session_state.get('authenticated', False):
            self.render_login_page()
            return
        
        # Render user header
        self.render_user_header()
        
        # Check if admin panel should be shown
        if st.session_state.get('show_admin_panel', False):
            user_info = st.session_state.get('user_info', {})
            if user_info.get('role') == 'administrator':
                self.render_admin_panel()
                return
            else:
                st.session_state.show_admin_panel = False
        
        # Render main interface based on user role
        user_info = st.session_state.get('user_info', {})
        user_role = user_info.get('role', 'chat_user')
        
        if user_role == 'administrator':
            # Admins see both chat interface and can access admin panel
            self.render_chat_interface()
        elif user_role == 'chat_user':
            # Chat users see only the chat interface
            self.render_chat_interface()
        else:
            st.error("Unknown user role")
    
    def render_admin_panel(self):
        """Render admin configuration panel"""
        st.markdown('<h2 class="sub-header">⚙️ Administrator Panel</h2>', unsafe_allow_html=True)
        
        # Back button
        if st.button("← Back to Main App"):
            st.session_state.show_admin_panel = False
            st.rerun()
        
        # Admin tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "System Settings", "AI Models", "User Management", "System Status", "MinIO Processor"
        ])
        
        with tab1:
            self.render_system_settings()
        
        with tab2:
            self.render_ai_model_settings()
        
        with tab3:
            self.render_user_management()
        
        with tab4:
            self.render_system_status()
        
        with tab5:
            self.render_minio_processor()
    
    def render_system_settings(self):
        """Render system settings configuration"""
        st.markdown("### General System Settings")
        
        settings_manager = get_settings_manager()
        current_settings = settings_manager.get_settings()
        
        with st.form("system_settings_form"):
            # Processing settings
            st.markdown("#### Document Processing")
            chunk_size = st.number_input(
                "Chunk Size", 
                min_value=100, 
                max_value=4000, 
                value=current_settings.chunk_size,
                help="Size of text chunks for processing"
            )
            
            chunk_overlap = st.number_input(
                "Chunk Overlap", 
                min_value=0, 
                max_value=1000, 
                value=current_settings.chunk_overlap,
                help="Overlap between consecutive chunks"
            )
            
            max_chunks = st.number_input(
                "Max Chunks per Query", 
                min_value=1, 
                max_value=50, 
                value=current_settings.max_chunks_per_query,
                help="Maximum number of chunks to retrieve for each query"
            )
            
            max_file_size = st.number_input(
                "Max File Size (MB)", 
                min_value=1, 
                max_value=500, 
                value=current_settings.max_file_size_mb,
                help="Maximum allowed file size for uploads"
            )
            
            # User management settings
            st.markdown("#### User Management")
            allow_registration = st.checkbox(
                "Allow User Registration", 
                value=current_settings.allow_user_registration,
                help="Allow new users to register accounts"
            )
            
            require_approval = st.checkbox(
                "Require Admin Approval", 
                value=current_settings.require_admin_approval,
                help="Require admin approval for new registrations"
            )
            
            session_duration = st.number_input(
                "Session Duration (Hours)", 
                min_value=1, 
                max_value=168, 
                value=current_settings.session_duration_hours,
                help="How long user sessions remain active"
            )
            
            if st.form_submit_button("Save Settings"):
                updates = {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "max_chunks_per_query": max_chunks,
                    "max_file_size_mb": max_file_size,
                    "allow_user_registration": allow_registration,
                    "require_admin_approval": require_approval,
                    "session_duration_hours": session_duration
                }
                
                success, message = settings_manager.update_settings(updates)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    def render_ai_model_settings(self):
        """Render AI model configuration"""
        st.markdown("### AI Model Configuration")
        
        settings_manager = get_settings_manager()
        current_settings = settings_manager.get_settings()
        
        # Provider selection
        st.markdown("#### Provider Selection")
        col1, col2 = st.columns(2)
        
        with col1:
            chat_provider = st.selectbox(
                "Chat Provider",
                options=["openai", "ollama"],
                index=0 if current_settings.preferred_chat_provider == "openai" else 1,
                format_func=lambda x: "OpenAI" if x == "openai" else "Ollama (Local)",
                help="Choose between cloud OpenAI or local Ollama for chat"
            )
        
        with col2:
            embedding_provider = st.selectbox(
                "Embedding Provider",
                options=["openai", "ollama"],
                index=0 if current_settings.preferred_embedding_provider == "openai" else 1,
                format_func=lambda x: "OpenAI" if x == "openai" else "Ollama (Local)",
                help="Choose between cloud OpenAI or local Ollama for embeddings"
            )
        
        # OpenAI Configuration
        st.markdown("#### OpenAI Configuration")
        with st.expander("OpenAI Settings", expanded=chat_provider == "openai"):
            openai_api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value="***" if current_settings.openai_api_key else "",
                help="Your OpenAI API key from https://platform.openai.com/api-keys"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                openai_chat_model = st.selectbox(
                    "Chat Model",
                    options=["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
                    index=self._get_model_index(current_settings.openai_chat_model, 
                                              ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"]),
                    help="OpenAI model for chat responses"
                )
            
            with col2:
                openai_embedding_model = st.selectbox(
                    "Embedding Model",
                    options=["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
                    index=self._get_model_index(current_settings.openai_embedding_model,
                                              ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]),
                    help="OpenAI model for document embeddings"
                )
            
            if st.button("Test OpenAI Connection"):
                if openai_api_key and openai_api_key != "***":
                    success, message = settings_manager.test_openai_connection(openai_api_key)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter an API key to test")
        
        # Ollama Configuration
        st.markdown("#### Ollama Configuration")
        with st.expander("Ollama Settings", expanded=chat_provider == "ollama"):
            ollama_enabled = st.checkbox(
                "Enable Ollama",
                value=current_settings.ollama_enabled,
                help="Enable local Ollama models"
            )
            
            ollama_endpoint = st.text_input(
                "Ollama Endpoint",
                value=current_settings.ollama_endpoint,
                help="Ollama server endpoint (e.g., http://localhost:11434)"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                ollama_chat_model = st.text_input(
                    "Chat Model",
                    value=current_settings.ollama_chat_model,
                    help="Ollama chat model name (e.g., llama2, mistral, codellama)"
                )
                
                # Show available chat models if connected
                if st.button("List Available Chat Models"):
                    try:
                        from src.core.ollama_integration import OllamaClient
                        client = OllamaClient(ollama_endpoint)
                        if client.health_check():
                            models = client.list_models()
                            if models:
                                st.write("**Available Models:**")
                                for model in models:
                                    st.write(f"- {model.name} ({format_file_size(model.size)})")
                            else:
                                st.info("No models found. Pull models with: `ollama pull model_name`")
                        else:
                            st.error("Cannot connect to Ollama server")
                    except Exception as e:
                        st.error(f"Error listing models: {e}")
            
            with col2:
                ollama_embedding_model = st.text_input(
                    "Embedding Model",
                    value=current_settings.ollama_embedding_model,
                    help="Ollama embedding model name (e.g., nomic-embed-text)"
                )
                
                # Pull model functionality
                model_to_pull = st.text_input(
                    "Pull New Model",
                    placeholder="Enter model name (e.g., llama2, mistral)",
                    help="Download a new model from Ollama registry"
                )
                
                if st.button("Pull Model") and model_to_pull:
                    try:
                        from src.core.ollama_integration import OllamaClient
                        client = OllamaClient(ollama_endpoint)
                        
                        with st.spinner(f"Pulling model {model_to_pull}..."):
                            success = client.pull_model(model_to_pull)
                        
                        if success:
                            st.success(f"Successfully pulled {model_to_pull}")
                        else:
                            st.error(f"Failed to pull {model_to_pull}")
                    except Exception as e:
                        st.error(f"Error pulling model: {e}")
            
            if st.button("Test Ollama Connection"):
                success, message = settings_manager.test_ollama_connection(ollama_endpoint)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # Qdrant Configuration
        st.markdown("#### Vector Database Configuration")
        with st.expander("Qdrant Settings"):
            qdrant_mode = st.selectbox(
                "Qdrant Mode",
                options=["local", "cloud"],
                index=0 if current_settings.qdrant_mode == "local" else 1,
                help="Use local Qdrant instance or cloud service"
            )
            
            if qdrant_mode == "local":
                col1, col2 = st.columns(2)
                with col1:
                    qdrant_host = st.text_input(
                        "Host",
                        value=current_settings.qdrant_local_host,
                        help="Qdrant server host (e.g., localhost)"
                    )
                
                with col2:
                    qdrant_port = st.number_input(
                        "Port",
                        min_value=1,
                        max_value=65535,
                        value=current_settings.qdrant_local_port,
                        help="Qdrant server port (default: 6333)"
                    )
                
                st.info("💡 To run Qdrant locally: `docker run -p 6333:6333 qdrant/qdrant`")
                
            else:
                qdrant_cloud_url = st.text_input(
                    "Cloud URL",
                    value=current_settings.qdrant_cloud_url or "",
                    help="Qdrant cloud cluster URL"
                )
                
                qdrant_api_key = st.text_input(
                    "API Key",
                    type="password",
                    value="***" if current_settings.qdrant_cloud_api_key else "",
                    help="Qdrant cloud API key"
                )
            
            qdrant_collection = st.text_input(
                "Collection Name",
                value=current_settings.qdrant_collection_name,
                help="Name for the document collection"
            )
            
            if st.button("Test Qdrant Connection"):
                try:
                    from src.core.qdrant_manager import QdrantManager
                    test_manager = QdrantManager(qdrant_mode)
                    if test_manager.health_check():
                        collections = test_manager.get_client().get_collections()
                        st.success(f"Qdrant connection successful! Found {len(collections.collections)} collections")
                    else:
                        st.error("Qdrant connection failed")
                except Exception as e:
                    st.error(f"Qdrant test failed: {str(e)}")
        
        # Save Settings Button
        st.markdown("---")
        if st.button("💾 Save AI Model Settings", type="primary"):
            updates = {
                "preferred_chat_provider": chat_provider,
                "preferred_embedding_provider": embedding_provider,
                "ollama_enabled": ollama_enabled,
                "ollama_endpoint": ollama_endpoint,
                "ollama_chat_model": ollama_chat_model,
                "ollama_embedding_model": ollama_embedding_model,
                "openai_chat_model": openai_chat_model,
                "openai_embedding_model": openai_embedding_model,
                "qdrant_mode": qdrant_mode,
                "qdrant_collection_name": qdrant_collection
            }
            
            # Add API keys only if they were changed
            if openai_api_key and openai_api_key != "***":
                updates["openai_api_key"] = openai_api_key
            
            if qdrant_mode == "local":
                updates.update({
                    "qdrant_local_host": qdrant_host,
                    "qdrant_local_port": qdrant_port
                })
            else:
                if qdrant_cloud_url:
                    updates["qdrant_cloud_url"] = qdrant_cloud_url
                if qdrant_api_key and qdrant_api_key != "***":
                    updates["qdrant_cloud_api_key"] = qdrant_api_key
            
            success, message = settings_manager.update_settings(updates)
            if success:
                st.success(message)
                st.info("💡 Restart the application for some changes to take effect.")
            else:
                st.error(message)
    
    def _get_model_index(self, current_model: str, model_list: list) -> int:
        """Get index of current model in list"""
        try:
            return model_list.index(current_model)
        except ValueError:
            return 0
    
    def render_user_management(self):
        """Render user management interface"""
        st.markdown("### User Management")
        
        try:
            auth_manager = st.session_state.auth_manager
            users = auth_manager.user_store.list_users()
            
            if users:
                st.markdown(f"**Total Users:** {len(users)}")
                
                # Users table
                user_data = []
                for user in users:
                    user_data.append({
                        "Username": user.username,
                        "Email": user.email,
                        "Role": user.role.value.replace("_", " ").title(),
                        "Active": "✅" if user.is_active else "❌",
                        "Last Login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never",
                        "Created": user.created_at.strftime("%Y-%m-%d")
                    })
                
                st.dataframe(user_data, use_container_width=True)
            else:
                st.info("No users found")
        
        except Exception as e:
            st.error(f"Error managing users: {e}")
    
    def render_minio_processor(self):
        """Render MinIO processor interface for admins"""
        st.markdown("### 🗄️ MinIO Document Processor")
        st.info("Process PDF documents directly from MinIO buckets (Admin Only)")
        
        # Check if MinIO is available
        try:
            from src.utils.minio_helpers import MinIOClient
            minio_available = True
        except ImportError:
            minio_available = False
        
        if not minio_available:
            st.error("❌ MinIO not available")
            st.info("Install MinIO: `pip install minio>=7.2.0`")
            return
        
        # MinIO Configuration
        with st.expander("⚙️ MinIO Configuration", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                minio_endpoint = st.text_input(
                    "MinIO Endpoint", 
                    value="10.16.100.2:9000",
                    help="MinIO server endpoint"
                )
                minio_access_key = st.text_input(
                    "Access Key", 
                    value="minioadmin",
                    help="MinIO access key"
                )
            
            with col2:
                minio_secret_key = st.text_input(
                    "Secret Key", 
                    value="minioadmin",
                    type="password",
                    help="MinIO secret key"
                )
                minio_secure = st.checkbox(
                    "Use HTTPS", 
                    value=False,
                    help="Use secure HTTPS connection"
                )
            
            if st.button("Test MinIO Connection"):
                try:
                    client = MinIOClient(
                        endpoint=minio_endpoint,
                        access_key=minio_access_key,
                        secret_key=minio_secret_key,
                        secure=minio_secure
                    )
                    
                    buckets = client.list_buckets()
                    st.success(f"✅ Connected successfully! Found {len(buckets)} buckets")
                    
                    if buckets:
                        st.markdown("**Available Buckets:**")
                        for bucket in buckets:
                            st.markdown(f"- {bucket}")
                
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
        
        # PDF Processing from MinIO
        st.markdown("### 📄 Process PDFs from MinIO")
        
        col1, col2 = st.columns(2)
        
        with col1:
            bucket_name = st.text_input(
                "Bucket Name",
                value="documents",
                help="Name of the MinIO bucket containing PDFs"
            )
        
        with col2:
            pdf_prefix = st.text_input(
                "PDF Prefix/Path",
                value="",
                help="Optional prefix to filter PDFs (e.g., 'pdfs/' or 'documents/2024/')"
            )
        
        if st.button("🔍 List PDFs from MinIO"):
            if bucket_name:
                try:
                    client = MinIOClient(
                        endpoint=minio_endpoint,
                        access_key=minio_access_key,
                        secret_key=minio_secret_key,
                        secure=minio_secure
                    )
                    
                    with st.spinner("Connecting to MinIO and listing PDFs..."):
                        pdf_files = client.list_pdf_files(bucket_name, pdf_prefix)
                    
                    if pdf_files:
                        st.success(f"Found {len(pdf_files)} PDF files")
                        
                        # Show file list
                        selected_files = st.multiselect(
                            "Select PDFs to process:",
                            options=pdf_files,
                            default=pdf_files[:5] if len(pdf_files) <= 5 else pdf_files[:3],
                            help="Select which PDF files to download and process"
                        )
                        
                        if selected_files and st.button("🚀 Process Selected PDFs", type="primary"):
                            self.process_minio_pdfs(client, bucket_name, selected_files)
                    else:
                        st.warning("No PDF files found in the specified bucket/path")
                
                except Exception as e:
                    st.error(f"Error listing PDFs: {str(e)}")
            else:
                st.error("Please enter a bucket name")
    
    def process_minio_pdfs(self, minio_client, bucket_name: str, pdf_files: List[str]):
        """Process PDFs from MinIO"""
        try:
            # Initialize processing components
            if not st.session_state.pdf_processor:
                st.session_state.pdf_processor = PDFProcessor()
            
            if not st.session_state.vector_store:
                user_id = st.session_state.user_info.get('id')
                st.session_state.vector_store = UserVectorStore(user_id=user_id)
            
            if not st.session_state.chat_engine:
                user_id = st.session_state.user_info.get('id')
                st.session_state.chat_engine = EnhancedChatEngine(
                    user_id=user_id,
                    vector_store=st.session_state.vector_store
                )
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            documents = []
            processed_files = []
            
            for i, pdf_file in enumerate(pdf_files):
                status_text.text(f"Processing {pdf_file}...")
                progress_bar.progress((i + 1) / len(pdf_files))
                
                try:
                    # Download and process PDF from MinIO
                    temp_path = minio_client.download_file(bucket_name, pdf_file)
                    
                    # Process the downloaded PDF
                    pdf_docs = st.session_state.pdf_processor.load_pdfs_from_directory(
                        str(temp_path.parent)
                    )
                    
                    if pdf_docs:
                        documents.extend(pdf_docs)
                        processed_files.append(pdf_file)
                    
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
                
                except Exception as e:
                    st.error(f"Error processing {pdf_file}: {str(e)}")
            
            if documents:
                status_text.text("Creating text chunks...")
                chunks = st.session_state.pdf_processor.split_documents(documents)
                
                status_text.text("Storing in vector database...")
                document_id = str(uuid.uuid4())
                success = st.session_state.vector_store.add_documents(chunks, document_id)
                
                if success:
                    # Update session state
                    st.session_state.documents_processed = True
                    st.session_state.processed_files.extend(processed_files)
                    st.session_state.file_stats = {
                        'total_documents': len(documents),
                        'total_chunks': len(chunks),
                        'processed_files': processed_files,
                        'source': 'MinIO'
                    }
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Processing complete!")
                    
                    st.success(f"Successfully processed {len(processed_files)} PDFs from MinIO!")
                    st.markdown(f"**Processed:** {len(documents)} pages into {len(chunks)} chunks")
                    
                    # Show processed files
                    with st.expander("View processed files"):
                        for filename in processed_files:
                            st.markdown(f"- {filename}")
                else:
                    st.error("Failed to store documents in vector database")
            else:
                st.warning("No documents were successfully processed")
        
        except Exception as e:
            st.error(f"Error during MinIO processing: {str(e)}")
            logger.error(f"MinIO processing error: {e}")
    
    def render_system_status(self):
        """Render system status and health checks"""
        st.markdown("### System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Core Services")
            
            # Qdrant status
            try:
                qdrant_manager = get_qdrant_client()
                qdrant_healthy = qdrant_manager.health_check()
                st.markdown(f"🔵 Qdrant: {'✅ Healthy' if qdrant_healthy else '❌ Error'}")
            except Exception as e:
                st.markdown(f"🔵 Qdrant: ❌ Error")
            
            # Authentication status
            st.markdown("🔐 Authentication: ✅ Active")
        
        with col2:
            st.markdown("#### Statistics")
            
            try:
                # User count
                auth_manager = st.session_state.auth_manager
                users = auth_manager.user_store.list_users()
                st.metric("Total Users", len(users))
                
                # Active users
                active_users = [u for u in users if u.is_active]
                st.metric("Active Users", len(active_users))
                
            except Exception as e:
                st.error(f"Error getting statistics: {e}")


def main():
    """Main function to run the Streamlit app"""
    try:
        app = ZenithAuthenticatedApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}")
        if config.debug_mode:
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
