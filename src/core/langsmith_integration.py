"""
Langsmith integration for Zenith - Observability and evaluation support
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

from ..core.config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LangsmithClient:
    """Client for Langsmith observability and evaluation"""
    
    def __init__(self, api_key: Optional[str] = None, project_name: Optional[str] = None):
        self.api_key = api_key or config.langsmith_api_key
        self.project_name = project_name or config.langsmith_project_name
        self.endpoint = config.langsmith_endpoint
        self.tracing_enabled = config.langsmith_tracing_enabled
        self.evaluation_enabled = config.langsmith_evaluation_enabled
        
        # Initialize Langsmith if enabled
        if self.api_key and self.tracing_enabled:
            self._setup_langsmith()
    
    def _setup_langsmith(self):
        """Setup Langsmith environment and tracing"""
        try:
            # Set environment variables for Langsmith
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = self.endpoint
            os.environ["LANGCHAIN_API_KEY"] = self.api_key
            os.environ["LANGCHAIN_PROJECT"] = self.project_name
            
            logger.info(f"Langsmith tracing initialized for project: {self.project_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup Langsmith: {e}")
    
    def is_enabled(self) -> bool:
        """Check if Langsmith is properly configured and enabled"""
        return bool(self.api_key and self.tracing_enabled)
    
    def trace_chat_interaction(self, 
                              user_input: str, 
                              response: str, 
                              provider: str,
                              model: str,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Trace a chat interaction
        Returns: run_id for the traced interaction
        """
        if not self.is_enabled():
            return ""
        
        try:
            from langsmith import Client
            
            client = Client(api_key=self.api_key, api_url=self.endpoint)
            
            # Create run data
            run_data = {
                "name": "chat_interaction",
                "inputs": {
                    "user_input": user_input,
                    "provider": provider,
                    "model": model,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "outputs": {
                    "response": response
                },
                "run_type": "chain",
                "project_name": self.project_name
            }
            
            # Add metadata if provided
            if metadata:
                run_data["extra"] = metadata
            
            # Create the run
            run = client.create_run(**run_data)
            logger.debug(f"Traced chat interaction with run_id: {run.id}")
            
            return str(run.id)
            
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
        Trace document processing
        Returns: run_id for the traced processing
        """
        if not self.is_enabled():
            return ""
        
        try:
            from langsmith import Client
            
            client = Client(api_key=self.api_key, api_url=self.endpoint)
            
            # Create run data
            run_data = {
                "name": "document_processing",
                "inputs": {
                    "filename": filename,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "outputs": {
                    "chunk_count": chunk_count,
                    "processing_time_seconds": processing_time,
                    "success": success
                },
                "run_type": "tool",
                "project_name": self.project_name
            }
            
            # Add metadata if provided
            if metadata:
                run_data["extra"] = metadata
            
            # Create the run
            run = client.create_run(**run_data)
            logger.debug(f"Traced document processing with run_id: {run.id}")
            
            return str(run.id)
            
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
        Returns: run_id for the traced query
        """
        if not self.is_enabled():
            return ""
        
        try:
            from langsmith import Client
            
            client = Client(api_key=self.api_key, api_url=self.endpoint)
            
            # Create run data
            run_data = {
                "name": "search_query",
                "inputs": {
                    "query": query,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "outputs": {
                    "results_count": results_count,
                    "retrieval_time_seconds": retrieval_time
                },
                "run_type": "retriever",
                "project_name": self.project_name
            }
            
            # Add metadata if provided
            if metadata:
                run_data["extra"] = metadata
            
            # Create the run
            run = client.create_run(**run_data)
            logger.debug(f"Traced search query with run_id: {run.id}")
            
            return str(run.id)
            
        except Exception as e:
            logger.error(f"Failed to trace search query: {e}")
            return ""
    
    def create_evaluation_dataset(self, 
                                 dataset_name: str, 
                                 examples: List[Dict[str, Any]]) -> bool:
        """
        Create an evaluation dataset in Langsmith
        """
        if not self.evaluation_enabled or not self.is_enabled():
            logger.warning("Langsmith evaluation is not enabled")
            return False
        
        try:
            from langsmith import Client
            
            client = Client(api_key=self.api_key, api_url=self.endpoint)
            
            # Create dataset
            dataset = client.create_dataset(
                dataset_name=dataset_name,
                description=f"Evaluation dataset for {self.project_name}"
            )
            
            # Add examples to dataset
            for example in examples:
                client.create_example(
                    dataset_id=dataset.id,
                    inputs=example.get("inputs", {}),
                    outputs=example.get("outputs", {}),
                    metadata=example.get("metadata", {})
                )
            
            logger.info(f"Created evaluation dataset '{dataset_name}' with {len(examples)} examples")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create evaluation dataset: {e}")
            return False
    
    def run_evaluation(self, 
                      dataset_name: str, 
                      evaluator_function,
                      experiment_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run an evaluation on a dataset
        """
        if not self.evaluation_enabled or not self.is_enabled():
            logger.warning("Langsmith evaluation is not enabled")
            return {}
        
        try:
            from langsmith import Client
            from langsmith.evaluation import evaluate
            
            client = Client(api_key=self.api_key, api_url=self.endpoint)
            
            # Run evaluation
            experiment_name = experiment_name or f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            results = evaluate(
                evaluator_function,
                data=dataset_name,
                experiment_prefix=experiment_name,
                client=client
            )
            
            logger.info(f"Completed evaluation '{experiment_name}' on dataset '{dataset_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Failed to run evaluation: {e}")
            return {}


# Global Langsmith client instance
_langsmith_client: Optional[LangsmithClient] = None


def get_langsmith_client() -> Optional[LangsmithClient]:
    """Get the global Langsmith client instance"""
    global _langsmith_client
    
    if _langsmith_client is None and config.langsmith_enabled:
        _langsmith_client = LangsmithClient()
    
    return _langsmith_client


def initialize_langsmith(settings) -> bool:
    """Initialize Langsmith with settings"""
    global _langsmith_client
    
    try:
        if settings.is_langsmith_enabled():
            api_key = settings.langsmith_api_key or config.langsmith_api_key
            project_name = settings.langsmith_project_name or config.langsmith_project_name
            
            _langsmith_client = LangsmithClient(api_key=api_key, project_name=project_name)
            logger.info("Langsmith initialized successfully")
            return True
        else:
            logger.info("Langsmith is not enabled")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize Langsmith: {e}")
        return False


def trace_chat_if_enabled(user_input: str, 
                         response: str, 
                         provider: str, 
                         model: str,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace chat interactions if Langsmith is enabled"""
    client = get_langsmith_client()
    if client:
        return client.trace_chat_interaction(user_input, response, provider, model, metadata)
    return ""


def trace_document_if_enabled(filename: str, 
                             chunk_count: int, 
                             processing_time: float, 
                             success: bool,
                             metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace document processing if Langsmith is enabled"""
    client = get_langsmith_client()
    if client:
        return client.trace_document_processing(filename, chunk_count, processing_time, success, metadata)
    return ""


def trace_search_if_enabled(query: str, 
                           results_count: int, 
                           retrieval_time: float,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to trace search queries if Langsmith is enabled"""
    client = get_langsmith_client()
    if client:
        return client.trace_search_query(query, results_count, retrieval_time, metadata)
    return ""
