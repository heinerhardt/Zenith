"""
Enhanced Settings Manager for Zenith - Handles dynamic reinitialization and provider switching
"""

from typing import Dict, Any, Optional, List, Tuple, Callable
import json
from datetime import datetime
import threading

from .qdrant_manager import get_qdrant_client
from .config import config
from ..auth.models import SystemSettings
from ..utils.logger import get_logger
from qdrant_client.http import models

logger = get_logger(__name__)


class ProviderInitializationError(Exception):
    """Exception raised when provider initialization fails"""
    pass


class EnhancedSettingsManager:
    """
    Enhanced settings manager with dynamic reinitialization and provider switching
    """
    
    def __init__(self):
        """Initialize enhanced settings manager"""
        self.qdrant_manager = get_qdrant_client()
        self.collection_name = "zenith_settings"
        self.settings_id = 1
        
        # Thread lock for settings operations
        self._lock = threading.Lock()
        
        # Provider state tracking
        self._provider_states = {
            'ollama_initialized': False,
            'openai_initialized': False,
            'last_chat_provider': None,
            'last_embedding_provider': None
        }
        
        # Callbacks for when providers change
        self._provider_change_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # Ensure settings collection exists
        self._ensure_settings_collection()
        
        # Load current settings
        self._current_settings = self._load_settings()
        
        # Initialize provider states
        self._initialize_provider_states()
    
    def register_provider_change_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Register callback to be called when provider settings change
        
        Args:
            callback: Function to call with (provider_type, new_settings) when provider changes
        """
        self._provider_change_callbacks.append(callback)
    
    def _ensure_settings_collection(self):
        """Ensure settings collection exists"""
        try:
            if not self.qdrant_manager.collection_exists(self.collection_name):
                # Create collection with minimal vector size for settings
                success = self.qdrant_manager.create_collection(
                    self.collection_name,
                    vector_size=384,
                    distance=models.Distance.COSINE
                )
                
                if success:
                    # Create index for setting types
                    self.qdrant_manager.create_index(
                        self.collection_name, 
                        "setting_type", 
                        "keyword"
                    )
                    logger.info("Created settings collection")
                
        except Exception as e:
            logger.error(f"Error ensuring settings collection: {e}")
    
    def _create_settings_vector(self, settings_id: int) -> List[float]:
        """Create a simple vector for settings storage"""
        import hashlib
        
        # Create a deterministic vector based on settings ID
        hash_obj = hashlib.sha256(str(settings_id).encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 384-dimensional vector
        vector = []
        for i in range(384):
            byte_index = i % len(hash_bytes)
            vector.append((hash_bytes[byte_index] - 128) / 128.0)
        
        return vector
    
    def _load_settings(self) -> SystemSettings:
        """Load settings from Qdrant"""
        try:
            # Try to retrieve existing settings
            points = self.qdrant_manager.get_points(
                self.collection_name,
                [self.settings_id],
                with_vectors=False
            )
            
            if points and len(points) > 0:
                settings_data = points[0].payload
                if settings_data.get("setting_type") == "system":
                    # Remove metadata
                    clean_data = {k: v for k, v in settings_data.items() 
                                if k not in ["setting_type", "vector"]}
                    return SystemSettings.from_dict(clean_data)
            
            # Create default settings if none exist
            logger.info("Creating default system settings")
            default_settings = SystemSettings()
            self._save_settings(default_settings)
            return default_settings
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return SystemSettings()
    
    def _save_settings(self, settings: SystemSettings) -> bool:
        """Save settings to Qdrant"""
        try:
            # Create vector for storage
            vector = self._create_settings_vector(self.settings_id)
            
            # Prepare payload
            payload = settings.to_dict()
            payload["setting_type"] = "system"
            
            # Create point
            point = models.PointStruct(
                id=self.settings_id,
                vector=vector,
                payload=payload
            )
            
            # Upsert to Qdrant
            success = self.qdrant_manager.upsert_points(
                self.collection_name,
                [point]
            )
            
            if success:
                logger.info("System settings saved successfully")
                return True
            else:
                logger.error("Failed to save system settings")
                return False
                
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def _initialize_provider_states(self):
        """Initialize provider states based on current settings"""
        settings = self._current_settings
        
        # Update provider states
        self._provider_states.update({
            'last_chat_provider': settings.preferred_chat_provider,
            'last_embedding_provider': settings.preferred_embedding_provider,
            'ollama_initialized': settings.ollama_enabled,
            'openai_initialized': bool(settings.openai_api_key)
        })
    
    def get_settings(self) -> SystemSettings:
        """Get current system settings"""
        with self._lock:
            return self._current_settings
    
    def update_settings(self, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update system settings with dynamic reinitialization
        
        Args:
            updates: Dictionary of setting updates
            
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            try:
                # Validate updates
                validation_error = self._validate_settings_update(updates)
                if validation_error:
                    return False, validation_error
                
                # Store previous settings for comparison
                old_settings = self._current_settings.to_dict()
                
                # Apply updates to current settings
                settings_dict = self._current_settings.to_dict()
                settings_dict.update(updates)
                settings_dict["updated_at"] = datetime.now()
                
                # Create new settings object
                new_settings = SystemSettings.from_dict(settings_dict)
                
                # Check what changed and needs reinitialization
                provider_changes = self._detect_provider_changes(old_settings, settings_dict)
                
                # Test new provider configurations before saving
                validation_result = self._validate_provider_configurations(new_settings, provider_changes)
                if not validation_result[0]:
                    return validation_result
                
                # Save to Qdrant
                if self._save_settings(new_settings):
                    self._current_settings = new_settings
                    
                    # Apply provider changes dynamically
                    self._apply_provider_changes(provider_changes, new_settings)
                    
                    # Update global config for backward compatibility
                    self._update_global_config(new_settings)
                    
                    logger.info(f"Settings updated with provider changes: {list(updates.keys())}")
                    return True, "Settings updated successfully with provider reinitialization"
                else:
                    return False, "Failed to save settings"
                    
            except Exception as e:
                logger.error(f"Error updating settings: {e}")
                return False, f"Update failed: {str(e)}"
    
    def _detect_provider_changes(self, old_settings: Dict[str, Any], new_settings: Dict[str, Any]) -> Dict[str, bool]:
        """Detect which providers need reinitialization"""
        changes = {
            'chat_provider_changed': False,
            'embedding_provider_changed': False,
            'ollama_settings_changed': False,
            'openai_settings_changed': False,
            'ollama_enabled_changed': False
        }
        
        # Check for provider switches
        if old_settings.get('preferred_chat_provider') != new_settings.get('preferred_chat_provider'):
            changes['chat_provider_changed'] = True
        
        if old_settings.get('preferred_embedding_provider') != new_settings.get('preferred_embedding_provider'):
            changes['embedding_provider_changed'] = True
        
        # Check for Ollama configuration changes
        ollama_settings = [
            'ollama_enabled', 'ollama_endpoint', 'ollama_chat_model', 'ollama_embedding_model'
        ]
        for setting in ollama_settings:
            if old_settings.get(setting) != new_settings.get(setting):
                changes['ollama_settings_changed'] = True
                if setting == 'ollama_enabled':
                    changes['ollama_enabled_changed'] = True
                break
        
        # Check for OpenAI configuration changes
        openai_settings = [
            'openai_api_key', 'openai_chat_model', 'openai_embedding_model'
        ]
        for setting in openai_settings:
            if old_settings.get(setting) != new_settings.get(setting):
                changes['openai_settings_changed'] = True
                break
        
        return changes
    
    def _validate_provider_configurations(self, new_settings: SystemSettings, changes: Dict[str, bool]) -> Tuple[bool, str]:
        """Validate new provider configurations before applying"""
        
        # Test Ollama if enabled or settings changed
        if new_settings.ollama_enabled and (changes['ollama_settings_changed'] or changes['ollama_enabled_changed']):
            ollama_result = self._test_ollama_configuration(new_settings, skip_model_pull=False)
            if not ollama_result[0]:
                return False, f"Ollama validation failed: {ollama_result[1]}"
        
        # Test OpenAI if it's the selected provider or settings changed
        needs_openai = (
            new_settings.preferred_chat_provider == "openai" or 
            new_settings.preferred_embedding_provider == "openai" or
            changes['openai_settings_changed']
        )
        
        if needs_openai and new_settings.openai_api_key:
            openai_result = self._test_openai_configuration(new_settings)
            if not openai_result[0]:
                return False, f"OpenAI validation failed: {openai_result[1]}"
        
        return True, "All provider configurations validated successfully"
    
    def check_ollama_models_availability(self, settings: SystemSettings) -> Tuple[bool, str, Dict[str, bool]]:
        """Quick check if Ollama models are available without attempting to pull them"""
        try:
            from .ollama_integration import OllamaClient
            
            client = OllamaClient(settings.ollama_endpoint)
            if not client.health_check():
                return False, f"Cannot connect to Ollama at {settings.ollama_endpoint}", {}
            
            # Get available models
            available_models = client.list_models()
            model_names = [model.name for model in available_models]
            
            # Check model availability
            models_status = {
                'chat_model': settings.ollama_chat_model in model_names,
                'embedding_model': settings.ollama_embedding_model in model_names
            }
            
            all_available = all(models_status.values())
            
            if all_available:
                return True, "All required Ollama models are available", models_status
            else:
                missing = [name for name, available in [
                    ('chat', models_status['chat_model']), 
                    ('embedding', models_status['embedding_model'])
                ] if not available]
                return False, f"Missing Ollama models: {', '.join(missing)}", models_status
                
        except Exception as e:
            return False, f"Ollama check failed: {str(e)}", {}

    def _test_ollama_configuration(self, settings: SystemSettings, skip_model_pull: bool = False) -> Tuple[bool, str]:
        """Test Ollama configuration"""
        try:
            from .ollama_integration import OllamaClient
            
            client = OllamaClient(settings.ollama_endpoint)
            if not client.health_check():
                return False, f"Cannot connect to Ollama at {settings.ollama_endpoint}"
            
            # Check if required models exist
            available_models = client.list_models()
            model_names = [model.name for model in available_models]
            
            logger.info(f"Available Ollama models: {model_names}")
            
            # Check chat model
            if settings.ollama_chat_model in model_names:
                logger.info(f"Chat model '{settings.ollama_chat_model}' is already available")
            else:
                if skip_model_pull:
                    logger.warning(f"Chat model '{settings.ollama_chat_model}' not available (skipping auto-pull)")
                    return False, f"Chat model '{settings.ollama_chat_model}' not available"
                else:
                    # Try to pull the model
                    logger.info(f"Attempting to pull missing chat model: {settings.ollama_chat_model}")
                    if not client.pull_model(settings.ollama_chat_model):
                        return False, f"Chat model '{settings.ollama_chat_model}' not available and could not be pulled"
            
            # Check embedding model
            if settings.ollama_embedding_model in model_names:
                logger.info(f"Embedding model '{settings.ollama_embedding_model}' is already available")
            else:
                if skip_model_pull:
                    logger.warning(f"Embedding model '{settings.ollama_embedding_model}' not available (skipping auto-pull)")
                    return False, f"Embedding model '{settings.ollama_embedding_model}' not available"
                else:
                    logger.info(f"Attempting to pull missing embedding model: {settings.ollama_embedding_model}")
                    if not client.pull_model(settings.ollama_embedding_model):
                        return False, f"Embedding model '{settings.ollama_embedding_model}' not available and could not be pulled"
            
            return True, "Ollama configuration validated successfully"
            
        except Exception as e:
            return False, f"Ollama test failed: {str(e)}"
    
    def _test_openai_configuration(self, settings: SystemSettings) -> Tuple[bool, str]:
        """Test OpenAI configuration"""
        try:
            import openai
            
            # Create temporary client
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            # Test with a simple API call
            response = client.models.list()
            models = [model.id for model in response.data]
            
            # Check if required models are available
            required_models = [settings.openai_chat_model, settings.openai_embedding_model]
            missing_models = [model for model in required_models if model not in models]
            
            if missing_models:
                return False, f"Required OpenAI models not available: {missing_models}"
            
            return True, f"OpenAI configuration validated successfully. {len(models)} models available."
        
        except Exception as e:
            return False, f"OpenAI test failed: {str(e)}"
    
    def _apply_provider_changes(self, changes: Dict[str, bool], new_settings: SystemSettings):
        """Apply provider changes and notify callbacks"""
        
        # Notify callbacks about changes
        if changes['chat_provider_changed']:
            self._notify_callbacks('chat_provider', {
                'provider': new_settings.preferred_chat_provider,
                'settings': self._get_provider_settings(new_settings.preferred_chat_provider, new_settings)
            })
        
        if changes['embedding_provider_changed']:
            self._notify_callbacks('embedding_provider', {
                'provider': new_settings.preferred_embedding_provider,
                'settings': self._get_provider_settings(new_settings.preferred_embedding_provider, new_settings)
            })
        
        if changes['ollama_settings_changed']:
            self._notify_callbacks('ollama_settings', {
                'enabled': new_settings.ollama_enabled,
                'endpoint': new_settings.ollama_endpoint,
                'chat_model': new_settings.ollama_chat_model,
                'embedding_model': new_settings.ollama_embedding_model
            })
        
        if changes['openai_settings_changed']:
            self._notify_callbacks('openai_settings', {
                'api_key_set': bool(new_settings.openai_api_key),
                'chat_model': new_settings.openai_chat_model,
                'embedding_model': new_settings.openai_embedding_model
            })
        
        # Update provider states
        self._provider_states.update({
            'last_chat_provider': new_settings.preferred_chat_provider,
            'last_embedding_provider': new_settings.preferred_embedding_provider,
            'ollama_initialized': new_settings.ollama_enabled,
            'openai_initialized': bool(new_settings.openai_api_key)
        })
        
        logger.info(f"Applied provider changes: {changes}")
    
    def _get_provider_settings(self, provider: str, settings: SystemSettings) -> Dict[str, Any]:
        """Get settings for a specific provider"""
        if provider == "ollama":
            return {
                'endpoint': settings.ollama_endpoint,
                'chat_model': settings.ollama_chat_model,
                'embedding_model': settings.ollama_embedding_model,
                'enabled': settings.ollama_enabled
            }
        elif provider == "openai":
            return {
                'api_key_set': bool(settings.openai_api_key),
                'chat_model': settings.openai_chat_model,
                'embedding_model': settings.openai_embedding_model
            }
        return {}
    
    def _notify_callbacks(self, change_type: str, data: Dict[str, Any]):
        """Notify registered callbacks about provider changes"""
        for callback in self._provider_change_callbacks:
            try:
                callback(change_type, data)
            except Exception as e:
                logger.error(f"Error in provider change callback: {e}")
    
    def _update_global_config(self, settings: SystemSettings):
        """Update global config object for backward compatibility"""
        try:
            # Update key config attributes
            config.ollama_enabled = settings.ollama_enabled
            config.ollama_base_url = settings.ollama_endpoint
            config.ollama_chat_model = settings.ollama_chat_model
            config.ollama_embedding_model = settings.ollama_embedding_model
            
            config.openai_model = settings.openai_chat_model
            config.openai_embedding_model = settings.openai_embedding_model
            if settings.openai_api_key:
                config.openai_api_key = settings.openai_api_key
            
            config.chat_provider = settings.preferred_chat_provider
            config.embedding_provider = settings.preferred_embedding_provider
            
            logger.info("Updated global config with new settings")
            
        except Exception as e:
            logger.error(f"Error updating global config: {e}")
    
    def _validate_settings_update(self, updates: Dict[str, Any]) -> Optional[str]:
        """Validate settings updates"""
        
        # Validate model providers
        if "preferred_chat_provider" in updates:
            if updates["preferred_chat_provider"] not in ["openai", "ollama"]:
                return "Invalid chat provider. Must be 'openai' or 'ollama'"
        
        if "preferred_embedding_provider" in updates:
            if updates["preferred_embedding_provider"] not in ["openai", "ollama"]:
                return "Invalid embedding provider. Must be 'openai' or 'ollama'"
        
        # Validate Qdrant mode
        if "qdrant_mode" in updates:
            if updates["qdrant_mode"] not in ["local", "cloud"]:
                return "Invalid Qdrant mode. Must be 'local' or 'cloud'"
        
        # Validate numeric values
        numeric_fields = {
            "chunk_size": (100, 4000),
            "chunk_overlap": (0, 1000),
            "max_chunks_per_query": (1, 50),
            "max_file_size_mb": (1, 500),
            "session_duration_hours": (1, 168),
            "max_users": (1, 10000)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in updates:
                try:
                    value = int(updates[field])
                    if not (min_val <= value <= max_val):
                        return f"{field} must be between {min_val} and {max_val}"
                except (ValueError, TypeError):
                    return f"{field} must be a valid number"
        
        # Validate boolean fields
        boolean_fields = [
            "ollama_enabled", "minio_enabled", "allow_user_registration",
            "require_admin_approval", "minio_secure"
        ]
        
        for field in boolean_fields:
            if field in updates:
                if not isinstance(updates[field], bool):
                    return f"{field} must be true or false"
        
        return None
    
    def force_reinitialize_providers(self) -> Tuple[bool, str]:
        """Force reinitialization of all providers"""
        try:
            settings = self._current_settings
            
            # Force reinitialize Ollama if enabled
            if settings.ollama_enabled:
                # First, do a quick check to see if models are already available
                models_available, models_message, models_status = self.check_ollama_models_availability(settings)
                
                if models_available:
                    logger.info("All Ollama models are already available - skipping detailed validation")
                    # Just do a quick health check
                    ollama_result = self._test_ollama_configuration(settings, skip_model_pull=True)
                else:
                    logger.info(f"Ollama model status: {models_message}")
                    # Use skip_model_pull=True to avoid hanging during force reinitialization
                    ollama_result = self._test_ollama_configuration(settings, skip_model_pull=True)
                
                if not ollama_result[0]:
                    return False, f"Ollama reinitialization failed: {ollama_result[1]}"
            
            # Force reinitialize OpenAI if API key is set
            if settings.openai_api_key:
                openai_result = self._test_openai_configuration(settings)
                if not openai_result[0]:
                    return False, f"OpenAI reinitialization failed: {openai_result[1]}"
            
            # Notify all callbacks to force reinitialization
            self._notify_callbacks('force_reinitialize', {
                'chat_provider': settings.preferred_chat_provider,
                'embedding_provider': settings.preferred_embedding_provider,
                'ollama_enabled': settings.ollama_enabled,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info("Force reinitialization completed successfully")
            return True, "All providers reinitialized successfully"
            
        except Exception as e:
            logger.error(f"Error during force reinitialization: {e}")
            return False, f"Reinitialization failed: {str(e)}"
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get current provider status and health"""
        status = {
            'current_providers': {
                'chat': self._current_settings.preferred_chat_provider,
                'embedding': self._current_settings.preferred_embedding_provider
            },
            'provider_health': {},
            'last_updated': self._current_settings.updated_at.isoformat() if self._current_settings.updated_at else None
        }
        
        # Check OpenAI health
        if self._current_settings.openai_api_key:
            openai_health = self._test_openai_configuration(self._current_settings)
            status['provider_health']['openai'] = {
                'healthy': openai_health[0],
                'message': openai_health[1],
                'configured': True
            }
        else:
            status['provider_health']['openai'] = {
                'healthy': False,
                'message': "No API key configured",
                'configured': False
            }
        
        # Check Ollama health
        if self._current_settings.ollama_enabled:
            ollama_health = self._test_ollama_configuration(self._current_settings, skip_model_pull=True)
            status['provider_health']['ollama'] = {
                'healthy': ollama_health[0],
                'message': ollama_health[1],
                'configured': True,
                'enabled': True
            }
        else:
            status['provider_health']['ollama'] = {
                'healthy': False,
                'message': "Ollama not enabled",
                'configured': False,
                'enabled': False
            }
        
        return status
    
    # Backward compatibility methods
    def get_chat_provider_settings(self) -> Dict[str, Any]:
        """Get chat provider specific settings (backward compatibility)"""
        settings = self._current_settings
        
        return {
            "openai": {
                "enabled": bool(settings.openai_api_key),
                "api_key_set": bool(settings.openai_api_key),
                "chat_model": settings.openai_chat_model,
                "embedding_model": settings.openai_embedding_model
            },
            "ollama": {
                "enabled": settings.ollama_enabled,
                "endpoint": settings.ollama_endpoint,
                "chat_model": settings.ollama_chat_model,
                "embedding_model": settings.ollama_embedding_model
            },
            "current": {
                "chat_provider": settings.preferred_chat_provider,
                "embedding_provider": settings.preferred_embedding_provider
            }
        }
    
    def test_openai_connection(self, api_key: str) -> Tuple[bool, str]:
        """Test OpenAI connection (backward compatibility)"""
        try:
            # Create temporary settings object for testing
            test_settings = SystemSettings()
            test_settings.openai_api_key = api_key
            test_settings.openai_chat_model = self._current_settings.openai_chat_model
            test_settings.openai_embedding_model = self._current_settings.openai_embedding_model
            
            return self._test_openai_configuration(test_settings)
        except Exception as e:
            return False, f"Test failed: {str(e)}"
    
    def test_ollama_connection(self, endpoint: str) -> Tuple[bool, str]:
        """Test Ollama connection (backward compatibility)"""
        try:
            # Create temporary settings object for testing
            test_settings = SystemSettings()
            test_settings.ollama_endpoint = endpoint
            test_settings.ollama_chat_model = self._current_settings.ollama_chat_model
            test_settings.ollama_embedding_model = self._current_settings.ollama_embedding_model
            
            return self._test_ollama_configuration(test_settings, skip_model_pull=False)
        except Exception as e:
            return False, f"Test failed: {str(e)}"


# Global instance
_enhanced_settings_manager = None

def get_enhanced_settings_manager() -> EnhancedSettingsManager:
    """Get global enhanced settings manager instance"""
    global _enhanced_settings_manager
    if _enhanced_settings_manager is None:
        _enhanced_settings_manager = EnhancedSettingsManager()
    return _enhanced_settings_manager


# Backward compatibility
def get_settings_manager():
    """Get settings manager (backward compatibility)"""
    return get_enhanced_settings_manager()
