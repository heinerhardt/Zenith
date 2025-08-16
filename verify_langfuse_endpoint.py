#!/usr/bin/env python3
"""
Verify Langfuse endpoint configuration without Unicode characters
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config

def verify_endpoint_config():
    """Verify that Langfuse client uses the correct ingestion endpoint"""
    
    print("Langfuse Endpoint Verification")
    print("=" * 40)
    print(f"Host from config: {config.langfuse_host}")
    print(f"Enabled: {config.langfuse_enabled}")
    print(f"Public Key: {config.langfuse_public_key[:20] if config.langfuse_public_key else 'Not set'}...")
    
    if not config.langfuse_enabled:
        print("ERROR: Langfuse is not enabled! Set LANGFUSE_ENABLED=true in .env")
        return False
        
    if not config.langfuse_public_key or not config.langfuse_secret_key:
        print("ERROR: Langfuse keys not configured!")
        return False
    
    try:
        from langfuse import Langfuse
        
        # Test the ingestion endpoint configuration
        expected_endpoint = f"{config.langfuse_host.rstrip('/')}/api/public/ingestion"
        print(f"Expected ingestion endpoint: {expected_endpoint}")
        
        # Initialize client with ingestion endpoint
        client = Langfuse(
            host=expected_endpoint,
            public_key=config.langfuse_public_key,
            secret_key=config.langfuse_secret_key
        )
        
        print("SUCCESS: Langfuse client initialized with ingestion endpoint")
        
        # Check if client has required methods
        if hasattr(client, 'create_trace_id'):
            print("SUCCESS: Client has create_trace_id method")
        if hasattr(client, 'create_event'):
            print("SUCCESS: Client has create_event method")
        if hasattr(client, 'flush'):
            print("SUCCESS: Client has flush method")
            
        # Try a simple operation
        try:
            trace_id = client.create_trace_id()
            print(f"SUCCESS: Created trace ID: {trace_id}")
            
            # Create a test event
            event = client.create_event(
                name="endpoint-verification-test",
                input={"test": "data"},
                metadata={"verification": True}
            )
            print("SUCCESS: Created test event")
            
            # Flush to send data
            client.flush()
            print("SUCCESS: Flushed data to Langfuse")
            
            print("\nAll tests passed! Langfuse is properly configured.")
            print(f"Check your dashboard: {config.langfuse_host}")
            return True
            
        except Exception as e:
            print(f"ERROR during operation: {e}")
            return False
        
    except Exception as e:
        print(f"ERROR: Failed to initialize Langfuse: {e}")
        return False

if __name__ == "__main__":
    success = verify_endpoint_config()
    
    if success:
        print("\nVERIFICATION PASSED: Langfuse endpoint is correctly configured")
    else:
        print("\nVERIFICATION FAILED: Check configuration and try again")