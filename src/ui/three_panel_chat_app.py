"""
Enhanced Three-Panel Chat Interface for Zenith PDF Chatbot
ChatGPT-inspired clean professional design with preserved functionality
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
    page_title="Zenith AI Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide default sidebar for custom layout
)

# Professional CSS styling with proper gradient background
st.markdown("""
<style>
/* ===== PROFESSIONAL ZENITH AI INTERFACE ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body {
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
    margin: 0;
    padding: 0;
    height: 100vh;
    width: 100vw;
    overflow-x: hidden;
}

:root {
    /* Professional Blue Gradient System */
    --primary-blue: #1a2b3c;
    --primary-blue-dark: #0d1a2b;
    --primary-blue-light: #2d4a5a;
    --accent-blue: #3b82f6;
    --accent-blue-light: #60a5fa;
    
    /* Professional Backgrounds */
    --bg-main: #ffffff;
    --bg-panel: rgba(255, 255, 255, 0.95);
    --bg-panel-dark: rgba(26, 43, 60, 0.9);
    --bg-secondary: rgba(255, 255, 255, 0.98);
    --bg-accent: rgba(248, 250, 252, 0.95);
    --bg-overlay: rgba(26, 43, 60, 0.1);
    
    /* Professional Typography */
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --text-muted: #94a3b8;
    --text-light: #f8fafc;
    --text-white: #ffffff;
    
    /* Professional Shadows & Effects */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    --glass-effect: backdrop-filter: blur(10px);
    
    /* Professional Spacing */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-5: 1.25rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
    --space-12: 3rem;
    
    /* Professional Borders */
    --radius: 0.375rem;
    --radius-lg: 0.5rem;
    --radius-xl: 0.75rem;
    --radius-full: 9999px;
    --border-width: 1px;
    
    /* Professional Colors */
    --gray-50: #f8fafc;
    --gray-100: #f1f5f9;
    --gray-200: #e2e8f0;
    --gray-300: #cbd5e1;
    --gray-400: #94a3b8;
    --gray-500: #64748b;
    --gray-600: #475569;
    --gray-700: #334155;
    --gray-800: #1e293b;
    --gray-900: #0f172a;
    
    /* Professional Button Colors */
    --button-primary: #1a2b3c;
    --button-primary-hover: #0d1a2b;
    --button-secondary: #f8fafc;
    --button-secondary-hover: #f1f5f9;
    
    /* Professional Message Colors */
    --message-hover: rgba(0, 0, 0, 0.02);
}

/* Professional Base Setup */
.stApp {
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    min-height: 100vh !important;
    width: 100vw !important;
    overflow-x: hidden !important;
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    margin: 0 !important;
    width: 100vw !important;
    min-height: 100vh !important;
}

/* Hide Streamlit Elements */
header, footer, .stDeployButton, .stDecoration {
    display: none !important;
}

[data-testid="stSidebar"] {
    display: none !important;
}

/* Professional Three-Panel Layout */
.three-panel-container {
    display: flex !important;
    height: 100vh !important;
    width: 100vw !important;
    margin: 0 !important;
    padding: 0 !important;
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
}

/* Professional Left Panel */
.left-panel {
    width: 320px;
    min-width: 320px;
    background: var(--bg-panel);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}

.left-panel-header {
    padding: var(--space-6);
    background: rgba(26, 43, 60, 0.9);
    color: var(--text-light);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}

.left-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-4);
    background: rgba(255, 255, 255, 0.98);
}

/* Professional Center Panel */
.center-panel {
    flex: 1;
    background: rgba(255, 255, 255, 0.95);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    backdrop-filter: blur(10px);
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.chat-header {
    padding: var(--space-6);
    background: rgba(255, 255, 255, 0.95);
    border-bottom: 1px solid var(--gray-200);
    backdrop-filter: blur(10px);
    text-align: center;
}

.chat-title {
    color: var(--primary-blue);
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: var(--space-2);
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.chat-subtitle {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-6);
    background: rgba(255, 255, 255, 0.98);
}

.chat-input-container {
    padding: var(--space-6);
    background: rgba(255, 255, 255, 0.95);
    border-top: 1px solid var(--gray-200);
    backdrop-filter: blur(10px);
}

.chat-input-wrapper {
    max-width: 768px;
    margin: 0 auto;
    position: relative;
}

/* Professional Right Panel */
.right-panel {
    width: 320px;
    min-width: 320px;
    background: var(--bg-panel);
    backdrop-filter: blur(10px);
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}

.right-panel-header {
    padding: var(--space-6);
    background: rgba(26, 43, 60, 0.9);
    color: var(--text-light);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    backdrop-filter: blur(10px);
}

.right-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-4);
    background: rgba(255, 255, 255, 0.98);
}

