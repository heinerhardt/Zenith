#!/usr/bin/env python3
"""
Quick test to check current Zenith settings and provider selection
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    try:
        print("Checking Zenith settings and provider configuration...")
        
        # Check .env configuration first
        from core.config import config
        print(f"\n.env Configuration:")
        print(f"   OLLAMA_ENABLED: {config.ollama_enabled}")
        print(f"   CHAT_PROVIDER: {config.chat_provider}")
        print(f"   EMBEDDING_PROVIDER: {config.embedding_provider}")
        print(f"   OPENAI_API_KEY: {'Set' if config.openai_api_key else 'Not set'}")
        
        # Check database settings
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        settings_manager = get_enhanced_settings_manager()
        current_settings = settings_manager.get_current_settings()
        
        print(f"\nDatabase Settings:")
        print(f"   ollama_enabled: {current_settings.ollama_enabled}")
        print(f"   preferred_chat_provider: {current_settings.preferred_chat_provider}")
        print(f"   preferred_embedding_provider: {current_settings.preferred_embedding_provider}")
        print(f"   openai_api_key: {'Set' if current_settings.openai_api_key else 'Not set'}")
        
        print(f"\nEffective Providers:")
        print(f"   Chat: {current_settings.get_effective_chat_provider()}")
        print(f"   Embedding: {current_settings.get_effective_embedding_provider()}")
        print(f"   Ollama enabled: {current_settings.is_ollama_enabled()}")
        
        # Test individual method logic
        print(f"\nMethod Test Results:")
        print(f"   current_settings.ollama_enabled: {current_settings.ollama_enabled}")
        print(f"   config.ollama_enabled: {config.ollama_enabled}")
        print(f"   current_settings.preferred_chat_provider: {current_settings.preferred_chat_provider}")
        print(f"   config.chat_provider: {config.chat_provider}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    main()
