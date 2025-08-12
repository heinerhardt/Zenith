"""
Enhanced Vector Store Module for Zenith PDF Chatbot
Supports user isolation, multiple embedding providers, and advanced features
"""

import logging
from typing import List, Optional, Dict, Any, Union
import uuid

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from .config import config
from .qdrant_manager import get_qdrant_client, QdrantManager
from .ollama_integration import get_ollama_manager, OllamaEmbeddingEngine
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingProvider:
    """Abstract base for embedding providers"""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        raise NotImplementedError
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        raise NotImplementedError
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        raise NotImplementedError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name or config.openai_embedding_model
        self.api_key = api_key or config.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.api_key,
            model=self.model_name
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)
    
    def get_dimension(self) -> int:
        # OpenAI embedding dimensions
        dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072
        }
        return dimensions.get(self.model_name, 1536)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.ollama_embedding_model
        
        # Check if Ollama is available
        ollama_manager = get_ollama_manager()
        if not ollama_manager.is_available():
            raise ValueError("Ollama is not available")
        
        self.embedding_engine = OllamaEmbeddingEngine(self.model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_engine.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        embedding = self.embedding_engine.embed_text(text)
        if embedding is None:
            raise RuntimeError("Failed to generate embedding")
        return embedding
    
    def get_dimension(self) -> int:
        # Common Ollama embedding model dimensions
        dimensions = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384
        }
        return dimensions.get(self.model_name, 384)


def get_embedding_provider(provider: Optional[str] = None) -> EmbeddingProvider:
    """Get embedding provider based on configuration"""
    provider = provider or config.embedding_provider
    
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    elif provider == "ollama":
        return OllamaEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