/* Professional Login Page - Fixed overlay issue */
.login-container {
    min-height: 100vh;
    width: 100vw;
    background: linear-gradient(to bottom, #1a2b3c, #0d1a2b) !important;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-6);
    /* Removed position: fixed and z-index to prevent overlay issues */
}

.login-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    padding: var(--space-8);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-xl);
    border: 1px solid rgba(255, 255, 255, 0.2);
    width: 100%;
    max-width: 420px;
}

.login-title {
    text-align: center;
    font-size: 1.875rem;
    font-weight: 700;
    color: var(--primary-blue);
    margin-bottom: var(--space-8);
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Professional ChatGPT-Style Messages */
.message-container {
    display: flex;
    gap: var(--space-4);
    margin-bottom: var(--space-6);
    align-items: flex-start;
    padding: var(--space-4);
    border-radius: var(--radius-lg);
    transition: background-color 0.2s ease;
}

.message-container:hover {
    background: var(--message-hover);
}

.message-avatar {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    font-weight: 600;
}

.user-avatar {
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    color: var(--text-white);
}

.ai-avatar {
    background: linear-gradient(135deg, var(--gray-800), var(--gray-600));
    color: var(--text-white);
}

.message-content {
    flex: 1;
    min-width: 0;
    font-size: 15px;
    line-height: 1.6;
    color: var(--text-primary);
}

.message-user, .message-ai {
    background: transparent !important;
    color: var(--text-primary) !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    box-shadow: none !important;
}

/* Professional Session Items */
.session-item {
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-2);
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
    background: rgba(255, 255, 255, 0.8);
}

.session-item:hover {
    background: rgba(59, 130, 246, 0.1);
    border-color: var(--accent-blue-light);
    box-shadow: var(--shadow-md);
}

.session-item.active {
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    border-color: var(--primary-blue);
    color: var(--text-white);
    box-shadow: var(--shadow-lg);
}

.session-title {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 14px;
    margin-bottom: var(--space-1);
}

.session-item.active .session-title {
    color: var(--text-white);
}

.session-meta {
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 500;
}

.session-item.active .session-meta {
    color: rgba(255, 255, 255, 0.9);
}

/* Professional Buttons */
.chat-btn {
    background: linear-gradient(135deg, var(--primary-blue), var(--accent-blue));
    color: var(--text-white);
    border: none;
    border-radius: var(--radius-lg);
    padding: var(--space-3) var(--space-6);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: var(--shadow-md);
}

.chat-btn:hover {
    background: linear-gradient(135deg, var(--primary-blue-dark), var(--primary-blue));
    box-shadow: var(--shadow-lg);
    transform: translateY(-1px);
}

.chat-btn-secondary {
    background: rgba(255, 255, 255, 0.9);
    color: var(--primary-blue);
    border: 1px solid var(--gray-300);
    backdrop-filter: blur(10px);
}

.chat-btn-secondary:hover {
    background: rgba(255, 255, 255, 1);
    border-color: var(--accent-blue);
    box-shadow: var(--shadow-md);
}

/* Professional Empty State */
.empty-state {
    text-align: center;
    padding: var(--space-12) var(--space-8);
    color: var(--text-secondary);
    background: rgba(255, 255, 255, 0.8);
    border-radius: var(--radius-xl);
    margin: var(--space-6);
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
}

/* Professional Typing Indicator */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: var(--space-4) var(--space-6);
    color: var(--text-secondary);
    font-size: 14px;
    font-weight: 500;
}

.typing-dots {
    display: flex;
    gap: 6px;
}

.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: var(--radius-full);
    background: var(--accent-blue);
    animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
    0%, 60%, 100% { 
        opacity: 0.3; 
        transform: scale(0.8);
    }
    30% { 
        opacity: 1;
        transform: scale(1);
    }
}

