#!/usr/bin/env python3
"""
Test Langfuse configuration and fix common issues
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config

def test_langfuse_config():
    """Test and diagnose Langfuse configuration issues"""
    
    print("Langfuse Configuration Analysis")
    print("=" * 50)
    
    # Check basic config
    print(f"LANGFUSE_ENABLED: {config.langfuse_enabled}")
    print(f"LANGFUSE_HOST: {config.langfuse_host}")
    print(f"LANGFUSE_PUBLIC_KEY: {config.langfuse_public_key[:20] if config.langfuse_public_key else 'None'}...")
    print(f"LANGFUSE_SECRET_KEY: {config.langfuse_secret_key[:20] if config.langfuse_secret_key else 'None'}...")
    print(f"LANGFUSE_PROJECT_NAME: {config.langfuse_project_name}")
    print(f"LANGFUSE_TRACING_ENABLED: {config.langfuse_tracing_enabled}")
    
    # Issue 1: Check if Langfuse is enabled
    if not config.langfuse_enabled:
        print("\nISSUE 1: Langfuse is DISABLED")
        print("  FIX: Set LANGFUSE_ENABLED=True in .env file")
        return False
    
    # Issue 2: Check if keys are properly configured
    if not config.langfuse_public_key or not config.langfuse_secret_key:
        print("\nISSUE 2: Missing Langfuse keys")
        print("  FIX: Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env file")
        return False
    
    # Issue 3: Check if public and secret keys are the same (common mistake)
    if config.langfuse_public_key == config.langfuse_secret_key:
        print("\nISSUE 3: Public and Secret keys are identical!")
        print("  This is incorrect - they should be different keys")
        print("  FIX: Get separate public (pk-lf-...) and secret (sk-lf-...) keys from Langfuse")
        return False
    
    # Issue 4: Check key format
    if not config.langfuse_public_key.startswith('pk-lf-'):
        print(f"\nISSUE 4: Public key doesn't start with 'pk-lf-': {config.langfuse_public_key[:10]}...")
        print("  FIX: Use the correct public key format from Langfuse dashboard")
        return False
    
    if not config.langfuse_secret_key.startswith('sk-lf-'):
        print(f"\nISSUE 5: Secret key doesn't start with 'sk-lf-': {config.langfuse_secret_key[:10]}...")
        print("  FIX: Use the correct secret key format from Langfuse dashboard")
        return False
    
    print("\nConfiguration looks correct! Testing connection...")
    
    try:
        from langfuse import Langfuse
        
        # Test with base host (correct approach)
        clean_host = config.langfuse_host.rstrip('/')
        print(f"Testing connection to: {clean_host}")
        
        client = Langfuse(
            host=clean_host,
            public_key=config.langfuse_public_key,
            secret_key=config.langfuse_secret_key
        )
        
        print("✅ Langfuse client created successfully")
        
        # Try creating a trace ID
        trace_id = client.create_trace_id()
        print(f"✅ Created trace ID: {trace_id}")
        
        # Try creating a simple event
        event = client.create_event(
            name="config-test",
            input={"test": "data"},
            metadata={"config_test": True}
        )
        print("✅ Created test event")
        
        # Flush data
        client.flush()
        print("✅ Data flushed successfully")
        
        print(f"\n🎉 SUCCESS! Langfuse is working correctly.")
        print(f"📊 Check your dashboard: {config.langfuse_host}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        
        # Common error analysis
        error_str = str(e).lower()
        if "404" in error_str:
            print("\n🔍 404 Error Analysis:")
            print("  This usually means the endpoint URL is incorrect")
            print("  Common causes:")
            print("  1. Using /api/public/ingestion endpoint directly (incorrect)")
            print("  2. Wrong host URL")
            print("  3. Self-hosted Langfuse not running")
            
        elif "connection" in error_str or "refused" in error_str:
            print("\n🔍 Connection Error Analysis:")
            print("  Langfuse server might not be running or accessible")
            print(f"  Check if {config.langfuse_host} is accessible in browser")
            
        elif "auth" in error_str or "401" in error_str or "403" in error_str:
            print("\n🔍 Authentication Error Analysis:")
            print("  Keys might be incorrect or expired")
            print("  Check your Langfuse dashboard for correct keys")
        
        return False

def generate_fixed_config():
    """Generate corrected .env configuration"""
    print("\n" + "=" * 50)
    print("CORRECTED .ENV CONFIGURATION")
    print("=" * 50)
    print("""
# Langfuse Configuration (Self-hosted observability)
LANGFUSE_ENABLED=True
LANGFUSE_HOST=http://137.131.137.189:3000
LANGFUSE_PUBLIC_KEY=pk-lf-your-actual-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-actual-secret-key-here
LANGFUSE_PROJECT_NAME=zenith-pdf-chatbot
LANGFUSE_TRACING_ENABLED=True
LANGFUSE_EVALUATION_ENABLED=False
""")
    print("NOTES:")
    print("1. Set LANGFUSE_ENABLED=True")
    print("2. Get separate public and secret keys from your Langfuse dashboard")
    print("3. Public key should start with 'pk-lf-'")
    print("4. Secret key should start with 'sk-lf-'")
    print("5. Make sure your Langfuse server at http://137.131.137.189:3000 is running")

if __name__ == "__main__":
    success = test_langfuse_config()
    
    if not success:
        generate_fixed_config()
        print("\n❌ Langfuse configuration needs fixes")
    else:
        print("\n✅ Langfuse configuration is working correctly!")
