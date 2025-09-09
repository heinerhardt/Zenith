"""
PDF Processing Module for Zenith PDF Chatbot
Handles PDF loading, text extraction, and document chunking
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Union
import tempfile
import shutil

from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import pdfplumber

from .config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFProcessor:
    """
    Handles PDF processing including loading, text extraction, and chunking
    """
    
    def __init__(self, 
                 chunk_size: Optional[int] = None,
                 chunk_overlap: Optional[int] = None):
        """
        Initialize PDF processor
        
        Args:
            chunk_size: Size of text chunks (default from config)
            chunk_overlap: Overlap between chunks (default from config)
        """
        self.chunk_size = chunk_size or config.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        logger.info(f"PDFProcessor initialized with chunk_size={self.chunk_size}, "
                   f"chunk_overlap={self.chunk_overlap}")
    
    def load_pdf(self, pdf_path: Union[str, Path]) -> List[Document]:
        """
        Load a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of Document objects
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF processing fails
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        try:
            logger.info(f"Loading PDF: {pdf_path}")
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata.update({
                    'source': str(pdf_path),
                    'filename': pdf_path.name,
                    'file_size': pdf_path.stat().st_size,
                    'processing_timestamp': str(pd.Timestamp.now())
                })
            
            logger.info(f"Successfully loaded {len(documents)} pages from {pdf_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {e}")
            raise
    
    def load_pdfs_from_directory(self, 
                                directory_path: Union[str, Path],
                                recursive: bool = True) -> List[Document]:
        """
        Load all PDF files from a directory
        
        Args:
            directory_path: Path to directory containing PDFs
            recursive: Whether to search subdirectories
            
        Returns:
            List of Document objects
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            Exception: If PDF processing fails
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        try:
            logger.info(f"Loading PDFs from directory: {directory_path}")
            
            # Set glob pattern based on recursive option
            glob_pattern = "**/*.pdf" if recursive else "*.pdf"
            
            loader = DirectoryLoader(
                str(directory_path),
                glob=glob_pattern,
                loader_cls=PyPDFLoader,
                show_progress=True,
                use_multithreading=True
            )
            
            documents = loader.load()
            
            # Add metadata to all documents
            for doc in documents:
                source_path = Path(doc.metadata.get('source', ''))
                doc.metadata.update({
                    'filename': source_path.name,
                    'file_size': source_path.stat().st_size if source_path.exists() else 0,
                    'processing_timestamp': str(pd.Timestamp.now()),
                    'directory': str(directory_path)
                })
            
            logger.info(f"Successfully loaded {len(documents)} pages from {directory_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading PDFs from directory {directory_path}: {e}")
            raise
    
    def extract_text_with_pdfplumber(self, pdf_path: Union[str, Path]) -> str:
        """
        Extract text using pdfplumber for better text extraction
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        pdf_path = Path(pdf_path)
        text_content = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {page_num + 1} ---\n{text}\n")
            
            full_text = "\n".join(text_content)
            logger.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunked Document objects
        """
        try:
            logger.info(f"Splitting {len(documents)} documents into chunks")
            chunks = self.text_splitter.split_documents(documents)
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'chunk_id': i,
                    'chunk_size': len(chunk.page_content),
                    'total_chunks': len(chunks)
                })
            
            logger.info(f"Successfully split documents into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting documents: {e}")
            raise
    
    def process_uploaded_files(self, uploaded_files: List) -> List[Document]:
        """
        Process uploaded files from Streamlit
        
        Args:
            uploaded_files: List of uploaded file objects
            
        Returns:
            List of processed Document objects
        """
        documents = []
        temp_dir = Path(config.temp_dir)
        temp_dir.mkdir(exist_ok=True)
        
        try:
            for uploaded_file in uploaded_files:
                # Save uploaded file temporarily
                temp_path = temp_dir / uploaded_file.name
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())
                
                # Process the PDF
                file_documents = self.load_pdf(temp_path)
                documents.extend(file_documents)
                
                # Clean up temporary file
                temp_path.unlink()
            
            logger.info(f"Processed {len(uploaded_files)} uploaded files")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing uploaded files: {e}")
            raise
        finally:
            # Clean up any remaining temporary files
            self._cleanup_temp_files()
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dir = Path(config.temp_dir)
            if temp_dir.exists():
                for file_path in temp_dir.glob("*.pdf"):
                    file_path.unlink()
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {e}")
    
    def validate_pdf(self, pdf_path: Union[str, Path]) -> bool:
        """
        Validate if a file is a readable PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if valid PDF, False otherwise
        """
        pdf_path = Path(pdf_path)
        
        try:
            # Check file extension
            if not pdf_path.suffix.lower() == '.pdf':
                return False
            
            # Check file size
            if pdf_path.stat().st_size > config.max_file_size_mb * 1024 * 1024:
                logger.warning(f"PDF file too large: {pdf_path}")
                return False
            
            # Try to load the PDF
            with pdfplumber.open(pdf_path) as pdf:
                # Try to read first page
                if len(pdf.pages) > 0:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text()
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"PDF validation failed for {pdf_path}: {e}")
            return False
    
    def get_pdf_info(self, pdf_path: Union[str, Path]) -> dict:
        """
        Get information about a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF information
        """
        pdf_path = Path(pdf_path)
        info = {
            'filename': pdf_path.name,
            'file_size': 0,
            'num_pages': 0,
            'text_length': 0,
            'is_valid': False
        }
        
        try:
            if pdf_path.exists():
                info['file_size'] = pdf_path.stat().st_size
                info['is_valid'] = self.validate_pdf(pdf_path)
                
                if info['is_valid']:
                    with pdfplumber.open(pdf_path) as pdf:
                        info['num_pages'] = len(pdf.pages)
                        
                        # Estimate text length from first few pages
                        sample_text = ""
                        for i, page in enumerate(pdf.pages[:3]):  # Sample first 3 pages
                            text = page.extract_text()
                            if text:
                                sample_text += text
                        
                        # Estimate total text length
                        avg_chars_per_page = len(sample_text) / min(3, info['num_pages'])
                        info['text_length'] = int(avg_chars_per_page * info['num_pages'])
            
        except Exception as e:
            logger.warning(f"Error getting PDF info for {pdf_path}: {e}")
        
        return info


# Import pandas for timestamp
import pandas as pd
