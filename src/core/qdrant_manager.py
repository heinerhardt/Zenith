"""
Qdrant Manager for Zenith - Supports both local and cloud instances
"""

from typing import Optional, List, Dict, Any, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import numpy as np

from src.core.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QdrantManager:
    """Unified Qdrant client manager supporting local and cloud deployments"""
    
    def __init__(self, mode: Optional[str] = None):
        """
        Initialize Qdrant client based on mode
        
        Args:
            mode: 'local' or 'cloud'. If None, uses config default
        """
        self.mode = mode or config.qdrant_mode
        self.client = self._create_client()
        
    def _create_client(self) -> QdrantClient:
        """Create Qdrant client based on configuration"""
        try:
            if self.mode == "local":
                logger.info(f"Connecting to local Qdrant at {config.qdrant_url}:{config.qdrant_port}")
                client = QdrantClient(
                    host=config.qdrant_url,
                    port=config.qdrant_port,
                    timeout=30
                )
            elif self.mode == "cloud":
                if not config.qdrant_api_key:
                    raise ValueError("Qdrant API key required for cloud mode")
                
                logger.info(f"Connecting to Qdrant cloud at {config.qdrant_url}")
                client = QdrantClient(
                    url=config.qdrant_url,
                    api_key=config.qdrant_api_key,
                    timeout=30
                )
            else:
                raise ValueError(f"Invalid Qdrant mode: {self.mode}")
            
            # Test connection
            client.get_collections()
            logger.info(f"Successfully connected to Qdrant in {self.mode} mode")
            return client
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise ConnectionError(f"Could not connect to Qdrant: {e}")
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    def create_collection(self, collection_name: str, vector_size: int = 1536, 
                         distance: Distance = Distance.COSINE) -> bool:
        """Create a collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            existing_names = [col.name for col in collections.collections]
            
            if collection_name in existing_names:
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists"""
        try:
            collections = self.client.get_collections()
            return collection_name in [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status,
                'optimizer_status': info.optimizer_status,
                'indexed_vectors_count': info.indexed_vectors_count,
            }
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return None
    
    def upsert_points(self, collection_name: str, points: List[models.PointStruct]) -> bool:
        """Upsert points into a collection"""
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.debug(f"Upserted {len(points)} points to {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            return False
    
    def search_points(self, collection_name: str, query_vector: List[float],
                     limit: int = 10, score_threshold: Optional[float] = None,
                     filter_conditions: Optional[models.Filter] = None) -> List[models.ScoredPoint]:
        """Search for similar vectors"""
        try:
            search_params = {
                'collection_name': collection_name,
                'query_vector': query_vector,
                'limit': limit
            }
            
            if score_threshold is not None:
                search_params['score_threshold'] = score_threshold
            
            if filter_conditions is not None:
                search_params['query_filter'] = filter_conditions
            
            results = self.client.search(**search_params)
            return results
        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            return []
    
    def get_points(self, collection_name: str, point_ids: List[Union[str, int]],
                  with_vectors: bool = False) -> List[models.Record]:
        """Retrieve specific points by ID"""
        try:
            return self.client.retrieve(
                collection_name=collection_name,
                ids=point_ids,
                with_vectors=with_vectors
            )
        except Exception as e:
            logger.error(f"Failed to retrieve points from {collection_name}: {e}")
            return []
    
    def scroll_points(self, collection_name: str, limit: int = 100,
                     offset: Optional[Union[str, int]] = None,
                     filter_conditions: Optional[models.Filter] = None,
                     with_vectors: bool = False) -> tuple:
        """Scroll through points in a collection"""
        try:
            scroll_params = {
                'collection_name': collection_name,
                'limit': limit,
                'with_vectors': with_vectors
            }
            
            if offset is not None:
                scroll_params['offset'] = offset
            
            if filter_conditions is not None:
                scroll_params['scroll_filter'] = filter_conditions
            
            return self.client.scroll(**scroll_params)
        except Exception as e:
            logger.error(f"Scroll failed in {collection_name}: {e}")
            return [], None
    
    def delete_points(self, collection_name: str, point_ids: List[Union[str, int]]) -> bool:
        """Delete specific points"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            logger.info(f"Deleted {len(point_ids)} points from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete points from {collection_name}: {e}")
            return False
    
    def delete_points_by_filter(self, collection_name: str, 
                               filter_conditions: models.Filter) -> bool:
        """Delete points matching filter criteria"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=filter_conditions
                )
            )
            logger.info(f"Deleted points by filter from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete points by filter from {collection_name}: {e}")
            return False
    
    def count_points(self, collection_name: str, 
                    filter_conditions: Optional[models.Filter] = None) -> int:
        """Count points in collection"""
        try:
            count_params = {'collection_name': collection_name}
            if filter_conditions:
                count_params['count_filter'] = filter_conditions
            
            result = self.client.count(**count_params)
            return result.count
        except Exception as e:
            logger.error(f"Failed to count points in {collection_name}: {e}")
            return 0
    
    def create_index(self, collection_name: str, field_name: str, 
                    field_type: str = "keyword") -> bool:
        """Create an index on a payload field"""
        try:
            if field_type == "keyword":
                field_schema = models.KeywordIndexParams(
                    type="keyword",
                    is_tenant=False
                )
            elif field_type == "integer":
                field_schema = models.IntegerIndexParams(
                    type="integer",
                    range=True,
                    lookup=True
                )
            else:
                raise ValueError(f"Unsupported field type: {field_type}")
            
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema
            )
            
            logger.info(f"Created {field_type} index on {field_name} in {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index on {field_name}: {e}")
            return False
    
    def get_client(self) -> QdrantClient:
        """Get the underlying Qdrant client"""
        return self.client
    
    def close(self):
        """Close the Qdrant client connection"""
        try:
            self.client.close()
            logger.info("Qdrant client connection closed")
        except Exception as e:
            logger.error(f"Error closing Qdrant client: {e}")


# Global instance
_qdrant_manager = None

def get_qdrant_client() -> QdrantManager:
    """Get global Qdrant client instance"""
    global _qdrant_manager
    if _qdrant_manager is None:
        _qdrant_manager = QdrantManager()
    return _qdrant_manager

def reset_qdrant_client():
    """Reset global Qdrant client (useful for config changes)"""
    global _qdrant_manager
    if _qdrant_manager:
        _qdrant_manager.close()
        _qdrant_manager = None