/* Professional Responsive Design */
@media (max-width: 1440px) {
    .left-panel, .right-panel {
        width: 300px;
        min-width: 300px;
    }
}

@media (max-width: 1200px) {
    .left-panel, .right-panel {
        width: 280px;
        min-width: 280px;
    }
}

@media (max-width: 1024px) {
    .three-panel-container {
        flex-direction: column;
        height: 100vh;
    }
    
    .left-panel, .right-panel {
        width: 100%;
        min-width: 100%;
        height: 180px;
        flex: none;
    }
    
    .center-panel {
        flex: 1;
        min-height: 0;
    }
}

@media (max-width: 768px) {
    .left-panel, .right-panel {
        display: none;
    }
    
    .center-panel {
        width: 100vw;
        height: 100vh;
    }
    
    .three-panel-container {
        width: 100vw;
        height: 100vh;
    }
}

/* Professional Streamlit Component Overrides */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: var(--radius-lg) !important;
    border: 2px solid var(--gray-300) !important;
    background: rgba(255, 255, 255, 0.95) !important;
    font-size: 15px !important;
    color: var(--text-primary) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s ease !important;
    padding: 16px 16px !important;
    min-height: 44px !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary-blue) !important;
    box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1) !important;
    outline: none !important;
}

.stButton > button {
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
    padding: var(--space-3) var(--space-4) !important;
    min-height: 44px !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light)) !important;
    color: var(--text-light) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(30, 64, 175, 0.25) !important;
    font-weight: 600 !important;
    border-radius: var(--radius-lg) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--primary-blue-dark), var(--primary-blue)) !important;
    box-shadow: 0 6px 20px rgba(30, 64, 175, 0.35) !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="secondary"] {
    background: var(--button-secondary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--gray-300) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: var(--button-secondary-hover) !important;
    border-color: var(--gray-400) !important;
}

.stSelectbox > div > div {
    border-radius: var(--radius) !important;
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(10px) !important;
}

.stTabs > div > div > div > div {
    border-radius: var(--radius) !important;
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(10px) !important;
}

/* File upload styling */
.stFileUploader > div > div {
    border-radius: var(--radius-lg) !important;
    border-style: dashed !important;
    border-color: var(--accent-blue) !important;
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Link accessibility - minimum 44px touch targets */
a {
    min-height: 44px !important;
    display: inline-flex !important;
    align-items: center !important;
    padding: 8px 4px !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
}

a:hover {
    text-decoration: underline !important;
}

/* Admin panel styling */
.admin-section {
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 16px;
    backdrop-filter: blur(15px);
    box-shadow: var(--shadow-sm);
}

.admin-section h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
}

.stats-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid var(--glass-border);
    font-size: 14px;
}

.stats-item:last-child {
    border-bottom: none;
}

.stats-label {
    color: var(--text-secondary);
    font-weight: 500;
}

