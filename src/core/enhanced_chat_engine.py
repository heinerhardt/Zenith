"""
Enhanced Chat Engine for Zenith - Supports multiple AI providers and user context
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import time
from ..core.langfuse_integration import trace_rag_flow_if_enabled, flush_langfuse

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.documents import Document

from .config import config
from .enhanced_vector_store import UserVectorStore
from .ollama_integration import get_ollama_manager, OllamaChatEngine
from .provider_manager import get_provider_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    """Chat message with metadata"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    user_id: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None


class ChatProvider:
    """Abstract base for chat providers"""
    
    def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> str:
        """Generate chat response"""
        raise NotImplementedError
    
    def health_check(self) -> bool:
        """Check if provider is healthy"""
        raise NotImplementedError


class OpenAIChatProvider(ChatProvider):
    """OpenAI chat provider"""
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name or config.openai_model
        self.api_key = api_key or config.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model=self.model_name,
            temperature=0.3
        )
    
    def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> str:
        """Generate chat response using OpenAI"""
        try:
            # Convert to LangChain messages
            langchain_messages = []
            
            # Add system message if provided
            if system_prompt:
                langchain_messages.append(SystemMessage(content=system_prompt))
            
            # Add conversation messages
            for msg in messages:
                if msg.role == "user":
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    langchain_messages.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    langchain_messages.append(SystemMessage(content=msg.content))
            
            # Generate response
            response = self.llm.invoke(langchain_messages)
            return response.content
            
        except Exception as e:
            logger.error(f"OpenAI chat generation failed: {e}")
            raise RuntimeError(f"Chat generation failed: {e}")
    
    def health_check(self) -> bool:
        """Check if OpenAI is accessible"""
        try:
            # Simple test with minimal message
            test_message = [ChatMessage(
                role="user",
                content="Hello",
                timestamp=datetime.now()
            )]
            response = self.chat(test_message)
            return bool(response)
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False


