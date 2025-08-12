"""
Test script to verify Ollama persistence and dynamic switching functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
from src.core.enhanced_settings_manager import get_enhanced_settings_manager
from src.core.provider_manager import get_provider_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_ollama_persistence():
    """Test Ollama settings persistence and dynamic switching"""
    print("🧪 Testing Ollama Persistence and Dynamic Switching")
    print("=" * 60)
    
    try:
        # Get managers
        settings_manager = get_enhanced_settings_manager()
        provider_manager = get_provider_manager()
        
        print("✅ Managers initialized successfully")
        
        # Get current settings
        current_settings = settings_manager.get_settings()
        print(f"📊 Current Ollama enabled: {current_settings.ollama_enabled}")
        print(f"📊 Current chat provider: {current_settings.preferred_chat_provider}")
        
        # Test 1: Enable Ollama if not enabled
        if not current_settings.ollama_enabled:
            print("\n🔄 Test 1: Enabling Ollama...")
            
            updates = {
                "ollama_enabled": True,
                "ollama_endpoint": "http://localhost:11434",
                "preferred_chat_provider": "ollama"
            }
            
            success, message = settings_manager.update_settings(updates)
            if success:
                print(f"✅ {message}")
                
                # Wait for providers to initialize
                time.sleep(2)
                
                # Check provider status
                status = provider_manager.get_provider_status()
                print(f"📊 New chat provider: {status['current_providers']['chat']}")
                
                ollama_health = status['provider_health']['chat'].get('ollama', {})
                if ollama_health.get('healthy'):
                    print("✅ Ollama chat provider is healthy")
                else:
                    print(f"⚠️ Ollama chat provider health: {ollama_health.get('message', 'Unknown')}")
            else:
                print(f"❌ Failed to enable Ollama: {message}")
        
        # Test 2: Switch back to OpenAI
        print("\n🔄 Test 2: Switching to OpenAI...")
        
        updates = {
            "preferred_chat_provider": "openai"
        }
        
        success, message = settings_manager.update_settings(updates)
        if success:
            print(f"✅ {message}")
            
            # Wait for providers to initialize
            time.sleep(2)
            
            # Check provider status
            status = provider_manager.get_provider_status()
            print(f"📊 New chat provider: {status['current_providers']['chat']}")
            
            openai_health = status['provider_health']['chat'].get('openai', {})
            if openai_health.get('healthy'):
                print("✅ OpenAI chat provider is healthy")
            else:
                print(f"⚠️ OpenAI chat provider health: {openai_health.get('message', 'Unknown')}")
        else:
            print(f"❌ Failed to switch to OpenAI: {message}")
        
        # Test 3: Test persistence by reloading settings
        print("\n🔄 Test 3: Testing persistence...")
        
        # Reload settings from database
        reloaded_settings = settings_manager._load_settings()
        print(f"📊 Persisted chat provider: {reloaded_settings.preferred_chat_provider}")
        print(f"📊 Persisted Ollama enabled: {reloaded_settings.ollama_enabled}")
        
        # Test 4: Force reinitialization
        print("\n🔄 Test 4: Testing force reinitialization...")
        
        success, message = settings_manager.force_reinitialize_providers()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        print("\n🎉 All tests completed!")
        
        # Show final status
        final_status = provider_manager.get_provider_status()
        print("\n📊 Final Provider Status:")
        print(f"  Chat: {final_status['current_providers']['chat']}")
        print(f"  Embedding: {final_status['current_providers']['embedding']}")
        
        for provider_type, providers in final_status['provider_health'].items():
            print(f"\n  {provider_type.title()} Provider Health:")
            for name, health in providers.items():
                icon = "✅" if health.get('healthy') else "❌"
                print(f"    {icon} {name}: {health.get('message', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ollama_persistence()
