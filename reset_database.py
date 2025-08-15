#!/usr/bin/env python3
"""
Reset Database Script - Cleans up problematic settings and recreates defaults
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.qdrant_manager import get_qdrant_client
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging("INFO")
logger = get_logger(__name__)


def reset_settings():
    """Reset system settings collection"""
    try:
        qdrant_manager = get_qdrant_client()
        collection_name = "zenith_settings"
        
        logger.info("Resetting system settings...")
        
        # Delete settings collection if it exists
        if qdrant_manager.collection_exists(collection_name):
            logger.info(f"Deleting existing {collection_name} collection...")
            qdrant_manager.qdrant_client.delete_collection(collection_name)
            logger.info(f"Collection {collection_name} deleted successfully")
        
        logger.info("Settings reset completed. Application will recreate defaults on next startup.")
        
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return False
    
    return True


def main():
    """Main function"""
    print("🔄 Zenith Database Reset Tool")
    print("=" * 40)
    
    response = input("This will reset all system settings. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Reset cancelled.")
        return
    
    print("\n🔧 Resetting database...")
    
    if reset_settings():
        print("✅ Database reset completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your .env file with proper Langfuse credentials")
        print("2. Start your application: python main.py ui")
        print("3. The app will recreate settings from your .env configuration")
    else:
        print("❌ Database reset failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()