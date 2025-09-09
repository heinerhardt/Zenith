#!/usr/bin/env python3
"""
Interactive Enterprise Setup Launcher
Launches the Streamlit setup UI for first-time configuration
"""

import sys
import subprocess
import sqlite3
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'data' / 'logs' / 'setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_setup_needed() -> bool:
    """Check if enterprise setup is needed"""
    try:
        # Check for enterprise marker
        enterprise_marker = project_root / 'data' / 'enterprise' / '.enterprise_configured'
        if enterprise_marker.exists():
            logger.info("Enterprise marker found, checking database setup status")
            
            # Check database setup status
            db_path = project_root / 'data' / 'enterprise' / 'zenith.db'
            if not db_path.exists():
                logger.info("Database not found, setup needed")
                return True
                
            # Check FIRST_SETUP flag in database
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Check for system_settings table
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='system_settings'
                """)
                
                if not cursor.fetchone():
                    logger.info("system_settings table not found, setup needed")
                    conn.close()
                    return True
                
                # Check FIRST_SETUP flag
                cursor.execute("""
                    SELECT value FROM system_settings 
                    WHERE key='FIRST_SETUP'
                """)
                
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0] == 'False':
                    logger.info("FIRST_SETUP=False, setup not needed")
                    return False
                    
                logger.info("FIRST_SETUP not set properly, setup needed")
                return True
                
            except Exception as e:
                logger.warning(f"Database check failed: {e}, assuming setup needed")
                return True
        else:
            logger.info("Enterprise marker not found, setup needed")
            return True
            
    except Exception as e:
        logger.error(f"Error checking setup status: {e}")
        return True


def launch_setup_ui() -> bool:
    """Launch the interactive setup UI using Streamlit"""
    try:
        logger.info("Launching interactive setup UI...")
        
        # Ensure setup UI file exists
        setup_ui_path = project_root / 'src' / 'ui' / 'setup_flow_app.py'
        if not setup_ui_path.exists():
            logger.error(f"Setup UI not found: {setup_ui_path}")
            return False
        
        # Launch Streamlit with the setup UI
        cmd = [
            sys.executable, '-m', 'streamlit', 'run',
            str(setup_ui_path),
            '--server.port=8502',  # Use different port from main app
            '--server.headless=false',
            '--browser.gatherUsageStats=false',
            '--server.address=localhost'
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run Streamlit setup UI
        result = subprocess.run(cmd, cwd=project_root, check=False)
        
        if result.returncode == 0:
            logger.info("Setup UI completed successfully")
            return True
        else:
            logger.error(f"Setup UI exited with code {result.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to launch setup UI: {e}")
        return False


def fallback_to_cli_setup() -> bool:
    """Fallback to CLI-based enterprise setup"""
    try:
        logger.info("Falling back to CLI-based setup...")
        
        # Import and run enterprise setup
        from src.setup.enterprise_setup import EnterpriseSetupManager
        import asyncio
        
        setup_manager = EnterpriseSetupManager()
        
        # Run async setup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success, results = loop.run_until_complete(
            setup_manager.run_complete_setup(interactive=True)
        )
        
        loop.close()
        
        if success:
            logger.info("CLI setup completed successfully")
            return True
        else:
            logger.error("CLI setup failed")
            for result in results:
                if hasattr(result, 'status') and result.status.value == 'failed':
                    logger.error(f"Phase {result.phase.value}: {result.message}")
            return False
            
    except Exception as e:
        logger.error(f"CLI setup failed: {e}")
        return False


def main():
    """Main setup launcher"""
    print("🚀 Zenith Interactive Setup Launcher")
    print("=" * 50)
    
    # Ensure required directories exist
    (project_root / 'data' / 'logs').mkdir(parents=True, exist_ok=True)
    (project_root / 'data' / 'enterprise').mkdir(parents=True, exist_ok=True)
    
    # Check if setup is needed
    if not check_setup_needed():
        print("✅ Setup already completed!")
        print("Use the admin panel or reset mode to reconfigure.")
        return 0
    
    print("🔧 First-time setup required")
    print("Launching interactive setup interface...")
    print("")
    
    # Try to launch interactive setup UI
    if launch_setup_ui():
        print("✅ Interactive setup completed successfully!")
        return 0
    
    print("⚠️  Interactive setup failed, trying CLI fallback...")
    
    # Fallback to CLI setup
    if fallback_to_cli_setup():
        print("✅ CLI setup completed successfully!")
        return 0
    
    print("❌ Setup failed! Please check the logs and try again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())