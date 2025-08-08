"""
Settings Manager for Zenith - Handles system configuration and admin settings
"""

from typing import Dict, Any, Optional, List, Tuple
import json
from datetime import datetime

from .qdrant_manager import get_qdrant_client
from .config import config
from ..auth.models import SystemSettings
from ..utils.logger import get_logger
from qdrant_client.http import models

logger = get_logger(__name__)


class SettingsManager:
    """
    Manages system settings stored in Qdrant
    """
    
    def __init__(self):
        """Initialize settings manager"""
        self.qdrant_manager = get_qdrant_client()
        self.collection_name = "zenith_settings"
        self.settings_id = 1  # Use integer ID instead of string
        
        # Ensure settings collection exists
        self._ensure_settings_collection()
        
        # Load or create default settings
        self._current_settings = self._load_settings()
    
    def _ensure_settings_collection(self):
        """Ensure settings collection exists"""
        try:
            if not self.qdrant_manager.collection_exists(self.collection_name):
                # Create collection with minimal vector size for settings
                success = self.qdrant_manager.create_collection(
                    self.collection_name,
                    vector_size=384,  # Small vector for settings
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
    
    def get_settings(self) -> SystemSettings:
        """Get current system settings"""
        return self._current_settings
    
    def update_settings(self, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update system settings
        
        Args:
            updates: Dictionary of setting updates
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate updates
            validation_error = self._validate_settings_update(updates)
            if validation_error:
                return False, validation_error
            
            # Apply updates to current settings
            settings_dict = self._current_settings.to_dict()
            settings_dict.update(updates)
            settings_dict["updated_at"] = datetime.now()
            
            # Create new settings object
            new_settings = SystemSettings.from_dict(settings_dict)
            
            # Save to Qdrant
            if self._save_settings(new_settings):
                self._current_settings = new_settings
                logger.info(f"Settings updated: {list(updates.keys())}")
                return True, "Settings updated successfully"
            else:
                return False, "Failed to save settings"
                
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False, f"Update failed: {str(e)}"
    
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
            "session_duration_hours": (1, 168),  # 1 hour to 1 week
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
    
    def get_chat_provider_settings(self) -> Dict[str, Any]:
        """Get chat provider specific settings"""
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
    
    def get_qdrant_settings(self) -> Dict[str, Any]:
        """Get Qdrant specific settings"""
        settings = self._current_settings
        
        return {
            "mode": settings.qdrant_mode,
            "local": {
                "host": settings.qdrant_local_host,
                "port": settings.qdrant_local_port
            },
            "cloud": {
                "url": settings.qdrant_cloud_url,
                "api_key_set": bool(settings.qdrant_cloud_api_key)
            },
            "collection_name": settings.qdrant_collection_name
        }
    
    def get_processing_settings(self) -> Dict[str, Any]:
        """Get document processing settings"""
        settings = self._current_settings
        
        return {
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "max_chunks_per_query": settings.max_chunks_per_query,
            "max_file_size_mb": settings.max_file_size_mb
        }
    
    def get_user_management_settings(self) -> Dict[str, Any]:
        """Get user management settings"""
        settings = self._current_settings
        
        return {
            "allow_user_registration": settings.allow_user_registration,
            "require_admin_approval": settings.require_admin_approval,
            "session_duration_hours": settings.session_duration_hours,
            "max_users": settings.max_users
        }
    
    def get_minio_settings(self) -> Dict[str, Any]:
        """Get MinIO settings"""
        settings = self._current_settings
        
        return {
            "enabled": settings.minio_enabled,
            "endpoint": settings.minio_endpoint,
            "access_key_set": bool(settings.minio_access_key),
            "secret_key_set": bool(settings.minio_secret_key),
            "secure": settings.minio_secure
        }
    
    def test_openai_connection(self, api_key: Optional[str] = None) -> Tuple[bool, str]:
        """Test OpenAI connection"""
        try:
            from ..core.enhanced_chat_engine import OpenAIChatProvider
            
            test_key = api_key or self._current_settings.openai_api_key
            if not test_key:
                return False, "No API key provided"
            
            provider = OpenAIChatProvider(api_key=test_key)
            healthy = provider.health_check()
            
            if healthy:
                return True, "OpenAI connection successful"
            else:
                return False, "OpenAI connection failed"
                
        except Exception as e:
            return False, f"OpenAI test failed: {str(e)}"
    
    def test_ollama_connection(self, endpoint: Optional[str] = None) -> Tuple[bool, str]:
        """Test Ollama connection"""
        try:
            from ..core.ollama_integration import OllamaClient
            
            test_endpoint = endpoint or self._current_settings.ollama_endpoint
            client = OllamaClient(test_endpoint)
            
            if client.health_check():
                models = client.list_models()
                return True, f"Ollama connection successful. Found {len(models)} models"
            else:
                return False, "Ollama server not accessible"
                
        except Exception as e:
            return False, f"Ollama test failed: {str(e)}"
    
    def test_qdrant_connection(self, mode: str, **kwargs) -> Tuple[bool, str]:
        """Test Qdrant connection"""
        try:
            from ..core.qdrant_manager import QdrantManager
            
            # Create temporary manager with test settings
            test_manager = QdrantManager(mode)
            
            if test_manager.health_check():
                collections = test_manager.get_client().get_collections()
                return True, f"Qdrant connection successful. Found {len(collections.collections)} collections"
            else:
                return False, "Qdrant connection failed"
                
        except Exception as e:
            return False, f"Qdrant test failed: {str(e)}"
    
    def reset_to_defaults(self) -> Tuple[bool, str]:
        """Reset settings to defaults"""
        try:
            default_settings = SystemSettings()
            
            if self._save_settings(default_settings):
                self._current_settings = default_settings
                logger.info("Settings reset to defaults")
                return True, "Settings reset to defaults successfully"
            else:
                return False, "Failed to reset settings"
                
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False, f"Reset failed: {str(e)}"
    
    def export_settings(self) -> Dict[str, Any]:
        """Export settings for backup"""
        settings_dict = self._current_settings.to_dict()
        
        # Remove sensitive information
        sensitive_fields = [
            "openai_api_key", "qdrant_cloud_api_key", 
            "minio_access_key", "minio_secret_key"
        ]
        
        for field in sensitive_fields:
            if field in settings_dict and settings_dict[field]:
                settings_dict[field] = "***REDACTED***"
        
        return {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "settings": settings_dict
        }
    
    def import_settings(self, settings_data: Dict[str, Any], 
                       include_sensitive: bool = False) -> Tuple[bool, str]:
        """Import settings from backup"""
        try:
            if "settings" not in settings_data:
                return False, "Invalid settings format"
            
            imported_settings = settings_data["settings"]
            
            # Filter out redacted sensitive fields unless explicitly including them
            if not include_sensitive:
                sensitive_fields = [
                    "openai_api_key", "qdrant_cloud_api_key",
                    "minio_access_key", "minio_secret_key"
                ]
                
                for field in sensitive_fields:
                    if field in imported_settings and imported_settings[field] == "***REDACTED***":
                        # Keep current value
                        current_value = getattr(self._current_settings, field, None)
                        imported_settings[field] = current_value
            
            # Validate and update
            validation_error = self._validate_settings_update(imported_settings)
            if validation_error:
                return False, f"Validation error: {validation_error}"
            
            # Create new settings
            imported_settings["updated_at"] = datetime.now()
            new_settings = SystemSettings.from_dict(imported_settings)
            
            if self._save_settings(new_settings):
                self._current_settings = new_settings
                logger.info("Settings imported successfully")
                return True, "Settings imported successfully"
            else:
                return False, "Failed to save imported settings"
                
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False, f"Import failed: {str(e)}"


# Global instance
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """Get global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
