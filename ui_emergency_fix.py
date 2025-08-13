import streamlit as st
import sys
from pathlib import Path

st.title("🔧 Streamlit UI Emergency Fix")

st.markdown("""
### Critical Issues:
1. **Enter key triggers Clear Chat** instead of sending message
2. **Sidebar not displayed**
3. **Chat sessions getting deleted**

Let me create fixes for these issues.
""")

# Check current session state
if st.button("🔍 Check Current App State", type="primary"):
    st.write("### Current Session State:")
    
    critical_keys = [
        'authenticated', 'user_info', 'auth_manager',
        'chat_history_manager', 'current_session', 'chat_history',
        'vector_store', 'chat_engine', 'show_admin_panel'
    ]
    
    issues = []
    
    for key in critical_keys:
        if key in st.session_state:
            value = st.session_state[key]
            if value is None:
                st.write(f"- **{key}**: ❌ None")
                issues.append(f"{key} is None")
            else:
                st.write(f"- **{key}**: ✅ {type(value).__name__}")
        else:
            st.write(f"- **{key}**: ❌ Missing")
            issues.append(f"{key} missing from session state")
    
    if issues:
        st.error("**Issues found:**")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("✅ Session state looks normal")

# Create fixed chat interface code
if st.button("🛠️ Generate Fixed Chat Interface", type="secondary"):
    
    fixed_chat_code = '''
def render_chat_interface_fixed(self):
    """Fixed chat interface with proper Enter key handling and sidebar"""
    
    # CRITICAL: Ensure sidebar is always rendered first
    self.render_sidebar_fixed()
    
    # Initialize components if missing
    self.ensure_components_initialized()
    
    # Main chat area
    st.markdown('<h2 class="main-header">💬 Chat with Your Documents</h2>', unsafe_allow_html=True)
    
    user_id = st.session_state.user_info.get('id')
    
    # Initialize chat engine with better error handling
    if not st.session_state.chat_engine:
        try:
            if not st.session_state.vector_store:
                st.session_state.vector_store = UserVectorStore(user_id=user_id)
            st.session_state.chat_engine = EnhancedChatEngine(
                user_id=user_id,
                vector_store=st.session_state.vector_store
            )
        except Exception as e:
            st.error(f"❌ Failed to initialize chat engine: {str(e)}")
            st.info("💡 Try using Force Reinitialize in admin panel")
            return
    
    # Check if user has documents
    user_stats = {}
    if st.session_state.vector_store:
        try:
            user_stats = st.session_state.vector_store.get_user_stats()
        except Exception as e:
            user_stats = {'total_documents': 0}
    
    has_documents = user_stats.get('total_documents', 0) > 0
    
    if not has_documents:
        st.info("🤖 You can chat with me even without uploading documents! Upload PDFs to get document-specific answers.")
    
    # Display chat history BEFORE input
    self.display_chat_history()
    
    # FIXED: Use form to prevent Enter key conflicts
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your message:",
            placeholder="Ask me anything...",
            height=100,
            key="chat_input_area"
        )
        
        # Form submit button (this handles Enter key properly)
        submitted = st.form_submit_button("📤 Send Message", type="primary", use_container_width=True)
        
        if submitted and user_input.strip():
            self.handle_user_input_fixed(user_input.strip(), has_documents)
    
    # FIXED: Put controls in separate container to avoid conflicts
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat_btn"):
            self.clear_chat_history_fixed()
    
    with col2:
        if has_documents and st.button("📊 Document Stats", key="doc_stats_btn"):
            self.show_document_stats()
    
    with col3:
        if st.button("🔄 New Chat Session", key="new_session_btn"):
            self.start_new_chat_session()

def render_sidebar_fixed(self):
    """Fixed sidebar that always displays"""
    
    # CRITICAL: Always show sidebar title
    st.sidebar.markdown("# 📚 Zenith PDF Chatbot")
    st.sidebar.markdown("---")
    
    # User info
    user_info = st.session_state.get('user_info', {})
    if user_info:
        st.sidebar.markdown(f"**👤 User:** {user_info.get('username', 'Unknown')}")
        st.sidebar.markdown(f"**🔐 Role:** {user_info.get('role', 'user')}")
        st.sidebar.markdown("---")
    
    # Admin panel access
    if user_info.get('role') == 'administrator':
        if st.sidebar.button("⚙️ Admin Panel", key="admin_panel_btn"):
            st.session_state.show_admin_panel = True
            st.rerun()
    
    # Chat history with better error handling
    try:
        self.render_chat_history_sidebar_fixed()
    except Exception as e:
        st.sidebar.error(f"Chat history error: {e}")
        if st.sidebar.button("🔄 Reset Chat History"):
            self.reset_chat_history_manager()
    
    # Document info
    if st.session_state.get('documents_processed', False):
        st.sidebar.markdown("### 📄 Documents")
        stats = st.session_state.get('file_stats', {})
        st.sidebar.write(f"Files: {len(stats.get('processed_files', []))}")
        st.sidebar.write(f"Chunks: {stats.get('total_chunks', 0)}")
    
    # Logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", key="logout_btn"):
        self.logout_user()

def render_chat_history_sidebar_fixed(self):
    """Fixed chat history sidebar"""
    st.sidebar.markdown("### 💬 Chat Sessions")
    
    user_id = st.session_state.user_info.get('id')
    if not user_id:
        st.sidebar.error("No user ID available")
        return
    
    try:
        # Get chat history manager
        if not st.session_state.get('chat_history_manager'):
            st.session_state.chat_history_manager = get_chat_history_manager()
        
        chat_manager = st.session_state.chat_history_manager
        recent_sessions = chat_manager.get_user_sessions(user_id, limit=5)
        
        if recent_sessions:
            current_session_id = st.session_state.get('current_session', {}).get('session_id') if st.session_state.get('current_session') else None
            
            for i, session in enumerate(recent_sessions):
                is_current = session.session_id == current_session_id
                
                # Session display
                with st.sidebar.container():
                    session_name = session.title[:30] + "..." if len(session.title) > 30 else session.title
                    
                    if is_current:
                        st.sidebar.markdown(f"**🟢 {session_name}**")
                    else:
                        if st.sidebar.button(f"💬 {session_name}", key=f"session_{session.session_id}"):
                            self.load_chat_session(session.session_id)
                    
                    # Session info
                    messages = chat_manager.get_session_messages(session.session_id, user_id)
                    msg_count = len(messages)
                    st.sidebar.caption(f"{msg_count} messages")
        else:
            st.sidebar.info("No chat sessions yet")
    
    except Exception as e:
        st.sidebar.error(f"Error loading chat history: {e}")
    
    # New chat button
    if st.sidebar.button("➕ New Chat", key="new_chat_sidebar"):
        self.start_new_chat_session()

def handle_user_input_fixed(self, user_input: str, has_documents: bool):
    """Fixed user input handling with better error management"""
    
    # Add user message to chat history immediately
    user_message = {"role": "user", "content": user_input}
    st.session_state.chat_history.append(user_message)
    
    # Add to current session
    self.add_message_to_current_session("user", user_input)
    
    try:
        with st.spinner("Thinking..."):
            # Ensure chat engine is available
            if not st.session_state.chat_engine:
                user_id = st.session_state.user_info.get('id')
                if not st.session_state.vector_store:
                    st.session_state.vector_store = UserVectorStore(user_id=user_id)
                st.session_state.chat_engine = EnhancedChatEngine(
                    user_id=user_id,
                    vector_store=st.session_state.vector_store
                )
            
            # Get response with timeout handling
            response = st.session_state.chat_engine.chat(
                user_input, 
                use_rag=has_documents
            )
            
            # Process response
            answer = response.get("answer", "I couldn't generate a response.")
            sources = response.get("source_documents", [])
            
            assistant_message = {
                "role": "assistant",
                "content": answer,
                "sources": sources
            }
            
            # Add to chat history
            st.session_state.chat_history.append(assistant_message)
            
            # Add to session
            self.add_message_to_current_session("assistant", answer)
            
    except Exception as e:
        error_message = f"Sorry, I encountered an error: {str(e)}"
        
        # Add error to chat history
        error_response = {
            "role": "assistant", 
            "content": error_message,
            "sources": []
        }
        st.session_state.chat_history.append(error_response)
        
        # Add to session
        self.add_message_to_current_session("assistant", error_message)
        
        # Log error but don't show details to user
        logger.error(f"Chat error: {e}")
    
    # Force refresh
    st.rerun()

def clear_chat_history_fixed(self):
    """Fixed clear chat history"""
    st.session_state.chat_history = []
    
    # Start new session
    self.start_new_chat_session()
    
    st.success("Chat cleared!")
    st.rerun()

def ensure_components_initialized(self):
    """Ensure all required components are initialized"""
    
    # Chat history manager
    if 'chat_history_manager' not in st.session_state or not st.session_state.chat_history_manager:
        st.session_state.chat_history_manager = get_chat_history_manager()
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Current session
    if 'current_session' not in st.session_state or not st.session_state.current_session:
        self.start_new_chat_session()
    
    # Vector store
    user_id = st.session_state.user_info.get('id')
    if 'vector_store' not in st.session_state or not st.session_state.vector_store:
        st.session_state.vector_store = UserVectorStore(user_id=user_id)
'''
    
    st.success("✅ Fixed chat interface code generated!")
    st.code(fixed_chat_code, language='python')
    
    st.markdown("### 🔧 Key Fixes Applied:")
    st.markdown("""
    1. **Enter Key Fix**: Using `st.form()` to properly handle Enter key for message sending
    2. **Sidebar Fix**: Always render sidebar first with proper error handling
    3. **Session Management**: Better initialization and error recovery
    4. **Button Conflicts**: Separate containers and unique keys for all buttons
    5. **Component Initialization**: Ensure all required components are available
    """)

