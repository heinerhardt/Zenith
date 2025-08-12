"""
Dynamic Provider Manager for Zenith - Handles hot-swapping between AI providers
"""

from typing import Dict, Any, Optional, Set
import threading
from datetime import datetime

from .config import config
from .enhanced_settings_manager import get_enhanced_settings_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProviderManager:
    """
    Manages dynamic switching between AI providers without requiring app restarts
    """
    
    def __init__(self):
        """Initialize provider manager"""
        self._lock = threading.Lock()
        
        # Provider instances cache
        self._chat_providers: Dict[str, Any] = {}
        self._embedding_providers: Dict[str, Any] = {}
        
        # Active provider tracking
        self._current_chat_provider = None
        self._current_embedding_provider = None
        
        # Component instances that need reinitialization
        self._registered_components: Set[Any] = set()
        
        # Settings manager
        self._settings_manager = get_enhanced_settings_manager()
        
        # Register for settings changes
        self._settings_manager.register_provider_change_callback(self._handle_provider_change)
        
        # Initialize providers
        self._initialize_providers()
        
        logger.info("Provider manager initialized")
    
    def _initialize_providers(self):
        """Initialize providers based on current settings"""
        settings = self._settings_manager.get_settings()
        
        # Initialize chat provider
        self._current_chat_provider = settings.preferred_chat_provider
        self._ensure_chat_provider(self._current_chat_provider)
        
        # Initialize embedding provider
        self._current_embedding_provider = settings.preferred_embedding_provider
        self._ensure_embedding_provider(self._current_embedding_provider)
    
    def _ensure_chat_provider(self, provider: str) -> bool:
        """Ensure chat provider is available and initialized"""
        try:
            if provider not in self._chat_providers or not self._chat_providers[provider]:
                if provider == "openai":
                    self._chat_providers[provider] = self._create_openai_chat_provider()
                elif provider == "ollama":
                    self._chat_providers[provider] = self._create_ollama_chat_provider()
                else:
                    raise ValueError(f"Unknown chat provider: {provider}")
            
            # Test provider health
            if self._chat_providers[provider]:
                if hasattr(self._chat_providers[provider], 'health_check'):
                    if not self._chat_providers[provider].health_check():
                        logger.warning(f"Chat provider {provider} failed health check")
                        return False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error ensuring chat provider {provider}: {e}")
            self._chat_providers[provider] = None
            return False
    
    def _ensure_embedding_provider(self, provider: str) -> bool:
        """Ensure embedding provider is available and initialized"""
        try:
            if provider not in self._embedding_providers or not self._embedding_providers[provider]:
                if provider == "openai":
                    self._embedding_providers[provider] = self._create_openai_embedding_provider()
                elif provider == "ollama":
                    self._embedding_providers[provider] = self._create_ollama_embedding_provider()
                else:
                    raise ValueError(f"Unknown embedding provider: {provider}")
            
            # Test provider health
            if self._embedding_providers[provider]:
                if hasattr(self._embedding_providers[provider], 'health_check'):
                    if not self._embedding_providers[provider].health_check():
                        logger.warning(f"Embedding provider {provider} failed health check")
                        return False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error ensuring embedding provider {provider}: {e}")
            self._embedding_providers[provider] = None
            return False
    
    def _create_openai_chat_provider(self):
        """Create OpenAI chat provider"""
        try:
            from .enhanced_chat_engine import OpenAIChatProvider
            settings = self._settings_manager.get_settings()
            
            if not settings.openai_api_key:
                logger.warning("No OpenAI API key configured")
                return None
            
            provider = OpenAIChatProvider(
                model_name=settings.openai_chat_model,
                api_key=settings.openai_api_key
            )
            
            logger.info(f"Created OpenAI chat provider with model: {settings.openai_chat_model}")
            return provider
            
        except Exception as e:
            logger.error(f"Error creating OpenAI chat provider: {e}")
            return None
    
    def _create_ollama_chat_provider(self):
        """Create Ollama chat provider"""
        try:
            from .enhanced_chat_engine import OllamaChatProvider
            settings = self._settings_manager.get_settings()
            
            if not settings.ollama_enabled:
                logger.warning("Ollama not enabled")
                return None
            
            provider = OllamaChatProvider(model_name=settings.ollama_chat_model)
            logger.info(f"Created Ollama chat provider with model: {settings.ollama_chat_model}")
            return provider
            
        except Exception as e:
            logger.error(f"Error creating Ollama chat provider: {e}")
            return None
    
    def _create_openai_embedding_provider(self):
        """Create OpenAI embedding provider"""
        try:
            from langchain_openai import OpenAIEmbeddings
            settings = self._settings_manager.get_settings()
            
            if not settings.openai_api_key:
                logger.warning("No OpenAI API key configured")
                return None
            
            embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model=settings.openai_embedding_model
            )
            
            logger.info(f"Created OpenAI embedding provider with model: {settings.openai_embedding_model}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating OpenAI embedding provider: {e}")
            return None
    
    def _create_ollama_embedding_provider(self):
        """Create Ollama embedding provider"""
        try:
            from .ollama_integration import OllamaEmbeddingEngine
            settings = self._settings_manager.get_settings()
            
            if not settings.ollama_enabled:
                logger.warning("Ollama not enabled")
                return None
            
            # Create a simple wrapper to match OpenAI embedding interface
            class OllamaEmbeddingWrapper:
                def __init__(self, model_name):
                    self.embedding_engine = OllamaEmbeddingEngine(model_name)
                    self.model_name = model_name
                
                def embed_documents(self, texts):
                    return self.embedding_engine.embed_documents(texts)
                
                def embed_query(self, text):
                    embedding = self.embedding_engine.embed_text(text)
                    if embedding is None:
                        raise RuntimeError("Failed to generate embedding")
                    return embedding
                
                def health_check(self):
                    return self.embedding_engine.health_check()
            
            embeddings = OllamaEmbeddingWrapper(settings.ollama_embedding_model)
            logger.info(f"Created Ollama embedding provider with model: {settings.ollama_embedding_model}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating Ollama embedding provider: {e}")
            return None
    
    def _handle_provider_change(self, change_type: str, data: Dict[str, Any]):
        """Handle provider changes from settings manager"""
        with self._lock:
            try:
                logger.info(f"Handling provider change: {change_type} with data: {data}")
                
                if change_type == 'chat_provider':
                    self._switch_chat_provider(data['provider'])
                
                elif change_type == 'embedding_provider':
                    self._switch_embedding_provider(data['provider'])
                
                elif change_type == 'ollama_settings':
                    self._reinitialize_ollama_providers(data)
                
                elif change_type == 'openai_settings':
                    self._reinitialize_openai_providers(data)
                
                elif change_type == 'force_reinitialize':
                    self._force_reinitialize_all()
                
                # Notify registered components
                self._notify_components_of_changes(change_type, data)
                
            except Exception as e:
                logger.error(f"Error handling provider change: {e}")
    
    def _switch_chat_provider(self, new_provider: str):
        """Switch to a different chat provider"""
        try:
            old_provider = self._current_chat_provider
            
            # Ensure new provider is available
            if not self._ensure_chat_provider(new_provider):
                raise RuntimeError(f"Failed to initialize chat provider: {new_provider}")
            
            self._current_chat_provider = new_provider
            logger.info(f"Switched chat provider from {old_provider} to {new_provider}")
            
        except Exception as e:
            logger.error(f"Error switching chat provider to {new_provider}: {e}")
            raise
    
    def _switch_embedding_provider(self, new_provider: str):
        """Switch to a different embedding provider"""
        try:
            old_provider = self._current_embedding_provider
            
            # Ensure new provider is available
            if not self._ensure_embedding_provider(new_provider):
                raise RuntimeError(f"Failed to initialize embedding provider: {new_provider}")
            
            self._current_embedding_provider = new_provider
            logger.info(f"Switched embedding provider from {old_provider} to {new_provider}")
            
        except Exception as e:
            logger.error(f"Error switching embedding provider to {new_provider}: {e}")
            raise
    
    def _reinitialize_ollama_providers(self, data: Dict[str, Any]):
        """Reinitialize Ollama providers with new settings"""
        try:
            # Clear existing Ollama providers
            if 'ollama' in self._chat_providers:
                del self._chat_providers['ollama']
            if 'ollama' in self._embedding_providers:
                del self._embedding_providers['ollama']
            
            # Reinitialize if enabled
            if data.get('enabled', False):
                if self._current_chat_provider == 'ollama':
                    self._ensure_chat_provider('ollama')
                if self._current_embedding_provider == 'ollama':
                    self._ensure_embedding_provider('ollama')
            
            logger.info("Reinitialized Ollama providers")
            
        except Exception as e:
            logger.error(f"Error reinitializing Ollama providers: {e}")
    
    def _reinitialize_openai_providers(self, data: Dict[str, Any]):
        """Reinitialize OpenAI providers with new settings"""
        try:
            # Clear existing OpenAI providers
            if 'openai' in self._chat_providers:
                del self._chat_providers['openai']
            if 'openai' in self._embedding_providers:
                del self._embedding_providers['openai']
            
            # Reinitialize if API key is set
            if data.get('api_key_set', False):
                if self._current_chat_provider == 'openai':
                    self._ensure_chat_provider('openai')
                if self._current_embedding_provider == 'openai':
                    self._ensure_embedding_provider('openai')
            
            logger.info("Reinitialized OpenAI providers")
            
        except Exception as e:
            logger.error(f"Error reinitializing OpenAI providers: {e}")
    
    def _force_reinitialize_all(self):
        """Force reinitialize all providers"""
        try:
            # Clear all provider caches
            self._chat_providers.clear()
            self._embedding_providers.clear()
            
            # Reinitialize current providers
            settings = self._settings_manager.get_settings()
            self._current_chat_provider = settings.preferred_chat_provider
            self._current_embedding_provider = settings.preferred_embedding_provider
            
            self._ensure_chat_provider(self._current_chat_provider)
            self._ensure_embedding_provider(self._current_embedding_provider)
            
            logger.info("Force reinitialized all providers")
            
        except Exception as e:
            logger.error(f"Error during force reinitialization: {e}")
    
    def _notify_components_of_changes(self, change_type: str, data: Dict[str, Any]):
        """Notify registered components of provider changes"""
        for component in self._registered_components:
            try:
                if hasattr(component, 'on_provider_change'):
                    component.on_provider_change(change_type, data)
                elif hasattr(component, 'reinitialize_providers'):
                    component.reinitialize_providers()
            except Exception as e:
                logger.error(f"Error notifying component {component} of provider change: {e}")
    
    def register_component(self, component: Any):
        """Register a component to be notified of provider changes"""
        self._registered_components.add(component)
        logger.info(f"Registered component {type(component).__name__} for provider change notifications")
    
    def unregister_component(self, component: Any):
        """Unregister a component from provider change notifications"""
        self._registered_components.discard(component)
    
    def get_chat_provider(self, provider: Optional[str] = None):
        """Get current or specific chat provider"""
        provider = provider or self._current_chat_provider
        
        with self._lock:
            if provider not in self._chat_providers or not self._chat_providers[provider]:
                if not self._ensure_chat_provider(provider):
                    raise RuntimeError(f"Chat provider {provider} is not available")
            
            return self._chat_providers[provider]
    
    def get_embedding_provider(self, provider: Optional[str] = None):
        """Get current or specific embedding provider"""
        provider = provider or self._current_embedding_provider
        
        with self._lock:
            if provider not in self._embedding_providers or not self._embedding_providers[provider]:
                if not self._ensure_embedding_provider(provider):
                    raise RuntimeError(f"Embedding provider {provider} is not available")
            
            return self._embedding_providers[provider]
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            'current_providers': {
                'chat': self._current_chat_provider,
                'embedding': self._current_embedding_provider
            },
            'available_providers': {
                'chat': list(self._chat_providers.keys()),
                'embedding': list(self._embedding_providers.keys())
            },
            'provider_health': {}
        }
        
        # Check health of all providers
        for provider_type, providers in [('chat', self._chat_providers), ('embedding', self._embedding_providers)]:
            status['provider_health'][provider_type] = {}
            
            for provider_name, provider_instance in providers.items():
                if provider_instance and hasattr(provider_instance, 'health_check'):
                    try:
                        healthy = provider_instance.health_check()
                        status['provider_health'][provider_type][provider_name] = {
                            'healthy': healthy,
                            'message': 'OK' if healthy else 'Health check failed'
                        }
                    except Exception as e:
                        status['provider_health'][provider_type][provider_name] = {
                            'healthy': False,
                            'message': f'Health check error: {str(e)}'
                        }
                else:
                    status['provider_health'][provider_type][provider_name] = {
                        'healthy': provider_instance is not None,
                        'message': 'No health check available' if provider_instance else 'Not initialized'
                    }
        
        return status
    
    def test_provider(self, provider_type: str, provider_name: str) -> Dict[str, Any]:
        """Test a specific provider"""
        try:
            if provider_type == 'chat':
                provider = self.get_chat_provider(provider_name)
                if hasattr(provider, 'health_check'):
                    healthy = provider.health_check()
                    return {
                        'success': healthy,
                        'message': 'Provider is healthy' if healthy else 'Provider health check failed'
                    }
            
            elif provider_type == 'embedding':
                provider = self.get_embedding_provider(provider_name)
                if hasattr(provider, 'health_check'):
                    healthy = provider.health_check()
                    return {
                        'success': healthy,
                        'message': 'Provider is healthy' if healthy else 'Provider health check failed'
                    }
            
            return {
                'success': True,
                'message': f'Provider {provider_name} is available but no health check implemented'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Provider test failed: {str(e)}'
            }
    
    def cleanup(self):
        """Cleanup provider manager resources"""
        with self._lock:
            # Clear all providers
            self._chat_providers.clear()
            self._embedding_providers.clear()
            self._registered_components.clear()
            
            logger.info("Provider manager cleaned up")


# Global instance
_provider_manager = None

def get_provider_manager() -> ProviderManager:
    """Get global provider manager instance"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager
