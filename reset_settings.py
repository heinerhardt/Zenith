#!/usr/bin/env python3
"""
Force reset Zenith settings to match .env configuration
This script will reset all settings to use .env values, particularly fixing Ollama provider selection
"""

import sys
import os
from pathlib import Path

def main():
    try:
        print("Force resetting Zenith settings to match .env configuration...")
        
        # Set working directory to Zenith root
        zenith_root = Path(__file__).parent
        os.chdir(zenith_root)
        
        # Add the src directory to Python path
        src_path = zenith_root / "src"
        sys.path.insert(0, str(src_path))
        
        # Import after setting up path
        from core.enhanced_settings_manager import get_enhanced_settings_manager
        
        # Get settings manager
        settings_manager = get_enhanced_settings_manager()
        
        # Show current state first
        print("\nCurrent settings:")
        current_settings = settings_manager.get_current_settings()
        print(f"   Chat: {current_settings.preferred_chat_provider}")
        print(f"   Embedding: {current_settings.preferred_embedding_provider}")
        print(f"   Ollama enabled: {current_settings.ollama_enabled}")
        
        # Force reset to .env settings
        success = settings_manager.force_reset_to_env_settings()
        
        if success:
            print("\nSettings reset successfully!")
            
            # Show new effective providers
            current_settings = settings_manager.get_current_settings()
            print(f"New providers:")
            print(f"   Chat: {current_settings.get_effective_chat_provider()}")
            print(f"   Embedding: {current_settings.get_effective_embedding_provider()}")
            print(f"   Ollama enabled: {current_settings.is_ollama_enabled()}")
            print(f"   Langsmith enabled: {current_settings.is_langsmith_enabled()}")
            
            # Force reinitialization
            print("\nForce reinitializing providers...")
            success, message = settings_manager.force_reinitialize_providers()
            
            if success:
                print(f"SUCCESS: {message}")
            else:
                print(f"FAILED: {message}")
                
        else:
            print("Failed to reset settings")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    print(f"\n{'='*50}")
    if exit_code == 0:
        print("Settings reset complete! Restart your Streamlit app to see changes.")
    else:
        print("Settings reset failed! Check the error messages above.")
    sys.exit(exit_code)
