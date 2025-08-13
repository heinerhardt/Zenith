with col2:
            # Fixed Force Reinitialize button - simplified version to prevent infinite loops
            if st.button("🔄 Force Reinitialize", help="Force reinitialize all providers", use_container_width=True):
                
                # Perform reinitialization immediately without complex state management
                with st.spinner("🔄 Reinitializing all providers..."):
                    try:
                        settings_manager = get_enhanced_settings_manager()
                        success, message = settings_manager.force_reinitialize_providers()
                        
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                            
                    except Exception as e:
                        st.error(f"❌ Force reinitialization failed: {e}")
                        logger.error(f"Force reinitialization error: {e}")

"""
Enhanced Streamlit Web Interface for Zenith PDF Chatbot
Includes authentication, role-based access, and improved features
"""

import os
import sys
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
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
from src.core.enhanced_settings_manager import get_enhanced_settings_manager
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

# Explicitly disable multipage navigation
try:
    # Clear any existing pages
    if hasattr(st, '_pages'):
        st._pages.clear()
    if hasattr(st, 'session_state') and hasattr(st.session_state, '_pages'):
        st.session_state._pages.clear()
    
    # Disable page discovery
    import streamlit.runtime.pages_manager
    if hasattr(streamlit.runtime.pages_manager, '_main_script_path'):
        # Force single-page mode
        pass
except:
    pass

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

/* AGGRESSIVELY HIDE ALL UNWANTED NAVIGATION */
div[data-testid="stSidebar"] > div > div > div > div:first-child {
    display: none !important;
}

/* Hide multipage navigation if it appears */
.css-1kyxreq, .css-12oz5g7, .css-1v3fvcr, .css-1e5imcs {
    display: none !important;
}

/* Hide any page navigation elements */
[data-testid="stSidebarNav"], 
[data-testid="stSidebarNavItems"],
.css-1544g2n,
.css-1d391kg,
.css-1rs6os,
.css-17eq0hr,
.css-pkbazv,
.css-1emrehy {
    display: none !important;
}

/* Force clean sidebar - hide first element */
section[data-testid="stSidebar"] > div:first-child > div:first-child > div:first-child {
    display: none !important;
}

/* Hide any selectbox or navigation in sidebar */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
    display: none !important;
}

/* Hide page selector if it exists */
div[data-baseweb="select"] {
    display: none !important;
}