class OllamaChatProvider(ChatProvider):
    """Ollama chat provider"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.ollama_chat_model
        
        # Check if Ollama is available
        ollama_manager = get_ollama_manager()
        if not ollama_manager.is_available():
            raise ValueError("Ollama is not available")
        
        self.chat_engine = OllamaChatEngine(self.model_name)
    
    def chat(self, messages: List[ChatMessage], system_prompt: Optional[str] = None) -> str:
        """Generate chat response using Ollama"""
        try:
            # Clear previous conversation for fresh context
            self.chat_engine.clear_history()
            
            # Add non-user/assistant messages to history
            for msg in messages[:-1]:  # All except the last message
                if msg.role in ["user", "assistant"]:
                    self.chat_engine.conversation_history.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Get the last user message
            last_message = messages[-1]
            if last_message.role != "user":
                raise ValueError("Last message must be from user")
            
            # Generate response
            response = self.chat_engine.chat(last_message.content, system_prompt)
            return response
            
        except Exception as e:
            logger.error(f"Ollama chat generation failed: {e}")
            raise RuntimeError(f"Chat generation failed: {e}")
    
    def health_check(self) -> bool:
        """Check if Ollama is accessible"""
        return self.chat_engine.health_check()


def get_chat_provider(provider: Optional[str] = None) -> ChatProvider:
    """Get chat provider based on configuration (uses provider manager)"""
    try:
        provider_manager = get_provider_manager()
        return provider_manager.get_chat_provider(provider)
    except Exception as e:
        logger.error(f"Error getting chat provider from manager, falling back: {e}")
        # Fallback to direct creation
        provider = provider or config.chat_provider
        
        if provider == "openai":
            return OpenAIChatProvider()
        elif provider == "ollama":
            return OllamaChatProvider()
        else:
            raise ValueError(f"Unknown chat provider: {provider}")


class EnhancedChatEngine:
    """
    Enhanced chat engine with user context, multiple providers, and RAG capabilities
    """
    
    def __init__(self, 
                 user_id: Optional[str] = None,
                 vector_store: Optional[UserVectorStore] = None,
                 chat_provider: Optional[str] = None):
        """
        Initialize enhanced chat engine
        
        Args:
            user_id: User ID for conversation isolation
            vector_store: Vector store for RAG
            chat_provider: Chat provider to use
        """
        self.user_id = user_id
        self.vector_store = vector_store
        
        # Initialize chat provider with better error handling
        try:
            self.chat_provider = get_chat_provider(chat_provider)
            logger.info(f"Chat provider initialized: {type(self.chat_provider).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize chat provider: {e}")
            # Try fallback initialization
            try:
                from ..core.config import config
                fallback_provider = config.chat_provider
                logger.warning(f"Trying fallback provider: {fallback_provider}")
                
                if fallback_provider == "openai":
                    from .openai_integration import OpenAIChatProvider
                    self.chat_provider = OpenAIChatProvider()
                elif fallback_provider == "ollama":
                    from .ollama_integration import OllamaChatProvider
                    self.chat_provider = OllamaChatProvider()
                else:
                    raise ValueError(f"No valid chat provider available")
                    
                logger.info(f"Fallback chat provider initialized: {type(self.chat_provider).__name__}")
            except Exception as fallback_error:
                logger.error(f"Fallback provider initialization failed: {fallback_error}")
                raise RuntimeError(f"Cannot initialize any chat provider: {e}, fallback: {fallback_error}")
        
        # Conversation history
        self.conversation_history: List[ChatMessage] = []
        
        # System prompt
        self.system_prompt = self._get_default_system_prompt()
        
        # Register with provider manager for dynamic updates
        try:
            provider_manager = get_provider_manager()
            provider_manager.register_component(self)
        except Exception as e:
            logger.warning(f"Could not register with provider manager: {e}")
        
        logger.info(f"Enhanced chat engine initialized for user: {user_id}")
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt"""
        return """You are Zenith, an AI assistant specialized in analyzing and discussing PDF documents. 

Your capabilities:
- Answer questions based on uploaded document content
- Provide detailed explanations and summaries
- Help users understand complex information
- Cite sources when possible

Guidelines:
- Be accurate and helpful
- If information isn't in the documents, say so clearly
- Provide specific references when quoting from documents
- Be concise but thorough in your responses
- Always be respectful and professional

When no documents are available, you can still assist with general questions using your knowledge."""
    
    def set_system_prompt(self, prompt: str):
        """Set custom system prompt"""
        self.system_prompt = prompt
    
    def chat(self, 
             message: str, 
             use_rag: bool = True,
             max_context_messages: int = 10,
             user_filter: bool = False) -> Dict[str, Any]:
        """
        Generate chat response with optional RAG
        
        Args:
            message: User message
            use_rag: Whether to use RAG for context
            max_context_messages: Maximum context messages to include
            user_filter: Whether to filter documents by current user only (False = search all documents)
            
        Returns:
            Dict with answer and source documents
        """
        start_time = time.time()
        
        try:
            # Create user message
            user_message = ChatMessage(
                role="user",
                content=message,
                timestamp=datetime.now(),
                user_id=self.user_id
            )
            
            # Get relevant documents if using RAG
            source_documents = []
            enhanced_prompt = self.system_prompt
            
            if use_rag and self.vector_store:
                # Search for relevant documents with user filter preference
                relevant_docs = self.vector_store.similarity_search(
                    query=message,
                    k=config.max_chunks_per_query,
                    user_filter=user_filter  # Use provided filter setting
                )
                
                if relevant_docs:
                    # Prepare context from documents
                    context_chunks = []
                    for doc in relevant_docs:
                        # Extract metadata for sources
                        source_info = {
                            "content": doc.page_content[:200] + "...",
                            "filename": doc.metadata.get("filename", "Unknown"),
                            "page": doc.metadata.get("page", "Unknown"),
                            "document_id": doc.metadata.get("document_id"),
                            "chunk_index": doc.metadata.get("chunk_index", 0)
                        }
                        source_documents.append(source_info)
                        context_chunks.append(doc.page_content)
                    
                    # Enhance system prompt with context
                    context_text = "\n\n".join(context_chunks)
                    
                    # Customize prompt based on search scope
                    if user_filter:
                        context_source = "USER'S DOCUMENTS"
                    else:
                        context_source = "SYSTEM DOCUMENTS (ALL USERS)"
                    
                    enhanced_prompt = f"""{self.system_prompt}

CONTEXT FROM {context_source}:
{context_text}

Please answer the user's question based on the provided context. If the context doesn't contain relevant information, mention that and provide what help you can with your general knowledge."""
            
            # Prepare conversation context
            context_messages = self.conversation_history[-max_context_messages:] if self.conversation_history else []
            context_messages.append(user_message)
            
            # Generate response
            try:
                response_content = self.chat_provider.chat(context_messages, enhanced_prompt)
            except Exception as provider_error:
                logger.error(f"Chat provider error: {provider_error}")
                # Try to provide a helpful error message
                if "connection" in str(provider_error).lower() or "timeout" in str(provider_error).lower():
                    return {
                        "answer": "I'm sorry, but I'm having trouble connecting to the AI service. Please check if the AI provider is running and try again.",
                        "source_documents": source_documents,
                        "error": f"Connection error: {str(provider_error)}"
                    }
                elif "api" in str(provider_error).lower() or "key" in str(provider_error).lower():
                    return {
                        "answer": "I'm sorry, but there's an issue with the AI service configuration. Please check the API key settings.",
                        "source_documents": source_documents,
                        "error": f"API error: {str(provider_error)}"
                    }
                else:
                    return {
                        "answer": "I'm sorry, but I encountered an error while generating a response. Please try again or contact support.",
                        "source_documents": source_documents,
                        "error": f"Provider error: {str(provider_error)}"
                    }
            
            # Create assistant message
            assistant_message = ChatMessage(
                role="assistant",
                content=response_content,
                timestamp=datetime.now(),
                user_id=self.user_id,
                sources=source_documents
            )
            
            # Update conversation history
            self.conversation_history.append(user_message)
            self.conversation_history.append(assistant_message)
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-40:]
            
            # Calculate total time and trace the complete RAG flow
            total_time = time.time() - start_time
            
            # Prepare search results for tracing
            search_results_for_trace = []
            if use_rag and 'relevant_docs' in locals() and relevant_docs:
                for doc in relevant_docs[:3]:  # First 3 for brevity
                    search_results_for_trace.append({
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "page": doc.metadata.get("page", "Unknown")
                    })
            
            # Trace the complete RAG flow
            trace_rag_flow_if_enabled(
                user_input=message,
                search_query=message,
                search_results=search_results_for_trace,
                llm_response=response_content,
                provider=type(self.chat_provider).__name__,
                model=getattr(self.chat_provider, 'model', 'unknown'),
                total_time=total_time,
                metadata={
                    "use_rag": use_rag,
                    "user_filter": user_filter,
                    "user_id": self.user_id,
                    "session_id": getattr(self, 'session_id', None),
                    "source_documents_count": len(source_documents)
                }
            )
            
            # Flush traces to ensure they're sent
            flush_langfuse()
            
            return {
                "answer": response_content,
                "source_documents": source_documents,
                "timestamp": assistant_message.timestamp.isoformat(),
                "metadata": {
                    "total_time": total_time,
                    "search_results": len(search_results_for_trace),
                    "trace_logged": "langfuse"
                }
            }
            
        except Exception as e:
            logger.error(f"Chat generation error: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your request. Please try again.",
                "source_documents": [],
                "error": str(e)
            }
    
    def chat_without_documents(self, message: str) -> Dict[str, Any]:
        """
        Chat without using documents (fallback mode)
        
        Args:
            message: User message
            
        Returns:
            Dict with answer
        """
        return self.chat(message, use_rag=False)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history in JSON format"""
        history = []
        for msg in self.conversation_history:
            history.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sources": msg.sources or []
            })
        return history
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info(f"Cleared conversation history for user: {self.user_id}")
    
    def get_user_document_stats(self) -> Dict[str, Any]:
        """Get user's document statistics"""
        if not self.vector_store:
            return {"error": "No vector store available"}
        
        return self.vector_store.get_user_stats()
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        status = {
            "chat_provider": {
                "type": config.chat_provider,
                "healthy": False
            },
            "vector_store": {
                "available": self.vector_store is not None,
                "healthy": False
            },
            "user_documents": 0
        }
        
        # Check chat provider
        try:
            status["chat_provider"]["healthy"] = self.chat_provider.health_check()
        except Exception as e:
            logger.error(f"Chat provider health check failed: {e}")
        
        # Check vector store
        if self.vector_store:
            try:
                status["vector_store"]["healthy"] = self.vector_store.health_check()
                user_stats = self.vector_store.get_user_stats()
                status["user_documents"] = user_stats.get("total_documents", 0)
            except Exception as e:
                logger.error(f"Vector store health check failed: {e}")
        
        return status
    
    def on_provider_change(self, change_type: str, data: Dict[str, Any]):
        """Handle provider changes from provider manager"""
        try:
            logger.info(f"Chat engine handling provider change: {change_type}")
            
            # Reinitialize chat provider if it changed
            if change_type in ['chat_provider', 'ollama_settings', 'openai_settings', 'force_reinitialize']:
                old_provider = self.chat_provider
                
                # Get new provider
                self.chat_provider = get_chat_provider()
                
                logger.info(f"Chat engine provider updated from {type(old_provider).__name__} to {type(self.chat_provider).__name__}")
                
                # Optionally clear conversation history to avoid confusion
                if change_type == 'chat_provider':
                    logger.info("Clearing conversation history due to provider switch")
                    self.conversation_history = []
            
        except Exception as e:
            logger.error(f"Error handling provider change in chat engine: {e}")
    
    def reinitialize_providers(self):
        """Reinitialize providers (called by provider manager)"""
        try:
            self.chat_provider = get_chat_provider()
            logger.info("Chat engine providers reinitialized")
        except Exception as e:
            logger.error(f"Error reinitializing chat engine providers: {e}")
    
    def setup_conversation_chain(self):
        """Setup conversation chain (legacy compatibility)"""
        # This method exists for backward compatibility
        # The new system doesn't require explicit setup
        logger.info("Conversation chain setup completed (legacy compatibility)")
    
    def __del__(self):
        """Cleanup when chat engine is destroyed"""
        try:
            provider_manager = get_provider_manager()
            provider_manager.unregister_component(self)
        except:
            pass  # Ignore errors during cleanup


