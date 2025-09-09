"""
Helper utilities for Zenith PDF Chatbot
Common utility functions used across the application
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import tempfile
import mimetypes
import time

from src.core.config import config
from .logger import get_logger

logger = get_logger(__name__)


def ensure_directory_exists(directory_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Path object of the directory
    """
    directory_path = Path(directory_path)
    directory_path.mkdir(parents=True, exist_ok=True)
    return directory_path


def clean_temp_directory():
    """Clean up temporary files"""
    try:
        temp_dir = Path(config.temp_dir)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            temp_dir.mkdir(exist_ok=True)
            logger.info("Cleaned temporary directory")
    except Exception as e:
        logger.error(f"Error cleaning temp directory: {e}")


def get_file_hash(file_path: Union[str, Path]) -> str:
    """
    Get MD5 hash of a file
    
    Args:
        file_path: Path to file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return ""


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_file_type(file_path: Union[str, Path], allowed_extensions: List[str] = None) -> bool:
    """
    Validate file type based on extension
    
    Args:
        file_path: Path to file
        allowed_extensions: List of allowed extensions (default: .pdf)
        
    Returns:
        True if file type is valid
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf']
    
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    return extension in [ext.lower() for ext in allowed_extensions]


def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name


def create_temp_file(content: bytes, suffix: str = ".pdf") -> Path:
    """
    Create a temporary file with content
    
    Args:
        content: File content as bytes
        suffix: File suffix
        
    Returns:
        Path to temporary file
    """
    temp_dir = ensure_directory_exists(config.temp_dir)
    
    with tempfile.NamedTemporaryFile(
        delete=False, 
        suffix=suffix, 
        dir=temp_dir
    ) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)
    
    return temp_path


def batch_process(items: List[Any], batch_size: int = None) -> List[List[Any]]:
    """
    Split items into batches
    
    Args:
        items: List of items to batch
        batch_size: Size of each batch (default from config)
        
    Returns:
        List of batches
    """
    batch_size = batch_size or config.batch_size
    batches = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batches.append(batch)
    
    return batches


def retry_operation(func, max_retries: int = 3, delay: float = 1.0):
    """
    Retry an operation with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay in seconds
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (2 ** attempt)
                logger.warning(f"Operation failed (attempt {attempt + 1}), "
                             f"retrying in {wait_time:.1f}s: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"Operation failed after {max_retries + 1} attempts")
    
    raise last_exception


def estimate_processing_time(file_size_mb: float, pages: int = None) -> float:
    """
    Estimate processing time for a PDF
    
    Args:
        file_size_mb: File size in MB
        pages: Number of pages (optional)
        
    Returns:
        Estimated processing time in seconds
    """
    # Base time estimates
    base_time_per_mb = 2.0  # seconds per MB
    base_time_per_page = 0.5  # seconds per page
    
    # Calculate estimates
    size_time = file_size_mb * base_time_per_mb
    page_time = pages * base_time_per_page if pages else 0
    
    # Use the higher estimate
    estimated_time = max(size_time, page_time, 5.0)  # Minimum 5 seconds
    
    return estimated_time


def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging
    
    Returns:
        Dictionary with system information
    """
    import platform
    import psutil
    
    try:
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_free_gb": round(psutil.disk_usage('.').free / (1024**3), 2)
        }
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {"error": str(e)}


def sanitize_text(text: str, max_length: int = None) -> str:
    """
    Sanitize text for safe processing
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (optional)
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())
    
    # Truncate if necessary
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized


def chunk_text_by_tokens(text: str, max_tokens: int = 1000, overlap_tokens: int = 100) -> List[str]:
    """
    Chunk text by approximate token count
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Rough approximation: 1 token ≈ 4 characters
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap_tokens * chars_per_token
    
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at sentence or word boundary
        chunk_text = text[start:end]
        
        # Look for sentence boundary
        last_period = chunk_text.rfind('. ')
        last_newline = chunk_text.rfind('\n')
        
        if last_period > len(chunk_text) * 0.7:  # If period is in last 30%
            end = start + last_period + 2
        elif last_newline > len(chunk_text) * 0.7:
            end = start + last_newline + 1
        else:
            # Break at word boundary
            last_space = chunk_text.rfind(' ')
            if last_space > len(chunk_text) * 0.5:
                end = start + last_space
        
        chunks.append(text[start:end])
        start = max(start + 1, end - overlap_chars)
    
    return chunks


def merge_metadata(metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple metadata dictionaries
    
    Args:
        metadata_list: List of metadata dictionaries
        
    Returns:
        Merged metadata dictionary
    """
    merged = {}
    
    for metadata in metadata_list:
        for key, value in metadata.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, list):
                if isinstance(merged[key], list):
                    merged[key].extend(value)
                else:
                    merged[key] = [merged[key]] + value
            elif key == 'source':
                # Handle multiple sources
                if isinstance(merged[key], list):
                    merged[key].append(value)
                else:
                    merged[key] = [merged[key], value]
    
    return merged


def validate_config() -> List[str]:
    """
    Validate configuration settings
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required API keys
    if not config.openai_api_key or config.openai_api_key == "your_openai_api_key_here":
        errors.append("OpenAI API key is required")
    
    # Check numeric values
    if config.chunk_size <= 0:
        errors.append("Chunk size must be positive")
    
    if config.chunk_overlap < 0:
        errors.append("Chunk overlap cannot be negative")
    
    if config.chunk_overlap >= config.chunk_size:
        errors.append("Chunk overlap must be less than chunk size")
    
    # Check memory limits
    if config.memory_limit_gb <= 0:
        errors.append("Memory limit must be positive")
    
    # Check file size limits
    if config.max_file_size_mb <= 0:
        errors.append("Max file size must be positive")
    
    return errors


def create_progress_callback(total_items: int, description: str = "Processing"):
    """
    Create a progress callback function
    
    Args:
        total_items: Total number of items to process
        description: Description for progress
        
    Returns:
        Progress callback function
    """
    def progress_callback(current_item: int):
        percentage = (current_item / total_items) * 100
        logger.info(f"{description}: {current_item}/{total_items} ({percentage:.1f}%)")
    
    return progress_callback
