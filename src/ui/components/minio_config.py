"""
MinIO Configuration Component for Streamlit UI - FIXED VERSION
Provides interface for configuring MinIO connection settings
"""

import streamlit as st
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.minio_client import MinIOClient
    from src.utils.logger import get_logger
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please ensure MinIO dependencies are installed: pip install minio>=7.2.0")
    st.stop()

logger = get_logger(__name__)


class MinIOConfigUI:
    """MinIO configuration UI component"""
    
    def __init__(self):
        """Initialize MinIO configuration UI"""
        self.client: Optional[MinIOClient] = None
    
    def render_config_form(self) -> Dict[str, Any]:
        """
        Render MinIO configuration form
        
        Returns:
            Dict with configuration settings
        """
        st.header("🗄️ MinIO Configuration")
        
        # Load current settings from environment or session state
        with st.form("minio_config_form"):
            st.write("Configure your MinIO server connection:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                endpoint = st.text_input(
                    "MinIO Endpoint",
                    value=st.session_state.get('minio_endpoint', os.getenv('MINIO_ENDPOINT', 'localhost:9000')),
                    help="MinIO server endpoint (host:port)",
                    key="minio_endpoint_input"
                )
                
                access_key = st.text_input(
                    "Access Key",
                    value=st.session_state.get('minio_access_key', os.getenv('MINIO_ACCESS_KEY', '')),
                    help="MinIO access key",
                    key="minio_access_key_input"
                )
                
                secure = st.checkbox(
                    "Use HTTPS",
                    value=st.session_state.get('minio_secure', os.getenv('MINIO_SECURE', 'False').lower() == 'true'),
                    help="Use secure HTTPS connection",
                    key="minio_secure_input"
                )
            
            with col2:
                secret_key = st.text_input(
                    "Secret Key",
                    value=st.session_state.get('minio_secret_key', os.getenv('MINIO_SECRET_KEY', '')),
                    type="password",
                    help="MinIO secret key",
                    key="minio_secret_key_input"
                )
                
                region = st.text_input(
                    "Region",
                    value=st.session_state.get('minio_region', os.getenv('MINIO_REGION', 'us-east-1')),
                    help="MinIO region",
                    key="minio_region_input"
                )
            
            # Form buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                save_config = st.form_submit_button("💾 Save Configuration", type="primary")
            
            with col2:
                test_connection = st.form_submit_button("🔍 Test Connection")
            
            with col3:
                load_defaults = st.form_submit_button("🔄 Load Defaults")
            
            config = {
                'endpoint': endpoint,
                'access_key': access_key,
                'secret_key': secret_key,
                'secure': secure,
                'region': region
            }
            
            # Handle form submissions
            if load_defaults:
                self._load_default_config()
                st.rerun()
            
            if save_config:
                self._save_config(config)
            
            if test_connection:
                self._test_connection(config)
            
            return config
    
    def render_connection_status(self) -> bool:
        """
        Render connection status section
        
        Returns:
            bool: True if connected successfully
        """
        st.header("🔌 Connection Status")
        
        # Get current configuration
        config = self._get_current_config()
        
        if not config['access_key'] or not config['secret_key']:
            st.warning("⚠️ MinIO credentials not configured")
            return False
        
        try:
            # Test connection
            client = MinIOClient(
                endpoint=config['endpoint'],
                access_key=config['access_key'],
                secret_key=config['secret_key'],
                secure=config['secure'],
                region=config['region']
            )
            
            if client.test_connection():
                st.success("✅ Connected to MinIO successfully!")
                
                # Show connection details
                with st.expander("Connection Details"):
                    info = client.get_connection_info()
                    st.json(info)
                
                # Store working client in session state
                st.session_state['minio_client'] = client
                return True
            else:
                st.error("❌ Failed to connect to MinIO")
                return False
                
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")
            logger.error(f"MinIO connection error: {e}")
            return False
    
    def render_bucket_overview(self) -> Optional[List[Dict[str, Any]]]:
        """
        Render bucket overview if connected
        
        Returns:
            List of bucket information or None
        """
        client = st.session_state.get('minio_client')
        if not client:
            return None
        
        st.header("📦 Buckets Overview")
        
        try:
            with st.spinner("Loading buckets..."):
                buckets = client.list_buckets()
            
            if not buckets:
                st.info("No buckets found")
                return []
            
            # Display bucket information
            st.write(f"Found **{len(buckets)}** buckets:")
            
            # Create bucket table
            bucket_data = []
            for bucket in buckets:
                try:
                    with st.spinner(f"Loading stats for {bucket['name']}..."):
                        stats = client.get_bucket_stats(bucket['name'])
                    bucket_data.append({
                        'Bucket': bucket['name'],
                        'Created': bucket['creation_date_str'],
                        'Objects': stats['total_objects'],
                        'PDFs': stats['pdf_objects'],
                        'Size': stats['total_size_str']
                    })
                except Exception as e:
                    logger.warning(f"Error getting stats for bucket {bucket['name']}: {e}")
                    bucket_data.append({
                        'Bucket': bucket['name'],
                        'Created': bucket['creation_date_str'],
                        'Objects': 'Error',
                        'PDFs': 'Error',
                        'Size': 'Error'
                    })
            
            st.dataframe(bucket_data, use_container_width=True)
            
            return buckets
            
        except Exception as e:
            st.error(f"Error loading buckets: {str(e)}")
            logger.error(f"Error loading buckets: {e}")
            return None
    
    def _get_current_config(self) -> Dict[str, Any]:
        """Get current MinIO configuration"""
        return {
            'endpoint': st.session_state.get('minio_endpoint', os.getenv('MINIO_ENDPOINT', 'localhost:9000')),
            'access_key': st.session_state.get('minio_access_key', os.getenv('MINIO_ACCESS_KEY', '')),
            'secret_key': st.session_state.get('minio_secret_key', os.getenv('MINIO_SECRET_KEY', '')),
            'secure': st.session_state.get('minio_secure', os.getenv('MINIO_SECURE', 'False').lower() == 'true'),
            'region': st.session_state.get('minio_region', os.getenv('MINIO_REGION', 'us-east-1'))
        }
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to session state"""
        st.session_state['minio_endpoint'] = config['endpoint']
        st.session_state['minio_access_key'] = config['access_key']
        st.session_state['minio_secret_key'] = config['secret_key']
        st.session_state['minio_secure'] = config['secure']
        st.session_state['minio_region'] = config['region']
        
        st.success("✅ Configuration saved successfully!")
        logger.info("MinIO configuration saved")
    
    def _test_connection(self, config: Dict[str, Any]):
        """Test MinIO connection with provided configuration"""
        if not config['access_key'] or not config['secret_key']:
            st.error("❌ Access key and secret key are required")
            return
        
        with st.spinner("Testing MinIO connection..."):
            try:
                client = MinIOClient(
                    endpoint=config['endpoint'],
                    access_key=config['access_key'],
                    secret_key=config['secret_key'],
                    secure=config['secure'],
                    region=config['region']
                )
                
                if client.test_connection():
                    st.success("✅ Connection test successful!")
                    
                    # Try to get bucket count
                    try:
                        buckets = client.list_buckets()
                        st.info(f"Found {len(buckets)} bucket(s)")
                    except Exception as e:
                        st.warning(f"Connected, but couldn't list buckets: {str(e)}")
                        
                else:
                    st.error("❌ Connection test failed")
                    
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
                logger.error(f"MinIO connection test error: {e}")
    
    def _load_default_config(self):
        """Load default configuration values"""
        st.session_state['minio_endpoint'] = 'localhost:9000'
        st.session_state['minio_access_key'] = ''
        st.session_state['minio_secret_key'] = ''
        st.session_state['minio_secure'] = False
        st.session_state['minio_region'] = 'us-east-1'
        
        st.info("Default configuration loaded")
    
    def render_quick_setup_guide(self):
        """Render quick setup guide"""
        with st.expander("📖 Quick Setup Guide"):
            st.markdown("""
            ### Setting up MinIO Connection
            
            1. **Start MinIO Server**: Make sure your MinIO server is running
            2. **Get Credentials**: Obtain your MinIO access key and secret key
            3. **Configure Endpoint**: Enter your MinIO server endpoint (e.g., `localhost:9000`)
            4. **Test Connection**: Use the "Test Connection" button to verify settings
            5. **Save Configuration**: Save your settings for future sessions
            
            ### Common Endpoints
            - **Local MinIO**: `localhost:9000`
            - **Docker MinIO**: `minio:9000` (if using Docker networks)
            - **Remote MinIO**: `your-domain.com:9000`
            
            ### Security Notes
            - Enable HTTPS for production environments
            - Store credentials securely
            - Use dedicated MinIO users with minimal required permissions
            
            ### Troubleshooting
            - Check if MinIO server is accessible
            - Verify network connectivity
            - Ensure credentials have bucket access permissions
            - Check firewall settings if connection fails
            """)


def render_minio_config_page():
    """
    Main function to render the complete MinIO configuration page
    """
    st.title("⚙️ MinIO Configuration")
    st.write("Configure your MinIO server connection to process PDFs from buckets.")
    
    # Check if MinIO is available
    try:
        from src.core.minio_client import MinIOClient
    except ImportError:
        st.error("❌ MinIO integration not available. Please install required dependencies:")
        st.code("pip install minio>=7.2.0")
        return
    
    config_ui = MinIOConfigUI()
    
    # Render configuration sections
    config = config_ui.render_config_form()
    
    st.divider()
    
    # Show connection status
    is_connected = config_ui.render_connection_status()
    
    if is_connected:
        st.divider()
        # Show bucket overview if connected
        config_ui.render_bucket_overview()
    
    st.divider()
    
    # Show setup guide
    config_ui.render_quick_setup_guide()


# Main execution for testing
if __name__ == "__main__":
    render_minio_config_page()