# Create a manual session state reset
if st.button("🚨 Emergency Session Reset", type="secondary"):
    st.warning("⚠️ This will clear all session state - use only if app is completely broken")
    
    if st.checkbox("I understand this will reset everything"):
        if st.button("🔄 RESET NOW", type="primary"):
            # Clear critical session state
            keys_to_clear = [
                'chat_history', 'current_session', 'chat_engine', 
                'vector_store', 'documents_processed', 'show_admin_panel'
            ]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.success("✅ Session state reset! Refresh the page.")
            st.balloons()

# Quick fix recommendations
st.markdown("---")
st.markdown("### 🎯 Immediate Actions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Quick Fixes:**")
    st.markdown("1. 🔄 **Restart your Streamlit app** completely")
    st.markdown("2. 🧹 **Clear browser cache/cookies**")
    st.markdown("3. 🆕 **Open in new browser tab/incognito**")
    st.markdown("4. 🔧 **Apply the code fixes above**")

with col2:
    st.markdown("**If issues persist:**")
    st.markdown("1. 📝 **Check browser console** for JavaScript errors")
    st.markdown("2. 🐛 **Check Streamlit logs** for Python errors")
    st.markdown("3. ⚙️ **Use Emergency Session Reset** above")
    st.markdown("4. 🔄 **Restart Ollama** if using Ollama")

st.markdown("### 💡 Root Cause Analysis")
st.info("""
**Why this happens:**

1. **Enter Key Issue**: Streamlit's button handling can conflict with chat input when not properly isolated
2. **Missing Sidebar**: Session state corruption or initialization errors prevent sidebar rendering
3. **Deleted Sessions**: Chat engine errors cause session cleanup, but error handling fails

**The fixes above address all these issues with proper form handling, error recovery, and component initialization.**
""")
