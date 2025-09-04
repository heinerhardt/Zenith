#!/usr/bin/env python3
"""
Force reset Zenith settings to match .env configuration
This script will override any saved admin settings with your .env file values
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.core.enhanced_settings_manager import get_enhanced_settings_manager
    from src.core.config import config
    
    def main():
        print("Zenith Settings Reset Tool")
        print("=" * 40)
        
        # Show current .env configuration
        print("\nCurrent .env configuration:")
        print(f"  OLLAMA_ENABLED: {config.ollama_enabled}")
        print(f"  CHAT_PROVIDER: {config.chat_provider}")
        print(f"  EMBEDDING_PROVIDER: {config.embedding_provider}")
        print(f"  OPENAI_API_KEY: {'Set' if config.openai_api_key else 'Not set'}")
        
        # Get settings manager
        settings_manager = get_enhanced_settings_manager()
        
        # Show current effective settings
        print("\nCurrent effective settings:")
        current_settings = settings_manager.get_settings()
        print(f"  Ollama enabled: {current_settings.ollama_enabled}")
        print(f"  Chat provider: {settings_manager.get_effective_chat_provider()}")
        print(f"  Embedding provider: {settings_manager.get_effective_embedding_provider()}")
        
        # Confirm reset
        print("\nThis will reset all admin settings to match your .env file.")
        response = input("Continue? (y/N): ").strip().lower()
        
        if response != 'y':
            print("Reset cancelled.")
            return
        
        # Force reset
        print("\nResetting settings...")
        success = settings_manager.force_reset_to_env_settings()
        
        if success:
            print("✓ Settings reset successfully!")
            
            # Show new effective settings
            print("\nNew effective settings:")
            new_settings = settings_manager.get_settings()
            print(f"  Ollama enabled: {new_settings.ollama_enabled}")
            print(f"  Chat provider: {settings_manager.get_effective_chat_provider()}")
            print(f"  Embedding provider: {settings_manager.get_effective_embedding_provider()}")
            
            print("\n✓ Your app should now use the .env configuration!")
            print("  Run your app again to test the changes.")
            
        else:
            print("✗ Failed to reset settings. Check logs for details.")
            return 1
        
        return 0

    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)