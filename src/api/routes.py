"""
API Routes for Zenith PDF Chatbot
Defines REST API endpoints for PDF processing and chat functionality
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import tempfile
from pathlib import Path
import asyncio
import logging

from src.core.pdf_processor import PDFProcessor
from src.core.vector_store import VectorStore
from src.core.chat_engine import ChatEngine
from src.core.config import config
from src.utils.logger import get_logger
from src.utils.helpers import validate_file_type, format_file_size, create_temp_file

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Pydantic models for request/response
class ChatRequest(BaseModel):
    question: str
    use_conversation: bool = True
    max_chunks: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    question: str
    source_documents: List[Dict[str, Any]]
    num_sources: int
    error: bool = False
    timestamp: str


class ProcessPDFRequest(BaseModel):
    pdf_directory: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    collection_name: Optional[str] = None


class ProcessPDFResponse(BaseModel):
    success: bool
    message: str
    total_documents: int
    total_chunks: int
    processed_files: List[str]


class SystemInfoResponse(BaseModel):
    status: str
    components: Dict[str, bool]
    collection_info: Optional[Dict[str, Any]] = None
    config: Dict[str, Any]


# Global components (will be injected by main app)
_pdf_processor: Optional[PDFProcessor] = None
_vector_store: Optional[VectorStore] = None
_chat_engine: Optional[ChatEngine] = None


def set_components(pdf_processor: PDFProcessor, vector_store: VectorStore, chat_engine: ChatEngine):
    """Set global component instances"""
    global _pdf_processor, _vector_store, _chat_engine
    _pdf_processor = pdf_processor
    _vector_store = vector_store
    _chat_engine = chat_engine


def get_components():
    """Get initialized components"""
    if not all([_pdf_processor, _vector_store, _chat_engine]):
        raise HTTPException(
            status_code=503,
            detail="API components not initialized"
        )
    
    return {
        "pdf_processor": _pdf_processor,
        "vector_store": _vector_store,
        "chat_engine": _chat_engine
    }


@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """
    Chat with processed documents
    
    Args:
        request: Chat request with question and options
        
    Returns:
        Chat response with answer and sources
    """
    try:
        components = get_components()
        chat_engine = components["chat_engine"]
        
        # Generate response
        response = chat_engine.chat(
            question=request.question,
            use_conversation=request.use_conversation
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.post("/process-pdfs", response_model=ProcessPDFResponse)
async def process_pdfs_directory(request: ProcessPDFRequest):
    """
    Process PDFs from a directory
    
    Args:
        request: Processing request with directory path and options
        
    Returns:
        Processing result with statistics
    """
    try:
        components = get_components()
        pdf_processor = components["pdf_processor"]
        vector_store = components["vector_store"]
        chat_engine = components["chat_engine"]
        
        if not request.pdf_directory:
            raise HTTPException(
                status_code=400,
                detail="PDF directory path is required"
            )
        
        directory_path = Path(request.pdf_directory)
        if not directory_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {request.pdf_directory}"
            )
        
        # Update processor settings if provided
        if request.chunk_size:
            pdf_processor.chunk_size = request.chunk_size
            pdf_processor.text_splitter.chunk_size = request.chunk_size
        
        if request.chunk_overlap:
            pdf_processor.chunk_overlap = request.chunk_overlap
            pdf_processor.text_splitter.chunk_overlap = request.chunk_overlap
        
        # Load documents
        documents = pdf_processor.load_pdfs_from_directory(request.pdf_directory)
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No PDF documents found in the specified directory"
            )
        
        # Split documents
        chunks = pdf_processor.split_documents(documents)
        
        # Store in vector database
        success = vector_store.add_documents(chunks)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to store documents in vector database"
            )
        
        # Setup chat engine
        chat_engine.setup_conversation_chain()
        
        # Get processed file names
        pdf_files = list(directory_path.glob("**/*.pdf"))
        processed_files = [f.name for f in pdf_files]
        
        return ProcessPDFResponse(
            success=True,
            message=f"Successfully processed {len(documents)} pages into {len(chunks)} chunks",
            total_documents=len(documents),
            total_chunks=len(chunks),
            processed_files=processed_files
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF processing API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDFs: {str(e)}"
        )


@router.post("/upload-pdfs", response_model=ProcessPDFResponse)
async def upload_and_process_pdfs(
    files: List[UploadFile] = File(...),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None)
):
    """
    Upload and process PDF files
    
    Args:
        files: List of uploaded PDF files
        chunk_size: Optional chunk size override
        chunk_overlap: Optional chunk overlap override
        
    Returns:
        Processing result with statistics
    """
    try:
        components = get_components()
        pdf_processor = components["pdf_processor"]
        vector_store = components["vector_store"]
        chat_engine = components["chat_engine"]
        
        # Validate files
        for file in files:
            if not validate_file_type(file.filename, ['.pdf']):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Only PDF files are allowed."
                )
        
        # Update processor settings if provided
        if chunk_size:
            pdf_processor.chunk_size = chunk_size
            pdf_processor.text_splitter.chunk_size = chunk_size
        
        if chunk_overlap:
            pdf_processor.chunk_overlap = chunk_overlap
            pdf_processor.text_splitter.chunk_overlap = chunk_overlap
        
        # Process uploaded files
        temp_files = []
        documents = []
        
        try:
            # Save uploaded files temporarily
            for file in files:
                content = await file.read()
                temp_path = create_temp_file(content, suffix=".pdf")
                temp_files.append(temp_path)
                
                # Load PDF
                file_documents = pdf_processor.load_pdf(temp_path)
                documents.extend(file_documents)
            
            if not documents:
                raise HTTPException(
                    status_code=400,
                    detail="No valid PDF documents were processed"
                )
            
            # Split documents
            chunks = pdf_processor.split_documents(documents)
            
            # Store in vector database
            success = vector_store.add_documents(chunks)
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to store documents in vector database"
                )
            
            # Setup chat engine
            chat_engine.setup_conversation_chain()
            
            processed_files = [file.filename for file in files]
            
            return ProcessPDFResponse(
                success=True,
                message=f"Successfully processed {len(documents)} pages into {len(chunks)} chunks",
                total_documents=len(documents),
                total_chunks=len(chunks),
                processed_files=processed_files
            )
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file}: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload PDF API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing uploaded PDFs: {str(e)}"
        )


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_documents(
    query: str,
    k: int = 5,
    score_threshold: Optional[float] = None
):
    """
    Search for relevant documents
    
    Args:
        query: Search query
        k: Number of documents to return
        score_threshold: Minimum similarity score
        
    Returns:
        List of relevant documents
    """
    try:
        components = get_components()
        vector_store = components["vector_store"]
        
        # Perform similarity search
        documents = vector_store.similarity_search(
            query=query,
            k=k,
            score_threshold=score_threshold
        )
        
        # Format results
        results = []
        for i, doc in enumerate(documents):
            results.append({
                "id": i,
                "content": doc.page_content,
                "metadata": doc.metadata,
                "filename": doc.metadata.get("filename", "Unknown"),
                "page": doc.metadata.get("page", "Unknown")
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )


@router.get("/system-info", response_model=SystemInfoResponse)
async def get_system_info():
    """
    Get system information and status
    
    Returns:
        System information including component status
    """
    try:
        components = get_components()
        vector_store = components["vector_store"]
        chat_engine = components["chat_engine"]
        
        # Check component health
        vector_health = vector_store.health_check()
        chat_health = chat_engine.health_check()
        
        # Get collection info
        collection_info = vector_store.get_collection_info()
        
        return SystemInfoResponse(
            status="healthy" if vector_health and chat_health else "degraded",
            components={
                "pdf_processor": _pdf_processor is not None,
                "vector_store": vector_health,
                "chat_engine": chat_health
            },
            collection_info=collection_info,
            config={
                "qdrant_url": config.qdrant_url,
                "qdrant_port": config.qdrant_port,
                "collection_name": config.qdrant_collection_name,
                "chunk_size": config.chunk_size,
                "chunk_overlap": config.chunk_overlap,
                "max_chunks_per_query": config.max_chunks_per_query
            }
        )
        
    except Exception as e:
        logger.error(f"System info API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system information: {str(e)}"
        )


@router.delete("/collection")
async def delete_collection():
    """
    Delete the current collection and clear all data
    
    Returns:
        Success message
    """
    try:
        components = get_components()
        vector_store = components["vector_store"]
        chat_engine = components["chat_engine"]
        
        # Delete collection
        success = vector_store.delete_collection()
        
        if success:
            # Clear chat history
            chat_engine.clear_conversation_history()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Collection deleted successfully"
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete collection"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete collection API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting collection: {str(e)}"
        )


@router.get("/conversation-history")
async def get_conversation_history():
    """
    Get conversation history
    
    Returns:
        List of conversation messages
    """
    try:
        components = get_components()
        chat_engine = components["chat_engine"]
        
        history = chat_engine.get_conversation_history()
        
        # Format history for JSON response
        formatted_history = []
        for message in history:
            formatted_history.append({
                "type": message.type if hasattr(message, 'type') else "unknown",
                "content": message.content if hasattr(message, 'content') else str(message)
            })
        
        return {
            "conversation_history": formatted_history,
            "total_messages": len(formatted_history)
        }
        
    except Exception as e:
        logger.error(f"Conversation history API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation history: {str(e)}"
        )


@router.delete("/conversation-history")
async def clear_conversation_history():
    """
    Clear conversation history
    
    Returns:
        Success message
    """
    try:
        components = get_components()
        chat_engine = components["chat_engine"]
        
        chat_engine.clear_conversation_history()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Conversation history cleared successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Clear conversation history API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing conversation history: {str(e)}"
        )


@router.post("/batch-questions")
async def ask_batch_questions(questions: List[str]):
    """
    Ask multiple questions in batch
    
    Args:
        questions: List of questions to ask
        
    Returns:
        List of responses
    """
    try:
        components = get_components()
        chat_engine = components["chat_engine"]
        
        responses = chat_engine.ask_multiple_questions(questions)
        
        return {
            "responses": responses,
            "total_questions": len(questions),
            "success_count": sum(1 for r in responses if not r.get("error", False))
        }
        
    except Exception as e:
        logger.error(f"Batch questions API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing batch questions: {str(e)}"
        )
