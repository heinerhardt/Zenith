"""
Unit tests for Vector Store
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.vector_store import VectorStore
from src.core.config import config
from langchain.schema import Document


class TestVectorStore:
    """Test cases for Vector Store"""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Create mock Qdrant client"""
        with patch('src.core.vector_store.QdrantClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def vector_store(self, mock_qdrant_client):
        """Create vector store instance for testing"""
        with patch('src.core.vector_store.OpenAIEmbeddings'):
            return VectorStore(collection_name="test_collection")
    
    def test_vector_store_initialization(self, vector_store):
        """Test vector store initialization"""
        assert vector_store.collection_name == "test_collection"
        assert vector_store.embeddings is not None
        assert vector_store.qdrant_client is not None
    
    def test_create_collection_success(self, vector_store, mock_qdrant_client):
        """Test successful collection creation"""
        # Mock collections response
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        result = vector_store.create_collection()
        
        assert result is True
        mock_qdrant_client.create_collection.assert_called_once()
    
    def test_create_collection_already_exists(self, vector_store, mock_qdrant_client):
        """Test collection creation when collection already exists"""
        # Mock existing collection
        mock_collection = Mock()
        mock_collection.name = "test_collection"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        result = vector_store.create_collection()
        
        assert result is True
        mock_qdrant_client.create_collection.assert_not_called()
    
    def test_add_documents_empty_list(self, vector_store):
        """Test adding empty document list"""
        documents = []
        result = vector_store.add_documents(documents)
        assert result is False
    
    def test_add_documents_success(self, vector_store, mock_qdrant_client):
        """Test successful document addition"""
        # Mock successful collection creation
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        # Create test documents
        documents = [
            Document(page_content="Test content 1", metadata={"source": "test1.pdf"}),
            Document(page_content="Test content 2", metadata={"source": "test2.pdf"})
        ]
        
        with patch.object(vector_store, 'vector_store') as mock_vector_store:
            result = vector_store.add_documents(documents)
            
            # Should attempt to create collection and add documents
            assert mock_qdrant_client.create_collection.called
    
    def test_similarity_search_no_vector_store(self, vector_store):
        """Test similarity search when vector store is not initialized"""
        with patch('src.core.vector_store.Qdrant') as mock_qdrant:
            mock_instance = Mock()
            mock_qdrant.return_value = mock_instance
            mock_instance.similarity_search.return_value = []
            
            result = vector_store.similarity_search("test query")
            assert result == []
    
    def test_health_check_success(self, vector_store, mock_qdrant_client):
        """Test successful health check"""
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections
        
        result = vector_store.health_check()
        assert result is True
    
    def test_health_check_failure(self, vector_store, mock_qdrant_client):
        """Test health check failure"""
        mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")
        
        result = vector_store.health_check()
        assert result is False
    
    def test_delete_collection_success(self, vector_store, mock_qdrant_client):
        """Test successful collection deletion"""
        result = vector_store.delete_collection()
        
        assert result is True
        mock_qdrant_client.delete_collection.assert_called_once_with("test_collection")
        assert vector_store.vector_store is None
    
    def test_delete_collection_failure(self, vector_store, mock_qdrant_client):
        """Test collection deletion failure"""
        mock_qdrant_client.delete_collection.side_effect = Exception("Delete failed")
        
        result = vector_store.delete_collection()
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
