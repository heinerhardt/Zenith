import streamlit as st
import base64
from pathlib import Path
from datetime import datetime, timedelta
import time

def load_logo():
    """Load logo if available"""
    logo_path = Path("images/logo.PNG")
    if logo_path.exists():
        try:
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            return None
    return None

def apply_custom_css():
    """Apply clean custom CSS"""
    logo_b64 = load_logo()
    
    css = f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Color Variables */
    :root {{
        --pale-cyan: #8ed1fc;
        --vivid-cyan: #0693e3;
        --gradient: linear-gradient(135deg, #8ed1fc 0%, #0693e3 100%);
        --white: #ffffff;
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-300: #d1d5db;
        --gray-400: #9ca3af;
        --gray-500: #6b7280;
        --gray-600: #4b5563;
        --gray-700: #374151;
        --gray-800: #1f2937;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* Main app styling with sophisticated background */
    .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, 
            rgba(248, 250, 252, 0.95) 0%,
            rgba(241, 245, 249, 0.90) 25%,
            rgba(226, 232, 240, 0.85) 50%,
            rgba(203, 213, 225, 0.80) 75%,
            rgba(148, 163, 184, 0.75) 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }}
    
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 20%, rgba(142, 209, 252, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(6, 147, 227, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 40% 60%, rgba(248, 250, 252, 0.4) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }}
    
    /* Ensure content is above background */
    .main .block-container {{
        position: relative;
        z-index: 1;
    }}
    
    /* Header styling with blue gradient */
    .app-header {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: var(--gradient);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 20px rgba(6, 147, 227, 0.3);
        z-index: 1000;
        height: 80px;
        display: flex;
        align-items: center;
        padding: 0 2rem;
    }}
    
    .header-logo {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex-shrink: 0;
    }}
    
    .header-logo img {{
        height: 45px;
        max-width: 150px;
        object-fit: contain;
    }}
    
    .header-center {{
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    
    .app-title {{
        font-size: 1.75rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-align: center;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }}
    
    .app-subtitle {{
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
        text-align: center;
        font-weight: 500;
    }}
    
    /* Adjust main content for header */
    .main .block-container {{
        padding-top: 100px !important;
        position: relative;
        z-index: 1;
    }}
    
    /* Remove old logo section styles */
    .logo-section {{
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        padding: 1rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    
    .section-title {{
        color: var(--gray-700);
        font-weight: 600;
        font-size: 1rem;
        margin: 0;
        background: var(--gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Chat message styling - like the reference image */
    .chat-message {{
        margin: 1.5rem 0;
        width: 100%;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }}
    
    .chat-message.user {{
        flex-direction: row-reverse;
        justify-content: flex-start;
    }}
    
    .message-avatar {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.875rem;
        font-weight: 600;
        flex-shrink: 0;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background-size: cover;
        background-position: center;
    }}
    
    .user-avatar {{
        background: var(--gradient);
        color: white;
        box-shadow: 0 4px 12px rgba(6, 147, 227, 0.3);
    }}
    
    .assistant-avatar {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }}
    
    .message-wrapper {{
        flex: 1;
        max-width: 65%;
        display: flex;
        flex-direction: column;
    }}
    
    .message-header {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }}
    
    .message-sender {{
        font-weight: 600;
        font-size: 0.875rem;
        color: var(--gray-700);
    }}
    
    .message-content {{
        padding: 1rem 1.25rem;
        border-radius: 1.25rem;
        line-height: 1.6;
        font-size: 0.95rem;
        word-wrap: break-word;
        position: relative;
    }}
    
    .user-message {{
        background: var(--gradient);
        color: white;
        border-radius: 1.5rem 1.5rem 0.5rem 1.5rem;
        box-shadow: 
            0 8px 25px rgba(6, 147, 227, 0.3),
            0 3px 10px rgba(6, 147, 227, 0.2);
        margin-left: auto;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    
    .assistant-message {{
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.95) 0%,
            rgba(248, 250, 252, 0.9) 100%);
        color: var(--gray-800);
        border: 1px solid rgba(229, 231, 235, 0.4);
        border-radius: 1.5rem 1.5rem 1.5rem 0.5rem;
        box-shadow: 
            0 4px 20px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(15px);
    }}
    
    .message-time {{
        font-size: 0.75rem;
        color: var(--gray-400);
        margin-top: 0.5rem;
        text-align: right;
    }}
    
    .chat-message.user .message-time {{
        text-align: left;
    }}
    
    /* User message name styling */
    .chat-message.user .message-sender {{
        color: var(--vivid-cyan);
        font-weight: 600;
    }}
    
    .chat-message .message-sender {{
        color: var(--gray-600);
        font-weight: 600;
    }}
    
    /* Professional chat interface like reference image */
    .pure-chat-interface {{
        height: calc(100vh - 120px);
        display: flex;
        flex-direction: column;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
        margin: 0.5rem 0;
        overflow: hidden;
    }}
    
    .messages-area {{
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem;
        background: transparent;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }}
    
    /* Fix column alignment and ensure proper side-by-side layout */
    .main .block-container {{
        padding-top: 100px !important;
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    
    /* Ensure columns are properly aligned */
    .stColumn {{
        padding: 0 0.5rem !important;
    }}
    
    /* Professional glass-morphism effect for chat */
    .chat-container {{
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.9) 0%,
            rgba(248, 250, 252, 0.85) 50%,
            rgba(241, 245, 249, 0.8) 100%);
        backdrop-filter: blur(25px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 
            0 25px 50px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
        overflow: hidden;
    }}
    
    .chat-input-bottom {{
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.95) 0%,
            rgba(248, 250, 252, 0.9) 100%);
        backdrop-filter: blur(20px);
        border-radius: 0 0 20px 20px;
        padding: 1.5rem;
        margin: 0;
        border-top: 1px solid rgba(229, 231, 235, 0.3);
        box-shadow: 
            0 -4px 20px rgba(0, 0, 0, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
        position: relative;
        z-index: 10;
    }}
    
    /* Professional chat input field styling */
    .chat-input-bottom .stTextArea > div > div > textarea {{
        border: 1px solid rgba(229, 231, 235, 0.6) !important;
        border-radius: 16px !important;
        font-size: 0.95rem !important;
        padding: 1rem 1.25rem !important;
        resize: none !important;
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.9) 0%,
            rgba(248, 250, 252, 0.85) 100%) !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 
            0 4px 15px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        transition: all 0.3s ease !important;
        line-height: 1.5 !important;
    }}
    
    .chat-input-bottom .stTextArea > div > div > textarea:focus {{
        border-color: var(--vivid-cyan) !important;
        box-shadow: 
            0 0 0 3px rgba(6, 147, 227, 0.15),
            0 6px 20px rgba(6, 147, 227, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        background: rgba(255, 255, 255, 0.95) !important;
    }}
    
    /* Professional send button styling */
    .chat-input-bottom .stButton > button {{
        background: var(--gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.8rem 2rem !important;
        margin-top: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 
            0 4px 15px rgba(6, 147, 227, 0.3),
            0 2px 8px rgba(6, 147, 227, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
    
    .chat-input-bottom .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 
            0 6px 20px rgba(6, 147, 227, 0.4),
            0 4px 12px rgba(6, 147, 227, 0.3) !important;
    }}
    
    /* Minimal chat input when no conversation exists */
    .minimal-chat-input {{
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.9) 0%,
            rgba(248, 250, 252, 0.85) 100%);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
        text-align: center;
    }}
    
    /* Style the input in minimal mode */
    .minimal-chat-input .stTextArea > div > div > textarea {{
        border: 1px solid rgba(229, 231, 235, 0.6) !important;
        border-radius: 16px !important;
        font-size: 0.95rem !important;
        padding: 1rem 1.25rem !important;
        resize: none !important;
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 
            0 4px 15px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        transition: all 0.3s ease !important;
        text-align: center !important;
    }}
    
    .minimal-chat-input .stButton > button {{
        background: var(--gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.8rem 2rem !important;
        margin-top: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 
            0 4px 15px rgba(6, 147, 227, 0.3),
            0 2px 8px rgba(6, 147, 227, 0.2) !important;
    }}
    
    /* Upload section with sophisticated styling */
    .upload-area {{
        border: 2px dashed rgba(142, 209, 252, 0.4);
        border-radius: 16px;
        padding: 2rem 1rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }}
    
    .upload-area:hover {{
        border-color: var(--pale-cyan);
        background: rgba(142, 209, 252, 0.1);
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(142, 209, 252, 0.2);
    }}
    
    .upload-icon {{
        font-size: 2rem;
        margin-bottom: 0.5rem;
        color: var(--gray-400);
    }}
    
    .upload-text {{
        color: var(--gray-600);
        font-weight: 500;
        margin-bottom: 0.25rem;
    }}
    
    .upload-subtext {{
        color: var(--gray-400);
        font-size: 0.875rem;
    }}
    
    /* Widget sections with sophisticated background matching chat */
    .widget-box {{
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.85) 0%,
            rgba(248, 250, 252, 0.8) 100%);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.12),
            inset 0 1px 0 rgba(255, 255, 255, 0.5);
        transition: all 0.3s ease;
    }}
    
    .widget-box:hover {{
        transform: translateY(-2px);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }}
    
    .widget-title {{
        font-weight: 600;
        color: var(--gray-800);
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    /* Statistics cards with sophisticated styling */
    .stat-card {{
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 
            0 4px 20px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }}
    
    .stat-card:hover {{
        background: rgba(255, 255, 255, 0.8);
        transform: translateY(-3px);
        box-shadow: 
            0 8px 30px rgba(0, 0, 0, 0.12),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }}
    
    .stat-value {{
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--vivid-cyan);
        margin-bottom: 0.25rem;
    }}
    
    .stat-label {{
        color: var(--gray-600);
        font-size: 0.875rem;
        font-weight: 500;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: var(--gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
    }}
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {{
        border: 1px solid var(--gray-300) !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: var(--vivid-cyan) !important;
        box-shadow: 0 0 0 3px rgba(6, 147, 227, 0.1) !important;
    }}
    
    /* File uploader */
    .stFileUploader {{
        display: none;
    }}
    
    /* Success/Error messages */
    .stSuccess {{
        background: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.2) !important;
        border-radius: 8px !important;
    }}
    
    .stError {{
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        border-radius: 8px !important;
    }}
    
    .stInfo {{
        background: rgba(142, 209, 252, 0.1) !important;
        border: 1px solid var(--pale-cyan) !important;
        border-radius: 8px !important;
    }}
    
    /* Typing indicator */
    .typing-indicator {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        background: var(--gray-100);
        border-radius: 1rem;
        color: var(--gray-600);
        font-style: italic;
        margin: 1rem 0;
    }}
    
    .typing-dots {{
        display: flex;
        gap: 0.25rem;
    }}
    
    .typing-dot {{
        width: 4px;
        height: 4px;
        background: var(--gray-400);
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }}
    
    .typing-dot:nth-child(1) {{ animation-delay: -0.32s; }}
    .typing-dot:nth-child(2) {{ animation-delay: -0.16s; }}
    
    @keyframes typing {{
        0%, 80%, 100% {{ 
            transform: scale(0);
            opacity: 0.5;
        }}
        40% {{ 
            transform: scale(1);
            opacity: 1;
        }}
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .chat-container {{
            height: 50vh;
        }}
        
        .message-content {{
            max-width: 90%;
        }}
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def display_message(role, content, timestamp=None, sender_name=None):
    """Display a chat message like the reference image"""
    if timestamp is None:
        timestamp = datetime.now()
    
    time_str = timestamp.strftime("%H:%M")
    
    if role == "user":
        name = sender_name or "You"
        st.markdown(f"""
        <div class="chat-message user">
            <div class="message-wrapper">
                <div class="message-header">
                    <span class="message-sender">{name}</span>
                    <span class="message-time">{time_str}</span>
                </div>
                <div class="message-content user-message">{content}</div>
            </div>
            <div class="message-avatar user-avatar">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        name = sender_name or "Zenith AI"
        st.markdown(f"""
        <div class="chat-message">
            <div class="message-avatar assistant-avatar">🤖</div>
            <div class="message-wrapper">
                <div class="message-header">
                    <span class="message-sender">{name}</span>
                    <span class="message-time">{time_str}</span>
                </div>
                <div class="message-content assistant-message">{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_typing():
    """Show typing indicator"""
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

def main():
    # Page config
    st.set_page_config(
        page_title="Zenith AI Chat",
        page_icon="🔷",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply CSS
    apply_custom_css()
    
    # Create header
    logo_b64 = load_logo()
    if logo_b64:
        st.markdown(f"""
        <div class="app-header">
            <div class="header-logo">
                <img src="data:image/png;base64,{logo_b64}" alt="Logo">
            </div>
            <div class="header-center">
                <div>
                    <div class="app-title">Zenith AI</div>
                    <div class="app-subtitle">Document Intelligence Platform</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="app-header">
            <div class="header-logo">
                <div style="font-size: 1.8rem; color: #0693e3;">🔷</div>
            </div>
            <div class="header-center">
                <div>
                    <div class="app-title">Zenith AI</div>
                    <div class="app-subtitle">Document Intelligence Platform</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize session state with empty messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'document_uploaded' not in st.session_state:
        st.session_state.document_uploaded = False
    
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    # Create perfectly aligned 3-column layout like reference image
    left_col, middle_col, right_col = st.columns([1, 2, 1], gap="large")
    
    # LEFT COLUMN - Upload & Controls
    with left_col:
        
        # Upload section
        st.markdown('<div class="widget-box">', unsafe_allow_html=True)
        st.markdown('<div class="widget-title">📄 Document Upload</div>', unsafe_allow_html=True)
        
        if not st.session_state.document_uploaded:
            st.markdown("""
            <div class="upload-area">
                <div class="upload-icon">📄</div>
                <div class="upload-text">Drop your PDF here</div>
                <div class="upload-subtext">or click to browse</div>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("Choose file", type=['pdf'], key="uploader")
            
            if uploaded_file:
                st.session_state.document_uploaded = True
                st.success(f"✅ {uploaded_file.name} uploaded!")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Great! I've processed '{uploaded_file.name}'. You can now ask me questions about the document.",
                    "timestamp": datetime.now()
                })
                st.rerun()
        else:
            st.success("✅ Document ready")
            if st.button("📤 Upload New", use_container_width=True):
                st.session_state.document_uploaded = False
                st.session_state.messages = [st.session_state.messages[0]]
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick actions
        st.markdown('<div class="widget-box">', unsafe_allow_html=True)
        st.markdown('<div class="widget-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
        
        if st.button("💡 Suggest Questions", use_container_width=True):
            if st.session_state.document_uploaded:
                suggestions = "Here are some questions you might ask:\n\n• What's the main topic?\n• Can you summarize the key points?\n• What are the conclusions?\n• Any important data mentioned?"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": suggestions,
                    "timestamp": datetime.now(),
                    "sender": "Zenith AI"
                })
                st.rerun()
        
        if st.button("📊 Document Summary", use_container_width=True):
            if st.session_state.document_uploaded:
                summary = "**Document Summary:**\n\nThis document contains important information organized into several key sections. The main topics include research findings, analysis, and recommendations. The document appears to be well-structured with clear conclusions."
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": summary,
                    "timestamp": datetime.now(),
                    "sender": "Zenith AI"
                })
                st.rerun()
        
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # MIDDLE COLUMN - Clean Chat Interface (no empty containers)
    with middle_col:
        # Only show chat container when there are actual messages or processing
        if len(st.session_state.messages) > 0 or st.session_state.processing:
            # Create sophisticated chat container with proper glass-morphism
            st.markdown('<div class="pure-chat-interface">', unsafe_allow_html=True)
            
            # Messages area with professional styling
            st.markdown('<div class="messages-area">', unsafe_allow_html=True)
            
            # Display all messages
            for i, message in enumerate(st.session_state.messages):
                display_message(
                    message["role"],
                    message["content"],
                    message.get("timestamp"),
                    message.get("sender")
                )
            
            # Show typing if processing
            if st.session_state.processing:
                show_typing()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Professional chat input integrated into the container
            st.markdown('<div class="chat-input-bottom">', unsafe_allow_html=True)
        else:
            # Minimal chat input when no conversation exists
            st.markdown('<div class="minimal-chat-input">', unsafe_allow_html=True)
        
        # Improved input layout 
        user_input = st.text_area(
            "",
            placeholder="Type your message here...",
            height=80,
            key="chat_input",
            label_visibility="collapsed"
        )
        
        # Create button row with proper spacing
        btn_col1, btn_col2, btn_col3 = st.columns([3, 1, 0.5])
        with btn_col2:
            send_button = st.button("Send", use_container_width=True, type="primary")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Close the chat interface container only if it was opened
        if len(st.session_state.messages) > 0 or st.session_state.processing:
            st.markdown('</div>', unsafe_allow_html=True)
        
        if send_button and user_input.strip():
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now(),
                "sender": "You"
            })
            
            # Set processing state
            st.session_state.processing = True
            st.session_state.chat_input = ""
            st.rerun()
        
        # Handle AI response
        if st.session_state.processing:
            time.sleep(1)  # Simulate processing time
            
            # Generate response based on context
            if st.session_state.document_uploaded:
                last_message = [msg for msg in st.session_state.messages if msg["role"] == "user"][-1]["content"]
                response = f"Based on the document, regarding '{last_message}': I can provide detailed analysis of this topic. The document contains relevant information that addresses your question. Here are the key insights:\n\n• Main finding related to your question\n• Supporting evidence from the text\n• Additional context and implications\n\nWould you like me to elaborate on any specific aspect?"
            else:
                response = "Please upload a document first so I can help analyze it and answer your questions accurately."
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(),
                "sender": "Zenith AI"
            })
            
            st.session_state.processing = False
            st.rerun()
    
    # RIGHT COLUMN - Stats & Settings
    with right_col:
        # Statistics
        st.markdown('<div class="widget-box">', unsafe_allow_html=True)
        st.markdown('<div class="widget-title">📊 Statistics</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">24</div>
            <div class="stat-label">Messages</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">3</div>
            <div class="stat-label">Documents</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">98%</div>
            <div class="stat-label">Accuracy</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Settings
        st.markdown('<div class="widget-box">', unsafe_allow_html=True)
        st.markdown('<div class="widget-title">⚙️ Settings</div>', unsafe_allow_html=True)
        
        model = st.selectbox("AI Model", ["GPT-3.5", "GPT-4", "Claude"], index=0)
        temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.1)
        chunk_size = st.slider("Chunk Size", 500, 2000, 1000, 100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Export
        st.markdown('<div class="widget-box">', unsafe_allow_html=True)
        st.markdown('<div class="widget-title">📥 Export</div>', unsafe_allow_html=True)
        
        if st.button("💾 Export Chat", use_container_width=True):
            st.success("Chat exported!")
        
        if st.button("📋 Export Analysis", use_container_width=True):
            st.success("Analysis exported!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Status
        st.markdown("""
        <div class="widget-box" style="text-align: center;">
            <div style="color: #0693e3; font-weight: 600; margin-bottom: 0.5rem;">
                🟢 System Online
            </div>
            <div style="color: #6b7280; font-size: 0.875rem;">
                All systems operational
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()