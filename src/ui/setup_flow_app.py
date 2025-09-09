"""
Comprehensive Enterprise Setup Flow UI for Zenith
Interactive Streamlit interface for first-time deployment and setup
"""

import os
import sys
import streamlit as st
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import asdict
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import setup components
from src.setup.enterprise_setup import (
    EnterpriseSetupManager, EnterpriseSetupConfig, SetupPhase, SetupStatus, SetupResult
)
from src.database.enterprise_schema import EnterpriseDatabase
from src.utils.database_security import secure_sqlite_connection, validate_database_path
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Zenith Enterprise Setup",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Setup Flow CSS - Matching existing design system
st.markdown("""
<style>
/* ===== SETUP FLOW STYLES - SERCOMPE INSPIRED ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --setup-primary: #32373c;
    --setup-secondary: #2c5282;
    --setup-accent: #4299e1;
    --setup-light: #f7fafc;
    --setup-white: #ffffff;
    --setup-gray-50: #f9fafb;
    --setup-gray-100: #f3f4f6;
    --setup-gray-200: #e5e7eb;
    --setup-gray-600: #6b7280;
    --setup-success: #10b981;
    --setup-warning: #f59e0b;
    --setup-error: #ef4444;
    --setup-border-radius: 12px;
    --setup-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}

/* Setup container */
.setup-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    background: var(--setup-white);
    border-radius: var(--setup-border-radius);
    box-shadow: var(--setup-shadow);
}

/* Progress bar */
.setup-progress {
    background: var(--setup-gray-100);
    border-radius: 10px;
    height: 8px;
    overflow: hidden;
    margin: 1rem 0 2rem 0;
}

.setup-progress-bar {
    background: linear-gradient(90deg, var(--setup-accent) 0%, var(--setup-secondary) 100%);
    height: 100%;
    border-radius: 10px;
    transition: width 0.3s ease;
}

/* Phase indicator */
.phase-indicator {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
    padding: 0 1rem;
}

.phase-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    flex: 1;
    position: relative;
}

.phase-step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 8px;
    transition: all 0.3s ease;
}

.phase-step.completed .phase-step-number {
    background: var(--setup-success);
    color: white;
}

.phase-step.current .phase-step-number {
    background: var(--setup-accent);
    color: white;
}

.phase-step.pending .phase-step-number {
    background: var(--setup-gray-200);
    color: var(--setup-gray-600);
}

.phase-step-label {
    font-size: 12px;
    color: var(--setup-gray-600);
    max-width: 80px;
}

/* Configuration sections */
.config-section {
    background: var(--setup-gray-50);
    padding: 1.5rem;
    border-radius: var(--setup-border-radius);
    margin: 1rem 0;
    border: 1px solid var(--setup-gray-200);
}

.config-section h4 {
    margin-top: 0;
    color: var(--setup-primary);
    font-weight: 600;
}

/* Status indicators */
.status-success {
    color: var(--setup-success);
    font-weight: 600;
}

.status-error {
    color: var(--setup-error);
    font-weight: 600;
}

.status-warning {
    color: var(--setup-warning);
    font-weight: 600;
}

/* Buttons */
.stButton > button {
    background: var(--setup-accent) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--setup-border-radius) !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: var(--setup-secondary) !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)


class SetupFlowManager:
    """Manages the interactive setup flow state and UI"""
    
    def __init__(self):
        self.setup_manager = None
        self.current_phase_index = 0
        self.setup_config = EnterpriseSetupConfig()
        self.setup_results = []
        
        # Initialize session state
        if 'setup_state' not in st.session_state:
            st.session_state.setup_state = 'welcome'
        if 'setup_progress' not in st.session_state:
            st.session_state.setup_progress = 0
        if 'setup_config' not in st.session_state:
            st.session_state.setup_config = asdict(self.setup_config)
    
    def check_setup_state(self) -> Tuple[bool, bool]:
        """
        Check if setup has been completed and if existing data exists
        Returns: (is_first_setup, has_existing_data)
        """
        try:
            # Check for setup completion marker
            db_path = Path(self.setup_config.database_path)
            if not db_path.exists():
                return True, False
            
            # Check if database has been setup
            with secure_sqlite_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Check for system_settings table and FIRST_SETUP flag
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='system_settings'
                """)
                
                if not cursor.fetchone():
                    return True, True  # Database exists but not setup
                
                cursor.execute("""
                    SELECT value FROM system_settings 
                    WHERE key='FIRST_SETUP'
                """)
                
                result = cursor.fetchone()
                if result and result[0] == 'False':
                    return False, True  # Setup completed
                
                return True, True  # Database exists with data
                
        except Exception as e:
            logger.error(f"Error checking setup state: {e}")
            return True, False
    
    def render_progress_bar(self, phases: List[str], current_index: int):
        """Render visual progress bar and phase indicators"""
        # Native Streamlit progress bar
        progress_percent = current_index / len(phases) 
        st.progress(progress_percent)
        
        # Clean phase indicators using columns
        cols = st.columns(len(phases))
        for i, (col, phase) in enumerate(zip(cols, phases)):
            with col:
                if i < current_index:
                    st.write(f"✅ **{i+1}. {phase}**")  # Completed
                elif i == current_index:
                    st.write(f"🔄 **{i+1}. {phase}**")  # Current  
                else:
                    st.write(f"⏳ {i+1}. {phase}")      # Pending
    
    def render_welcome_screen(self):
        """Render welcome screen with prerequisites"""
        # Clean header with emoji and title
        st.title("🚀 Welcome to Zenith Enterprise Setup")
        
        # Description
        st.write(
            "This setup wizard will guide you through configuring your Zenith enterprise deployment. "
            "The process typically takes 5-10 minutes and includes:"
        )
        
        # Feature list using columns for clean layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🗄️ Database Configuration**")
            st.caption("SQLite database setup and initialization")
            
            st.write("**🔐 Security Setup**")
            st.caption("Authentication and password policies")
            
            st.write("**🤖 AI Provider Configuration**")
            st.caption("OpenAI, Ollama, or custom endpoints")
        
        with col2:
            st.write("**👤 Administrator Account**")
            st.caption("Create your admin user account")
            
            st.write("**⚙️ System Validation**")
            st.caption("Health checks and configuration testing")
        
        # Add some spacing
        st.markdown("---")
        
        # Check system prerequisites
        st.subheader("📋 System Prerequisites")
        
        prerequisites = self._check_prerequisites()
        all_passed = True
        
        for check, status, message in prerequisites:
            if status:
                st.success(f"✅ {check}: {message}")
            else:
                st.error(f"❌ {check}: {message}")
                all_passed = False
        
        if all_passed:
            st.success("🎉 All prerequisites met! Ready to begin setup.")
            
            # Prominent call-to-action button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Begin Enterprise Setup", key="begin_setup", type="primary", use_container_width=True):
                    st.session_state.setup_state = 'configuration'
                    st.rerun()
        else:
            st.error("⚠️ Please resolve the above issues before continuing.")
            st.info("💡 **Tip:** Make sure you have write permissions and Python 3.9+ installed.")
    
    def _check_prerequisites(self) -> List[Tuple[str, bool, str]]:
        """Check system prerequisites"""
        checks = []
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 9):
            checks.append(("Python Version", True, f"Python {python_version.major}.{python_version.minor} ✓"))
        else:
            checks.append(("Python Version", False, f"Python 3.9+ required, found {python_version.major}.{python_version.minor}"))
        
        # Check write permissions
        try:
            test_dir = Path("./data/enterprise")
            test_dir.mkdir(parents=True, exist_ok=True)
            test_file = test_dir / "permission_test.tmp"
            test_file.write_text("test")
            test_file.unlink()
            checks.append(("File Permissions", True, "Write access verified"))
        except Exception as e:
            checks.append(("File Permissions", False, f"Cannot write to data directory: {e}"))
        
        # Check required directories
        required_dirs = ["./data", "./data/enterprise"]
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists() or path.mkdir(parents=True, exist_ok=True):
                checks.append((f"Directory {dir_path}", True, "Accessible"))
            else:
                checks.append((f"Directory {dir_path}", False, "Cannot create directory"))
        
        return checks
    
    def render_reset_confirmation(self):
        """Render reset confirmation screen for existing installations"""
        st.warning("⚠️ **Existing Installation Detected**")
        
        st.markdown("""
        <div class="config-section">
            <h4>🔄 System Reset Required</h4>
            <p>An existing Zenith installation has been detected. Proceeding with setup will:</p>
            <ul>
                <li>❗ Reset all configuration settings</li>
                <li>❗ Remove existing user accounts</li>
                <li>❗ Clear all chat history and documents</li>
                <li>❗ Reset security configurations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Show data impact estimation
        try:
            impact = self._estimate_data_impact()
            if impact:
                st.info(f"📊 **Estimated Data Loss**: {impact}")
        except:
            pass
        
        # Two-step confirmation
        st.subheader("🔒 Confirmation Required")
        
        confirm_checkbox = st.checkbox("I understand that this will reset all existing data")
        
        if confirm_checkbox:
            confirm_text = st.text_input(
                "Type **RESET** to confirm:",
                placeholder="RESET",
                key="reset_confirmation"
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("📤 Export Backup First", key="export_backup"):
                    self._export_backup()
            
            with col2:
                if st.button("❌ Cancel", key="cancel_reset"):
                    st.session_state.setup_state = 'welcome'
                    st.rerun()
            
            with col3:
                if confirm_text == "RESET" and st.button("🔄 Proceed with Reset", key="confirm_reset"):
                    self._perform_reset()
                    st.session_state.setup_state = 'configuration'
                    st.rerun()
    
    def _estimate_data_impact(self) -> Optional[str]:
        """Estimate data that will be lost during reset"""
        try:
            db_path = Path(self.setup_config.database_path)
            if not db_path.exists():
                return None
            
            with secure_sqlite_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Count users, sessions, documents, etc.
                counts = []
                
                for table in ['users', 'chat_sessions', 'documents', 'system_settings']:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            counts.append(f"{count} {table.replace('_', ' ')}")
                    except:
                        continue
                
                return ", ".join(counts) if counts else "No user data found"
                
        except Exception:
            return "Unable to assess data impact"
    
    def _export_backup(self):
        """Export backup before reset"""
        try:
            backup_dir = Path("./data/enterprise/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"zenith_backup_{timestamp}.db"
            
            db_path = Path(self.setup_config.database_path)
            if db_path.exists():
                import shutil
                shutil.copy2(db_path, backup_path)
                st.success(f"✅ Backup created: {backup_path}")
            else:
                st.warning("No database found to backup")
                
        except Exception as e:
            st.error(f"❌ Backup failed: {e}")
    
    def _perform_reset(self):
        """Perform system reset"""
        try:
            # Remove existing database
            db_path = Path(self.setup_config.database_path)
            if db_path.exists():
                db_path.unlink()
            
            # Clear other data directories if needed
            for dir_path in ["./data/enterprise/secrets", "./data/enterprise/logs"]:
                path = Path(dir_path)
                if path.exists():
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
            
            st.success("✅ System reset completed")
            
        except Exception as e:
            st.error(f"❌ Reset failed: {e}")
    
    def render_configuration_phases(self):
        """Render configuration phases with step-by-step UI"""
        phases = [
            "Welcome", "Database", "Vector DB", "AI Providers", 
            "Security", "Admin User", "Validation", "Complete"
        ]
        
        self.render_progress_bar(phases, st.session_state.get('current_phase', 1))
        
        phase = st.session_state.get('current_phase', 1)
        
        if phase == 1:
            self._render_database_config()
        elif phase == 2:
            self._render_vector_db_config()
        elif phase == 3:
            self._render_ai_provider_config()
        elif phase == 4:
            self._render_security_config()
        elif phase == 5:
            self._render_admin_user_config()
        elif phase == 6:
            self._render_validation_phase()
        elif phase == 7:
            self._render_completion_phase()
    
    def _render_database_config(self):
        """Render database configuration phase"""
        st.subheader("🗄️ Database Configuration")
        
        # Clean description without HTML
        st.write("**SQLite Database Setup**")
        st.caption("Configure your primary database storage location and security settings.")
        
        # Database path
        db_path = st.text_input(
            "Database File Path",
            value=st.session_state.setup_config.get('database_path', './data/enterprise/zenith.db'),
            help="Path where the SQLite database will be stored"
        )
        
        # Validate path
        if db_path:
            is_valid, message, _ = validate_database_path(db_path)
            if is_valid:
                st.success(f"✅ Valid path: {message}")
            else:
                st.error(f"❌ Invalid path: {message}")
        
        # Advanced options
        with st.expander("Advanced Database Options"):
            enable_wal = st.checkbox("Enable WAL Mode", value=True, help="Write-Ahead Logging for better performance")
            backup_enabled = st.checkbox("Enable Automatic Backups", value=True)
            
            if backup_enabled:
                backup_frequency = st.selectbox(
                    "Backup Frequency",
                    ["daily", "weekly", "monthly"],
                    index=1
                )
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back", key="db_back"):
                st.session_state.setup_state = 'welcome'
                st.rerun()
        
        with col2:
            if st.button("Continue →", key="db_continue") and db_path:
                # Save configuration
                st.session_state.setup_config.update({
                    'database_path': db_path,
                    'enable_wal_mode': enable_wal,
                    'backup_before_setup': backup_enabled
                })
                st.session_state.current_phase = 2
                st.rerun()
    
    def _render_vector_db_config(self):
        """Render vector database configuration"""
        st.subheader("🧠 Vector Database Configuration")
        
        deployment_mode = st.radio(
            "Deployment Mode",
            ["Local Instance", "Cloud Service"],
            help="Choose how to deploy your Qdrant vector database"
        )
        
        if deployment_mode == "Local Instance":
            col1, col2 = st.columns(2)
            with col1:
                qdrant_port = st.number_input("Port", value=6333, min_value=1024, max_value=65535)
                storage_path = st.text_input("Storage Path", value="./data/qdrant")
            
            with col2:
                memory_allocation = st.slider("Memory Allocation (MB)", 512, 4096, 1024)
        else:
            qdrant_url = st.text_input("Qdrant Cloud URL", placeholder="https://your-cluster.qdrant.io")
            qdrant_api_key = st.text_input("API Key", type="password")
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back", key="vector_back"):
                st.session_state.current_phase = 1
                st.rerun()
        
        with col2:
            if st.button("Continue →", key="vector_continue"):
                st.session_state.current_phase = 3
                st.rerun()
    
    def _render_ai_provider_config(self):
        """Render AI provider configuration"""
        st.subheader("🤖 AI Provider Configuration")
        
        provider = st.selectbox(
            "Primary AI Provider",
            ["OpenAI", "Ollama", "Custom Endpoint"],
            help="Choose your primary language model provider"
        )
        
        if provider == "OpenAI":
            api_key = st.text_input("OpenAI API Key", type="password")
            model = st.selectbox("Model", ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"])
        elif provider == "Ollama":
            ollama_url = st.text_input("Ollama Base URL", value="http://localhost:11434")
            model = st.text_input("Model Name", value="llama2")
        else:
            endpoint_url = st.text_input("Custom Endpoint URL")
            api_key = st.text_input("API Key", type="password")
        
        # Embedding model configuration
        st.subheader("📊 Embedding Model")
        embedding_provider = st.selectbox("Embedding Provider", ["OpenAI", "Local", "Custom"])
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back", key="ai_back"):
                st.session_state.current_phase = 2
                st.rerun()
        
        with col2:
            if st.button("Continue →", key="ai_continue"):
                st.session_state.current_phase = 4
                st.rerun()
    
    def _render_security_config(self):
        """Render security configuration"""
        st.subheader("🔐 Security Configuration")
        
        st.markdown("""
        <div class="config-section">
            <h4>Password Policy</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            min_length = st.number_input("Minimum Length", value=12, min_value=8, max_value=32)
            require_uppercase = st.checkbox("Require Uppercase", value=True)
            require_lowercase = st.checkbox("Require Lowercase", value=True)
        
        with col2:
            require_numbers = st.checkbox("Require Numbers", value=True)
            require_symbols = st.checkbox("Require Symbols", value=True)
            password_expiry = st.number_input("Password Expiry (days)", value=90, min_value=0)
        
        # Session management
        st.markdown("### Session Management")
        session_timeout = st.number_input("Session Timeout (minutes)", value=60, min_value=15)
        max_concurrent = st.number_input("Max Concurrent Sessions", value=5, min_value=1)
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back", key="security_back"):
                st.session_state.current_phase = 3
                st.rerun()
        
        with col2:
            if st.button("Continue →", key="security_continue"):
                st.session_state.current_phase = 5
                st.rerun()
    
    def _render_admin_user_config(self):
        """Render admin user creation"""
        st.subheader("👤 Administrator Account")
        
        col1, col2 = st.columns(2)
        with col1:
            admin_username = st.text_input("Username", value="admin")
            admin_email = st.text_input("Email", value="admin@zenith.local")
            admin_full_name = st.text_input("Full Name", value="System Administrator")
        
        with col2:
            admin_password = st.text_input("Password", type="password", help="Leave blank to auto-generate")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.checkbox("Auto-generate secure password"):
                if 'generated_password' not in st.session_state:
                    # Generate secure password
                    import secrets
                    import string
                    characters = string.ascii_letters + string.digits + "!@#$%^&*"
                    st.session_state.generated_password = ''.join(
                        secrets.choice(characters) for _ in range(16)
                    )
                
                admin_password = st.session_state.generated_password
                confirm_password = admin_password
                
                # Show the generated password
                st.info(f"🔑 **Generated Password:** `{admin_password}`")
                st.caption("⚠️ **Important:** Save this password securely!")
        
        # Validation
        if admin_password and admin_password != confirm_password:
            st.error("❌ Passwords do not match")
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back", key="admin_back"):
                st.session_state.current_phase = 4
                st.rerun()
        
        with col2:
            can_continue = bool(admin_username and admin_email and 
                              (not admin_password or admin_password == confirm_password))
            
            if st.button("Continue →", key="admin_continue", disabled=not can_continue):
                # Save admin configuration
                st.session_state.setup_config.update({
                    'admin_username': admin_username,
                    'admin_email': admin_email,
                    'admin_full_name': admin_full_name,
                    'admin_password': admin_password
                })
                st.session_state.current_phase = 6
                st.rerun()
    
    def _render_validation_phase(self):
        """Render validation and testing phase"""
        st.subheader("✅ Configuration Validation")
        
        st.info("🔍 Testing your configuration before final setup...")
        
        # Run validation tests
        validation_results = self._run_validation_tests()
        
        for test_name, status, message in validation_results:
            if status:
                st.success(f"✅ {test_name}: {message}")
            else:
                st.error(f"❌ {test_name}: {message}")
        
        all_passed = all(result[1] for result in validation_results)
        
        if all_passed:
            st.success("🎉 All validation tests passed!")
            
            # Configuration summary
            st.subheader("📋 Configuration Summary")
            config = st.session_state.setup_config
            
            st.markdown(f"""
            <div class="config-section">
                <h4>Setup Configuration</h4>
                <ul>
                    <li><strong>Database:</strong> {config.get('database_path', 'Default')}</li>
                    <li><strong>Admin User:</strong> {config.get('admin_username', 'admin')} ({config.get('admin_email', 'N/A')})</li>
                    <li><strong>Security:</strong> Enhanced password policies enabled</li>
                    <li><strong>Backup:</strong> {'Enabled' if config.get('backup_before_setup') else 'Disabled'}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Navigation
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Back", key="validation_back"):
                st.session_state.current_phase = 5
                st.rerun()
        
        with col2:
            if st.button("🚀 Complete Setup", key="complete_setup", disabled=not all_passed):
                self._run_enterprise_setup()
    
    def _run_validation_tests(self) -> List[Tuple[str, bool, str]]:
        """Run configuration validation tests"""
        tests = []
        
        # Database path validation
        db_path = st.session_state.setup_config.get('database_path')
        if db_path:
            is_valid, message, _ = validate_database_path(db_path)
            tests.append(("Database Path", is_valid, message))
        
        # Directory creation test
        try:
            Path("./data/enterprise").mkdir(parents=True, exist_ok=True)
            tests.append(("Directory Access", True, "Can create required directories"))
        except Exception as e:
            tests.append(("Directory Access", False, f"Cannot create directories: {e}"))
        
        # Configuration completeness
        required_config = ['admin_username', 'admin_email']
        missing = [key for key in required_config if not st.session_state.setup_config.get(key)]
        
        if not missing:
            tests.append(("Configuration", True, "All required settings provided"))
        else:
            tests.append(("Configuration", False, f"Missing: {', '.join(missing)}"))
        
        return tests
    
    def _run_enterprise_setup(self):
        """Execute the actual enterprise setup process"""
        try:
            with st.spinner("🔧 Running enterprise setup..."):
                # Convert session config to EnterpriseSetupConfig
                config_dict = st.session_state.setup_config
                setup_config = EnterpriseSetupConfig(**config_dict)
                
                # Initialize and run setup
                setup_manager = EnterpriseSetupManager(setup_config)
                
                # Run async setup in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                success, results = loop.run_until_complete(
                    setup_manager.run_complete_setup(interactive=False)
                )
                
                loop.close()
                
                if success:
                    st.session_state.current_phase = 7
                    st.session_state.setup_results = [asdict(result) for result in results]
                    st.rerun()
                else:
                    st.error("❌ Enterprise setup failed")
                    for result in results:
                        if result.status == SetupStatus.FAILED:
                            st.error(f"Phase {result.phase.value}: {result.message}")
        
        except Exception as e:
            st.error(f"❌ Setup error: {e}")
            logger.error(f"Enterprise setup failed: {e}")
    
    def _render_completion_phase(self):
        """Render setup completion screen"""
        st.success("🎉 Enterprise Setup Complete!")
        
        st.markdown("""
        <div class="config-section">
            <h4>✅ Setup Successful</h4>
            <p>Your Zenith enterprise deployment has been successfully configured!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show setup results
        if 'setup_results' in st.session_state:
            st.subheader("📊 Setup Results")
            
            for result in st.session_state.setup_results:
                phase_name = result['phase'].value.replace('_', ' ').title()
                duration = result['duration_seconds']
                
                if result['status'] == 'completed':
                    st.success(f"✅ {phase_name} - {result['message']} ({duration:.2f}s)")
                elif result['status'] == 'failed':
                    st.error(f"❌ {phase_name} - {result['message']}")
                else:
                    st.info(f"ℹ️ {phase_name} - {result['message']}")
        
        # Next steps
        st.subheader("🚀 Next Steps")
        st.markdown("""
        1. **Access your application**: The Zenith interface is now ready to use
        2. **Log in with admin account**: Use the administrator credentials you configured
        3. **Upload your first documents**: Start building your knowledge base
        4. **Configure additional users**: Add team members through the admin panel
        5. **Customize settings**: Fine-tune your deployment in the settings panel
        """)
        
        # Quick actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📚 Launch Zenith", key="launch_app"):
                st.success("✅ Setup completed! Launching main application...")
                st.info("💡 Close this browser tab and restart the application to access Zenith.")
                st.markdown("**Manual Launch:** Run `start_zenith.bat` again to start the main application.")
                
                # Show instructions instead of trying to redirect or exit
                st.markdown("""
                **Next Steps:**
                1. Close this browser tab
                2. Run `start_zenith.bat` again 
                3. The main Zenith application will launch automatically
                """)
                
                # Set a flag to prevent further setup attempts
                st.session_state.setup_completed = True
        
        with col2:
            if st.button("⚙️ Admin Panel", key="admin_panel"):
                st.info("Opening administrator panel...")
        
        with col3:
            if st.button("📖 Documentation", key="documentation"):
                st.info("Opening setup documentation...")


def main():
    """Main setup flow application"""
    setup_flow = SetupFlowManager()
    
    # Check setup state
    is_first_setup, has_existing_data = setup_flow.check_setup_state()
    
    # Handle different setup scenarios
    if not is_first_setup:
        # Setup already completed - redirect or show maintenance interface
        st.success("✅ Zenith Enterprise Setup Already Complete")
        st.info("Your system is already configured. Use the admin panel to modify settings.")
        
        if st.button("🔧 Reconfigure System"):
            st.session_state.setup_state = 'reset_confirmation'
            st.rerun()
        
        return
    
    # Handle setup flow states
    if st.session_state.setup_state == 'welcome':
        setup_flow.render_welcome_screen()
    
    elif st.session_state.setup_state == 'reset_confirmation' and has_existing_data:
        setup_flow.render_reset_confirmation()
    
    elif st.session_state.setup_state == 'configuration':
        setup_flow.render_configuration_phases()


if __name__ == "__main__":
    main()