#!/usr/bin/env python3
"""
Test Langfuse connection and send a test trace
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging("INFO")
logger = get_logger(__name__)

def test_langfuse_connection():
    """Test Langfuse connection and send test trace"""
    
    logger.info("Testing Langfuse connection...")
    logger.info(f"Host: {config.langfuse_host}")
    logger.info(f"Enabled: {config.langfuse_enabled}")
    logger.info(f"Public Key: {config.langfuse_public_key[:20] if config.langfuse_public_key else 'Not set'}...")
    logger.info(f"Secret Key: {'Set' if config.langfuse_secret_key else 'Not set'}")
    
    if not config.langfuse_enabled:
        logger.error("❌ Langfuse is not enabled! Set LANGFUSE_ENABLED=true in .env")
        return False
        
    if not config.langfuse_public_key or not config.langfuse_secret_key:
        logger.error("❌ Langfuse keys not configured! Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        return False
    
    try:
        from langfuse import Langfuse
        
        # Initialize Langfuse client
        langfuse = Langfuse(
            host=config.langfuse_host,
            public_key=config.langfuse_public_key,
            secret_key=config.langfuse_secret_key
        )
        
        logger.info("✅ Langfuse client initialized successfully")
        
        # Send a test trace
        trace = langfuse.trace(
            name="zenith-connection-test",
            metadata={"test": True, "source": "zenith-test-script"}
        )
        
        # Add a span
        span = trace.span(
            name="test-span",
            input={"message": "Testing Langfuse connection from Zenith"},
            output={"status": "success"}
        )
        span.end()
        
        # Flush to ensure data is sent
        langfuse.flush()
        
        logger.info("✅ Test trace sent successfully!")
        logger.info(f"🔗 Check your Langfuse dashboard: {config.langfuse_host}")
        logger.info("   Look for a trace named 'zenith-connection-test'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Langfuse connection failed: {e}")
        logger.error(f"   Host: {config.langfuse_host}")
        logger.error(f"   Public Key: {config.langfuse_public_key[:20] if config.langfuse_public_key else 'None'}...")
        return False

def main():
    """Main function"""
    print("🔍 Zenith Langfuse Connection Test")
    print("=" * 40)
    
    success = test_langfuse_connection()
    
    if success:
        print("\n✅ Connection test completed successfully!")
        print("Your Zenith app should now be sending traces to Langfuse.")
    else:
        print("\n❌ Connection test failed!")
        print("Please check your configuration and try again.")
        print("\nTroubleshooting:")
        print("1. Ensure Langfuse is running: docker-compose -f docker-compose.langfuse-v4.yml ps")
        print("2. Check your .env file has correct LANGFUSE_* settings")
        print("3. Verify API keys from Langfuse dashboard")
        print("4. Test Langfuse URL in browser")

if __name__ == "__main__":
    main()