.stats-value {
    color: var(--text-primary);
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

class ZenithThreePanelApp:
    """Three-panel ChatGPT-inspired Streamlit application"""
    
    def __init__(self):
        """Initialize the application"""
        self.initialize_session_state()
        self.initialize_auth()
    
    def get_logo_base64(self):
        """Get base64 encoded logo image"""
        try:
            import base64
            logo_path = Path(__file__).parent.parent.parent / "images" / "logo.PNG"
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            else:
                # Fallback: create a simple colored rectangle if logo not found
                return ""
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            return ""
        
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        # Authentication state - ensure login is required
        init_auth_session()
        
        # Force authentication check - ensure user must login
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        
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
            
        # UI state
        if 'typing_indicator' not in st.session_state:
            st.session_state.typing_indicator = False
        if 'current_message_id' not in st.session_state:
            st.session_state.current_message_id = None
    
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
                st.session_state.auth_manager = None
                st.stop()

    def render_login_page(self):
        """Render clean professional login page"""
        # Logo and title section
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Logo
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="data:image/png;base64,{}" alt="Zenith AI Company Logo" style="
                    width: 200px; 
                    height: auto; 
                    margin: 0 auto 20px auto;
                    display: block;
                    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
                " />
                <h1 style="
                    color: white; 
                    margin: 0;
                    font-size: 24px; 
                    font-weight: 600;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">Zenith AI</h1>
                <p style="
                    color: rgba(255,255,255,0.8); 
                    margin: 8px 0 0 0;
                    font-size: 16px;
                ">Intelligent Document Chat System</p>
            </div>
            """.format(self.get_logo_base64()), unsafe_allow_html=True)
            
            # Login form in a styled container (no margin-bottom to remove white space)
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                padding: 5px;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
            """, unsafe_allow_html=True)
            
            st.markdown("### Welcome Back")
            st.markdown("Sign in to your account")
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "Email or Username", 
                    key="login_username", 
                    placeholder="Enter your email or username"
                )
                
                password = st.text_input(
                    "Password", 
                    type="password", 
                    key="login_password", 
                    placeholder="Enter your password"
                )
                
                col_rem, col_forgot = st.columns([1, 1])
                with col_rem:
                    remember_me = st.checkbox("Remember Me")
                with col_forgot:
                    st.markdown('<div style="text-align: right; margin-top: 8px;"><a href="#" style="color: #3b82f6; text-decoration: none; font-size: 14px;">Forgot Password?</a></div>', unsafe_allow_html=True)
                
                if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                    if username and password:
                        try:
                            auth_manager = st.session_state.auth_manager
                            if auth_manager:
                                login_request = UserLoginRequest(username_or_email=username, password=password)
                                success, message, token = auth_manager.login_user(
                                    login_request, 
                                    ip_address="127.0.0.1", 
                                    user_agent="Streamlit App"
                                )
                                
                                if success:
                                    st.session_state.authenticated = True
                                    st.session_state.user_info = {
                                        'username': username,
                                        'token': token,
                                        'id': message.get('user_id') if isinstance(message, dict) else None,
                                        'role': message.get('role', 'user') if isinstance(message, dict) else 'user'
                                    }
                                    st.rerun()
                                else:
                                    st.error(f"Login failed: {message}")
                            else:
                                st.error("Authentication system not available")
                        except Exception as e:
                            st.error(f"Login error: {str(e)}")
                            logger.error(f"Login error: {e}")
                    else:
                        st.warning("Please enter both username and password")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Additional links
            st.markdown(
                '<div style="text-align: center; color: rgba(255,255,255,0.8);">'
                'Don\'t have an account? '
                '<a href="#" style="color: #60a5fa; text-decoration: none;">Sign up here</a>'
                '</div>', 
                unsafe_allow_html=True
            )

    def render_login_form(self):
        """Render enhanced login form"""
        
        with st.form("login_form"):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 24px;">
                <h3 style="
                    color: #1e293b; 
                    font-size: 20px; 
                    font-weight: 600; 
                    margin: 0;
                ">Welcome back</h3>
                <p style="
                    color: #64748b; 
                    font-size: 14px; 
                    margin: 8px 0 0 0;
                ">Sign in to your account</p>
            </div>
            """, unsafe_allow_html=True)
            
            email = st.text_input("Email", key="login_email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                if email and password:
                    try:
                        auth_manager = st.session_state.auth_manager
                        if auth_manager:
                            login_request = UserLoginRequest(username_or_email=email, password=password)
                            success, message, token = auth_manager.login_user(
                                login_request, 
                                ip_address="127.0.0.1", 
                                user_agent="Streamlit App"
                            )
                            
                            if success:
                                st.session_state.authenticated = True
                                st.session_state.user_token = token
                                
                                # Get user info from token
                                user = auth_manager.get_current_user(token)
                                if user:
                                    st.session_state.user_info = {
                                        'id': user.id,
                                        'username': user.username,
                                        'email': user.email,
                                        'role': user.role.value,
                                        'full_name': user.full_name
                                    }
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error(message or 'Login failed')
                        else:
                            st.error("Authentication system not available")
                    except Exception as e:
                        st.error(f"Login error: {str(e)}")
                        logger.error(f"Login error: {e}")
                else:
                    st.warning("Please enter both email and password")

    def render_registration_form(self):
        """Render enhanced registration form"""
        
        with st.form("registration_form"):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 24px;">
                <h3 style="
                    color: #1e293b; 
                    font-size: 20px; 
                    font-weight: 600; 
                    margin: 0;
                ">Create Account</h3>
                <p style="
                    color: #64748b; 
                    font-size: 14px; 
                    margin: 8px 0 0 0;
                ">Start your journey with Zenith AI</p>
            </div>
            """, unsafe_allow_html=True)
            
            email = st.text_input("Email", key="reg_email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", key="reg_password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password", placeholder="Confirm your password")
            
            if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                        return
                    
                    try:
                        auth_manager = st.session_state.auth_manager
                        if auth_manager:
                            # Default role is chat_user, first user becomes administrator
                            user_count = auth_manager.get_user_count()
                            role = UserRole.ADMINISTRATOR if user_count == 0 else UserRole.CHAT_USER
                            
                            reg_request = UserRegistrationRequest(
                                username=email.split('@')[0],  # Use email prefix as username
                                email=email, 
                                password=password,
                                role=role.value if hasattr(role, 'value') else role
                            )
                            success, message, user = auth_manager.register_user(
                                reg_request, 
                                ip_address="127.0.0.1"
                            )
                            
                            if success:
                                st.success("Account created successfully! Please sign in.")
                                if user_count == 0:
                                    st.info("As the first user, you have been granted administrator privileges.")
                            else:
                                st.error(message or 'Registration failed')
                        else:
                            st.error("Authentication system not available")
                    except Exception as e:
                        st.error(f"Registration error: {str(e)}")
                        logger.error(f"Registration error: {e}")
                else:
                    st.warning("Please fill in all fields")

    def render_three_panel_layout(self):
        """Render the main three-panel layout"""
        # Initialize user components if needed
        if not st.session_state.vector_store:
            user_id = st.session_state.user_info.get('id')
            st.session_state.vector_store = UserVectorStore(user_id=user_id)
            st.session_state.chat_engine = EnhancedChatEngine(
                user_id=user_id,
                vector_store=st.session_state.vector_store
            )

        # Professional three-panel HTML structure
        st.markdown('<div class="three-panel-container">', unsafe_allow_html=True)
        
        # Render each panel
        self.render_left_panel()
        self.render_center_panel()
        self.render_right_panel()
        
        st.markdown('</div>', unsafe_allow_html=True)

    def render_left_panel(self):
        """Render left panel with recent sessions"""
        st.markdown('<div class="left-panel">', unsafe_allow_html=True)
        
        # Panel header
        st.markdown("""
        <div class="left-panel-header">
            <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: var(--text-primary);">💬 Recent Chats</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Panel content
        st.markdown('<div class="left-panel-content">', unsafe_allow_html=True)
        
        # New Chat button
        if st.button("🆕 New Chat", key="new_chat_btn", use_container_width=True, type="primary"):
            try:
                self.start_new_chat_session()
                st.rerun()
            except Exception as e:
                st.error(f"Error starting new chat: {str(e)}")
                logger.error(f"New chat error: {e}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Recent sessions
        try:
            user_id = st.session_state.user_info.get('id')
            if st.session_state.chat_history_manager and user_id:
                recent_sessions = st.session_state.chat_history_manager.get_user_sessions(user_id, limit=5)
                
                if recent_sessions:
                    for i, session in enumerate(recent_sessions):
                        try:
                            # Create session display
                            display_title = getattr(session, 'title', f'Session {i+1}')
                            if len(display_title) > 25:
                                display_title = display_title[:22] + "..."
                            
                            # Get message count
                            try:
                                msg_count = session.get_message_count()
                            except:
                                msg_count = len(getattr(session, 'messages', []))
                            
                            # Session button
                            current_session_id = st.session_state.current_session.session_id if st.session_state.current_session else None
                            is_active = current_session_id == session.session_id
                            
                            button_key = f"session_{session.session_id}_{i}"
                            if st.button(
                                f"📄 {display_title}\n{msg_count} messages", 
                                key=button_key,
                                use_container_width=True,
                                type="primary" if is_active else "secondary"
                            ):
                                try:
                                    self.load_chat_session(session)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error loading session: {str(e)}")
                                    logger.error(f"Session load error: {e}")
                                    
                        except Exception as e:
                            logger.error(f"Error rendering session {i}: {e}")
                            continue
                            
                else:
                    st.markdown("""
                    <div style="text-align: center; color: var(--text-secondary); font-size: 14px; padding: 20px 0;">
                        No recent chats<br>
                        <small>Start a new conversation!</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
        except Exception as e:
            st.error("Error loading chat history")
            logger.error(f"Chat history error: {e}")
        
        # Minimal document status
        if st.session_state.get('documents_processed', False) and st.session_state.get('file_stats'):
            stats = st.session_state.file_stats
            file_count = len(stats.get('processed_files', []))
            st.markdown(f"""
            <div style="
                margin-top: 20px; 
                padding: 12px; 
                background: rgba(66, 153, 225, 0.1); 
                border-radius: var(--radius); 
                border-left: 3px solid var(--accent-blue);
                font-size: 13px;
                color: var(--text-secondary);
            ">
                📚 {file_count} document{'s' if file_count != 1 else ''} ready
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    def render_center_panel(self):
        """Render center chat panel"""
        st.markdown('<div class="center-panel">', unsafe_allow_html=True)
        
        # Clean chat header
        st.markdown("""
        <div class="chat-header">
            <div class="chat-title">🤖 Zenith AI</div>
            <div class="chat-subtitle">Intelligent Document Chat System</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages area
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        
        # Display messages or empty state
        if st.session_state.current_session and st.session_state.current_session.messages:
            self.render_chat_messages()
        else:
            self.render_empty_state()
        
        # Typing indicator
        if st.session_state.get('typing_indicator', False):
            st.markdown("""
            <div class="typing-indicator">
                <span>Zenith AI is typing</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input
        self.render_chat_input()
        
        st.markdown('</div>', unsafe_allow_html=True)

    def render_chat_messages(self):
        """Render simple clean chat messages"""
        for message in st.session_state.current_session.messages:
            if message.role == 'user':
                st.markdown(f"""
                <div class="message-user">
                    👤 **You:** {message.content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-ai">
                    🤖 **Zenith AI:** {message.content}
                </div>
                """, unsafe_allow_html=True)

    def render_empty_state(self):
        """Render clean empty state without extra buttons"""
        st.markdown("""
        <div class="empty-state">
            <h3 style="color: var(--text-primary); font-size: 24px; margin-bottom: 16px; font-weight: 600;">
                How can I help you today?
            </h3>
            <p style="margin-bottom: 32px; font-size: 16px; line-height: 1.6;">
                Upload documents in the settings panel and start chatting to get intelligent answers from your content.
            </p>
            <div style="color: var(--text-muted); font-size: 14px;">
                💡 Try asking questions about your documents once uploaded
            </div>
        </div>
        """, unsafe_allow_html=True)

    def render_chat_input(self):
        """Render ChatGPT-style chat input area"""
        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        st.markdown('<div class="chat-input-wrapper">', unsafe_allow_html=True)
        
        # Create form to handle Enter key properly
        with st.form(key="chat_input_form", clear_on_submit=True):
            # Single column layout for cleaner appearance
            user_input = st.text_area(
                "Message", 
                placeholder="Type a message...",
                height=60,
                key="user_message_input",
                label_visibility="collapsed"
            )
            
            # Hidden submit button (we'll use custom styling)
            send_clicked = st.form_submit_button("Send", type="primary")
            
            if send_clicked and user_input.strip():
                self.handle_user_message(user_input.strip())
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    def render_right_panel(self):
        """Render right panel with settings and admin controls"""
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        
        # Panel header with logo and sign out
        user_info = st.session_state.get('user_info', {})
        st.markdown(f"""
        <div class="right-panel-header">
            <div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-primary);">
                    👤 {user_info.get('email', 'User')}
                </div>
                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                    {user_info.get('role', 'chat_user').replace('_', ' ').title()}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Sign out button
        if st.button("🚪 Sign Out", key="signout_btn", use_container_width=True, type="secondary"):
            logout_user_session()
            st.rerun()
        
        st.markdown('<div class="right-panel-content">', unsafe_allow_html=True)
        
        # Admin panel for administrators
        if user_info.get('role') == 'administrator':
            self.render_admin_controls()
        
        # User settings section
        self.render_user_settings()
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    def render_admin_controls(self):
        """Render admin controls in right panel"""
        st.markdown("### ⚙️ Admin Controls")
        
        # System status
        with st.expander("📊 System Status", expanded=False):
            try:
                # Quick system info
                qdrant_client = get_qdrant_client().get_client()
                collections = qdrant_client.get_collections().collections
                st.markdown(f"**Collections:** {len(collections)}")
                
                # User stats
                if st.session_state.auth_manager:
                    user_count = st.session_state.auth_manager.get_user_count()
                    st.markdown(f"**Total Users:** {user_count}")
                
            except Exception as e:
                st.error(f"Error loading system status: {str(e)}")
        
        # User management
        with st.expander("👥 User Management", expanded=False):
            try:
                if st.session_state.auth_manager:
                    users = st.session_state.auth_manager.get_all_users()
                    if users:
                        for user in users[:5]:  # Limit for space
                            st.markdown(f"• {user.email} ({user.role.value})")
                    else:
                        st.markdown("No users found")
            except Exception as e:
                st.error(f"Error loading users: {str(e)}")
        
        # Advanced admin controls
        if st.button("🔧 Full Admin Panel", key="full_admin_btn", use_container_width=True):
            st.session_state.show_admin_panel = True
            st.rerun()

    def render_user_settings(self):
        """Render user settings section"""
        st.markdown("### ⚙️ Settings")
        
        # File upload section
        with st.expander("📁 Upload Documents", expanded=False):
            uploaded_files = st.file_uploader(
                "Choose PDF files",
                type=['pdf'],
                accept_multiple_files=True,
                key="document_uploader"
            )
            
            if uploaded_files:
                if st.button("Process Documents", key="process_docs_btn", type="primary", use_container_width=True):
                    self.process_uploaded_files(uploaded_files)
        
        # Chat preferences
        with st.expander("💬 Chat Preferences", expanded=False):
            use_rag = st.checkbox("Use document search (RAG)", value=True, key="use_rag_setting")
            filter_user_only = st.checkbox("Search only my documents", value=True, key="filter_user_setting")
            
            st.session_state.chat_use_rag = use_rag
            st.session_state.chat_filter_user_only = filter_user_only

    def handle_user_message(self, user_input: str):
        """Handle user message input"""
        try:
            # Create new session if none exists
            if not st.session_state.current_session:
                self.start_new_chat_session()
            
            # Add user message
            user_message = ChatMessage(
                role='user',
                content=user_input,
                timestamp=datetime.now()
            )
            st.session_state.current_session.add_message(user_message)
            
            # Show typing indicator
            st.session_state.typing_indicator = True
            st.rerun()
            
            # Get AI response
            use_rag = st.session_state.get('chat_use_rag', True)
            filter_user_only = st.session_state.get('chat_filter_user_only', True)
            
            # Process with chat engine
            if st.session_state.chat_engine:
                response = st.session_state.chat_engine.chat(
                    user_input,
                    use_rag=use_rag,
                    user_filter=filter_user_only
                )
                
                # Add AI response
                ai_message = ChatMessage(
                    role='assistant',
                    content=response.get('answer', 'Sorry, I could not process your request.'),
                    timestamp=datetime.now()
                )
                st.session_state.current_session.add_message(ai_message)
                
                # Save session
                st.session_state.chat_history_manager.save_session(st.session_state.current_session)
            
            # Hide typing indicator
            st.session_state.typing_indicator = False
            st.rerun()
            
        except Exception as e:
            st.session_state.typing_indicator = False
            st.error(f"Error processing message: {str(e)}")
            logger.error(f"Message processing error: {e}")

    def start_new_chat_session(self):
        """Start a new chat session"""
        try:
            user_id = st.session_state.user_info.get('id')
            if user_id and st.session_state.chat_history_manager:
                # Create new session
                session_id = str(uuid.uuid4())
                new_session = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    title="New Chat",
                    created_at=datetime.now()
                )
                
                # Set as current session
                st.session_state.current_session = new_session
                
                logger.info(f"Started new chat session: {session_id}")
                
        except Exception as e:
            st.error(f"Error starting new chat session: {str(e)}")
            logger.error(f"New session error: {e}")

    def load_chat_session(self, session: ChatSession):
        """Load an existing chat session"""
        try:
            # Load full session with messages
            full_session = st.session_state.chat_history_manager.get_session(session.session_id)
            if full_session:
                st.session_state.current_session = full_session
                logger.info(f"Loaded chat session: {session.session_id}")
            else:
                st.error("Could not load chat session")
                
        except Exception as e:
            st.error(f"Error loading chat session: {str(e)}")
            logger.error(f"Session load error: {e}")

    def handle_suggestion_click(self, suggestion: str):
        """Handle prompt suggestion click"""
        # Remove emoji and use as message
        clean_suggestion = suggestion.split(' ', 1)[1] if ' ' in suggestion else suggestion
        self.handle_user_message(clean_suggestion)

    def process_uploaded_files(self, uploaded_files):
        """Process uploaded PDF files"""
        try:
            if not st.session_state.pdf_processor:
                st.session_state.pdf_processor = PDFProcessor()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            processed_files = []
            total_files = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / total_files)
                
                # Save uploaded file temporarily
                temp_path = Path(f"/tmp/{uploaded_file.name}")
                temp_path.write_bytes(uploaded_file.getvalue())
                
                # Process the file
                result = st.session_state.pdf_processor.process_pdf(
                    file_path=temp_path,
                    user_id=st.session_state.user_info.get('id')
                )
                
                if result:
                    processed_files.append({
                        'name': uploaded_file.name,
                        'size': len(uploaded_file.getvalue()),
                        'pages': result.get('pages', 0),
                        'chunks': result.get('chunks', 0)
                    })
                
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()
            
            # Update session state
            st.session_state.processed_files = processed_files
            st.session_state.documents_processed = True
            st.session_state.file_stats = {
                'processed_files': processed_files,
                'total_documents': sum(f.get('pages', 0) for f in processed_files),
                'total_chunks': sum(f.get('chunks', 0) for f in processed_files)
            }
            
            status_text.success(f"Successfully processed {len(processed_files)} files!")
            progress_bar.progress(1.0)
            
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            logger.error(f"File processing error: {e}")

    def render_full_admin_panel(self):
        """Render full admin panel (simplified version)"""
        st.markdown("## ⚙️ Administrator Panel")
        
        if st.button("← Back to Chat", key="back_to_chat"):
            st.session_state.show_admin_panel = False
            st.rerun()
        
        # Simplified admin tabs
        tab1, tab2, tab3 = st.tabs(["System Settings", "User Management", "System Status"])
        
        with tab1:
            st.markdown("### System Configuration")
            # Add key system settings here
            st.info("System settings panel - implement based on original enhanced_streamlit_app.py")
        
        with tab2:
            st.markdown("### User Management")
            # Add user management here
            try:
                if st.session_state.auth_manager:
                    users = st.session_state.auth_manager.get_all_users()
                    if users:
                        for user in users:
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.text(user.email)
                            with col2:
                                st.text(user.role.value)
                            with col3:
                                st.button("Edit", key=f"edit_{user.id}", disabled=True)
                    else:
                        st.info("No users found")
            except Exception as e:
                st.error(f"Error loading users: {str(e)}")
        
        with tab3:
            st.markdown("### System Status")
            # Add system status here
            try:
                qdrant_client = get_qdrant_client().get_client()
                collections = qdrant_client.get_collections().collections
                st.metric("Collections", len(collections))
                
                if st.session_state.auth_manager:
                    user_count = st.session_state.auth_manager.get_user_count()
                    st.metric("Total Users", user_count)
                    
            except Exception as e:
                st.error(f"Error loading system status: {str(e)}")

    def run(self):
        """Run the main application"""
        # Ensure auth is properly initialized
        self.initialize_auth()
        
        # Check authentication
        if not st.session_state.get('authenticated', False):
            self.render_login_page()
            return
        
        # Check if full admin panel should be shown
        if st.session_state.get('show_admin_panel', False):
            user_info = st.session_state.get('user_info', {})
            if user_info.get('role') == 'administrator':
                self.render_full_admin_panel()
                return
            else:
                st.session_state.show_admin_panel = False
        
        # Render main three-panel interface
        self.render_three_panel_layout()


def main():
    """Main entry point"""
    app = ZenithThreePanelApp()
    app.run()


if __name__ == "__main__":
    main()