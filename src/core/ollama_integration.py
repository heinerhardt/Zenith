"""
Ollama integration for Zenith - Local AI model support
"""

import requests
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import numpy as np

from ..core.config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OllamaModel:
    """Ollama model information"""
    name: str
    size: int
    digest: str
    modified_at: str
    details: Dict[str, Any]


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize Ollama client"""
        self.base_url = base_url or config.ollama_base_url
        self.timeout = 120  # 2 minutes timeout for model operations
        
    def health_check(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def list_models(self) -> List[OllamaModel]:
        """List available models in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_info in data.get("models", []):
                model = OllamaModel(
                    name=model_info["name"],
                    size=model_info["size"],
                    digest=model_info["digest"],
                    modified_at=model_info["modified_at"],
                    details=model_info.get("details", {})
                )
                models.append(model)
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry"""
        try:
            logger.info(f"Pulling Ollama model: {model_name}")
            
            payload = {"name": model_name}
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    if "error" in data:
                        logger.error(f"Error pulling model: {data['error']}")
                        return False
                    
                    # Log progress
                    if "status" in data:
                        logger.info(f"Pull progress: {data['status']}")
            
            logger.info(f"Successfully pulled model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def generate_chat_completion(self, messages: List[Dict[str, str]], 
                               model: str, stream: bool = False) -> Dict[str, Any]:
        """Generate chat completion using Ollama"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if stream:
                return {"stream": response.iter_lines()}
            else:
                return response.json()
                
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return {"error": str(e)}
    
    def generate_embeddings(self, text: str, model: str) -> Optional[List[float]]:
        """Generate embeddings using Ollama"""
        try:
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("embedding")
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def model_exists(self, model_name: str) -> bool:
        """Check if a model exists locally"""
        models = self.list_models()
        return any(model.name == model_name for model in models)


class OllamaChatEngine:
    """Chat engine using Ollama models"""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize Ollama chat engine"""
        self.client = OllamaClient()
        self.model_name = model_name or config.ollama_chat_model
        self.conversation_history: List[Dict[str, str]] = []
        
        # Ensure model is available
        if not self.client.model_exists(self.model_name):
            logger.warning(f"Model {self.model_name} not found. Attempting to pull...")
            if not self.client.pull_model(self.model_name):
                raise RuntimeError(f"Failed to pull model {self.model_name}")
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """Generate chat response"""
        # Add system message if provided
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Generate response
        response = self.client.generate_chat_completion(messages, self.model_name)
        
        if "error" in response:
            raise RuntimeError(f"Chat generation failed: {response['error']}")
        
        assistant_message = response["message"]["content"]
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        # Keep only last 20 messages to manage memory
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return assistant_message
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def health_check(self) -> bool:
        """Check if chat engine is healthy"""
        return self.client.health_check() and self.client.model_exists(self.model_name)


class OllamaEmbeddingEngine:
    """Embedding engine using Ollama models"""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize Ollama embedding engine"""
        self.client = OllamaClient()
        self.model_name = model_name or config.ollama_embedding_model
        
        # Ensure model is available
        if not self.client.model_exists(self.model_name):
            logger.warning(f"Embedding model {self.model_name} not found. Attempting to pull...")
            if not self.client.pull_model(self.model_name):
                raise RuntimeError(f"Failed to pull embedding model {self.model_name}")
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embeddings for text"""
        return self.client.generate_embeddings(text, self.model_name)
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents"""
        embeddings = []
        for doc in documents:
            embedding = self.embed_text(doc)
            if embedding:
                embeddings.append(embedding)
            else:
                logger.warning(f"Failed to generate embedding for document: {doc[:100]}...")
                # Use zero vector as fallback
                embeddings.append([0.0] * 384)  # Default embedding size
        
        return embeddings
    
    def health_check(self) -> bool:
        """Check if embedding engine is healthy"""
        return self.client.health_check() and self.client.model_exists(self.model_name)


class OllamaManager:
    """High-level manager for Ollama services"""
    
    def __init__(self):
        """Initialize Ollama manager"""
        self.client = OllamaClient()
        self._chat_engine = None
        self._embedding_engine = None
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        return config.ollama_enabled and self.client.health_check()
    
    def get_chat_engine(self) -> OllamaChatEngine:
        """Get chat engine instance"""
        if not self._chat_engine:
            self._chat_engine = OllamaChatEngine()
        return self._chat_engine
    
    def get_embedding_engine(self) -> OllamaEmbeddingEngine:
        """Get embedding engine instance"""
        if not self._embedding_engine:
            self._embedding_engine = OllamaEmbeddingEngine()
        return self._embedding_engine
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """List available models categorized by type"""
        models = self.client.list_models()
        
        # Categorize models
        chat_models = []
        embedding_models = []
        
        for model in models:
            model_name = model.name.lower()
            
            # Simple heuristic to categorize models
            if any(keyword in model_name for keyword in ['embed', 'nomic']):
                embedding_models.append(model.name)
            else:
                chat_models.append(model.name)
        
        return {
            'chat': chat_models,
            'embedding': embedding_models
        }
    
    def ensure_models_available(self) -> bool:
        """Ensure required models are available"""
        if not self.is_available():
            return False
        
        # Check chat model
        if not self.client.model_exists(config.ollama_chat_model):
            logger.info(f"Pulling chat model: {config.ollama_chat_model}")
            if not self.client.pull_model(config.ollama_chat_model):
                logger.error(f"Failed to pull chat model: {config.ollama_chat_model}")
                return False
        
        # Check embedding model
        if not self.client.model_exists(config.ollama_embedding_model):
            logger.info(f"Pulling embedding model: {config.ollama_embedding_model}")
            if not self.client.pull_model(config.ollama_embedding_model):
                logger.error(f"Failed to pull embedding model: {config.ollama_embedding_model}")
                return False
        
        return True
    
    def get_model_info(self, model_name: str) -> Optional[OllamaModel]:
        """Get information about a specific model"""
        models = self.client.list_models()
        for model in models:
            if model.name == model_name:
                return model
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        status = {
            'available': self.is_available(),
            'models': {
                'chat': {
                    'configured': config.ollama_chat_model,
                    'available': False
                },
                'embedding': {
                    'configured': config.ollama_embedding_model,
                    'available': False
                }
            }
        }
        
        if status['available']:
            status['models']['chat']['available'] = self.client.model_exists(config.ollama_chat_model)
            status['models']['embedding']['available'] = self.client.model_exists(config.ollama_embedding_model)
        
        return status


# Global instance
_ollama_manager = None

def get_ollama_manager() -> OllamaManager:
    """Get global Ollama manager instance"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager()
    return _ollama_manager
