"""
Chat History Manager for Zenith PDF Chatbot
Manages user chat sessions and conversation history
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json

from src.utils.logger import get_logger
from src.core.qdrant_manager import get_qdrant_client

logger = get_logger(__name__)

@dataclass
class ChatMessage:
    """Individual chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_id: str = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary"""
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            message_id=data.get('message_id', str(uuid.uuid4()))
        )

@dataclass
class ChatSession:
    """Chat session containing multiple messages"""
    session_id: str
    user_id: str
    title: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    document_context: Optional[str] = None  # Associated document/context
    
    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
    
    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the session"""
        message = ChatMessage(role=role, content=content, timestamp=datetime.now())
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)
    
    def get_conversation_preview(self, max_length: int = 100) -> str:
        """Get a preview of the conversation"""
        if not self.messages:
            return "New conversation"
        
        first_user_message = next((msg for msg in self.messages if msg.role == 'user'), None)
        if first_user_message:
            preview = first_user_message.content[:max_length]
            if len(first_user_message.content) > max_length:
                preview += "..."
            return preview
        return "New conversation"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'title': self.title,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'document_context': self.document_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        """Create from dictionary"""
        messages = [ChatMessage.from_dict(msg_data) for msg_data in data.get('messages', [])]
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            title=data['title'],
            messages=messages,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            document_context=data.get('document_context')
        )

class ChatHistoryManager:
    """Manages chat history for users"""
    
    def __init__(self):
        """Initialize chat history manager"""
        self.qdrant_client = get_qdrant_client().get_client()
        self.collection_name = "zenith_chat_history"
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure chat history collection exists"""
        try:
            from qdrant_client.http import models
            
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection for chat history
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # Small vector size for chat data
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created chat history collection: {self.collection_name}")
                
                # Create indexes
                try:
                    self.qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="user_id",
                        field_schema=models.KeywordIndexParams(
                            type="keyword",
                            is_tenant=False
                        )
                    )
                    self.qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="type",
                        field_schema=models.KeywordIndexParams(
                            type="keyword",
                            is_tenant=False
                        )
                    )
                    logger.info("Created chat history indexes")
                except Exception as e:
                    logger.warning(f"Could not create chat history indexes: {e}")
                    
        except Exception as e:
            logger.error(f"Error ensuring chat history collection exists: {e}")
    
    def _create_session_vector(self, session_id: str) -> List[float]:
        """Create a vector for session storage"""
        import hashlib
        
        hash_obj = hashlib.sha256(session_id.encode())
        hash_bytes = hash_obj.digest()
        
        vector = []
        for i in range(384):
            byte_index = i % len(hash_bytes)
            vector.append((hash_bytes[byte_index] - 128) / 128.0)
        
        return vector
    
    def create_session(self, user_id: str, title: str = None, document_context: str = None) -> ChatSession:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        if not title:
            title = f"Chat Session {now.strftime('%Y-%m-%d %H:%M')}"
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
            document_context=document_context
        )
        
        self.save_session(session)
        return session
    
    def save_session(self, session: ChatSession) -> bool:
        """Save a chat session"""
        try:
            from qdrant_client.http import models
            
            vector = self._create_session_vector(session.session_id)
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=session.session_id,
                        vector=vector,
                        payload={
                            **session.to_dict(),
                            'type': 'chat_session'
                        }
                    )
                ]
            )
            
            logger.debug(f"Saved chat session: {session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving chat session {session.session_id}: {e}")
            return False
    
    def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a specific chat session"""
        try:
            result = self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[session_id]
            )
            
            if result and len(result) > 0:
                payload = result[0].payload
                if payload.get('type') == 'chat_session' and payload.get('user_id') == user_id:
                    return ChatSession.from_dict(payload)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting chat session {session_id}: {e}")
            return None
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[ChatSession]:
        """Get chat sessions for a user"""
        try:
            from qdrant_client.http import models
            
            result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value="chat_session")
                        ),
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True
            )
            
            sessions = []
            if result and result[0]:
                for point in result[0]:
                    try:
                        session = ChatSession.from_dict(point.payload)
                        sessions.append(session)
                    except Exception as e:
                        logger.warning(f"Error parsing chat session data: {e}")
            
            # Sort by updated_at descending (most recent first)
            sessions.sort(key=lambda s: s.updated_at, reverse=True)
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []
    
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        try:
            # Verify ownership before deletion
            session = self.get_session(session_id, user_id)
            if not session:
                logger.warning(f"Session {session_id} not found or not owned by user {user_id}")
                return False
            
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=[session_id]
            )
            
            logger.info(f"Deleted chat session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {e}")
            return False
    
    def cleanup_old_sessions(self, user_id: str, keep_count: int = 5) -> int:
        """Keep only the most recent N sessions for a user"""
        try:
            sessions = self.get_user_sessions(user_id, limit=100)  # Get more to cleanup
            
            if len(sessions) <= keep_count:
                return 0  # Nothing to cleanup
            
            # Delete oldest sessions
            sessions_to_delete = sessions[keep_count:]
            deleted_count = 0
            
            for session in sessions_to_delete:
                if self.delete_session(session.session_id, user_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old sessions for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions for user {user_id}: {e}")
            return 0
    
    def add_message_to_session(self, session_id: str, user_id: str, role: str, content: str) -> bool:
        """Add a message to an existing session"""
        try:
            session = self.get_session(session_id, user_id)
            if not session:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return False
            
            session.add_message(role, content)
            return self.save_session(session)
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False


# Global instance
_chat_history_manager = None

def get_chat_history_manager() -> ChatHistoryManager:
    """Get global chat history manager instance"""
    global _chat_history_manager
    if _chat_history_manager is None:
        _chat_history_manager = ChatHistoryManager()
    return _chat_history_manager
