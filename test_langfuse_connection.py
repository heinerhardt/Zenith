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
        
        # Debug: Show all available methods
        available_methods = [method for method in dir(langfuse) if not method.startswith('_')]
        logger.info(f"Available Langfuse methods: {available_methods}")
        
        # Check if client has trace method
        if not hasattr(langfuse, 'trace'):
            logger.error("❌ Langfuse client doesn't have 'trace' method!")
            logger.error(f"   Available methods: {available_methods}")
            
            # Try alternative patterns for modern Langfuse
            logger.info("Trying alternative Langfuse patterns...")
            
            # Pattern 1: Global langfuse instance
            try:
                from langfuse import langfuse as langfuse_global
                if hasattr(langfuse_global, 'trace'):
                    logger.info("✅ Found trace method in global langfuse instance")
                    langfuse = langfuse_global
                else:
                    logger.info(f"Global langfuse methods: {[m for m in dir(langfuse_global) if not m.startswith('_')]}")
            except ImportError:
                logger.info("No global langfuse instance available")
            
            # Pattern 2: Check for create_trace or other methods
            if hasattr(langfuse, 'create_trace'):
                logger.info("✅ Found 'create_trace' method - using compatibility mode")
            elif hasattr(langfuse, 'log'):
                logger.info("✅ Found 'log' method - using basic logging mode")
            elif hasattr(langfuse, 'observe'):
                logger.info("✅ Found 'observe' method - using decorator mode")
            else:
                logger.error("❌ No compatible tracing method found")
                return False
        
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