class UserVectorStore:
    """
    User-isolated vector store with support for multiple embedding providers
    """
    
    def __init__(self, 
                 user_id: Optional[str] = None,
                 collection_name: Optional[str] = None,
                 embedding_provider: Optional[str] = None):
        """
        Initialize user vector store
        
        Args:
            user_id: User ID for document isolation (None for global)
            collection_name: Name of Qdrant collection
            embedding_provider: Embedding provider to use
        """
        self.user_id = user_id
        self.collection_name = collection_name or config.qdrant_collection_name
        self.embedding_provider_name = embedding_provider or config.embedding_provider
        
        # Initialize embedding provider
        self.embedding_provider = get_embedding_provider(self.embedding_provider_name)
        
        # Initialize Qdrant manager
        self.qdrant_manager = get_qdrant_client()
        
        # Vector store instance
        self.vector_store = None
        
        logger.info(f"UserVectorStore initialized for user: {user_id}, "
                   f"collection: {self.collection_name}, "
                   f"provider: {self.embedding_provider_name}")
    
    def create_collection(self, force_recreate: bool = False) -> bool:
        """Create Qdrant collection if it doesn't exist"""
        try:
            vector_size = self.embedding_provider.get_dimension()
            
            if self.qdrant_manager.collection_exists(self.collection_name):
                if force_recreate:
                    logger.info(f"Deleting existing collection: {self.collection_name}")
                    self.qdrant_manager.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection {self.collection_name} already exists")
                    # Ensure indexes exist even if collection exists
                    self._ensure_indexes()
                    return True
            
            # Create collection with proper vector size
            success = self.qdrant_manager.create_collection(
                self.collection_name, 
                vector_size, 
                Distance.COSINE
            )
            
            if success:
                # Create indexes for user filtering
                self._ensure_indexes()
                
            return success
            
        except Exception as e:
            logger.error(f"Error creating collection {self.collection_name}: {e}")
            return False
    
    def _ensure_indexes(self):
        """Ensure all necessary indexes exist"""
        try:
            indexes_to_create = [
                ("user_id", "keyword"),
                ("document_id", "keyword"),
                ("chunk_index", "integer"),
                ("filename", "keyword"),
                ("embedding_provider", "keyword")
            ]
            
            for field_name, field_type in indexes_to_create:
                try:
                    self.qdrant_manager.create_index(
                        self.collection_name, 
                        field_name, 
                        field_type
                    )
                    logger.debug(f"Created/verified index for {field_name}")
                except Exception as e:
                    # Index might already exist, which is fine
                    logger.debug(f"Index creation for {field_name} failed (might already exist): {e}")
            
        except Exception as e:
            logger.warning(f"Error ensuring indexes: {e}")
    
    def add_documents(self, documents: List[Document], document_id: Optional[str] = None) -> bool:
        """
        Add documents to the vector store with user isolation
        
        Args:
            documents: List of Document objects to add
            document_id: Unique document identifier for grouping chunks
            
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
            
            # Generate document ID if not provided
            if not document_id:
                document_id = str(uuid.uuid4())
            
            # Prepare documents with metadata
            enhanced_documents = []
            for i, doc in enumerate(documents):
                # Add user and document metadata
                enhanced_metadata = doc.metadata.copy()
                enhanced_metadata.update({
                    "user_id": self.user_id or "global",
                    "document_id": document_id,
                    "chunk_index": i,
                    "embedding_provider": self.embedding_provider_name
                })
                
                enhanced_doc = Document(
                    page_content=doc.page_content,
                    metadata=enhanced_metadata
                )
                enhanced_documents.append(enhanced_doc)
            
            # Generate embeddings
            texts = [doc.page_content for doc in enhanced_documents]
            embeddings = self.embedding_provider.embed_documents(texts)
            
            # Create points for Qdrant
            points = []
            for i, (doc, embedding) in enumerate(zip(enhanced_documents, embeddings)):
                point = models.PointStruct(
                    id=str(uuid.uuid4()),  # Generate proper UUID string
                    vector=embedding,
                    payload={
                        "content": doc.page_content,
                        **doc.metadata
                    }
                )
                points.append(point)
            
            # Add to Qdrant in batches
            batch_size = config.batch_size
            total_points = len(points)
            
            for i in range(0, total_points, batch_size):
                batch = points[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_points + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} "
                           f"({len(batch)} points)")
                
                success = self.qdrant_manager.upsert_points(self.collection_name, batch)
                if not success:
                    raise Exception(f"Failed to upsert batch {batch_num}")
            
            logger.info(f"Successfully added {total_points} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def similarity_search(self, 
                         query: str, 
                         k: Optional[int] = None,
                         score_threshold: Optional[float] = None,
                         user_filter: bool = True) -> List[Document]:
        """
        Perform similarity search with user isolation
        
        Args:
            query: Search query
            k: Number of documents to return
            score_threshold: Minimum similarity score threshold
            user_filter: Whether to filter by current user
            
        Returns:
            List of similar documents
        """
        try:
            k = k or config.max_chunks_per_query
            
            # Generate query embedding
            query_embedding = self.embedding_provider.embed_query(query)
            
            # Build filter for user isolation
            filter_conditions = None
            if user_filter and self.user_id:
                filter_conditions = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=self.user_id)
                        )
                    ]
                )
            
            # Search in Qdrant with error handling for missing indexes
            try:
                search_results = self.qdrant_manager.search_points(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=k,
                    score_threshold=score_threshold,
                    filter_conditions=filter_conditions
                )
            except Exception as filter_error:
                if "Index required" in str(filter_error) and user_filter:
                    logger.warning(f"Index missing for user filtering, falling back to no filter: {filter_error}")
                    # Fallback: search without user filter
                    search_results = self.qdrant_manager.search_points(
                        collection_name=self.collection_name,
                        query_vector=query_embedding,
                        limit=k,
                        score_threshold=score_threshold,
                        filter_conditions=None
                    )
                    
                    # Filter results manually by user_id
                    if self.user_id:
                        filtered_results = []
                        for result in search_results:
                            if result.payload.get("user_id") == self.user_id:
                                filtered_results.append(result)
                        search_results = filtered_results[:k]
                else:
                    raise filter_error
            
            # Convert to LangChain documents
            documents = []
            for result in search_results:
                doc = Document(
                    page_content=result.payload.get("content", ""),
                    metadata={k: v for k, v in result.payload.items() if k != "content"}
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def get_user_documents(self, document_id: Optional[str] = None) -> List[Document]:
        """
        Get all documents for current user
        
        Args:
            document_id: Filter by specific document ID
            
        Returns:
            List of user documents
        """
        try:
            # Build filter conditions
            must_conditions = []
            
            if self.user_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=self.user_id)
                    )
                )
            
            if document_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id)
                    )
                )
            
            filter_conditions = models.Filter(must=must_conditions) if must_conditions else None
            
            # Scroll through all matching documents
            documents = []
            offset = None
            
            while True:
                results, next_offset = self.qdrant_manager.scroll_points(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=offset,
                    filter_conditions=filter_conditions,
                    with_vectors=False
                )
                
                if not results:
                    break
                
                for point in results:
                    doc = Document(
                        page_content=point.payload.get("content", ""),
                        metadata={k: v for k, v in point.payload.items() if k != "content"}
                    )
                    documents.append(doc)
                
                offset = next_offset
                if not offset:
                    break
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            return []
    
    def delete_user_documents(self, document_id: Optional[str] = None) -> bool:
        """
        Delete documents for current user
        
        Args:
            document_id: Delete specific document only
            
        Returns:
            True if successful
        """
        try:
            # Build filter conditions
            must_conditions = []
            
            if self.user_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=self.user_id)
                    )
                )
            
            if document_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id)
                    )
                )
            
            if not must_conditions:
                logger.warning("No filter conditions provided for deletion")
                return False
            
            filter_conditions = models.Filter(must=must_conditions)
            
            # Delete matching points
            success = self.qdrant_manager.delete_points_by_filter(
                self.collection_name, 
                filter_conditions
            )
            
            if success:
                logger.info(f"Deleted documents for user {self.user_id}, document {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting user documents: {e}")
            return False
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get statistics for current user's documents"""
        try:
            if not self.user_id:
                return {"error": "No user ID provided"}
            
            filter_conditions = models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=self.user_id)
                    )
                ]
            )
            
            # Count user documents with error handling
            try:
                total_chunks = self.qdrant_manager.count_points(
                    self.collection_name, 
                    filter_conditions
                )
            except Exception as count_error:
                if "Index required" in str(count_error):
                    logger.warning(f"Index missing for user stats, using fallback method: {count_error}")
                    # Fallback: get all documents and filter manually
                    all_documents = self.get_user_documents()
                    total_chunks = len(all_documents)
                else:
                    raise count_error
            
            # Get unique document IDs
            documents = self.get_user_documents()
            document_ids = set(doc.metadata.get("document_id") for doc in documents if doc.metadata.get("document_id"))
            
            return {
                "total_chunks": total_chunks,
                "total_documents": len(document_ids),
                "user_id": self.user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"error": str(e), "total_chunks": 0, "total_documents": 0}
    
    def health_check(self) -> bool:
        """Check if the vector store is healthy"""
        try:
            # Check Qdrant connection
            if not self.qdrant_manager.health_check():
                return False
            
            # Check if collection exists
            if not self.qdrant_manager.collection_exists(self.collection_name):
                return True  # Collection not existing is okay
            
            # Try to get collection info
            info = self.qdrant_manager.get_collection_info(self.collection_name)
            return info is not None
            
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the collection"""
        return self.qdrant_manager.get_collection_info(self.collection_name)


# Backward compatibility - keep the original VectorStore class
class VectorStore(UserVectorStore):
    """
    Legacy VectorStore class for backward compatibility
    """
    
    def __init__(self, 
                 collection_name: Optional[str] = None,
                 embedding_model: Optional[str] = None):
        # Map old embedding_model parameter to new system
        embedding_provider = config.embedding_provider
        
        super().__init__(
            user_id=None,  # No user isolation for legacy usage
            collection_name=collection_name,
            embedding_provider=embedding_provider
        )
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Legacy add_documents method"""
        return super().add_documents(documents, document_id=None)
    
    def get_retriever(self, 
                     search_type: str = "similarity",
                     search_kwargs: Optional[Dict[str, Any]] = None):
        """Get a retriever for the vector store (legacy compatibility)"""
        # This method provides compatibility with the old LangChain-based approach
        # For new implementations, use similarity_search directly
        try:
            search_kwargs = search_kwargs or {
                "k": config.max_chunks_per_query
            }
            
            class CustomRetriever:
                def __init__(self, vector_store):
                    self.vector_store = vector_store
                
                def get_relevant_documents(self, query: str) -> List[Document]:
                    return self.vector_store.similarity_search(
                        query, 
                        k=search_kwargs.get("k", config.max_chunks_per_query),
                        score_threshold=search_kwargs.get("score_threshold"),
                        user_filter=False  # Legacy mode without user filtering
                    )
            
            return CustomRetriever(self)
            
        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            return None
    
    def delete_collection(self) -> bool:
        """Delete the collection"""
        return self.qdrant_manager.delete_collection(self.collection_name)
