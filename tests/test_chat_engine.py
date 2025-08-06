"""
Unit tests for Chat Engine
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.chat_engine import ChatEngine
from src.core.vector_store import VectorStore


class TestChatEngine:
    """Test cases for Chat Engine"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store"""
        mock_store = Mock(spec=VectorStore)
        mock_store.get_retriever.return_value = Mock()
        mock_store.health_check.return_value = True
        return mock_store
    
    @pytest.fixture
    def chat_engine(self, mock_vector_store):
        """Create chat engine instance for testing"""
        with patch('src.core.chat_engine.ChatOpenAI'), \
             patch('src.core.chat_engine.ConversationBufferMemory'):
            return ChatEngine(mock_vector_store, model_name="gpt-3.5-turbo")
    
    def test_chat_engine_initialization(self, chat_engine, mock_vector_store):
        """Test chat engine initialization"""
        assert chat_engine.vector_store == mock_vector_store
        assert chat_engine.model_name == "gpt-3.5-turbo"
        assert chat_engine.llm is not None
        assert chat_engine.memory is not None
    
    def test_setup_conversation_chain_success(self, chat_engine):
        """Test successful conversation chain setup"""
        with patch('src.core.chat_engine.ConversationalRetrievalChain') as mock_chain, \
             patch('src.core.chat_engine.RetrievalQA') as mock_qa:
            
            result = chat_engine.setup_conversation_chain()
            
            assert result is True
            assert chat_engine.conversation_chain is not None
            assert chat_engine.qa_chain is not None
    
    def test_setup_conversation_chain_no_retriever(self, chat_engine):
        """Test conversation chain setup when retriever is None"""
        chat_engine.vector_store.get_retriever.return_value = None
        
        result = chat_engine.setup_conversation_chain()
        assert result is False
    
    def test_chat_without_setup(self, chat_engine):
        """Test chat when conversation chain is not setup"""
        chat_engine.conversation_chain = None
        
        with patch.object(chat_engine, 'setup_conversation_chain', return_value=False):
            response = chat_engine.chat("test question")
            
            assert response["error"] is True
            assert "Failed to setup" in response["answer"]
    
    def test_chat_success(self, chat_engine):
        """Test successful chat interaction"""
        # Mock conversation chain
        mock_chain = Mock()
        mock_chain.return_value = {
            "answer": "Test answer",
            "source_documents": []
        }
        chat_engine.conversation_chain = mock_chain
        
        response = chat_engine.chat("test question")
        
        assert response["error"] is False
        assert response["answer"] == "Test answer"
        assert response["question"] == "test question"
        assert isinstance(response["source_documents"], list)
    
    def test_chat_with_sources(self, chat_engine):
        """Test chat with source documents"""
        from langchain.schema import Document
        
        mock_doc = Document(
            page_content="Source content",
            metadata={"filename": "test.pdf", "page": 1}
        )
        
        mock_chain = Mock()
        mock_chain.return_value = {
            "answer": "Test answer",
            "source_documents": [mock_doc]
        }
        chat_engine.conversation_chain = mock_chain
        
        response = chat_engine.chat("test question")
        
        assert response["error"] is False
        assert response["num_sources"] == 1
        assert len(response["source_documents"]) == 1
        assert response["source_documents"][0]["filename"] == "test.pdf"
    
    def test_clear_conversation_history(self, chat_engine):
        """Test clearing conversation history"""
        mock_memory = Mock()
        chat_engine.memory = mock_memory
        
        chat_engine.clear_conversation_history()
        
        mock_memory.clear.assert_called_once()
    
    def test_get_conversation_history(self, chat_engine):
        """Test getting conversation history"""
        mock_memory = Mock()
        mock_memory.chat_memory.messages = ["message1", "message2"]
        chat_engine.memory = mock_memory
        
        history = chat_engine.get_conversation_history()
        
        assert len(history) == 2
        assert history == ["message1", "message2"]
    
    def test_get_relevant_documents(self, chat_engine):
        """Test getting relevant documents without chat"""
        mock_docs = [Mock(), Mock()]
        chat_engine.vector_store.similarity_search.return_value = mock_docs
        
        result = chat_engine.get_relevant_documents("test query", k=2)
        
        assert len(result) == 2
        chat_engine.vector_store.similarity_search.assert_called_with("test query", k=2)
    
    def test_ask_multiple_questions(self, chat_engine):
        """Test asking multiple questions"""
        questions = ["Question 1", "Question 2"]
        
        with patch.object(chat_engine, 'chat') as mock_chat:
            mock_chat.side_effect = [
                {"answer": "Answer 1", "error": False},
                {"answer": "Answer 2", "error": False}
            ]
            
            responses = chat_engine.ask_multiple_questions(questions)
            
            assert len(responses) == 2
            assert responses[0]["answer"] == "Answer 1"
            assert responses[1]["answer"] == "Answer 2"
    
    def test_health_check_success(self, chat_engine):
        """Test successful health check"""
        result = chat_engine.health_check()
        assert result is True
    
    def test_health_check_vector_store_unhealthy(self, chat_engine):
        """Test health check when vector store is unhealthy"""
        chat_engine.vector_store.health_check.return_value = False
        
        result = chat_engine.health_check()
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
