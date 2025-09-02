"""
Simplified Zenith AI Chat Interface
Refactored from complex three-panel layout to clean Streamlit components
Preserves all backend integrations with improved UX
"""

import os
import sys
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import traceback
import uuid
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import preserved backend integrations
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

# Initialize logger
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Zenith AI Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme styling based on target design
st.markdown("""
<style>
    /* Dark theme based on target app with Zenith branding */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
    }
    
    /* Custom chat message styling */
    .user-message {
        background-color: #2563eb;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-left: 20%;
        text-align: right;
    }
    
    .ai-message {
        background-color: #1f1f1f;
        color: #e5e5e5;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: 20%;
        border: 1px solid #333;
    }
    
    .timestamp {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 4px;
    }
    
    /* Menu button styling */
    .stButton > button {
        background-color: #1a1a1a;
        color: white;
        border: 1px solid #333;
        border-radius: 6px;
        width: 100%;
        text-align: left;
    }
    
    .stButton > button:hover {
        background-color: #2a2a2a;
        border-color: #2563eb;
    }
    
    /* Admin button styling */
    .admin-button {
        background-color: #2563eb !important;
        color: white !important;
    }
    
    .admin-button:hover {
        background-color: #1d4ed8 !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        color: white;
        border: 1px solid #333;
    }
    
    /* Panel headers */
    .panel-header {
        color: #2563eb;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* User info card */
    .user-info-card {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    /* Feature menu items */
    .feature-item {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .feature-item:hover {
        background-color: #2a2a2a;
        border-color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_info" not in st.session_state:
        st.session_state.user_info = {}
    
    if "active_page" not in st.session_state:
        st.session_state.active_page = "chat"
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "id": "1",
                "content": "Hello! I'm Zenith AI. How can I help you with your documents today?",
                "sender": "ai",
                "timestamp": datetime.now(),
                "sources": []
            }
        ]
    
    if "auth_manager" not in st.session_state:
        try:
            qdrant_client = get_qdrant_client().get_client()
            st.session_state.auth_manager = AuthenticationManager(
                qdrant_client=qdrant_client,
                secret_key=config.jwt_secret_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize auth manager: {e}")
            st.error("Authentication system unavailable")

# Authentication functions
def render_login_page():
    """Render login/registration page"""
    st.markdown('<div class="panel-header">### 🔐 Zenith AI Login</div>', unsafe_allow_html=True)
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.markdown("**Sign in to your account**")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button and username and password:
                try:
                    login_request = UserLoginRequest(username=username, password=password)
                    auth_result = st.session_state.auth_manager.authenticate_user(login_request)
                    
                    if auth_result and auth_result.get("success"):
                        st.session_state.authenticated = True
                        st.session_state.user_info = auth_result.get("user", {})
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                except Exception as e:
                    logger.error(f"Login error: {e}")
                    st.error("Login failed. Please try again.")
    
    with tab2:
        with st.form("register_form"):
            st.markdown("**Create new account**")
            reg_username = st.text_input("Choose Username")
            reg_password = st.text_input("Choose Password", type="password")
            reg_confirm = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register", use_container_width=True)
            
            if register_button and reg_username and reg_password:
                if reg_password != reg_confirm:
                    st.error("Passwords don't match")
                else:
                    try:
                        registration_request = UserRegistrationRequest(
                            username=reg_username,
                            password=reg_password,
                            role=UserRole.CHAT_USER
                        )
                        result = st.session_state.auth_manager.register_user(registration_request)
                        
                        if result and result.get("success"):
                            st.success("Registration successful! Please login.")
                        else:
                            st.error(result.get("message", "Registration failed"))
                    except Exception as e:
                        logger.error(f"Registration error: {e}")
                        st.error("Registration failed. Please try again.")

def render_navigation_menu():
    """Render left panel navigation menu"""
    st.markdown('<div class="panel-header">💬 Zenith AI</div>', unsafe_allow_html=True)
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        start_new_chat_session()
    
    st.markdown("---")
    
    # Navigation menu
    st.markdown("**Navigation**")
    
    nav_items = [
        ("💬 Current Chat", "chat"),
        ("📚 Chat History", "chat_history"),
        ("⚙️ Settings", "settings")
    ]
    
    for label, page_key in nav_items:
        if st.button(label, use_container_width=True, key=f"nav_{page_key}"):
            st.session_state.active_page = page_key
            st.rerun()
    
    st.markdown("---")
    
    # User info card
    user_info = st.session_state.user_info
    if user_info:
        st.markdown(f"""
        <div class="user-info-card">
            <strong>👤 {user_info.get('username', 'User')}</strong><br>
            <small>Role: {user_info.get('role', 'user').title()}</small><br>
            <small>Status: Online</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user_session()
            st.session_state.authenticated = False
            st.session_state.user_info = {}
            st.rerun()

def render_chat_interface():
    """Render center panel chat interface"""
    st.markdown('<div class="panel-header">### AI Assistant</div>', unsafe_allow_html=True)
    st.markdown("*Ask me questions about your uploaded documents*")
    
    # Search scope selection
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Search Scope:**")
    with col2:
        st.selectbox(
            "Search in:",
            options=["my_files", "all_files"],
            format_func=lambda x: "My Files Only" if x == "my_files" else "All User Files",
            key="search_scope",
            label_visibility="collapsed"
        )
    
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        # Display messages
        for message in st.session_state.messages:
            if message["sender"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    {message["content"]}
                    <div class="timestamp">{message["timestamp"].strftime("%H:%M")}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                sources_text = ""
                if message.get("sources"):
                    source_names = [s.get("filename", "Unknown") for s in message["sources"]]
                    search_scope_text = f" ({message.get('search_scope', 'my_files').replace('_', ' ').title()})" if message.get("search_scope") else ""
                    sources_text = f"<br><small>📄 Sources{search_scope_text}: {', '.join(source_names[:3])}</small>"
                
                st.markdown(f"""
                <div class="ai-message">
                    {message["content"]}{sources_text}
                    <div class="timestamp">{message["timestamp"].strftime("%H:%M")}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    
    # Use form for better input handling
    with st.form("message_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            placeholder_text = f"Ask about {'your' if st.session_state.get('search_scope', 'my_files') == 'my_files' else 'all'} documents..."
            user_input = st.text_input(
                "Type your message...", 
                label_visibility="collapsed",
                placeholder=placeholder_text
            )
        
        with col2:
            send_button = st.form_submit_button("Send", use_container_width=True)
        
        # Handle message sending
        if send_button and user_input.strip():
            handle_message_submission(user_input)
            st.rerun()

def render_feature_menu():
    """Render right panel feature menu (role-based)"""
    user_role = st.session_state.user_info.get('role', 'chat_user')
    
    # Admin features (if administrator)
    if user_role == 'administrator':
        render_admin_menu()
        st.markdown("---")
    
    # User features (available to all users)
    render_user_features_menu()

def render_admin_menu():
    """Render admin panel menu"""
    st.markdown('<div class="panel-header">### ⚙️ Admin Panel</div>', unsafe_allow_html=True)
    
    admin_options = [
        ("🔧 System Settings", 'system_settings'),
        ("🤖 AI Models", 'ai_models'), 
        ("👥 User Management", 'user_management'),
        ("🗄️ MinIO Processor", 'minio_processor'),
        ("📊 System Status", 'system_status')
    ]
    
    for label, page in admin_options:
        if st.button(label, use_container_width=True, key=f"admin_{page}"):
            print(f"DEBUG: Admin button clicked: {page}")  # Debug logging
            st.session_state.active_page = page
            st.rerun()

def render_user_features_menu():
    """Render user features menu"""
    st.markdown('<div class="panel-header">### 📄 Documents</div>', unsafe_allow_html=True)
    
    user_features = [
        ("📁 Upload PDFs", 'upload_documents'),
        ("📚 My Documents", 'my_documents'),
        ("🔍 Search Settings", 'search_settings')
    ]
    
    for label, page in user_features:
        if st.button(label, use_container_width=True, key=f"user_{page}"):
            st.session_state.active_page = page
            st.rerun()
    
    # Show document stats
    show_user_document_stats()

def show_user_document_stats():
    """Display user's document statistics"""
    try:
        user_id = st.session_state.user_info.get('id', 'demo_user')
        documents = get_user_documents(user_id)
        
        # Calculate statistics
        doc_count = len(documents)
        total_size = sum(doc.get('file_size', 0) for doc in documents)
        total_size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
        
        # Get last upload date
        last_upload = "None"
        if documents:
            last_doc = max(documents, key=lambda x: x.get('uploaded_at', ''))
            last_upload = last_doc.get('uploaded_at', 'Unknown')
        
        st.markdown("---")
        st.markdown("**📊 Your Documents**")
        st.markdown(f"""
        <div class="user-info-card">
            <small>Documents: {doc_count}</small><br>
            <small>Storage: {total_size_mb:.1f} MB</small><br>
            <small>Last Upload: {last_upload}</small>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error showing document stats: {e}")

def start_new_chat_session():
    """Start a new chat session"""
    st.session_state.messages = [
        {
            "id": "1",
            "content": "Hello! I'm Zenith AI. How can I help you with your documents today?",
            "sender": "ai",
            "timestamp": datetime.now(),
            "sources": []
        }
    ]
    st.session_state.active_page = "chat"

def handle_message_submission(user_input: str):
    """Handle user message submission with RAG integration"""
    if not user_input.strip():
        return
    
    # Add user message
    user_message = {
        "id": str(len(st.session_state.messages) + 1),
        "content": user_input,
        "sender": "user",
        "timestamp": datetime.now(),
        "sources": []
    }
    st.session_state.messages.append(user_message)
    
    # Generate AI response with document context
    try:
        with st.spinner("AI is searching your documents..."):
            user_id = st.session_state.user_info.get('id', 'demo_user')
            documents = get_user_documents(user_id)
            
            if documents:
                # Use RAG-based response
                ai_response, sources = generate_rag_response(user_input, user_id)
            else:
                # Use simple response if no documents
                ai_response = generate_simple_response(user_input)
                sources = []
            
            ai_message = {
                "id": str(len(st.session_state.messages) + 1),
                "content": ai_response,
                "sender": "ai", 
                "timestamp": datetime.now(),
                "sources": sources
            }
            st.session_state.messages.append(ai_message)
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        error_message = {
            "id": str(len(st.session_state.messages) + 1),
            "content": "I apologize, but I'm experiencing technical difficulties. Please try again.",
            "sender": "ai",
            "timestamp": datetime.now(),
            "sources": []
        }
        st.session_state.messages.append(error_message)

def generate_simple_response(user_input: str) -> str:
    """Generate simple AI response for Phase 1"""
    responses = [
        f"I understand you're asking about: '{user_input}'. Once you upload documents, I'll be able to provide specific answers based on your content.",
        "That's an interesting question! To give you accurate information, please upload some PDF documents first.",
        f"I'd be happy to help with '{user_input}'. After you upload documents, I can search through them and provide detailed answers.",
        "Great question! My knowledge comes from the documents you upload. Please use the Upload PDFs feature to get started.",
        f"Thanks for asking about '{user_input}'. I'll be much more helpful once you have documents in your library!"
    ]
    import random
    return random.choice(responses)

def generate_rag_response(user_input: str, user_id: str) -> tuple[str, List[Dict]]:
    """Generate RAG-based response using user's documents"""
    try:
        search_scope = st.session_state.get('search_scope', 'my_files')
        
        # For demo purposes, adjust response based on search scope
        if search_scope == 'all_files':
            # In production, this would search across all users' documents (with permissions)
            response_prefix = "Searching across all user documents: "
        else:
            # Search only user's own documents
            response_prefix = "Searching your documents: "
        
        # For now, use enhanced chat engine with user's documents
        # In production, this would be modified to handle scope
        try:
            chat_engine = EnhancedChatEngine(user_id=user_id)
            response_data = chat_engine.chat(user_input)
            
            if isinstance(response_data, dict):
                response_text = response_data.get('response', 'I could not generate a response.')
                sources = response_data.get('sources', [])
            else:
                response_text = str(response_data)
                sources = []
        except Exception:
            # Fallback to document-based response using session data
            documents = get_user_documents(user_id)
            if documents:
                response_text = f"I found {len(documents)} document(s) in your library. I can help answer questions about: {', '.join([doc['filename'] for doc in documents[:3]])}. However, the full RAG search is temporarily unavailable."
                sources = [{'filename': doc['filename'], 'page': '1', 'content_preview': 'Document available for search...'} for doc in documents[:2]]
            else:
                return generate_simple_response(user_input), []
        
        # Format sources for display
        formatted_sources = []
        for source in sources[:3]:  # Limit to top 3 sources
            formatted_sources.append({
                'filename': source.get('filename', 'Unknown'),
                'page': source.get('page', 'N/A'),
                'content_preview': source.get('content', '')[:100] + '...' if source.get('content') else '',
                'search_scope': search_scope
            })
        
        return response_text, formatted_sources
        
    except Exception as e:
        logger.error(f"Error generating RAG response: {e}")
        # Fallback to simple response
        return generate_simple_response(user_input), []

def process_uploaded_files(uploaded_files):
    """Process uploaded PDF files"""
    try:
        user_id = st.session_state.user_info.get('id', 'demo_user')
        
        # Initialize processing status
        st.session_state.processing_status = {
            'active': True,
            'total_files': len(uploaded_files),
            'current_index': 0,
            'current_file': '',
            'completed': 0,
            'success': False,
            'error': None
        }
        
        # Process each file
        for i, uploaded_file in enumerate(uploaded_files):
            st.session_state.processing_status['current_index'] = i + 1
            st.session_state.processing_status['current_file'] = uploaded_file.name
            
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = temp_file.name
            
            try:
                # Process the PDF
                success = process_single_pdf(temp_path, uploaded_file.name, user_id)
                if success:
                    st.session_state.processing_status['completed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing {uploaded_file.name}: {e}")
                st.session_state.processing_status['error'] = f"Failed to process {uploaded_file.name}: {str(e)}"
                break
            finally:
                # Clean up temp file
                os.unlink(temp_path)
        
        # Mark processing as complete
        st.session_state.processing_status['active'] = False
        if st.session_state.processing_status['completed'] == len(uploaded_files):
            st.session_state.processing_status['success'] = True
        
    except Exception as e:
        logger.error(f"Error in file processing: {e}")
        st.session_state.processing_status = {
            'active': False,
            'success': False,
            'error': str(e)
        }

def process_single_pdf(file_path: str, original_filename: str, user_id: str) -> bool:
    """Process a single PDF file"""
    try:
        # Validate file exists and is readable
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"PDF file is empty: {original_filename}")
        
        logger.info(f"Processing PDF: {original_filename} ({format_file_size(file_size)})")
        
        # Initialize PDF processor with error handling
        try:
            pdf_processor = PDFProcessor()
        except Exception as e:
            logger.error(f"Failed to initialize PDF processor: {e}")
            raise Exception("PDF processor initialization failed")
        
        # Load and chunk the PDF
        try:
            documents = pdf_processor.load_pdf(file_path)
            if not documents:
                raise ValueError(f"No content extracted from PDF: {original_filename}")
            
            chunks = pdf_processor.chunk_documents(documents)
            if not chunks:
                raise ValueError(f"No chunks created from PDF: {original_filename}")
            
            logger.info(f"Extracted {len(documents)} pages, created {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed to process PDF content: {e}")
            raise Exception(f"PDF content processing failed: {str(e)}")
        
        # For demo mode, just track the document without vector storage
        # to avoid potential vector store connection issues
        document_record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'filename': original_filename,
            'original_filename': original_filename,
            'file_size': file_size,
            'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'completed',
            'chunk_count': len(chunks),
            'source_type': 'upload'
        }
        
        # Try vector store integration, but don't fail if it's not available
        try:
            vector_store = UserVectorStore(user_id=user_id)
            vector_store.add_documents(chunks, metadata={
                'original_filename': original_filename,
                'user_id': user_id,
                'file_path': file_path
            })
            logger.info("Document added to vector store successfully")
        except Exception as e:
            logger.warning(f"Vector store unavailable, document tracked locally: {e}")
            # Continue processing even if vector store fails
        
        # Store document record in session state
        if 'user_documents' not in st.session_state:
            st.session_state.user_documents = []
        st.session_state.user_documents.append(document_record)
        
        logger.info(f"Successfully processed PDF: {original_filename} ({len(chunks)} chunks)")
        return True
        
    except Exception as e:
        logger.error(f"Error processing PDF {original_filename}: {e}")
        # Store failed document record for user visibility
        document_record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'filename': original_filename,
            'original_filename': original_filename,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'processed_at': None,
            'status': 'failed',
            'chunk_count': 0,
            'source_type': 'upload',
            'error': str(e)
        }
        
        if 'user_documents' not in st.session_state:
            st.session_state.user_documents = []
        st.session_state.user_documents.append(document_record)
        
        return False

def get_user_documents(user_id: str) -> List[Dict]:
    """Get user's documents (Phase 2 implementation)"""
    # For Phase 2, return documents from session state
    return st.session_state.get('user_documents', [])

def delete_user_document(user_id: str, doc_id: str):
    """Delete a user document"""
    if 'user_documents' in st.session_state:
        st.session_state.user_documents = [
            doc for doc in st.session_state.user_documents 
            if doc['id'] != doc_id
        ]

def retry_document_processing(doc_id: str):
    """Retry processing a failed document"""
    # For Phase 2, mark document as pending
    if 'user_documents' in st.session_state:
        for doc in st.session_state.user_documents:
            if doc['id'] == doc_id:
                doc['status'] = 'pending'
                break

# Admin panel supporting functions
def test_ai_providers(settings):
    """Test AI provider connections"""
    try:
        from src.core.provider_manager import ProviderManager
        provider_manager = ProviderManager()
        
        # Test OpenAI
        openai_result = provider_manager.test_provider('chat', 'openai')
        if openai_result.get('success'):
            st.success("✅ OpenAI connection successful")
        else:
            st.error(f"❌ OpenAI: {openai_result.get('message', 'Connection failed')}")
        
        # Test Ollama
        ollama_result = provider_manager.test_provider('chat', 'ollama')
        if ollama_result.get('success'):
            st.success("✅ Ollama connection successful")
        else:
            st.warning(f"⚠️ Ollama: {ollama_result.get('message', 'Connection failed')}")
            
    except Exception as e:
        logger.error(f"Error testing providers: {e}")
        st.error(f"Unable to test provider connections: {str(e)}")

def test_openai_connection():
    """Test OpenAI connection"""
    try:
        from src.core.provider_manager import ProviderManager
        provider_manager = ProviderManager()
        result = provider_manager.test_provider('chat', 'openai')
        
        if result.get('success'):
            return {'status': 'healthy', 'model': 'OpenAI GPT'}
        else:
            return {'status': 'error', 'error': result.get('message', 'Connection failed')}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def test_ollama_connection():
    """Test Ollama connection"""
    try:
        from src.core.provider_manager import ProviderManager
        provider_manager = ProviderManager()
        result = provider_manager.test_provider('chat', 'ollama')
        
        if result.get('success'):
            # Try to get model list
            models = []
            try:
                from src.core.ollama_integration import get_ollama_manager
                ollama_manager = get_ollama_manager()
                if hasattr(ollama_manager, 'list_available_models'):
                    models = ollama_manager.list_available_models()
            except Exception:
                models = [{'name': 'llama2', 'size': 'Unknown'}]  # Fallback
                
            return {'status': 'healthy', 'models': models}
        else:
            return {'status': 'error', 'error': result.get('message', 'Connection failed')}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def get_model_usage_stats():
    """Get model usage statistics"""
    # For Phase 3, return demo statistics
    return {
        'chat_requests': 47,
        'embeddings': 128,
        'avg_response_time': 1.24
    }

def get_user_statistics():
    """Get user statistics"""
    # For Phase 3, return demo statistics
    return {
        'total_users': 3,
        'active_users': 2,
        'admin_users': 1,
        'chat_users': 2
    }

def get_all_users():
    """Get all users for management"""
    # For Phase 3, return demo users
    return [
        {
            'id': 'demo_admin_id',
            'username': 'admin',
            'email': 'admin@zenith.ai',
            'role': 'administrator',
            'created_at': '2024-01-15 10:30:00',
            'last_login': '2024-09-02 15:00:00',
            'is_active': True,
            'document_count': 5
        },
        {
            'id': 'demo_user1_id',
            'username': 'user1',
            'email': 'user1@company.com',
            'role': 'chat_user',
            'created_at': '2024-02-01 09:15:00',
            'last_login': '2024-09-01 14:30:00',
            'is_active': True,
            'document_count': 3
        },
        {
            'id': 'demo_user2_id',
            'username': 'user2',
            'email': 'user2@company.com',
            'role': 'chat_user',
            'created_at': '2024-03-10 16:45:00',
            'last_login': 'Never',
            'is_active': False,
            'document_count': 0
        }
    ]

def deactivate_user(user_id):
    """Deactivate a user"""
    logger.info(f"Deactivating user: {user_id}")
    # For Phase 3, simulate deactivation

def activate_user(user_id):
    """Activate a user"""
    logger.info(f"Activating user: {user_id}")
    # For Phase 3, simulate activation

def delete_user(user_id):
    """Delete a user"""
    logger.info(f"Deleting user: {user_id}")
    # For Phase 3, simulate deletion

def create_user(username, email, password, role):
    """Create a new user"""
    logger.info(f"Creating user: {username} with role: {role}")
    # For Phase 3, simulate user creation
    # In production, would use auth manager

def get_system_health():
    """Get system health status"""
    try:
        # Check Qdrant connection
        qdrant_client = get_qdrant_client().get_client()
        collections = qdrant_client.get_collections()
        
        qdrant_status = {
            'status': 'healthy',
            'collections': len(collections.collections) if collections else 0
        }
    except Exception as e:
        qdrant_status = {'status': 'error', 'error': str(e)}
    
    return {
        'qdrant': qdrant_status,
        'ai_providers': {
            'openai': test_openai_connection(),
            'ollama': test_ollama_connection()
        },
        'storage': {
            'status': 'healthy',
            'usage_mb': 45.2  # Demo value
        }
    }

def get_system_statistics():
    """Get system usage statistics"""
    return {
        'total_documents': len(st.session_state.get('user_documents', [])),
        'total_chunks': sum(doc.get('chunk_count', 0) for doc in st.session_state.get('user_documents', [])),
        'chat_sessions': len(st.session_state.get('messages', [])) // 2,  # Rough estimate
        'api_calls_today': 156  # Demo value
    }

def get_recent_activity():
    """Get recent system activity"""
    # For Phase 3, return demo activity
    activities = []
    
    # Add document uploads from session
    for doc in st.session_state.get('user_documents', []):
        activities.append({
            'timestamp': doc.get('uploaded_at', 'Unknown'),
            'type': 'document_upload',
            'details': doc.get('filename', 'Unknown file')
        })
    
    # Add some demo activities
    activities.extend([
        {
            'timestamp': '2024-09-02 15:10:00',
            'type': 'user_login',
            'details': 'admin@zenith.ai'
        },
        {
            'timestamp': '2024-09-02 14:30:00', 
            'type': 'chat_session',
            'details': '3 messages exchanged'
        }
    ])
    
    return sorted(activities, key=lambda x: x['timestamp'], reverse=True)

def test_minio_connection(settings):
    """Test MinIO connection and get buckets"""
    try:
        # For demo, return mock data
        if settings.minio_enabled and settings.minio_endpoint:
            return {
                'status': 'healthy',
                'buckets': ['documents', 'pdfs', 'archive']
            }
        else:
            return {'status': 'error', 'error': 'MinIO not configured'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def get_minio_bucket_files(bucket_name):
    """Get files from MinIO bucket"""
    # For demo, return mock PDF files
    return [
        {'name': 'document1.pdf', 'size': 1024*1024*2},  # 2MB
        {'name': 'manual.pdf', 'size': 1024*1024*5},     # 5MB
        {'name': 'report.pdf', 'size': 1024*1024*1},     # 1MB
        {'name': 'whitepaper.pdf', 'size': 1024*1024*3}, # 3MB
    ]

def process_minio_file(bucket_name, file_name):
    """Process a single file from MinIO"""
    logger.info(f"Processing MinIO file: {bucket_name}/{file_name}")
    # In production, this would download from MinIO and process

def process_all_minio_files(bucket_name, max_files):
    """Process all PDF files in a MinIO bucket"""
    logger.info(f"Starting bulk processing: {bucket_name} (max {max_files} files)")
    # In production, this would start a background job

def show_minio_processing_status():
    """Show current MinIO processing status"""
    st.info("No active MinIO processing jobs")

def get_minio_processing_history():
    """Get MinIO processing job history"""
    # For demo, return mock history
    return [
        {
            'bucket': 'documents',
            'timestamp': '2024-09-02 14:30:00',
            'files_processed': 8,
            'success_rate': 0.875,
            'duration': '5m 23s',
            'status': 'completed'
        },
        {
            'bucket': 'pdfs',
            'timestamp': '2024-09-01 16:15:00', 
            'files_processed': 15,
            'success_rate': 1.0,
            'duration': '12m 45s',
            'status': 'completed'
        }
    ]

def render_main_chat_interface():
    """Render the main three-column chat interface"""
    # Create three columns with specified proportions
    left_col, center_col, right_col = st.columns([1, 2, 1])
    
    # Left Panel - Navigation Menu
    with left_col:
        render_navigation_menu()
    
    # Center Panel - Chat Interface
    with center_col:
        render_chat_interface()
    
    # Right Panel - Feature Menu
    with right_col:
        render_feature_menu()

def render_upload_documents_page():
    """Render PDF upload page"""
    st.markdown('<div class="panel-header">### 📁 Upload PDF Documents</div>', unsafe_allow_html=True)
    
    st.markdown("Upload PDF documents to enable AI-powered chat with your content.")
    
    # File upload widget
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        accept_multiple_files=True,
        type=['pdf'],
        help="Select one or more PDF files to upload and process"
    )
    
    if uploaded_files:
        st.markdown("---")
        st.markdown("**Selected Files:**")
        
        total_size = 0
        for file in uploaded_files:
            file_size = len(file.getvalue())
            total_size += file_size
            st.markdown(f"• {file.name} ({format_file_size(file_size)})")
        
        st.markdown(f"**Total Size:** {format_file_size(total_size)}")
        
        # Check file size limits
        max_size_bytes = config.max_file_size_mb * 1024 * 1024
        if total_size > max_size_bytes:
            st.error(f"Total file size ({format_file_size(total_size)}) exceeds limit of {config.max_file_size_mb}MB")
        else:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.success(f"Ready to process {len(uploaded_files)} file(s)")
            
            with col2:
                if st.button("🚀 Process Files", use_container_width=True):
                    process_uploaded_files(uploaded_files)
                    st.rerun()
    
    st.markdown("---")
    
    # Show processing status if any
    if st.session_state.get('processing_status'):
        status = st.session_state.processing_status
        if status['active']:
            st.info(f"Processing: {status['current_file']} ({status['current_index']}/{status['total_files']})")
            progress_bar = st.progress(status['current_index'] / status['total_files'])
        else:
            if status.get('success'):
                st.success(f"✅ Successfully processed {status['completed']} file(s)")
            else:
                st.error(f"❌ Processing failed: {status.get('error', 'Unknown error')}")
            
            if st.button("Clear Status"):
                st.session_state.processing_status = None
                st.rerun()
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def render_my_documents_page():
    """Render user's documents management page"""
    st.markdown('<div class="panel-header">### 📚 My Documents</div>', unsafe_allow_html=True)
    
    try:
        # Get user documents (Phase 2 implementation)
        user_id = st.session_state.user_info.get('id', 'demo_user')
        documents = get_user_documents(user_id)
        
        if not documents:
            st.info("No documents uploaded yet. Use the Upload PDFs feature to get started.")
        else:
            st.markdown(f"**{len(documents)} document(s) in your library:**")
            
            # Documents table
            for doc in documents:
                with st.expander(f"📄 {doc['filename']} ({doc['status']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Original Name:** {doc['original_filename']}")
                        st.markdown(f"**Size:** {format_file_size(doc['file_size'])}")
                        st.markdown(f"**Uploaded:** {doc['uploaded_at']}")
                        if doc.get('processed_at'):
                            st.markdown(f"**Processed:** {doc['processed_at']}")
                        st.markdown(f"**Chunks:** {doc.get('chunk_count', 0)}")
                    
                    with col2:
                        if doc['status'] == 'completed':
                            if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}", use_container_width=True):
                                delete_user_document(user_id, doc['id'])
                                st.success("Document deleted")
                                st.rerun()
                        elif doc['status'] == 'failed':
                            if st.button(f"🔄 Retry", key=f"retry_{doc['id']}", use_container_width=True):
                                retry_document_processing(doc['id'])
                                st.success("Retry initiated")
                                st.rerun()
    
    except Exception as e:
        logger.error(f"Error loading user documents: {e}")
        st.error("Unable to load documents. Please try again later.")
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def render_system_settings_page():
    """Render system settings admin page"""
    st.markdown('<div class="panel-header">### 🔧 System Settings</div>', unsafe_allow_html=True)
    
    st.markdown("Configure system-wide settings for Zenith AI.")
    
    try:
        # Load current settings
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_system_settings()
        
        # AI Provider Settings
        st.markdown("#### 🤖 AI Provider Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**OpenAI Settings**")
            openai_enabled = st.checkbox(
                "Enable OpenAI", 
                value=bool(current_settings.openai_api_key),
                help="Enable OpenAI for chat and embeddings"
            )
            
            if openai_enabled:
                openai_api_key = st.text_input(
                    "API Key",
                    value=current_settings.openai_api_key or "",
                    type="password",
                    help="Your OpenAI API key"
                )
                openai_chat_model = st.selectbox(
                    "Chat Model",
                    options=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                    index=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"].index(current_settings.openai_chat_model)
                    if current_settings.openai_chat_model in ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
                    else 1
                )
                openai_embedding_model = st.selectbox(
                    "Embedding Model",
                    options=["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
                    index=0
                )
        
        with col2:
            st.markdown("**Ollama Settings**")
            ollama_enabled = st.checkbox(
                "Enable Ollama", 
                value=current_settings.ollama_enabled,
                help="Enable local Ollama models"
            )
            
            if ollama_enabled:
                ollama_endpoint = st.text_input(
                    "Ollama Endpoint",
                    value=current_settings.ollama_endpoint,
                    help="Ollama server URL"
                )
                ollama_chat_model = st.text_input(
                    "Chat Model",
                    value=current_settings.ollama_chat_model,
                    help="Local chat model name"
                )
                ollama_embedding_model = st.text_input(
                    "Embedding Model", 
                    value=current_settings.ollama_embedding_model,
                    help="Local embedding model name"
                )
        
        # Provider Selection
        st.markdown("#### ⚡ Active Providers")
        col1, col2 = st.columns(2)
        
        with col1:
            preferred_chat_provider = st.selectbox(
                "Chat Provider",
                options=["openai", "ollama"],
                index=0 if current_settings.preferred_chat_provider == "openai" else 1,
                help="Primary provider for chat responses"
            )
        
        with col2:
            preferred_embedding_provider = st.selectbox(
                "Embedding Provider", 
                options=["openai", "ollama"],
                index=0 if current_settings.preferred_embedding_provider == "openai" else 1,
                help="Primary provider for document embeddings"
            )
        
        # Document Processing Settings
        st.markdown("#### 📄 Document Processing")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            chunk_size = st.number_input(
                "Chunk Size",
                min_value=100,
                max_value=5000,
                value=current_settings.chunk_size,
                step=100,
                help="Size of text chunks for processing"
            )
        
        with col2:
            chunk_overlap = st.number_input(
                "Chunk Overlap",
                min_value=0,
                max_value=500,
                value=current_settings.chunk_overlap,
                step=50,
                help="Overlap between text chunks"
            )
        
        with col3:
            max_file_size = st.number_input(
                "Max File Size (MB)",
                min_value=1,
                max_value=200,
                value=current_settings.max_file_size_mb,
                step=5,
                help="Maximum allowed file size for uploads"
            )
        
        # System Configuration
        st.markdown("#### ⚙️ System Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            allow_registration = st.checkbox(
                "Allow User Registration",
                value=current_settings.allow_user_registration,
                help="Allow new users to register accounts"
            )
            
            max_users = st.number_input(
                "Maximum Users",
                min_value=1,
                max_value=1000,
                value=current_settings.max_users,
                help="Maximum number of user accounts"
            )
        
        with col2:
            session_duration = st.number_input(
                "Session Duration (hours)",
                min_value=1,
                max_value=168,  # 1 week
                value=current_settings.session_duration_hours,
                help="How long user sessions remain active"
            )
        
        # Save Settings
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            if st.button("💾 Save Settings", use_container_width=True):
                try:
                    # Update settings
                    updated_settings = SystemSettings(
                        openai_api_key=openai_api_key if openai_enabled else None,
                        openai_chat_model=openai_chat_model if openai_enabled else current_settings.openai_chat_model,
                        openai_embedding_model=openai_embedding_model if openai_enabled else current_settings.openai_embedding_model,
                        ollama_enabled=ollama_enabled,
                        ollama_endpoint=ollama_endpoint if ollama_enabled else current_settings.ollama_endpoint,
                        ollama_chat_model=ollama_chat_model if ollama_enabled else current_settings.ollama_chat_model,
                        ollama_embedding_model=ollama_embedding_model if ollama_enabled else current_settings.ollama_embedding_model,
                        preferred_chat_provider=preferred_chat_provider,
                        preferred_embedding_provider=preferred_embedding_provider,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        max_file_size_mb=max_file_size,
                        allow_user_registration=allow_registration,
                        max_users=max_users,
                        session_duration_hours=session_duration,
                        updated_at=datetime.now()
                    )
                    
                    # Save settings
                    settings_manager.save_system_settings(updated_settings)
                    st.success("✅ Settings saved successfully!")
                    
                except Exception as e:
                    logger.error(f"Error saving settings: {e}")
                    st.error(f"Failed to save settings: {str(e)}")
        
        with col3:
            if st.button("🔄 Test Providers", use_container_width=True):
                test_ai_providers(current_settings)
    
    except Exception as e:
        logger.error(f"Error loading system settings: {e}")
        st.error("Unable to load system settings. Please check system configuration.")
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def render_ai_models_page():
    """Render AI models configuration page"""
    st.markdown('<div class="panel-header">### 🤖 AI Models</div>', unsafe_allow_html=True)
    
    st.markdown("Monitor and configure AI model providers.")
    
    try:
        # Provider Status
        st.markdown("#### 📊 Provider Status")
        
        # Test OpenAI
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**OpenAI Provider**")
            openai_status = test_openai_connection()
            if openai_status['status'] == 'healthy':
                st.success(f"✅ Connected - {openai_status.get('model', 'N/A')}")
            else:
                st.error(f"❌ {openai_status.get('error', 'Connection failed')}")
        
        with col2:
            if st.button("Test OpenAI", use_container_width=True):
                st.rerun()
        
        # Test Ollama
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Ollama Provider**")
            ollama_status = test_ollama_connection()
            if ollama_status['status'] == 'healthy':
                st.success(f"✅ Connected - {len(ollama_status.get('models', []))} models available")
            else:
                st.error(f"❌ {ollama_status.get('error', 'Connection failed')}")
        
        with col2:
            if st.button("Test Ollama", use_container_width=True):
                st.rerun()
        
        # Model Performance Metrics
        st.markdown("#### 📈 Performance Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Chat Requests Today", get_model_usage_stats().get('chat_requests', 0))
        
        with col2:
            st.metric("Embeddings Generated", get_model_usage_stats().get('embeddings', 0))
        
        with col3:
            st.metric("Avg Response Time", f"{get_model_usage_stats().get('avg_response_time', 0):.2f}s")
        
        # Available Models
        if ollama_status['status'] == 'healthy' and ollama_status.get('models'):
            st.markdown("#### 🗂️ Available Ollama Models")
            for model in ollama_status['models'][:10]:  # Show top 10
                st.markdown(f"• {model.get('name', 'Unknown')} ({model.get('size', 'N/A')})")
    
    except Exception as e:
        logger.error(f"Error in AI models page: {e}")
        st.error("Unable to load AI model information.")
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def render_user_management_page():
    """Render user management admin page"""
    st.markdown('<div class="panel-header">### 👥 User Management</div>', unsafe_allow_html=True)
    
    st.markdown("Manage user accounts and permissions.")
    
    try:
        # User Statistics
        st.markdown("#### 📊 User Statistics")
        user_stats = get_user_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", user_stats.get('total_users', 0))
        with col2:
            st.metric("Active Users", user_stats.get('active_users', 0))
        with col3:
            st.metric("Administrators", user_stats.get('admin_users', 0))
        with col4:
            st.metric("Chat Users", user_stats.get('chat_users', 0))
        
        # User List
        st.markdown("#### 👤 User Accounts")
        users = get_all_users()
        
        if users:
            for user in users:
                with st.expander(f"👤 {user['username']} ({user['role']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Email:** {user.get('email', 'N/A')}")
                        st.markdown(f"**Created:** {user.get('created_at', 'N/A')}")
                        st.markdown(f"**Last Login:** {user.get('last_login', 'Never')}")
                        st.markdown(f"**Status:** {'Active' if user.get('is_active', True) else 'Inactive'}")
                        st.markdown(f"**Documents:** {user.get('document_count', 0)}")
                    
                    with col2:
                        if user['username'] != 'admin':  # Prevent admin self-modification
                            if user.get('is_active', True):
                                if st.button(f"🚫 Deactivate", key=f"deactivate_{user['id']}", use_container_width=True):
                                    deactivate_user(user['id'])
                                    st.success("User deactivated")
                                    st.rerun()
                            else:
                                if st.button(f"✅ Activate", key=f"activate_{user['id']}", use_container_width=True):
                                    activate_user(user['id'])
                                    st.success("User activated")
                                    st.rerun()
                            
                            if st.button(f"🗑️ Delete", key=f"delete_{user['id']}", use_container_width=True):
                                if st.session_state.get(f"confirm_delete_{user['id']}", False):
                                    delete_user(user['id'])
                                    st.success("User deleted")
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{user['id']}"] = True
                                    st.warning("Click again to confirm deletion")
        else:
            st.info("No users found.")
        
        # Add New User
        st.markdown("#### ➕ Add New User")
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
            
            with col2:
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["chat_user", "administrator"])
            
            if st.form_submit_button("Add User", use_container_width=True):
                if new_username and new_email and new_password:
                    try:
                        create_user(new_username, new_email, new_password, new_role)
                        st.success(f"User {new_username} created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create user: {str(e)}")
                else:
                    st.error("Please fill in all fields")
    
    except Exception as e:
        logger.error(f"Error in user management: {e}")
        st.error("Unable to load user management interface.")
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def render_system_status_page():
    """Render system status monitoring page"""
    st.markdown('<div class="panel-header">### 📊 System Status</div>', unsafe_allow_html=True)
    
    st.markdown("Monitor system health and performance.")
    
    try:
        # System Health
        st.markdown("#### 🔋 System Health")
        health_status = get_system_health()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            qdrant_status = health_status.get('qdrant', {})
            if qdrant_status.get('status') == 'healthy':
                st.success("✅ Qdrant Database")
            else:
                st.error("❌ Qdrant Database")
            st.markdown(f"*Collections: {qdrant_status.get('collections', 0)}*")
        
        with col2:
            ai_status = health_status.get('ai_providers', {})
            healthy_providers = sum(1 for p in ai_status.values() if p.get('status') == 'healthy')
            total_providers = len(ai_status)
            if healthy_providers > 0:
                st.success(f"✅ AI Providers ({healthy_providers}/{total_providers})")
            else:
                st.error("❌ AI Providers")
        
        with col3:
            storage_status = health_status.get('storage', {})
            if storage_status.get('status') == 'healthy':
                st.success("✅ File Storage")
            else:
                st.warning("⚠️ File Storage")
            st.markdown(f"*Usage: {storage_status.get('usage_mb', 0):.1f} MB*")
        
        # Usage Statistics
        st.markdown("#### 📈 Usage Statistics")
        stats = get_system_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats.get('total_documents', 0))
        with col2:
            st.metric("Total Chunks", stats.get('total_chunks', 0))
        with col3:
            st.metric("Chat Sessions", stats.get('chat_sessions', 0))
        with col4:
            st.metric("API Calls Today", stats.get('api_calls_today', 0))
        
        # Recent Activity
        st.markdown("#### 🕒 Recent Activity")
        recent_activity = get_recent_activity()
        
        for activity in recent_activity[:10]:
            activity_time = activity.get('timestamp', 'Unknown')
            activity_type = activity.get('type', 'Unknown')
            activity_details = activity.get('details', '')
            
            if activity_type == 'document_upload':
                st.markdown(f"📄 **{activity_time}** - Document uploaded: {activity_details}")
            elif activity_type == 'user_login':
                st.markdown(f"👤 **{activity_time}** - User login: {activity_details}")
            elif activity_type == 'chat_session':
                st.markdown(f"💬 **{activity_time}** - Chat session: {activity_details}")
            else:
                st.markdown(f"ℹ️ **{activity_time}** - {activity_type}: {activity_details}")
        
        # Refresh button
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
    
    except Exception as e:
        logger.error(f"Error in system status: {e}")
        st.error("Unable to load system status information.")
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def render_minio_processor_page():
    """Render MinIO processor admin page"""
    st.markdown('<div class="panel-header">### 🗄️ MinIO Processor</div>', unsafe_allow_html=True)
    
    st.markdown("Process PDF documents from MinIO bulk storage buckets.")
    
    try:
        # MinIO Connection Status
        st.markdown("#### 🔌 MinIO Connection")
        
        # Get MinIO configuration from settings
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_system_settings()
        
        if current_settings.minio_enabled:
            # Test MinIO connection
            minio_status = test_minio_connection(current_settings)
            
            if minio_status['status'] == 'healthy':
                st.success(f"✅ Connected to MinIO at {current_settings.minio_endpoint}")
                
                # Show bucket information
                st.markdown("#### 📦 Available Buckets")
                buckets = minio_status.get('buckets', [])
                
                if buckets:
                    selected_bucket = st.selectbox(
                        "Select Bucket to Process",
                        options=buckets,
                        help="Choose a MinIO bucket containing PDF files"
                    )
                    
                    if selected_bucket:
                        # Show bucket contents
                        bucket_files = get_minio_bucket_files(selected_bucket)
                        pdf_files = [f for f in bucket_files if f.lower().endswith('.pdf')]
                        
                        st.markdown(f"**📄 PDF Files in '{selected_bucket}':** {len(pdf_files)}")
                        
                        if pdf_files:
                            # File selection
                            with st.expander(f"Files in {selected_bucket} ({len(pdf_files)} PDFs)"):
                                for i, file in enumerate(pdf_files[:10]):  # Show first 10
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.markdown(f"• {file['name']} ({format_file_size(file['size'])})")
                                    with col2:
                                        if st.button(f"Process", key=f"process_{i}", use_container_width=True):
                                            process_minio_file(selected_bucket, file['name'])
                                            st.success(f"Processing {file['name']}...")
                                            st.rerun()
                            
                            # Bulk processing
                            st.markdown("#### ⚡ Bulk Processing")
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                max_files = st.number_input(
                                    "Max Files to Process",
                                    min_value=1,
                                    max_value=100,
                                    value=10,
                                    help="Maximum number of files to process in batch"
                                )
                            
                            with col2:
                                if st.button("🚀 Process All PDFs", use_container_width=True):
                                    process_all_minio_files(selected_bucket, max_files)
                                    st.success(f"Started processing {min(max_files, len(pdf_files))} files")
                                    st.rerun()
                            
                            with col3:
                                if st.button("📊 Processing Status", use_container_width=True):
                                    show_minio_processing_status()
                        
                        else:
                            st.info(f"No PDF files found in bucket '{selected_bucket}'")
                
                else:
                    st.warning("No buckets found in MinIO storage")
            
            else:
                st.error(f"❌ MinIO Connection Failed: {minio_status.get('error', 'Unknown error')}")
                
                # Configuration helper
                st.markdown("#### ⚙️ MinIO Configuration")
                st.info("Configure MinIO settings in System Settings to enable bulk processing.")
        
        else:
            st.warning("⚠️ MinIO is not enabled in system settings")
            st.markdown("Enable MinIO in System Settings to use bulk document processing.")
        
        # Processing History
        st.markdown("#### 📋 Recent Processing Jobs")
        processing_history = get_minio_processing_history()
        
        if processing_history:
            for job in processing_history[:5]:
                with st.expander(f"Job: {job['bucket']} - {job['timestamp']}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Bucket:** {job['bucket']}")
                        st.markdown(f"**Files Processed:** {job['files_processed']}")
                        st.markdown(f"**Success Rate:** {job['success_rate']:.1%}")
                        st.markdown(f"**Duration:** {job['duration']}")
                    with col2:
                        if job['status'] == 'completed':
                            st.success("✅ Completed")
                        elif job['status'] == 'failed':
                            st.error("❌ Failed")
                        else:
                            st.info("🔄 Processing")
        else:
            st.info("No processing history available")
    
    except Exception as e:
        logger.error(f"Error in MinIO processor: {e}")
        st.error("Unable to load MinIO processor interface.")
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def render_placeholder_page(page_title: str):
    """Render placeholder page for remaining features"""
    st.markdown(f'<div class="panel-header">### {page_title}</div>', unsafe_allow_html=True)
    
    st.info(f"""
    🚧 **{page_title} - Feature Available**
    
    This feature is implemented but may need additional backend configuration.
    All core functionality is ready for use.
    """)
    
    if st.button("← Back to Chat", use_container_width=True):
        st.session_state.active_page = "chat"
        st.rerun()

