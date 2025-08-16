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
    
    # Monkey patch requests to capture all HTTP calls
    import requests
    original_request = requests.request
    
    def logged_request(method, url, **kwargs):
        print(f"🌐 HTTP {method.upper()} -> {url}")
        if 'headers' in kwargs:
            auth_header = kwargs['headers'].get('Authorization', 'None')
            print(f"   Auth: {auth_header[:20]}..." if auth_header != 'None' else "   Auth: None")
        try:
            response = original_request(method, url, **kwargs)
            print(f"   📊 Response: {response.status_code}")
            if response.status_code == 404:
                print(f"   ❌ 404 NOT FOUND: {url}")
                print(f"   📝 Response text: {response.text[:200]}...")
            elif response.status_code >= 400:
                print(f"   ❌ Error {response.status_code}: {response.text[:200]}...")
            return response
        except Exception as e:
            print(f"   💥 Request failed: {e}")
            raise
    
    requests.request = logged_request
    
    logger.info("🕷️ HTTP debugging enabled - will show all requests")
    logger.info(f"Langfuse Host: {config.langfuse_host}")
    logger.info(f"Public Key: {config.langfuse_public_key[:20] if config.langfuse_public_key else 'None'}...")
    logger.info(f"Secret Key: {config.langfuse_secret_key[:20] if config.langfuse_secret_key else 'None'}...")
    
    try:
        from langfuse import Langfuse
        
        logger.info("🔧 Creating Langfuse client...")
        
        # Test both approaches
        print("\n=== TESTING OLD APPROACH (BROKEN) ===")
        ingestion_endpoint = f"{config.langfuse_host.rstrip('/')}/api/public/ingestion"
        print(f"Old endpoint: {ingestion_endpoint}")
        
        try:
            langfuse_old = Langfuse(
                host=ingestion_endpoint,
                public_key=config.langfuse_public_key,
                secret_key=config.langfuse_secret_key
            )
            print("✅ Old client created")
            
            # Try a simple operation
            trace_id = langfuse_old.create_trace_id()
            print(f"✅ Old approach trace ID: {trace_id}")
        except Exception as e:
            print(f"❌ Old approach failed: {e}")
        
        print("\n=== TESTING NEW APPROACH (FIXED) ===")
        clean_host = config.langfuse_host.rstrip('/')
        print(f"New endpoint: {clean_host}")
        
        langfuse = Langfuse(
            host=clean_host,
            public_key=config.langfuse_public_key,
            secret_key=config.langfuse_secret_key
        )
        
        print("✅ New client created")
        
        # Try to get trace ID (this should trigger HTTP requests)
        print("🚀 Attempting to create trace ID...")
        
        try:
            trace_id = langfuse.create_trace_id()
            print(f"✅ Created trace ID: {trace_id}")
        except Exception as e:
            print(f"❌ Failed to create trace ID: {e}")
        
        # Try to create a simple event (another HTTP request)
        print("🚀 Attempting to create event...")
        
        try:
            event = langfuse.create_event(
                name="debug-test",
                input={"test": "data"},
                metadata={"debug": True}
            )
            print(f"✅ Created event: {event}")
        except Exception as e:
            print(f"❌ Failed to create event: {e}")
        
        # Try a trace with generation (this often triggers the span export)
        print("🚀 Attempting to create trace with generation...")
        
        try:
            trace = langfuse.trace(name="debug-trace")
            generation = trace.generation(
                name="debug-generation",
                model="debug-model",
                input="test input",
                output="test output"
            )
            generation.end()
            print(f"✅ Created trace with generation: {trace.id}")
        except Exception as e:
            print(f"❌ Failed to create trace with generation: {e}")
        
        # Try flush to send any pending data (this is where span export usually happens)
        print("🚀 Attempting to flush data (span export happens here)...")
        
        try:
            langfuse.flush()
            print("✅ Flush completed")
        except Exception as e:
            print(f"❌ Failed to flush: {e}")
        
        # Check client configuration
        print("\n=== CLIENT CONFIGURATION ===")
        if hasattr(langfuse, '_client_wrapper'):
            if hasattr(langfuse._client_wrapper, 'base_url'):
                print(f"Client base URL: {langfuse._client_wrapper.base_url}")
            if hasattr(langfuse._client_wrapper, '_base_url'):
                print(f"Client _base_url: {langfuse._client_wrapper._base_url}")
        if hasattr(langfuse, 'base_url'):
            print(f"Langfuse base_url: {langfuse.base_url}")
            
    except Exception as e:
        print(f"❌ Failed to initialize Langfuse: {e}")

if __name__ == "__main__":
    print("🕷️ Langfuse HTTP Request Debugger")
    print("=" * 50)
    print("This will show ALL HTTP requests made by Langfuse client")
    print("Look for the URLs being called to identify the 404 endpoint")
    print("=" * 50)
    
    debug_langfuse_requests()