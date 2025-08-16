#!/usr/bin/env python3
"""
Simple HTTP debugging with monkey patching
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config

def patch_requests():
    """Monkey patch requests to log all HTTP calls"""
    import requests
    original_request = requests.request
    
    def logged_request(method, url, **kwargs):
        print(f"🌐 HTTP {method.upper()} to: {url}")
        try:
            response = original_request(method, url, **kwargs)
            print(f"   Response: {response.status_code}")
            if response.status_code == 404:
                print(f"   ❌ 404 NOT FOUND: {url}")
            return response
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            raise
    
    requests.request = logged_request

def test_langfuse():
    """Test Langfuse with HTTP logging"""
    print(f"🔧 Testing Langfuse with host: {config.langfuse_host}")
    
    # Patch requests first
    patch_requests()
    
    try:
        from langfuse import Langfuse
        
        print("📡 Creating Langfuse client...")
        ingestion_endpoint = f"{config.langfuse_host.rstrip('/')}/api/public/ingestion"
        print(f"Using ingestion endpoint: {ingestion_endpoint}")
        
        langfuse = Langfuse(
            host=ingestion_endpoint,
            public_key=config.langfuse_public_key or "pk-test",
            secret_key=config.langfuse_secret_key or "sk-test"
        )
        
        print("📡 Attempting create_trace_id()...")
        try:
            trace_id = langfuse.create_trace_id()
            print(f"✅ Success: {trace_id}")
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        print("📡 Attempting create_event()...")
        try:
            event = langfuse.create_event(name="test")
            print(f"✅ Success: {event}")
        except Exception as e:
            print(f"❌ Failed: {e}")
            
        print("📡 Attempting flush()...")
        try:
            langfuse.flush()
            print("✅ Flush completed")
        except Exception as e:
            print(f"❌ Flush failed: {e}")
            
    except Exception as e:
        print(f"❌ Langfuse init failed: {e}")

if __name__ == "__main__":
    print("🕷️ Simple HTTP Debug for Langfuse")
    print("=" * 40)
    test_langfuse()