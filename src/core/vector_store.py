"""
Vector Store Module for Zenith PDF Chatbot
Handles Qdrant vector database operations and embeddings
"""

import logging
from typing import List, Optional, Dict, Any
import uuid

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from .config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    Handles vector database operations with Qdrant
    """
    
    def __init__(self, 
                 collection_name: Optional[str] = None,
                 embedding_model: Optional[str] = None):
        """
        Initialize vector store
        
        Args:
            collection_name: Name of Qdrant collection
            embedding_model: OpenAI embedding model name
        """
        self.collection_name = collection_name or config.qdrant_collection_name
        self.embedding_model = embedding_model or config.openai_embedding_model
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=config.openai_api_key,
            model=self.embedding_model
        )
        
        # Initialize Qdrant client
        self.qdrant_client = self._initialize_qdrant_client()
        
        # Vector store instance
        self.vector_store = None
        
        logger.info(f"VectorStore initialized for collection: {self.collection_name}")
    
    def _initialize_qdrant_client(self) -> QdrantClient:
        """
        Initialize Qdrant client with configuration
        
        Returns:
            QdrantClient instance
        """
        try:
            if config.qdrant_api_key:
                # Using Qdrant Cloud
                client = QdrantClient(
                    url=f"https://{config.qdrant_url}",
                    api_key=config.qdrant_api_key
                )
            else:
                # Using local Qdrant
                client = QdrantClient(
                    host=config.qdrant_url,
                    port=config.qdrant_port
                )
            
            logger.info(f"Connected to Qdrant at {config.qdrant_url}:{config.qdrant_port}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def create_collection(self, force_recreate: bool = False) -> bool:
        """
        Create Qdrant collection if it doesn't exist
        
        Args:
            force_recreate: Whether to recreate collection if it exists
            
        Returns:
            True if collection was created/exists, False otherwise
        """
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                if force_recreate:
                    logger.info(f"Deleting existing collection: {self.collection_name}")
                    self.qdrant_client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection {self.collection_name} already exists")
                    return True
            
            # Create collection
            logger.info(f"Creating collection: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI embedding dimension
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Successfully created collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {self.collection_name}: {e}")
            return False
    
    def add_documents(self, documents: List[Document]) -> bool:
        """
        Add documents to the vector store
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not documents:
                logger.warning("No documents provided to add")
                return False
            
            # Ensure collection exists
            if not self.create_collection():
                raise Exception("Failed to create/verify collection")
            
            # Create or get vector store
            if self.vector_store is None:
                self.vector_store = Qdrant(
                    client=self.qdrant_client,
                    collection_name=self.collection_name,
                    embeddings=self.embeddings
                )
            
            # Add documents in batches
            batch_size = config.batch_size
            total_docs = len(documents)
            
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_docs + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} "
                           f"({len(batch)} documents)")
                
                # Add batch to vector store
                self.vector_store.add_documents(batch)
            
            logger.info(f"Successfully added {total_docs} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def similarity_search(self, 
                         query: str, 
                         k: Optional[int] = None,
                         score_threshold: Optional[float] = None) -> List[Document]:
        """
        Perform similarity search
        
        Args:
            query: Search query
            k: Number of documents to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of similar documents
        """
        try:
            if self.vector_store is None:
                # Try to connect to existing collection
                self.vector_store = Qdrant(
                    client=self.qdrant_client,
                    collection_name=self.collection_name,
                    embeddings=self.embeddings
                )
            
            k = k or config.max_chunks_per_query
            
            if score_threshold:
                results = self.vector_store.similarity_search_with_score(
                    query, k=k * 2  # Get more results to filter by score
                )
                # Filter by score threshold
                filtered_results = [
                    doc for doc, score in results 
                    if score >= score_threshold
                ][:k]
                return filtered_results
            else:
                results = self.vector_store.similarity_search(query, k=k)
                return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def get_retriever(self, 
                     search_type: str = "similarity",
                     search_kwargs: Optional[Dict[str, Any]] = None):
        """
        Get a retriever for the vector store
        
        Args:
            search_type: Type of search ("similarity", "mmr", etc.)
            search_kwargs: Additional search parameters
            
        Returns:
            Retriever object
        """
        try:
            if self.vector_store is None:
                self.vector_store = Qdrant(
                    client=self.qdrant_client,
                    collection_name=self.collection_name,
                    embeddings=self.embeddings
                )
            
            search_kwargs = search_kwargs or {
                "k": config.max_chunks_per_query
            }
            
            retriever = self.vector_store.as_retriever(
                search_type=search_type,
                search_kwargs=search_kwargs
            )
            
            return retriever
            
        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            return None
    
    def delete_collection(self) -> bool:
        """
        Delete the collection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.qdrant_client.delete_collection(self.collection_name)
            self.vector_store = None
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection {self.collection_name}: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the collection
        
        Returns:
            Dictionary with collection information
        """
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
                                              
            # Get collection stats
            stats = {
                "name": self.collection_name,
                "status": collection_info.status,
                "vectors_count": collection_info.vectors_count,
                "segments_count": collection_info.segments_count,
                "disk_data_size": None,
                "ram_data_size": None,
                #"disk_data_size": collection_info.disk_data_size,
                #"ram_data_size": collection_info.ram_data_size,
                "config": {
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Check if the vector store is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get collections
            collections = self.qdrant_client.get_collections()
            
            # Check if our collection exists
            collection_names = [col.name for col in collections.collections]
            collection_exists = self.collection_name in collection_names
            
            if collection_exists:
                # Try to get collection info
                info = self.get_collection_info()
                return info is not None
            
            return True  # If collection doesn't exist, that's okay
            
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False
