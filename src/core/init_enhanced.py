"""
Initialization script for Zenith - Sets up enhanced components and provider management
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.core.enhanced_settings_manager import get_enhanced_settings_manager
from src.core.provider_manager import get_provider_manager

logger = get_logger(__name__)


def initialize_zenith_components():
    """
    Initialize enhanced Zenith components
    """
    try:
        logger.info("Initializing Zenith enhanced components...")
        
        # Initialize enhanced settings manager
        settings_manager = get_enhanced_settings_manager()
        logger.info("✅ Enhanced settings manager initialized")
        
        # Initialize provider manager
        provider_manager = get_provider_manager()
        logger.info("✅ Provider manager initialized")
        
        # Get current provider status
        status = provider_manager.get_provider_status()
        logger.info(f"✅ Provider status: Chat={status['current_providers']['chat']}, Embedding={status['current_providers']['embedding']}")
        
        # Test provider connectivity
        chat_provider = status['current_providers']['chat']
        chat_health = status['provider_health']['chat'].get(chat_provider, {})
        if chat_health.get('healthy'):
            logger.info(f"✅ Chat provider {chat_provider} is healthy")
        else:
            logger.warning(f"⚠️ Chat provider {chat_provider} health check failed: {chat_health.get('message')}")
        
        embed_provider = status['current_providers']['embedding']
        embed_health = status['provider_health']['embedding'].get(embed_provider, {})
        if embed_health.get('healthy'):
            logger.info(f"✅ Embedding provider {embed_provider} is healthy")
        else:
            logger.warning(f"⚠️ Embedding provider {embed_provider} health check failed: {embed_health.get('message')}")
        
        logger.info("🎉 Zenith enhanced components initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Zenith components: {e}")
        return False


def get_initialization_status():
    """
    Get initialization status of all components
    """
    status = {
        'settings_manager': False,
        'provider_manager': False,
        'providers': {
            'chat': {'initialized': False, 'healthy': False},
            'embedding': {'initialized': False, 'healthy': False}
        }
    }
    
    try:
        # Check settings manager
        settings_manager = get_enhanced_settings_manager()
        status['settings_manager'] = True
        
        # Check provider manager
        provider_manager = get_provider_manager()
        status['provider_manager'] = True
        
        # Check provider status
        provider_status = provider_manager.get_provider_status()
        
        # Chat provider
        chat_provider = provider_status['current_providers']['chat']
        if chat_provider in provider_status['provider_health']['chat']:
            status['providers']['chat']['initialized'] = True
            status['providers']['chat']['healthy'] = provider_status['provider_health']['chat'][chat_provider].get('healthy', False)
        
        # Embedding provider
        embed_provider = provider_status['current_providers']['embedding']
        if embed_provider in provider_status['provider_health']['embedding']:
            status['providers']['embedding']['initialized'] = True
            status['providers']['embedding']['healthy'] = provider_status['provider_health']['embedding'][embed_provider].get('healthy', False)
        
    except Exception as e:
        logger.error(f"Error getting initialization status: {e}")
    
    return status


if __name__ == "__main__":
    """Run initialization when script is executed directly"""
    success = initialize_zenith_components()
    
    if success:
        print("✅ Zenith enhanced components initialized successfully!")
        
        # Show detailed status
        status = get_initialization_status()
        print("\n📊 Component Status:")
        print(f"  Settings Manager: {'✅' if status['settings_manager'] else '❌'}")
        print(f"  Provider Manager: {'✅' if status['provider_manager'] else '❌'}")
        print(f"  Chat Provider: {'✅' if status['providers']['chat']['healthy'] else '⚠️' if status['providers']['chat']['initialized'] else '❌'}")
        print(f"  Embedding Provider: {'✅' if status['providers']['embedding']['healthy'] else '⚠️' if status['providers']['embedding']['initialized'] else '❌'}")
    else:
        print("❌ Zenith initialization failed!")
        sys.exit(1)
