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
from src.auth.auth_manager import (
    AuthenticationManager, init_auth_session, get_current_user_from_session,
    require_authentication, require_admin, logout_user_session
)
from src.auth.models import UserRole, UserRegistrationRequest, UserLoginRequest
from src.utils.helpers import format_file_size, format_duration
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
        st.markdown('<h1 class="main-header">🔐 Zenith Login</h1>', unsafe_allow_html=True)
        
        # Create tabs for login and registration
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            self.render_login_form()
        
        with tab2:
            self.render_registration_form()
    
    def render_login_form(self):
        """Render login form"""
        st.markdown("### Login to Your Account")
        
        # Check if auth manager is properly initialized
        if not st.session_state.get('auth_manager'):
            st.error("Authentication system not initialized. Please refresh the page.")
            if st.button("Refresh Page"):
                st.rerun()
            return
        
        with st.form("login_form"):
            username_or_email = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
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
                            
                            st.success("Login successful! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Login error: {str(e)}")
                        logger.error(f"Login error: {e}")
                else:
                    st.error("Please enter both username/email and password")
    
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
        
        # Create tabs for file upload and chat
        tab1, tab2 = st.tabs(["📁 Upload Documents", "💬 Chat"])
        
        with tab1:
            self.render_file_upload_interface()
        
        with tab2:
            self.render_chat_tab()
    
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
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
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
            
            # Add assistant response to history
            assistant_message = {
                "role": "assistant",
                "content": response["answer"],
                "sources": response.get("source_documents", [])
            }
            
            st.session_state.chat_history.append(assistant_message)
            
            # Rerun to display new messages
            st.rerun()
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            logger.error(f"Chat error: {e}")
    
    def clear_chat_history(self):
        """Clear chat history"""
        st.session_state.chat_history = []
        if st.session_state.chat_engine:
            st.session_state.chat_engine.clear_conversation_history()
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
        tab1, tab2, tab3, tab4 = st.tabs([
            "System Settings", "AI Models", "User Management", "System Status"
        ])
        
        with tab1:
            self.render_system_settings()
        
        with tab2:
            self.render_ai_model_settings()
        
        with tab3:
            self.render_user_management()
        
        with tab4:
            self.render_system_status()
    
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
        st.info("Configure your preferred AI providers and models")
        
        # This is a simplified version - full implementation would include
        # all the model configuration options
        st.markdown("Coming soon: Full AI model configuration interface")
    
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
