"""
FastAPI Main Application for Zenith PDF Chatbot
Provides REST API endpoints for PDF processing and chat functionality
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import os
import sys
from pathlib import Path
import logging
import traceback

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.core.pdf_processor import PDFProcessor
from src.core.vector_store import VectorStore
from src.core.chat_engine import ChatEngine
from src.utils.logger import get_logger, setup_logging
from src.utils.helpers import validate_file_type, format_file_size
from .routes import router

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Zenith PDF Chatbot API",
    description="REST API for PDF processing and conversational AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins.split(",") if config.cors_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
pdf_processor: Optional[PDFProcessor] = None
vector_store: Optional[VectorStore] = None
chat_engine: Optional[ChatEngine] = None


@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup"""
    global pdf_processor, vector_store, chat_engine
    
    try:
        logger.info("Initializing Zenith PDF Chatbot API...")
        
        # Initialize components
        pdf_processor = PDFProcessor()
        vector_store = VectorStore()
        chat_engine = ChatEngine(vector_store)
        
        logger.info("API initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Zenith PDF Chatbot API...")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Zenith PDF Chatbot API",
        "version": "1.0.0",
        "description": "REST API for PDF processing and conversational AI",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check component health
        vector_health = vector_store.health_check() if vector_store else False
        chat_health = chat_engine.health_check() if chat_engine else False
        
        return {
            "status": "healthy" if vector_health and chat_health else "degraded",
            "components": {
                "pdf_processor": pdf_processor is not None,
                "vector_store": vector_health,
                "chat_engine": chat_health
            },
            "config": {
                "qdrant_url": config.qdrant_url,
                "qdrant_port": config.qdrant_port,
                "collection_name": config.qdrant_collection_name
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Include API routes
app.include_router(router, prefix="/api/v1")


def get_components():
    """Dependency to get initialized components"""
    if not all([pdf_processor, vector_store, chat_engine]):
        raise HTTPException(
            status_code=503,
            detail="API components not initialized"
        )
    
    return {
        "pdf_processor": pdf_processor,
        "vector_store": vector_store,
        "chat_engine": chat_engine
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug_mode,
        log_level=config.log_level.lower()
    )
