"""
Langfuse integration for Zenith - Self-hosted observability and evaluation support
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import logging
import uuid

from src.core.config import config
from src.utils.logger import get_logger

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
        
        # Working HTTP solution for bypassing flush 404 issue
        self.ingestion_url = f"{self.host.rstrip('/')}/api/public/ingestion"
        self.auth = (self.public_key, self.secret_key) if self.public_key and self.secret_key else None
        
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
    
    
    def trace_chat_interaction(self, 
                              user_input: str, 
                              response: str, 
                              provider: str,
                              model: str,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Trace a chat interaction using working direct HTTP method
        Returns: trace_id for the traced interaction
        """
        if not self.is_enabled():
            return ""
        
        try:
            # Generate IDs
            trace_id = str(uuid.uuid4()).replace('-', '')
            generation_id = str(uuid.uuid4()).replace('-', '')
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create trace item
            trace_item = {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "chat_interaction",
                    "user_id": metadata.get("user_id") if metadata else None,
                    "session_id": metadata.get("session_id") if metadata else None,
                    "input": user_input,
                    "output": response,
                    "metadata": {
                        "provider": provider,
                        "model": model,
                        "project": self.project_name,
                        **(metadata or {})
                    }
                }
            }
            
            # Create generation item
            generation_item = {
                "id": generation_id,
                "type": "generation-create", 
                "timestamp": timestamp,
                "body": {
                    "id": generation_id,
                    "trace_id": trace_id,
                    "name": "llm_generation",
                    "model": model,
                    "input": user_input,
                    "output": response,
                    "metadata": {
                        "provider": provider,
                        "timestamp": timestamp,
                        **(metadata or {})
                    }
                }
            }
            
            # Send directly using working HTTP method
            success = self._send_batch_direct([trace_item, generation_item])
            
            if success:
                logger.debug(f"Successfully traced chat interaction: {trace_id}")
                return trace_id
            else:
                logger.error("Failed to send chat interaction trace")
                return ""
            
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
        Trace document processing using working direct HTTP method
        Returns: trace_id for the traced processing
        """
        if not self.is_enabled():
            return ""
        
        try:
            # Generate IDs
            trace_id = str(uuid.uuid4()).replace('-', '')
            span_id = str(uuid.uuid4()).replace('-', '')
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create trace item
            trace_item = {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "document_processing",
                    "user_id": metadata.get("user_id") if metadata else None,
                    "input": {"filename": filename},
                    "output": {
                        "chunk_count": chunk_count,
                        "processing_time_seconds": processing_time,
                        "success": success
                    },
                    "metadata": {
                        "project": self.project_name,
                        "document_filename": filename,
                        **(metadata or {})
                    }
                }
            }
            
            # Create span item
            span_item = {
                "id": span_id,
                "type": "span-create",
                "timestamp": timestamp,
                "body": {
                    "id": span_id,
                    "trace_id": trace_id,
                    "name": "pdf_processing",
                    "input": {"filename": filename},
                    "output": {
                        "chunk_count": chunk_count,
                        "processing_time_seconds": processing_time,
                        "success": success
                    },
                    "metadata": {
                        "timestamp": timestamp,
                        **(metadata or {})
                    }
                }
            }
            
            # Send directly using working HTTP method
            success_sent = self._send_batch_direct([trace_item, span_item])
            
            if success_sent:
                logger.debug(f"Successfully traced document processing: {trace_id}")
                return trace_id
            else:
                logger.error("Failed to send document processing trace")
                return ""
            
        except Exception as e:
            logger.error(f"Failed to trace document processing: {e}")
            return ""
    
    def trace_search_query(self, 
                          query: str, 
                          results_count: int, 
                          retrieval_time: float,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Trace a search/retrieval query using working direct HTTP method
        Returns: trace_id for the traced query
        """
        if not self.is_enabled():
            return ""
        
        try:
            # Generate IDs
            trace_id = str(uuid.uuid4()).replace('-', '')
            span_id = str(uuid.uuid4()).replace('-', '')
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create trace item
            trace_item = {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "search_query",
                    "user_id": metadata.get("user_id") if metadata else None,
                    "session_id": metadata.get("session_id") if metadata else None,
                    "input": {"query": query},
                    "output": {
                        "results_count": results_count,
                        "retrieval_time_seconds": retrieval_time
                    },
                    "metadata": {
                        "project": self.project_name,
                        **(metadata or {})
                    }
                }
            }
            
            # Create span item
            span_item = {
                "id": span_id,
                "type": "span-create",
                "timestamp": timestamp,
                "body": {
                    "id": span_id,
                    "trace_id": trace_id,
                    "name": "vector_search",
                    "input": {"query": query},
                    "output": {
                        "results_count": results_count,
                        "retrieval_time_seconds": retrieval_time
                    },
                    "metadata": {
                        "timestamp": timestamp,
                        **(metadata or {})
                    }
                }
            }
            
            # Send directly using working HTTP method
            success = self._send_batch_direct([trace_item, span_item])
            
            if success:
                logger.debug(f"Successfully traced search query: {trace_id}")
                return trace_id
            else:
                logger.error("Failed to send search query trace")
                return ""
            
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
        Trace a complete RAG flow with all components using working direct HTTP method
        Returns: trace_id for the traced flow
        """
        if not self.is_enabled():
            return ""
        
        try:
            # Generate IDs
            trace_id = str(uuid.uuid4()).replace('-', '')
            search_span_id = str(uuid.uuid4()).replace('-', '')
            generation_id = str(uuid.uuid4()).replace('-', '')
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create trace item
            trace_item = {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "rag_flow",
                    "user_id": metadata.get("user_id") if metadata else None,
                    "session_id": metadata.get("session_id") if metadata else None,
                    "input": user_input,
                    "output": llm_response,
                    "metadata": {
                        "project": self.project_name,
                        "provider": provider,
                        "model": model,
                        "total_time_seconds": total_time,
                        **(metadata or {})
                    }
                }
            }
            
            # Create search span item
            search_span_item = {
                "id": search_span_id,
                "type": "span-create",
                "timestamp": timestamp,
                "body": {
                    "id": search_span_id,
                    "trace_id": trace_id,
                    "name": "vector_search",
                    "input": {"query": search_query},
                    "output": {
                        "results_count": len(search_results),
                        "results": search_results[:3] if search_results else []  # First 3 results for brevity
                    },
                    "metadata": {
                        "search_type": "similarity_search",
                        "user_filter": metadata.get("user_filter", False) if metadata else False
                    }
                }
            }
            
            # Create generation item
            generation_item = {
                "id": generation_id,
                "type": "generation-create",
                "timestamp": timestamp,
                "body": {
                    "id": generation_id,
                    "trace_id": trace_id,
                    "name": "llm_generation",
                    "model": model,
                    "input": user_input,
                    "output": llm_response,
                    "metadata": {
                        "provider": provider,
                        "context_documents": len(search_results),
                        "use_rag": len(search_results) > 0
                    }
                }
            }
            
            # Send all items in batch using working HTTP method
            success = self._send_batch_direct([trace_item, search_span_item, generation_item])
            
            if success:
                logger.debug(f"Successfully traced complete RAG flow: {trace_id}")
                return trace_id
            else:
                logger.error("Failed to send RAG flow trace")
                return ""
            
        except Exception as e:
            logger.error(f"Failed to trace RAG flow: {e}")
            return ""
    
    def trace_session(self,
                     session_id: str,
                     user_id: Optional[str] = None,
                     session_data: Optional[Dict[str, Any]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Initialize a session by creating a session start trace
        Note: View sessions in Traces tab by filtering session_id (Sessions UI may not be available in all Langfuse versions)
        Returns: session_id for the traced session
        """
        if not self.is_enabled():
            return ""
        
        try:
            # Generate unique trace ID (different from session_id)
            trace_id = str(uuid.uuid4()).replace('-', '')
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create session start trace with clear labeling for easy discovery
            session_start_item = {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "session_start",
                    "user_id": user_id,
                    "session_id": session_id,  # Key field for session grouping
                    "input": {
                        "action": "session_start",
                        "user_id": user_id,
                        "session_data": session_data or {},
                        "timestamp": timestamp,
                        "session_identifier": session_id  # Additional identifier
                    },
                    "output": {
                        "session_id": session_id,
                        "session_status": "started",
                        "user_id": user_id,
                        "initialization_successful": True
                    },
                    "metadata": {
                        "project": self.project_name,
                        "session_type": "initialization", 
                        "session_data": session_data or {},
                        "searchable_session_id": session_id,  # For easy Traces tab search
                        "session_lifecycle": "start",
                        **(metadata or {})
                    }
                }
            }
            
            # Send directly using working HTTP method
            success = self._send_batch_direct([session_start_item])
            
            if success:
                logger.info(f"Session initialized: {session_id} (Find in Traces tab by searching: {session_id})")
                return session_id
            else:
                logger.error("Failed to send session start trace")
                return ""
            
        except Exception as e:
            logger.error(f"Failed to trace session: {e}")
            return ""
    
    def update_session(self,
                      session_id: str,
                      session_data: Optional[Dict[str, Any]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing session by creating a session update event
        Returns: True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create session update as an event
            update_event_id = str(uuid.uuid4()).replace('-', '')
            session_update_item = {
                "id": update_event_id,
                "type": "event-create",
                "timestamp": timestamp,
                "body": {
                    "id": update_event_id,
                    "name": "session_update",
                    "input": {
                        "session_id": session_id,
                        "action": "update"
                    },
                    "output": {
                        "update_successful": True,
                        "session_data": session_data or {}
                    },
                    "metadata": {
                        "project": self.project_name,
                        "session_id": session_id,
                        "update_type": "session_update",
                        "updated_at": timestamp,
                        "session_data": session_data or {},
                        **(metadata or {})
                    }
                }
            }
            
            # Send directly using working HTTP method
            success = self._send_batch_direct([session_update_item])
            
            if success:
                logger.debug(f"Successfully updated session: {session_id}")
                return True
            else:
                logger.error("Failed to send session update")
                return False
            
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False
    
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
    
    def _send_batch_direct(self, items: List[Dict[str, Any]]) -> bool:
        """Send batch directly to Langfuse using working HTTP method (bypasses SDK flush 404)"""
        if not self.auth or not items:
            return False
        
        payload = {"batch": items}
        
        try:
            response = requests.post(
                self.ingestion_url,
                json=payload,
                auth=self.auth,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201, 202, 207]:
                logger.debug(f"Successfully sent batch of {len(items)} items to Langfuse")
                return True
            else:
                logger.error(f"Failed to send batch: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending batch to Langfuse: {e}")
            return False
    
    def flush(self):
        """Flush pending traces to Langfuse using working method"""
        if not self.is_enabled():
            return
            
        try:
            # Try SDK flush first (in case it works in future versions)
            if self.client:
                self.client.flush()
                logger.debug("Successfully flushed using SDK method")
        except Exception as e:
            logger.warning(f"SDK flush failed (known 404 issue): {e}")
            logger.info("Note: This is a known issue with Langfuse SDK v3.x flush method")
            # We don't send direct batches here because individual trace methods 
            # now handle sending directly to avoid the flush 404 issue
    
    def get_session_viewing_instructions(self, session_id: str) -> str:
        """
        Get instructions for viewing sessions in Langfuse UI
        Returns: formatted instructions for finding sessions
        """
        return f"""
HOW TO VIEW SESSION: {session_id}

METHOD 1 - TRACES TAB (RECOMMENDED):
1. Go to Langfuse UI → Tracing → Traces
2. Search for: {session_id}
3. Filter by session_id in metadata
4. Sort by timestamp to see session flow

METHOD 2 - EVENTS TAB:
1. Go to Langfuse UI → Tracing → Events  
2. Search for: session_update
3. Look for events with session_id: {session_id}

METHOD 3 - USER ACTIVITY:
1. Filter by user_id to see all user sessions
2. Group traces by session_id manually

NOTE: Sessions UI may not be available in all Langfuse versions.
Use Traces tab with session_id filter for complete session view.
        """


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


def trace_session_if_enabled(session_id: str,
                             user_id: Optional[str] = None,
                             session_data: Optional[Dict[str, Any]] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace sessions if Langfuse is enabled"""
    client = get_langfuse_client()
    if client:
        return client.trace_session(session_id, user_id, session_data, metadata)
    return ""


def update_session_if_enabled(session_id: str,
                              session_data: Optional[Dict[str, Any]] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to update sessions if Langfuse is enabled"""
    client = get_langfuse_client()
    if client:
        return client.update_session(session_id, session_data, metadata)
    return False
