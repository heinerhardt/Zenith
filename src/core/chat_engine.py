"""
Chat Engine Module for Zenith PDF Chatbot
Handles conversational AI interactions with document retrieval
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.schema import Document, BaseMessage
from langchain.prompts import PromptTemplate

from .config import config
from .vector_store import VectorStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChatEngine:
    """
    Handles conversational AI interactions with document retrieval
    """
    
    def __init__(self, 
                 vector_store: VectorStore,
                 model_name: Optional[str] = None,
                 temperature: float = 0.1,
                 memory_type: str = "buffer"):
        """
        Initialize chat engine
        
        Args:
            vector_store: VectorStore instance
            model_name: OpenAI model name
            temperature: Model temperature for creativity
            memory_type: Type of memory ("buffer", "summary_buffer")
        """
        self.vector_store = vector_store
        self.model_name = model_name or config.openai_model
        self.temperature = temperature
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize memory
        self.memory = self._initialize_memory(memory_type)
        
        # Initialize conversation chain
        self.conversation_chain = None
        self.qa_chain = None
        
        logger.info(f"ChatEngine initialized with model: {self.model_name}")
    
    def _initialize_llm(self):
        """
        Initialize the language model
        
        Returns:
            LLM instance
        """
        try:
            if "gpt-3.5" in self.model_name or "gpt-4" in self.model_name:
                llm = ChatOpenAI(
                    openai_api_key=config.openai_api_key,
                    model_name=self.model_name,
                    temperature=self.temperature,
                    max_tokens=1000
                )
            else:
                llm = OpenAI(
                    openai_api_key=config.openai_api_key,
                    model_name=self.model_name,
                    temperature=self.temperature,
                    max_tokens=1000
                )
            
            logger.info(f"Initialized LLM: {self.model_name}")
            return llm
            
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise
    
    def _initialize_memory(self, memory_type: str):
        """
        Initialize conversation memory
        
        Args:
            memory_type: Type of memory to use
            
        Returns:
            Memory instance
        """
        try:
            if memory_type == "summary_buffer":
                memory = ConversationSummaryBufferMemory(
                    llm=self.llm,
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="answer",
                    max_token_limit=1000
                )
            else:
                memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="answer"
                )
            
            logger.info(f"Initialized memory type: {memory_type}")
            return memory
            
        except Exception as e:
            logger.error(f"Error initializing memory: {e}")
            raise
    
    def _create_custom_prompt(self) -> PromptTemplate:
        """
        Create a custom prompt template for better responses
        
        Returns:
            PromptTemplate instance
        """
        template = """You are an AI assistant that helps users understand and analyze documents. 
        Use the following pieces of context to answer the user's question. 
        If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.
        
        Always cite the source document when providing information.
        Be concise but comprehensive in your responses.
        If the question requires information from multiple documents, synthesize the information appropriately.
        
        Context: {context}
        
        Question: {question}
        
        Helpful Answer:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def setup_conversation_chain(self) -> bool:
        """
        Setup the conversational retrieval chain
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get retriever from vector store
            retriever = self.vector_store.get_retriever(
                search_type="similarity",
                search_kwargs={"k": config.max_chunks_per_query}
            )
            
            if retriever is None:
                logger.error("Failed to get retriever from vector store")
                return False
            
            # Create conversation chain
            self.conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=self.memory,
                return_source_documents=True,
                verbose=True,
                combine_docs_chain_kwargs={
                    "prompt": self._create_custom_prompt()
                }
            )
            
            # Create QA chain for single questions
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": self._create_custom_prompt()
                }
            )
            
            logger.info("Conversation chain setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up conversation chain: {e}")
            return False
    
    def chat(self, question: str, use_conversation: bool = True) -> Dict[str, Any]:
        """
        Chat with the documents
        
        Args:
            question: User question
            use_conversation: Whether to use conversation history
            
        Returns:
            Dictionary containing answer and source documents
        """
        try:
            if use_conversation:
                if self.conversation_chain is None:
                    if not self.setup_conversation_chain():
                        raise Exception("Failed to setup conversation chain")
                
                response = self.conversation_chain({"question": question})
            else:
                if self.qa_chain is None:
                    if not self.setup_conversation_chain():
                        raise Exception("Failed to setup QA chain")
                
                response = self.qa_chain({"query": question})
            
            # Process response
            processed_response = self._process_response(response, question)
            
            logger.info(f"Generated response for question: {question[:50]}...")
            return processed_response
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "source_documents": [],
                "question": question,
                "error": True
            }
    
    def _process_response(self, response: Dict[str, Any], question: str) -> Dict[str, Any]:
        """
        Process and format the response
        
        Args:
            response: Raw response from chain
            question: Original question
            
        Returns:
            Processed response dictionary
        """
        try:
            # Extract answer
            answer = response.get("answer", "No answer generated")
            
            # Extract source documents
            source_docs = response.get("source_documents", [])
            
            # Format source documents
            formatted_sources = []
            for i, doc in enumerate(source_docs):
                source_info = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source_id": i + 1,
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "page": doc.metadata.get("page", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", i)
                }
                formatted_sources.append(source_info)
            
            # Create processed response
            processed_response = {
                "answer": answer,
                "source_documents": formatted_sources,
                "question": question,
                "num_sources": len(formatted_sources),
                "error": False,
                "timestamp": str(pd.Timestamp.now())
            }
            
            return processed_response
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {
                "answer": "Error processing response",
                "source_documents": [],
                "question": question,
                "error": True
            }
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """
        Get conversation history
        
        Returns:
            List of conversation messages
        """
        try:
            if hasattr(self.memory, 'chat_memory'):
                return self.memory.chat_memory.messages
            return []
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        try:
            self.memory.clear()
            logger.info("Conversation history cleared")
            
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
    
    def summarize_conversation(self) -> str:
        """
        Get a summary of the conversation
        
        Returns:
            Conversation summary
        """
        try:
            if isinstance(self.memory, ConversationSummaryBufferMemory):
                return self.memory.moving_summary_buffer
            else:
                # Create a simple summary from buffer memory
                messages = self.get_conversation_history()
                if messages:
                    return f"Conversation with {len(messages)//2} exchanges"
                return "No conversation history"
                
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Error generating summary"
    
    def ask_multiple_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """
        Ask multiple questions in sequence
        
        Args:
            questions: List of questions to ask
            
        Returns:
            List of responses
        """
        responses = []
        
        for question in questions:
            try:
                response = self.chat(question)
                responses.append(response)
                
            except Exception as e:
                logger.error(f"Error processing question '{question}': {e}")
                responses.append({
                    "answer": f"Error processing question: {str(e)}",
                    "source_documents": [],
                    "question": question,
                    "error": True
                })
        
        return responses
    
    def get_relevant_documents(self, question: str, k: int = 5) -> List[Document]:
        """
        Get relevant documents without generating an answer
        
        Args:
            question: Query to search for
            k: Number of documents to return
            
        Returns:
            List of relevant documents
        """
        try:
            return self.vector_store.similarity_search(question, k=k)
            
        except Exception as e:
            logger.error(f"Error getting relevant documents: {e}")
            return []
    
    def health_check(self) -> bool:
        """
        Check if the chat engine is ready
        
        Returns:
            True if ready, False otherwise
        """
        try:
            # Check vector store
            if not self.vector_store.health_check():
                return False
            
            # Check if we can create chains
            if self.conversation_chain is None:
                return self.setup_conversation_chain()
            
            return True
            
        except Exception as e:
            logger.error(f"Chat engine health check failed: {e}")
            return False


# Import pandas for timestamp
import pandas as pd