/* Additional safety - hide any potential page navigation */
.stSelectbox, .css-1wa3eu0, .css-10trblm {
    display: none !important;
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
            settings_manager = get_enhanced_settings_manager()
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
        
        # Create tabs for chat and file upload (Chat first as default)
        tab1, tab2 = st.tabs(["💬 Chat", "📁 Upload Documents"])
        
        with tab1:
            self.render_chat_tab()
        
        with tab2:
            self.render_file_upload_interface()
    
    def render_sidebar_info(self):
        """Render sidebar information - CLEAN VERSION"""
        # Force hide any navigation with JavaScript
        st.markdown("""
        <script>
        setTimeout(function() {
            // Hide any page navigation elements
            const elements = document.querySelectorAll('[data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"], .css-1544g2n, .stSelectbox');
            elements.forEach(el => el.style.display = 'none');
            
            // Hide first child of sidebar if it contains navigation
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                const firstChild = sidebar.querySelector('div > div > div > div:first-child');
                if (firstChild && (firstChild.innerText.includes('Enhanced') || firstChild.innerText.includes('MinIO'))) {
                    firstChild.style.display = 'none';
                }
            }
        }, 100);
        </script>
        """, unsafe_allow_html=True)
        
        # Clear any previous sidebar content to prevent unwanted navigation
        if hasattr(st.session_state, 'page_selector'):
            del st.session_state.page_selector
        
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
        
        # Ensure components are initialized
        user_id = st.session_state.user_info.get('id')
        
        # Initialize vector store if needed
        if not st.session_state.vector_store:
            try:
                st.session_state.vector_store = UserVectorStore(user_id=user_id)
            except Exception as e:
                st.error(f"❌ Failed to initialize vector store: {str(e)}")
                return
        
        # Initialize chat engine if needed
        if not st.session_state.chat_engine:
            try:
                st.session_state.chat_engine = EnhancedChatEngine(
                    user_id=user_id,
                    vector_store=st.session_state.vector_store
                )
            except Exception as e:
                st.error(f"❌ Failed to initialize chat engine: {str(e)}")
                return
        
        # Check if user has documents or allow general chat
        user_stats = {}
        if st.session_state.vector_store:
            try:
                user_stats = st.session_state.vector_store.get_user_stats()
            except Exception as e:
                user_stats = {'total_documents': 0}
        
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
                # Initialize chat engine if not available
                if not st.session_state.chat_engine:
                    user_id = st.session_state.user_info.get('id')
                    if not st.session_state.vector_store:
                        st.session_state.vector_store = UserVectorStore(user_id=user_id)
                    st.session_state.chat_engine = EnhancedChatEngine(
                        user_id=user_id,
                        vector_store=st.session_state.vector_store
                    )
                
                # Get response from chat engine
                response = st.session_state.chat_engine.chat(
                    user_input, 
                    use_rag=has_documents
                )
                
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
            
            # Show error for debugging if needed
            with st.expander("🔍 Error Details", expanded=False):
                import traceback
                st.code(traceback.format_exc())
        
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
        
        settings_manager = get_enhanced_settings_manager()
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
        
        settings_manager = get_enhanced_settings_manager()
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
        
        # Provider Status
        st.markdown("#### Current Provider Status")
        try:
            from src.core.provider_manager import get_provider_manager
            provider_manager = get_provider_manager()
            status = provider_manager.get_provider_status()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Chat Provider**")
                current_chat = status['current_providers']['chat']
                chat_health = status['provider_health']['chat'].get(current_chat, {})
                health_icon = "✅" if chat_health.get('healthy') else "❌"
                st.markdown(f"{health_icon} {current_chat.title()}: {chat_health.get('message', 'Unknown')}")
            
            with col2:
                st.markdown("**Embedding Provider**")
                current_embed = status['current_providers']['embedding']
                embed_health = status['provider_health']['embedding'].get(current_embed, {})
                health_icon = "✅" if embed_health.get('healthy') else "❌"
                st.markdown(f"{health_icon} {current_embed.title()}: {embed_health.get('message', 'Unknown')}")
            
        except Exception as e:
            st.warning(f"Could not get provider status: {e}")
        
        # Save Settings Button
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Add state management for save button
            save_key = "save_settings_clicked"
            
            if st.button("💾 Save AI Model Settings", type="primary", use_container_width=True, key="save_settings_btn"):
                # Prevent multiple rapid clicks
                if save_key not in st.session_state:
                    st.session_state[save_key] = True
                    
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
                    
                    # Show processing indicator
                    with st.spinner("💾 Saving settings and reinitializing providers..."):
                        success, message = settings_manager.update_settings(updates)
                    
                    if success:
                        st.success(f"✅ {message}")
                        
                        # Show what changed
                        current_settings = settings_manager.get_settings()
                        changes_detected = []
                        if chat_provider != current_settings.preferred_chat_provider:
                            changes_detected.append(f"Chat provider → {chat_provider}")
                        if embedding_provider != current_settings.preferred_embedding_provider:
                            changes_detected.append(f"Embedding provider → {embedding_provider}")
                        if ollama_enabled != current_settings.ollama_enabled:
                            status = "enabled" if ollama_enabled else "disabled"
                            changes_detected.append(f"Ollama → {status}")
                        
                        if changes_detected:
                            st.info(f"🔄 **Dynamic changes applied:**\n" + "\n- ".join([""] + changes_detected))
                            st.info("✨ **No restart required!** Changes have been applied immediately.")
                        else:
                            st.info("ℹ️ Settings saved successfully. No provider changes detected.")
                        
                        # Clear the flag after successful operation
                        if save_key in st.session_state:
                            del st.session_state[save_key]
                        
                        # Show updated provider status after a brief delay
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                        # Clear the flag on error
                        if save_key in st.session_state:
                            del st.session_state[save_key]
            
            # Show current state if save is in progress
            if save_key in st.session_state:
                st.info("💾 Saving settings in progress...")
        
        with col2:
            # Add a flag to prevent infinite reinitialization
            reinit_key = "force_reinit_clicked"
            
            if st.button("🔄 Force Reinitialize", help="Force reinitialize all providers", use_container_width=True, key="force_reinit_btn"):
                # Set flag to prevent multiple clicks
                if reinit_key not in st.session_state:
                    st.session_state[reinit_key] = True
                    
                    with st.spinner("🔄 Reinitializing all providers..."):
                        try:
                            from src.core.provider_manager import get_provider_manager
                            provider_manager = get_provider_manager()
                            success, message = settings_manager.force_reinitialize_providers()
                            
                            if success:
                                st.success(f"✅ {message}")
                                # Clear the flag after successful operation
                                if reinit_key in st.session_state:
                                    del st.session_state[reinit_key]
                                # Don't rerun immediately, let user see the success message
                            else:
                                st.error(f"❌ {message}")
                                # Clear the flag on error too
                                if reinit_key in st.session_state:
                                    del st.session_state[reinit_key]
                        except Exception as e:
                            st.error(f"❌ Force reinitialization failed: {e}")
                            # Clear the flag on exception
                            if reinit_key in st.session_state:
                                del st.session_state[reinit_key]
            
            # Show current state if reinitialization is in progress
            if reinit_key in st.session_state:
                st.info("🔄 Reinitialization in progress...")
    
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
                with st.spinner("Testing MinIO connection..."):
                    try:
                        client = MinIOClient(
                            endpoint=minio_endpoint,
                            access_key=minio_access_key,
                            secret_key=minio_secret_key,
                            secure=minio_secure
                        )
                        
                        # Test connection and get buckets
                        buckets = client.list_buckets()
                        st.success(f"✅ Connected successfully! Found {len(buckets)} buckets")
                        
                        # Store connection info in session state for reuse
                        st.session_state.minio_config = {
                            'endpoint': minio_endpoint,
                            'access_key': minio_access_key,
                            'secret_key': minio_secret_key,
                            'secure': minio_secure,
                            'connected': True
                        }
                        
                        if buckets:
                            st.markdown("**Available Buckets:**")
                            for bucket in buckets:
                                st.markdown(f"- 🪣 {bucket}")
                        else:
                            st.warning("No buckets found in MinIO instance")
                    
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
                        st.session_state.minio_config = {'connected': False}
        
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
        
        # Initialize session state for PDF files
        if 'minio_pdf_files' not in st.session_state:
            st.session_state.minio_pdf_files = []
        if 'minio_bucket_name' not in st.session_state:
            st.session_state.minio_bucket_name = ""
        
        # List PDFs button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔍 List PDFs from MinIO", type="secondary"):
                if bucket_name:
                    try:
                        # Store current bucket name
                        st.session_state.minio_bucket_name = bucket_name
                        
                        # Create MinIO client
                        client = MinIOClient(
                            endpoint=minio_endpoint,
                            access_key=minio_access_key,
                            secret_key=minio_secret_key,
                            secure=minio_secure
                        )
                        
                        with st.spinner("🔍 Connecting to MinIO and listing PDFs..."):
                            pdf_files = client.list_pdf_files(bucket_name, pdf_prefix)
                        
                        # Store PDF files in session state
                        st.session_state.minio_pdf_files = pdf_files
                        
                        if pdf_files:
                            st.success(f"✅ Found {len(pdf_files)} PDF files in bucket '{bucket_name}'")
                        else:
                            st.warning(f"⚠️ No PDF files found in bucket '{bucket_name}' with prefix '{pdf_prefix}'")
                    
                    except Exception as e:
                        st.error(f"❌ Error listing PDFs: {str(e)}")
                        st.session_state.minio_pdf_files = []
                else:
                    st.error("⚠️ Please enter a bucket name")
        
        with col2:
            if st.button("🔄 Refresh List", help="Refresh the PDF file list"):
                if bucket_name and st.session_state.minio_pdf_files:
                    # Re-trigger the listing with current settings
                    st.rerun()
        
        with col3:
            if st.button("🗑️ Clear List", help="Clear the PDF file list"):
                st.session_state.minio_pdf_files = []
                st.session_state.minio_bucket_name = ""
                st.success("✅ PDF list cleared")
        
        # Show PDF file selection if files are available
        if st.session_state.minio_pdf_files:
            st.markdown("---")
            st.markdown(f"### 📋 Available PDFs in '{st.session_state.minio_bucket_name}' ({len(st.session_state.minio_pdf_files)} files)")
            
            # File selection options
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Initialize default selection if not set
                if 'minio_selected_files' not in st.session_state:
                    st.session_state.minio_selected_files = []
                
                # Multi-select for individual files
                selected_files = st.multiselect(
                    "Select specific PDFs to process:",
                    options=st.session_state.minio_pdf_files,
                    default=st.session_state.minio_selected_files,
                    help="Choose specific PDF files to download and process",
                    key="pdf_multiselect"
                )
                
                # Update session state with current selection
                st.session_state.minio_selected_files = selected_files
            
            with col2:
                st.markdown("**Quick Select:**")
                if st.button("📋 Select All", help="Select all PDF files"):
                    st.session_state.minio_selected_files = st.session_state.minio_pdf_files.copy()
                    st.rerun()
                
                if st.button("🔝 Select First 5", help="Select first 5 PDF files"):
                    st.session_state.minio_selected_files = st.session_state.minio_pdf_files[:5]
                    st.rerun()
                
                if st.button("🚫 Select None", help="Clear selection"):
                    st.session_state.minio_selected_files = []
                    st.rerun()
            
            # Show selected files info
            current_selection = st.session_state.minio_selected_files
            
            if current_selection:
                st.success(f"📁 **{len(current_selection)} files selected for processing:**")
                
                # Smart display: show files if ≤10, otherwise show summary
                if len(current_selection) <= 10:
                    # Display selected files in columns for small selections
                    cols = st.columns(3)
                    for i, filename in enumerate(current_selection):
                        with cols[i % 3]:
                            st.markdown(f"✅ {filename}")
                else:
                    # Show summary for large selections
                    st.info(f"📊 **Large selection:** {len(current_selection)} files selected")
                    
                    # Show first few and last few files
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**First 3 files:**")
                        for filename in current_selection[:3]:
                            st.markdown(f"✅ {filename}")
                    
                    with col2:
                        st.markdown("**Last 3 files:**")
                        for filename in current_selection[-3:]:
                            st.markdown(f"✅ {filename}")
                    
                    # Expandable list for full view
                    with st.expander(f"📋 View all {len(current_selection)} selected files", expanded=False):
                        cols = st.columns(3)
                        for i, filename in enumerate(current_selection):
                            with cols[i % 3]:
                                st.markdown(f"✅ {filename}")
                
                with col1:
                    # Add smart processing options
                    processing_mode = st.radio(
                        "Processing Mode:",
                        options=["🔄 Smart Processing (Skip Processed)", "🔁 Force Reprocess All"],
                        help="Smart processing skips files that were already processed successfully"
                    )
                    
                    # Show processing analysis
                    if processing_mode.startswith("🔄"):
                        # Check which files need processing
                        files_to_process, already_processed = self.analyze_files_for_processing(
                            current_selection, 
                            st.session_state.minio_bucket_name
                        )
                        
                        if already_processed:
                            st.info(f"📊 **Processing Analysis:**")
                            st.markdown(f"- ✅ {len(already_processed)} files already processed (will skip)")
                            st.markdown(f"- 🔄 {len(files_to_process)} files need processing")
                            
                            if files_to_process:
                                with st.expander("📋 Files to Process", expanded=False):
                                    for filename in files_to_process:
                                        st.markdown(f"🔄 {filename}")
                                        
                                with st.expander("✅ Files Already Processed", expanded=False):
                                    for filename in already_processed:
                                        st.markdown(f"✅ {filename}")
                            else:
                                st.success("🎉 All selected files are already processed!")
                        else:
                            st.info(f"🔄 All {len(files_to_process)} files need processing")
                    else:
                        files_to_process = current_selection
                        st.info(f"🔁 Will reprocess all {len(files_to_process)} files")
                
                # Process selected files button
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    button_text = "🚀 Process Selected PDFs"
                    if processing_mode.startswith("🔄"):
                        files_to_process, _ = self.analyze_files_for_processing(
                            current_selection, 
                            st.session_state.minio_bucket_name
                        )
                        if len(files_to_process) == 0:
                            button_text = "✅ All Files Processed"
                            st.button(button_text, disabled=True, use_container_width=True)
                        else:
                            button_text = f"🚀 Process {len(files_to_process)} New/Changed Files"
                    
                    if button_text.startswith("🚀") and st.button(button_text, type="primary", use_container_width=True):
                        # Determine which files to actually process
                        if processing_mode.startswith("🔄"):
                            files_to_process, _ = self.analyze_files_for_processing(
                                current_selection, 
                                st.session_state.minio_bucket_name
                            )
                        else:
                            files_to_process = current_selection
                        
                        # Store files for processing
                        st.session_state.processing_files = files_to_process
                        st.session_state.processing_bucket = st.session_state.minio_bucket_name
                        st.session_state.processing_mode = processing_mode
                        st.session_state.start_processing = True
                        st.rerun()
            else:
                st.warning("⚠️ **No files selected.** Please select PDFs to process using the multiselect above or quick select buttons.")
                
                # Show available files as reference
                with st.expander("📄 Available Files", expanded=False):
                    for i, filename in enumerate(st.session_state.minio_pdf_files, 1):
                        st.markdown(f"{i}. {filename}")
        
        # Show file list preview
        elif bucket_name:
            st.info("💡 Click '🔍 List PDFs from MinIO' to discover PDF files in the bucket")
        
        # Handle processing if triggered
        if st.session_state.get('start_processing', False):
            st.session_state.start_processing = False  # Reset flag
            
            # Validate we have everything needed for processing
            processing_files = st.session_state.get('processing_files', [])
            processing_bucket = st.session_state.get('processing_bucket', '')
            
            if processing_files and processing_bucket:
                st.markdown("---")
                st.info(f"🚀 **Starting processing of {len(processing_files)} files from bucket '{processing_bucket}'**")
                
                # Create MinIO client for processing
                try:
                    processing_client = MinIOClient(
                        endpoint=minio_endpoint,
                        access_key=minio_access_key,
                        secret_key=minio_secret_key,
                        secure=minio_secure
                    )
                    
                    # Start processing with enhanced tracking
                    self.process_minio_pdfs(
                        processing_client,
                        processing_bucket,
                        processing_files
                    )
                    
                except Exception as e:
                    st.error(f"❌ Failed to create MinIO client for processing: {str(e)}")
                    st.error("Please check your MinIO configuration and try again.")
            else:
                st.error("❌ Processing failed: No files or bucket specified")
                st.error("Please select files and try again.")
    
    def analyze_files_for_processing(self, selected_files: List[str], bucket_name: str) -> Tuple[List[str], List[str]]:
        """
        Analyze which files need processing vs which are already processed
        Returns: (files_to_process, already_processed_files)
        """
        files_to_process = []
        already_processed = []
        
        try:
            # Get current user's processed files from session state or vector store
            user_id = st.session_state.user_info.get('id')
            processed_files_info = st.session_state.get('processed_files_history', {})
            
            # Initialize vector store if needed to check existing documents
            if not st.session_state.vector_store:
                st.session_state.vector_store = UserVectorStore(user_id=user_id)
            
            for filename in selected_files:
                # Create a unique identifier for this file from this bucket
                file_key = f"{bucket_name}/{filename}"
                
                # Check if file was already processed
                if file_key in processed_files_info:
                    # File was processed before - check if it might have changed
                    # For now, we'll assume if it's in the history, it's processed
                    # In a more advanced version, we could check file modification dates
                    already_processed.append(filename)
                else:
                    # File not processed yet
                    files_to_process.append(filename)
            
            return files_to_process, already_processed
            
        except Exception as e:
            # If analysis fails, process all files to be safe
            logger.error(f"Error analyzing files for processing: {str(e)}")
            return selected_files, []
    
    def update_processed_files_history(self, bucket_name: str, processed_files: List[str]):
        """Update the history of processed files"""
        try:
            if 'processed_files_history' not in st.session_state:
                st.session_state.processed_files_history = {}
            
            import time
            current_time = time.time()
            
            for filename in processed_files:
                file_key = f"{bucket_name}/{filename}"
                st.session_state.processed_files_history[file_key] = {
                    'processed_at': current_time,
                    'bucket': bucket_name,
                    'filename': filename,
                    'user_id': st.session_state.user_info.get('id')
                }
            
            logger.info(f"Updated processed files history: {len(processed_files)} files from bucket {bucket_name}")
            
        except Exception as e:
            logger.error(f"Error updating processed files history: {str(e)}")

    def process_minio_pdfs(self, minio_client, bucket_name: str, pdf_files: List[str]):
        """Process PDFs from MinIO with detailed progress tracking"""
        # Immediate status update
        st.markdown("### 🚀 MinIO Processing Started")
        st.info(f"Starting to process {len(pdf_files)} files...")
        
        try:
            # Debug information
            st.markdown("#### 🔍 Debug Information")
            st.write(f"**Bucket:** {bucket_name}")
            st.write(f"**Files to process:** {pdf_files}")
            st.write(f"**MinIO client:** {type(minio_client)}")
            
            # Test basic MinIO connection first
            st.info("Testing MinIO connection...")
            buckets = minio_client.list_buckets()
            st.success(f"✅ MinIO connection working - found {len(buckets)} buckets")
            
            # Initialize processing components
            st.info("Initializing processing components...")
            if not st.session_state.pdf_processor:
                st.session_state.pdf_processor = PDFProcessor()
                st.success("✅ PDF processor initialized")
            
            if not st.session_state.vector_store:
                user_id = st.session_state.user_info.get('id')
                st.session_state.vector_store = UserVectorStore(user_id=user_id)
                st.success("✅ Vector store initialized")
            
            if not st.session_state.chat_engine:
                user_id = st.session_state.user_info.get('id')
                st.session_state.chat_engine = EnhancedChatEngine(
                    user_id=user_id,
                    vector_store=st.session_state.vector_store
                )
                st.success("✅ Chat engine initialized")
            
            # Progress tracking components
            st.markdown("### 📊 Processing Progress")
            
            # Main progress bar
            main_progress = st.progress(0)
            status_container = st.container()
            
            # Create expandable log area
            with st.expander("📋 Detailed Processing Log", expanded=True):
                log_container = st.empty()
                log_text = ""
            
            # Statistics container
            stats_container = st.container()
            
            # Processing variables
            total_files = len(pdf_files)
            documents = []
            processed_files = []
            failed_files = []
            processing_stats = {
                'total_files': total_files,
                'processed_files': 0,
                'failed_files': 0,
                'total_pages': 0,
                'total_chunks': 0,
                'start_time': time.time()
            }
            
            def update_log(message: str, level: str = "info"):
                nonlocal log_text
                timestamp = time.strftime("%H:%M:%S")
                if level == "error":
                    log_text += f"🔴 [{timestamp}] {message}\n"
                elif level == "success":
                    log_text += f"✅ [{timestamp}] {message}\n"
                elif level == "warning":
                    log_text += f"⚠️ [{timestamp}] {message}\n"
                else:
                    log_text += f"ℹ️ [{timestamp}] {message}\n"
                log_container.text(log_text)
            
            def update_stats():
                with stats_container:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Files Processed", f"{processing_stats['processed_files']}/{processing_stats['total_files']}")
                    with col2:
                        st.metric("Pages Found", processing_stats['total_pages'])
                    with col3:
                        st.metric("Text Chunks", processing_stats['total_chunks'])
                    with col4:
                        elapsed = time.time() - processing_stats['start_time']
                        st.metric("Elapsed Time", f"{elapsed:.1f}s")
            
            # Start processing
            update_log(f"🚀 Starting MinIO PDF processing for {total_files} files from bucket '{bucket_name}'")
            update_log(f"📁 Files to process: {', '.join(pdf_files)}")
            
            for i, pdf_file in enumerate(pdf_files):
                current_progress = i / total_files
                main_progress.progress(current_progress)
                
                with status_container:
                    st.markdown(f"**Current File:** `{pdf_file}` ({i+1}/{total_files})")
                
                update_log(f"📥 Downloading: {pdf_file}")
                
                try:
                    # Download file from MinIO
                    temp_path = minio_client.download_file(bucket_name, pdf_file)
                    file_size = temp_path.stat().st_size
                    update_log(f"✅ Downloaded: {pdf_file} ({format_file_size(file_size)})")
                    
                    # Process the downloaded PDF
                    update_log(f"🔄 Processing PDF: {pdf_file}")
                    pdf_docs = st.session_state.pdf_processor.load_pdf(
                        str(temp_path)
                    )
                    
                    if pdf_docs:
                        page_count = len(pdf_docs)
                        documents.extend(pdf_docs)
                        processed_files.append(pdf_file)
                        processing_stats['processed_files'] += 1
                        processing_stats['total_pages'] += page_count
                        
                        update_log(f"✅ Processed: {pdf_file} ({page_count} pages)", "success")
                    else:
                        failed_files.append(pdf_file)
                        processing_stats['failed_files'] += 1
                        update_log(f"❌ Failed to extract content from: {pdf_file}", "error")
                    
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
                        update_log(f"🗑️ Cleaned up temporary file for: {pdf_file}")
                
                except Exception as e:
                    failed_files.append(pdf_file)
                    processing_stats['failed_files'] += 1
                    error_msg = f"Error processing {pdf_file}: {str(e)}"
                    update_log(error_msg, "error")
                    logger.error(error_msg)
                
                # Update statistics
                update_stats()
            
            # Text chunking phase
            if documents:
                main_progress.progress(0.8)
                with status_container:
                    st.markdown("**Phase:** Creating text chunks...")
                
                update_log(f"🔄 Creating text chunks from {len(documents)} pages...")
                chunks = st.session_state.pdf_processor.split_documents(documents)
                processing_stats['total_chunks'] = len(chunks)
                update_log(f"✅ Created {len(chunks)} text chunks", "success")
                
                # Vector storage phase
                main_progress.progress(0.9)
                with status_container:
                    st.markdown("**Phase:** Storing in vector database...")
                
                update_log("💾 Storing documents in vector database...")
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
                        'source': 'MinIO',
                        'bucket': bucket_name
                    }
                    
                    # Update processed files history for future incremental processing
                    self.update_processed_files_history(bucket_name, processed_files)
                    
                    main_progress.progress(1.0)
                    with status_container:
                        st.markdown("**Status:** ✅ **Complete!**")
                    
                    update_log("💾 Successfully stored all documents in vector database", "success")
                    update_log(f"🎉 Processing complete! {len(processed_files)} files processed successfully", "success")
                    update_log(f"📝 Updated processing history for future incremental processing", "success")
                    
                    # Final statistics
                    update_stats()
                    
                    # Success summary
                    st.success(f"🎉 Successfully processed {len(processed_files)} PDFs from MinIO bucket '{bucket_name}'!")
                    
                    # Show detailed results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### ✅ Successfully Processed")
                        for filename in processed_files:
                            st.markdown(f"- ✅ {filename}")
                    
                    if failed_files:
                        with col2:
                            st.markdown("#### ❌ Failed to Process")
                            for filename in failed_files:
                                st.markdown(f"- ❌ {filename}")
                    
                    # Processing summary
                    total_time = time.time() - processing_stats['start_time']
                    st.info(f"📊 **Summary:** {processing_stats['total_pages']} pages → {processing_stats['total_chunks']} chunks in {total_time:.1f} seconds")
                    
                else:
                    update_log("❌ Failed to store documents in vector database", "error")
                    st.error("❌ Failed to store documents in vector database")
            else:
                main_progress.progress(1.0)
                st.markdown("**Status:** ⚠️ **No documents processed**")
                
                update_log("⚠️ No documents were successfully processed", "warning")
                st.warning("⚠️ No documents were successfully processed")
                
                if failed_files:
                    st.markdown("#### ❌ Failed Files")
                    for filename in failed_files:
                        st.markdown(f"- {filename}")
        
        except Exception as e:
            error_msg = f"Critical error during MinIO processing: {str(e)}"
            st.error(f"❌ {error_msg}")
            logger.error(error_msg)
            
            # Show stack trace for debugging
            import traceback
            st.error("**Full error details:**")
            st.code(traceback.format_exc())
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
