#!/usr/bin/env python3
"""
Debug Langfuse HTTP requests to see exact endpoints being called
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging("DEBUG")
logger = get_logger(__name__)

def debug_langfuse_requests():
    """Debug Langfuse requests with HTTP capture"""
    
    # Enable HTTP debugging at all levels
    import http.client as http_client
    import urllib3
    
    # Enable low-level HTTP debugging
    http_client.HTTPConnection.debuglevel = 1
    
    # Configure logging to capture HTTP traffic
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    
    urllib3_log = logging.getLogger("urllib3.connectionpool")
    urllib3_log.setLevel(logging.DEBUG)
    urllib3_log.propagate = True
    
    logger.info("🕷️ HTTP debugging enabled - will show all requests")
    logger.info(f"Langfuse Host: {config.langfuse_host}")
    
    try:
        from langfuse import Langfuse
        
        logger.info("🔧 Creating Langfuse client...")
        
        # Initialize client
        langfuse = Langfuse(
            host=config.langfuse_host,
            public_key=config.langfuse_public_key,
            secret_key=config.langfuse_secret_key
        )
        
        logger.info("✅ Langfuse client created")
        
        # Try to get trace ID (this should trigger HTTP requests)
        logger.info("🚀 Attempting to create trace ID...")
        
        try:
            trace_id = langfuse.create_trace_id()
            logger.info(f"✅ Created trace ID: {trace_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create trace ID: {e}")
        
        # Try to create a simple event (another HTTP request)
        logger.info("🚀 Attempting to create event...")
        
        try:
            event = langfuse.create_event(
                name="debug-test",
                input={"test": "data"},
                metadata={"debug": True}
            )
            logger.info(f"✅ Created event: {event}")
        except Exception as e:
            logger.error(f"❌ Failed to create event: {e}")
        
        # Try flush to send any pending data
        logger.info("🚀 Attempting to flush data...")
        
        try:
            langfuse.flush()
            logger.info("✅ Flush completed")
        except Exception as e:
            logger.error(f"❌ Failed to flush: {e}")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize Langfuse: {e}")

if __name__ == "__main__":
    print("🕷️ Langfuse HTTP Request Debugger")
    print("=" * 50)
    print("This will show ALL HTTP requests made by Langfuse client")
    print("Look for the URLs being called to identify the 404 endpoint")
    print("=" * 50)
    
    debug_langfuse_requests()