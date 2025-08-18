"""
Langfuse integration for Zenith - Self-hosted observability and evaluation support
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import logging
import uuid

from ..core.config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LangfuseClient:
    """Client for Langfuse observability and evaluation"""
    
    def __init__(self, host: Optional[str] = None, public_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, project_name: Optional[str] = None):
        self.host = host or config.langfuse_host
        self.public_key = public_key or config.langfuse_public_key
        self.secret_key = secret_key or config.langfuse_secret_key
        self.project_name = project_name or config.langfuse_project_name
        self.tracing_enabled = config.langfuse_tracing_enabled
        self.evaluation_enabled = config.langfuse_evaluation_enabled
        
        # Initialize Langfuse client
        self.client = None
        self._trace_method = None
        if self.public_key and self.secret_key and self.tracing_enabled:
            self._setup_langfuse()
    
    def _setup_langfuse(self):
        """Setup Langfuse client and environment"""
        try:
            from langfuse import Langfuse
            
            # Use clean host URL - SDK handles the ingestion endpoint internally
            clean_host = self.host.rstrip('/')
            
            self.client = Langfuse(
                host=clean_host,
                public_key=self.public_key,
                secret_key=self.secret_key
            )
            
            logger.info(f"Configured Langfuse client for host: {clean_host}")
            
            # Test the SDK's methods for v3.x (uses create_trace_id + start_span pattern)
            if hasattr(self.client, 'create_trace_id') and hasattr(self.client, 'start_span'):
                self._trace_method = 'sdk_v3_spans'
                logger.info("Using Langfuse SDK v3.x create_trace_id + start_span pattern")
            elif hasattr(self.client, 'create_event'):
                self._trace_method = 'sdk_v3_events'
                logger.info("Using Langfuse SDK v3.x create_event pattern")
            else:
                logger.error("No compatible Langfuse SDK method found")
                available_methods = [m for m in dir(self.client) if not m.startswith('_')]
                logger.error(f"Available methods: {available_methods}")
                self.client = None
                return
                
            # Set environment variables for LangChain integration
            # Ensure the host is clean and properly formatted
            clean_host = self.host.rstrip('/')
            os.environ["LANGFUSE_HOST"] = clean_host
            os.environ["LANGFUSE_PUBLIC_KEY"] = self.public_key
            os.environ["LANGFUSE_SECRET_KEY"] = self.secret_key
            
            logger.info(f"Langfuse environment configured:")
            logger.info(f"  Host: {clean_host}")
            logger.info(f"  Ingestion will use: {clean_host}/api/public/ingestion")
            
            # Check what the client is actually configured to use
            if hasattr(self.client, '_client_wrapper') and hasattr(self.client._client_wrapper, 'base_url'):
                actual_base_url = self.client._client_wrapper.base_url
                logger.info(f"  Actual client base URL: {actual_base_url}")
            elif hasattr(self.client, 'base_url'):
                logger.info(f"  Actual client base URL: {self.client.base_url}")
            elif hasattr(self.client, '_base_url'):
                logger.info(f"  Actual client base URL: {self.client._base_url}")
            else:
                logger.info("  Could not determine client base URL")
            
            logger.info(f"Langfuse tracing initialized for project: {self.project_name} at {self.host}")
            
        except ImportError:
            logger.error("Langfuse not installed. Install with: pip install langfuse")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to setup Langfuse: {e}")
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if Langfuse is properly configured and enabled"""
        return bool(self.client and self.tracing_enabled)
    
    def _create_trace_compatible(self, **kwargs):
        """Create trace using Langfuse v3.x SDK pattern"""
        if not self.client:
            return None
            
        try:
            if self._trace_method == 'sdk_v3_spans':
                # Langfuse v3.x pattern: create_trace_id + start_span
                trace_id = self.client.create_trace_id()
                
                # Create a wrapper that mimics the old trace object
                class LangfuseV3Trace:
                    def __init__(self, client, trace_id, name=None, input=None, output=None, metadata=None):
                        self.client = client
                        self.id = trace_id
                        self.name = name
                        self.input = input
                        self.output = output
                        self.metadata = metadata or {}
                        
                        # Update current trace context
                        self.client.update_current_trace(
                            name=name,
                            input=input,
                            output=output,
                            metadata=metadata
                        )
                        
                    def span(self, name, input=None, output=None, metadata=None):
                        """Create a span within this trace using context"""
                        span = self.client.start_as_current_span(
                            name=name,
                            input=input,
                            output=output,
                            metadata=metadata
                        )
                        return span
                        
                    def generation(self, name, model=None, input=None, output=None, metadata=None):
                        """Create a generation within this trace using context"""
                        generation = self.client.start_as_current_generation(
                            name=name,
                            model=model,
                            input=input,
                            output=output,
                            metadata=metadata
                        )
                        
                        # Wrap the context manager to add an end() method for compatibility
                        class GenerationWrapper:
                            def __init__(self, context_manager):
                                self.context_manager = context_manager
                                self._entered = False
                                self._generation = None
                                
                            def __enter__(self):
                                self._generation = self.context_manager.__enter__()
                                self._entered = True
                                return self
                                
                            def __exit__(self, exc_type, exc_val, exc_tb):
                                if self._entered:
                                    return self.context_manager.__exit__(exc_type, exc_val, exc_tb)
                                
                            def end(self):
                                """Compatibility method - for v3.x this is handled by context manager"""
                                if self._entered:
                                    self.__exit__(None, None, None)
                                    self._entered = False
                        
                        return GenerationWrapper(generation)
                
                trace = LangfuseV3Trace(
                    self.client, 
                    trace_id, 
                    name=kwargs.get('name'),
                    input=kwargs.get('input'),
                    output=kwargs.get('output'),
                    metadata=kwargs.get('metadata')
                )
                
                logger.debug(f"Created trace using SDK v3.x: {trace.id}")
                return trace
                
            elif self._trace_method == 'sdk_v3_events':
                # Fallback to events if span pattern doesn't work
                event = self.client.create_event(
                    name=kwargs.get('name', 'trace'),
                    input=kwargs.get('input'),
                    output=kwargs.get('output'),
                    metadata=kwargs.get('metadata', {})
                )
                
                # Create a simple wrapper
                class LangfuseV3Event:
                    def __init__(self, event):
                        self.id = getattr(event, 'id', 'event-trace')
                        
                    def span(self, **kwargs):
                        return self
                        
                    def generation(self, **kwargs):
                        return self
                        
                    def end(self):
                        pass
                
                logger.debug(f"Created event-based trace: {event}")
                return LangfuseV3Event(event)
            else:
                logger.error(f"Unknown trace method: {self._trace_method}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create trace: {e}")
            return None
    
    def trace_chat_interaction(self, 
                              user_input: str, 
                              response: str, 
                              provider: str,
                              model: str,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Trace a chat interaction using Langfuse v3.x context API
        Returns: trace_id for the traced interaction
        """
        if not self.is_enabled():
            return ""
        
        try:
            if self._trace_method == 'sdk_v3_spans':
                # Use v3.x context-based API with proper span context
                trace_id = self.client.create_trace_id()
                
                # First create a span context, then add generation within it
                with self.client.start_as_current_span(
                    name="chat_interaction",
                    input=user_input,
                    output=response,
                    metadata={
                        "provider": provider,
                        "project": self.project_name,
                        **(metadata or {})
                    }
                ) as span:
                    logger.debug(f"Started chat span in context: {span}")
                    
                    # Now update trace metadata within the span context
                    self.client.update_current_trace(
                        name="chat_interaction",
                        user_id=metadata.get("user_id") if metadata else None,
                        session_id=metadata.get("session_id") if metadata else None,
                        metadata={
                            "provider": provider,
                            "model": model,
                            "project": self.project_name,
                            **(metadata or {})
                        }
                    )
                    
                    # Add generation within the span context
                    with self.client.start_as_current_generation(
                        name="llm_generation",
                        model=model,
                        input=user_input,
                        output=response,
                        metadata={
                            "provider": provider,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            **(metadata or {})
                        }
                    ) as generation:
                        # Generation automatically ends when context exits
                        logger.debug(f"Started generation in context: {generation}")
                
                logger.debug(f"Traced chat interaction with trace_id: {trace_id}")
                return str(trace_id)
                
            else:
                # Fallback to event-based API
                event = self.client.create_event(
                    name="chat_interaction",
                    input=user_input,
                    output=response,
                    metadata={
                        "provider": provider,
                        "model": model,
                        "project": self.project_name,
                        **(metadata or {})
                    }
                )
                logger.debug(f"Created chat event: {event}")
                return str(getattr(event, 'id', 'event-based'))
            
        except Exception as e:
            logger.error(f"Failed to trace chat interaction: {e}")
            return ""
    
    def trace_document_processing(self, 
                                 filename: str, 
                                 chunk_count: int, 
                                 processing_time: float,
                                 success: bool,
                                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Trace document processing using Langfuse v3.x context API
        Returns: trace_id for the traced processing
        """
        if not self.is_enabled():
            return ""
        
        try:
            if self._trace_method == 'sdk_v3_spans':
                # Use v3.x context-based API with proper span context
                trace_id = self.client.create_trace_id()
                
                # Create span context first
                with self.client.start_as_current_span(
                    name="pdf_processing",
                    input={"filename": filename},
                    output={
                        "chunk_count": chunk_count,
                        "processing_time_seconds": processing_time,
                        "success": success
                    },
                    metadata={
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        **(metadata or {})
                    }
                ) as span:
                    logger.debug(f"Started processing span in context: {span}")
                    
                    # Update trace metadata within the span context
                    self.client.update_current_trace(
                        name="document_processing",
                        user_id=metadata.get("user_id") if metadata else None,
                        metadata={
                            "project": self.project_name,
                            "document_filename": filename,
                            **(metadata or {})
                        }
                    )
                
                logger.debug(f"Traced document processing with trace_id: {trace_id}")
                return str(trace_id)
                
            else:
                # Fallback to event-based API
                event = self.client.create_event(
                    name="document_processing",
                    input={"filename": filename},
                    output={
                        "chunk_count": chunk_count,
                        "processing_time_seconds": processing_time,
                        "success": success
                    },
                    metadata={
                        "project": self.project_name,
                        "document_filename": filename,
                        **(metadata or {})
                    }
                )
                logger.debug(f"Created document processing event: {event}")
                return str(getattr(event, 'id', 'event-based'))
            
        except Exception as e:
            logger.error(f"Failed to trace document processing: {e}")
            return ""
    
    def trace_search_query(self, 
                          query: str, 
                          results_count: int, 
                          retrieval_time: float,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Trace a search/retrieval query
        Returns: trace_id for the traced query
        """
        if not self.is_enabled():
            return ""
        
        try:
            # Create a new trace for search
            trace = self._create_trace_compatible(
                name="search_query",
                user_id=metadata.get("user_id") if metadata else None,
                session_id=metadata.get("session_id") if metadata else None,
                metadata={
                    "project": self.project_name,
                    **(metadata or {})
                }
            )
            
            # Create span for the search
            span = trace.span(
                name="vector_search",
                input={"query": query},
                output={
                    "results_count": results_count,
                    "retrieval_time_seconds": retrieval_time
                },
                metadata={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **(metadata or {})
                }
            )
            
            # End the span
            span.end()
            
            logger.debug(f"Traced search query with trace_id: {trace.id}")
            return str(trace.id)
            
        except Exception as e:
            logger.error(f"Failed to trace search query: {e}")
            return ""
    
    def trace_complete_rag_flow(self,
                               user_input: str,
                               search_query: str,
                               search_results: List[Dict],
                               llm_response: str,
                               provider: str,
                               model: str,
                               total_time: float,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Trace a complete RAG flow with all components
        Returns: trace_id for the traced flow
        """
        if not self.is_enabled():
            return ""
        
        try:
            # Create a new trace for the complete RAG flow
            trace = self._create_trace_compatible(
                name="rag_flow",
                user_id=metadata.get("user_id") if metadata else None,
                session_id=metadata.get("session_id") if metadata else None,
                input=user_input,
                output=llm_response,
                metadata={
                    "project": self.project_name,
                    "provider": provider,
                    "model": model,
                    "total_time_seconds": total_time,
                    **(metadata or {})
                }
            )
            
            # 1. Search span
            search_span = trace.span(
                name="vector_search",
                input={"query": search_query},
                output={
                    "results_count": len(search_results),
                    "results": search_results[:3] if search_results else []  # First 3 results for brevity
                },
                metadata={
                    "search_type": "similarity_search",
                    "user_filter": metadata.get("user_filter", False) if metadata else False
                }
            )
            search_span.end()
            
            # 2. LLM Generation span
            generation = trace.generation(
                name="llm_generation",
                model=model,
                input=user_input,
                output=llm_response,
                metadata={
                    "provider": provider,
                    "context_documents": len(search_results),
                    "use_rag": len(search_results) > 0
                }
            )
            generation.end()
            
            logger.debug(f"Traced complete RAG flow with trace_id: {trace.id}")
            return str(trace.id)
            
        except Exception as e:
            logger.error(f"Failed to trace RAG flow: {e}")
            return ""
    
    def create_evaluation_dataset(self, 
                                 dataset_name: str, 
                                 examples: List[Dict[str, Any]]) -> bool:
        """
        Create an evaluation dataset in Langfuse
        """
        if not self.evaluation_enabled or not self.is_enabled():
            logger.warning("Langfuse evaluation is not enabled")
            return False
        
        try:
            # Create dataset items
            for example in examples:
                self.client.create_dataset_item(
                    dataset_name=dataset_name,
                    input=example.get("input", {}),
                    expected_output=example.get("expected_output", {}),
                    metadata=example.get("metadata", {})
                )
            
            logger.info(f"Created evaluation dataset '{dataset_name}' with {len(examples)} examples")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create evaluation dataset: {e}")
            return False
    
    def score_generation(self,
                        trace_id: str,
                        name: str,
                        value: Union[float, int],
                        comment: Optional[str] = None) -> bool:
        """
        Add a score to a generation for evaluation
        """
        if not self.is_enabled():
            return False
        
        try:
            self.client.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment
            )
            
            logger.debug(f"Added score '{name}': {value} to trace {trace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to score generation: {e}")
            return False
    
    def flush(self):
        """Flush pending traces to Langfuse"""
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Failed to flush Langfuse client: {e}")


# Global Langfuse client instance
_langfuse_client: Optional[LangfuseClient] = None


def get_langfuse_client() -> Optional[LangfuseClient]:
    """Get the global Langfuse client instance"""
    global _langfuse_client
    
    if _langfuse_client is None and config.langfuse_enabled:
        _langfuse_client = LangfuseClient()
    
    return _langfuse_client


def initialize_langfuse(settings) -> bool:
    """Initialize Langfuse with settings"""
    global _langfuse_client
    
    try:
        if settings.is_langfuse_enabled():
            host = settings.langfuse_host or config.langfuse_host
            public_key = settings.langfuse_public_key or config.langfuse_public_key
            secret_key = settings.langfuse_secret_key or config.langfuse_secret_key
            project_name = settings.langfuse_project_name or config.langfuse_project_name
            
            _langfuse_client = LangfuseClient(
                host=host,
                public_key=public_key,
                secret_key=secret_key,
                project_name=project_name
            )
            logger.info("Langfuse initialized successfully")
            return True
        else:
            logger.info("Langfuse is not enabled")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")
        return False


def trace_chat_if_enabled(user_input: str, 
                         response: str, 
                         provider: str, 
                         model: str,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace chat interactions if Langfuse is enabled"""
    client = get_langfuse_client()
    if client:
        return client.trace_chat_interaction(user_input, response, provider, model, metadata)
    return ""


def trace_document_if_enabled(filename: str, 
                             chunk_count: int, 
                             processing_time: float, 
                             success: bool,
                             metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace document processing if Langfuse is enabled"""
    client = get_langfuse_client()
    if client:
        return client.trace_document_processing(filename, chunk_count, processing_time, success, metadata)
    return ""


def trace_search_if_enabled(query: str, 
                           results_count: int, 
                           retrieval_time: float,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace search queries if Langfuse is enabled"""
    client = get_langfuse_client()
    if client:
        return client.trace_search_query(query, results_count, retrieval_time, metadata)
    return ""


def trace_rag_flow_if_enabled(user_input: str,
                             search_query: str,
                             search_results: List[Dict],
                             llm_response: str,
                             provider: str,
                             model: str,
                             total_time: float,
                             metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace complete RAG flows if Langfuse is enabled"""
    client = get_langfuse_client()
    if client:
        return client.trace_complete_rag_flow(
            user_input, search_query, search_results, llm_response,
            provider, model, total_time, metadata
        )
    return ""


def score_generation_if_enabled(trace_id: str,
                               name: str,
                               value: Union[float, int],
                               comment: Optional[str] = None) -> bool:
    """Convenience function to score generations if Langfuse is enabled"""
    client = get_langfuse_client()
    if client:
        return client.score_generation(trace_id, name, value, comment)
    return False


def flush_langfuse():
    """Flush pending traces to Langfuse"""
    client = get_langfuse_client()
    if client:
        client.flush()
