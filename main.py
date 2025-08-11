#!/usr/bin/env python3
"""
Main entry point for Zenith PDF Chatbot
Provides command-line interface to run different components
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config, load_config
from src.utils.logger import setup_logging, get_logger
from src.utils.helpers import validate_config

# Setup logging
setup_logging(config.log_level)
logger = get_logger(__name__)


def run_streamlit():
    """Run the Streamlit web interface"""
    try:
        logger.info("Starting Zenith PDF Chatbot Streamlit interface...")
        
        import subprocess
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            "src/ui/enhanced_streamlit_app.py",  # Back to enhanced app with fixes
            "--server.port", str(config.app_port),
            "--server.address", "127.0.0.1",
            "--server.headless", "true" if not config.debug_mode else "false"
        ]
        
        subprocess.run(cmd, cwd=project_root)
        
    except KeyboardInterrupt:
        logger.info("Streamlit interface stopped by user")
    except Exception as e:
        logger.error(f"Error running Streamlit interface: {e}")
        sys.exit(1)


def run_api():
    """Run the FastAPI server"""
    try:
        logger.info("Starting Zenith PDF Chatbot API server...")
        
        import uvicorn
        from src.api.main import app
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=config.debug_mode,
            log_level=config.log_level.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("API server stopped by user")
    except Exception as e:
        logger.error(f"Error running API server: {e}")
        sys.exit(1)


def run_tests():
    """Run the test suite"""
    try:
        logger.info("Running Zenith PDF Chatbot test suite...")
        
        import pytest
        
        # Run pytest with coverage
        exit_code = pytest.main([
            "tests/",
            "-v",
            "--tb=short",
            "--cov=src",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ])
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1)


def setup_environment():
    """Setup the environment and dependencies"""
    try:
        logger.info("Setting up Zenith PDF Chatbot environment...")
        
        # Create necessary directories
        from src.utils.helpers import ensure_directory_exists
        from src.core.config import get_data_dir, get_logs_dir, get_temp_dir
        
        ensure_directory_exists(get_data_dir())
        ensure_directory_exists(get_logs_dir())
        ensure_directory_exists(get_temp_dir())
        
        logger.info("Environment setup completed successfully")
        
        # Validate configuration
        errors = validate_config()
        if errors:
            logger.warning("Configuration validation errors found:")
            for error in errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("Configuration validation passed")
        
        # Test Qdrant connection
        try:
            from src.core.vector_store import VectorStore
            vector_store = VectorStore()
            if vector_store.health_check():
                logger.info("✅ Qdrant connection successful")
            else:
                logger.warning("⚠️ Qdrant connection failed - please check your Qdrant server")
        except Exception as e:
            logger.warning(f"⚠️ Could not test Qdrant connection: {e}")
        
        # Test OpenAI connection
        if config.openai_api_key and config.openai_api_key != "your_openai_api_key_here":
            try:
                from src.core.chat_engine import ChatEngine
                from src.core.vector_store import VectorStore
                
                vector_store = VectorStore()
                chat_engine = ChatEngine(vector_store)
                logger.info("✅ OpenAI configuration appears valid")
            except Exception as e:
                logger.warning(f"⚠️ Could not test OpenAI connection: {e}")
        else:
            logger.warning("⚠️ OpenAI API key not configured")
        
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")
        sys.exit(1)


def show_system_info():
    """Show system information and status"""
    try:
        logger.info("Zenith PDF Chatbot System Information")
        logger.info("=" * 50)
        
        # Basic info
        logger.info(f"Project root: {project_root}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Debug mode: {config.debug_mode}")
        logger.info(f"Log level: {config.log_level}")
        
        # Configuration
        logger.info(f"Qdrant URL: {config.qdrant_url}:{config.qdrant_port}")
        logger.info(f"Collection: {config.qdrant_collection_name}")
        logger.info(f"Chunk size: {config.chunk_size}")
        logger.info(f"Chunk overlap: {config.chunk_overlap}")
        
        # System info
        try:
            from src.utils.helpers import get_system_info
            system_info = get_system_info()
            
            if "error" not in system_info:
                logger.info(f"Platform: {system_info.get('platform', 'Unknown')}")
                logger.info(f"CPU cores: {system_info.get('cpu_count', 'Unknown')}")
                logger.info(f"Total memory: {system_info.get('memory_total_gb', 'Unknown')} GB")
                logger.info(f"Available memory: {system_info.get('memory_available_gb', 'Unknown')} GB")
                logger.info(f"Free disk space: {system_info.get('disk_free_gb', 'Unknown')} GB")
        except Exception as e:
            logger.warning(f"Could not get system information: {e}")
        
        # Component status
        logger.info("\nComponent Status:")
        logger.info("-" * 20)
        
        try:
            from src.core.vector_store import VectorStore
            vector_store = VectorStore()
            if vector_store.health_check():
                logger.info("✅ Vector Store: Healthy")
                
                # Collection info
                collection_info = vector_store.get_collection_info()
                if collection_info:
                    logger.info(f"   Documents: {collection_info.get('vectors_count', 0)}")
                    logger.info(f"   Status: {collection_info.get('status', 'Unknown')}")
            else:
                logger.info("❌ Vector Store: Unhealthy")
        except Exception as e:
            logger.info(f"❌ Vector Store: Error ({e})")
        
        try:
            from src.core.chat_engine import ChatEngine
            vector_store = VectorStore()
            chat_engine = ChatEngine(vector_store)
            if chat_engine.health_check():
                logger.info("✅ Chat Engine: Healthy")
            else:
                logger.info("❌ Chat Engine: Unhealthy")
        except Exception as e:
            logger.info(f"❌ Chat Engine: Error ({e})")
        
    except Exception as e:
        logger.error(f"Error showing system info: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Zenith PDF Chatbot - AI-powered document chat system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ui                 # Run Streamlit web interface
  python main.py api                # Run FastAPI server
  python main.py setup              # Setup environment
  python main.py test               # Run test suite
  python main.py info               # Show system information
  python main.py ui --port 8502     # Run UI on custom port
        """
    )
    
    parser.add_argument(
        "command",
        choices=["ui", "api", "test", "setup", "info"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Port number for web interfaces"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address for web interfaces"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Update configuration based on arguments
    if args.debug:
        config.debug_mode = True
    
    if args.log_level:
        config.log_level = args.log_level
        setup_logging(args.log_level)
    
    if args.port:
        if args.command == "ui":
            config.app_port = args.port
    
    # Run the specified command
    if args.command == "ui":
        run_streamlit()
    elif args.command == "api":
        run_api()
    elif args.command == "test":
        run_tests()
    elif args.command == "setup":
        setup_environment()
    elif args.command == "info":
        show_system_info()


if __name__ == "__main__":
    main()