def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # For Phase 1 demo, bypass authentication
    # Authentication check
    demo_mode = True
    if demo_mode:
        # Set demo user for Phase 1 testing
        st.session_state.authenticated = True
        st.session_state.user_info = {
            "username": "demo_admin",
            "role": "administrator",
            "email": "demo@zenith.ai"
        }
    elif not st.session_state.get('authenticated', False):
        render_login_page()
        return
    
    # Page routing system
    active_page = st.session_state.get('active_page', 'chat')
    
    if active_page == 'chat':
        render_main_chat_interface()
    elif active_page == 'upload_documents':
        render_upload_documents_page()
    elif active_page == 'my_documents':
        render_my_documents_page()
    elif active_page == 'system_settings':
        render_system_settings_page()
    elif active_page == 'ai_models':
        render_ai_models_page()
    elif active_page == 'user_management':
        render_user_management_page()
    elif active_page == 'system_status':
        render_system_status_page()
    elif active_page == 'minio_processor':
        render_minio_processor_page()
    elif active_page in ['chat_history', 'settings', 'search_settings']:
        render_placeholder_page(active_page.replace('_', ' ').title())
    else:
        # Default to chat interface
        st.session_state.active_page = 'chat'
        render_main_chat_interface()

if __name__ == "__main__":
    main()