# Legacy ChatEngine class for backward compatibility
class ChatEngine(EnhancedChatEngine):
    """
    Legacy ChatEngine class for backward compatibility
    """
    
    def __init__(self, 
                 vector_store,
                 model_name: Optional[str] = None,
                 **kwargs):
        """
        Initialize legacy chat engine
        
        Args:
            vector_store: Vector store instance
            model_name: Model name (mapped to provider)
        """
        # Determine provider based on model name
        chat_provider = config.chat_provider
        if model_name:
            if "gpt" in model_name.lower():
                chat_provider = "openai"
            elif any(ollama_model in model_name.lower() for ollama_model in ["llama", "mistral", "codellama"]):
                chat_provider = "ollama"
        
        super().__init__(
            user_id=None,  # No user isolation for legacy usage
            vector_store=vector_store,
            chat_provider=chat_provider
        )
    
    def chat(self, message: str) -> Dict[str, Any]:
        """Legacy chat method"""
        result = super().chat(message, use_rag=True)
        
        # Convert to legacy format
        return {
            "answer": result["answer"],
            "source_documents": [
                {
                    "page_content": source["content"],
                    "metadata": {
                        "filename": source["filename"],
                        "page": source["page"]
                    }
                }
                for source in result["source_documents"]
            ]
        }
