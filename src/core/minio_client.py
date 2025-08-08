"""
MinIO Client Module for Zenith PDF Chatbot
Handles MinIO server connections and object operations
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Tuple, Any
from datetime import datetime
import tempfile
import mimetypes

from minio import Minio
from minio.error import S3Error, InvalidResponseError
from urllib3.exceptions import MaxRetryError

from .config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MinIOClient:
    """
    MinIO client wrapper for PDF operations
    """
    
    def __init__(self, 
                 endpoint: Optional[str] = None,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 secure: Optional[bool] = None,
                 region: Optional[str] = None):
        """
        Initialize MinIO client
        
        Args:
            endpoint: MinIO server endpoint
            access_key: MinIO access key
            secret_key: MinIO secret key
            secure: Use HTTPS connection
            region: MinIO region
        """
        self.endpoint = endpoint or os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = access_key or os.getenv('MINIO_ACCESS_KEY', '')
        self.secret_key = secret_key or os.getenv('MINIO_SECRET_KEY', '')
        self.secure = secure if secure is not None else os.getenv('MINIO_SECURE', 'False').lower() == 'true'
        self.region = region or os.getenv('MINIO_REGION', 'us-east-1')
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize MinIO client connection"""
        try:
            self.client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
                region=self.region
            )
            logger.info(f"MinIO client initialized for endpoint: {self.endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None
            raise
    
    def test_connection(self) -> bool:
        """
        Test MinIO connection
        
        Returns:
            bool: True if connection successful
        """
        if not self.client:
            return False
        
        try:
            # Test connection by listing buckets
            list(self.client.list_buckets())
            logger.info("MinIO connection test successful")
            return True
        except Exception as e:
            logger.error(f"MinIO connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information
        
        Returns:
            Dict with connection details
        """
        return {
            'endpoint': self.endpoint,
            'secure': self.secure,
            'region': self.region,
            'access_key': self.access_key[:8] + '***' if self.access_key else None,
            'connected': self.test_connection()
        }
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """
        List all available buckets
        
        Returns:
            List of bucket information dictionaries
        """
        if not self.client:
            raise RuntimeError("MinIO client not initialized")
        
        try:
            buckets = []
            for bucket in self.client.list_buckets():
                buckets.append({
                    'name': bucket.name,
                    'creation_date': bucket.creation_date,
                    'creation_date_str': bucket.creation_date.strftime('%Y-%m-%d %H:%M:%S') if bucket.creation_date else 'Unknown'
                })
            
            logger.info(f"Found {len(buckets)} buckets")
            return buckets
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            raise
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if bucket exists
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            bool: True if bucket exists
        """
        if not self.client:
            return False
        
        try:
            return self.client.bucket_exists(bucket_name)
        except Exception as e:
            logger.error(f"Error checking bucket existence: {e}")
            return False
    
    def list_objects(self, 
                    bucket_name: str, 
                    prefix: str = '',
                    recursive: bool = True,
                    include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        List objects in a bucket
        
        Args:
            bucket_name: Name of the bucket
            prefix: Object name prefix filter
            recursive: List objects recursively
            include_metadata: Include object metadata
            
        Returns:
            List of object information dictionaries
        """
        if not self.client:
            raise RuntimeError("MinIO client not initialized")
        
        if not self.bucket_exists(bucket_name):
            raise ValueError(f"Bucket '{bucket_name}' does not exist")
        
        try:
            objects = []
            for obj in self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive):
                obj_info = {
                    'name': obj.object_name,
                    'size': obj.size,
                    'size_str': self._format_size(obj.size),
                    'last_modified': obj.last_modified,
                    'last_modified_str': obj.last_modified.strftime('%Y-%m-%d %H:%M:%S') if obj.last_modified else 'Unknown',
                    'etag': obj.etag,
                    'content_type': obj.content_type or self._guess_content_type(obj.object_name),
                    'is_pdf': obj.object_name.lower().endswith('.pdf')
                }
                
                # Add metadata if requested
                if include_metadata:
                    try:
                        stat = self.client.stat_object(bucket_name, obj.object_name)
                        obj_info['metadata'] = stat.metadata or {}
                    except Exception as e:
                        logger.warning(f"Could not get metadata for {obj.object_name}: {e}")
                        obj_info['metadata'] = {}
                
                objects.append(obj_info)
            
            logger.info(f"Found {len(objects)} objects in bucket '{bucket_name}'")
            return objects
        except Exception as e:
            logger.error(f"Error listing objects in bucket '{bucket_name}': {e}")
            raise
    
    def list_pdf_objects(self, bucket_name: str, prefix: str = '') -> List[Dict[str, Any]]:
        """
        List PDF objects in a bucket
        
        Args:
            bucket_name: Name of the bucket
            prefix: Object name prefix filter
            
        Returns:
            List of PDF object information dictionaries
        """
        all_objects = self.list_objects(bucket_name, prefix=prefix)
        pdf_objects = [obj for obj in all_objects if obj['is_pdf']]
        
        logger.info(f"Found {len(pdf_objects)} PDF objects in bucket '{bucket_name}'")
        return pdf_objects
    
    def download_object(self, 
                       bucket_name: str, 
                       object_name: str, 
                       local_path: Optional[Path] = None) -> Path:
        """
        Download object to local file
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            local_path: Local file path (optional, uses temp file if not provided)
            
        Returns:
            Path to downloaded file
        """
        if not self.client:
            raise RuntimeError("MinIO client not initialized")
        
        try:
            # Create local path if not provided
            if local_path is None:
                temp_dir = Path(config.temp_dir)
                temp_dir.mkdir(exist_ok=True)
                local_path = temp_dir / Path(object_name).name
            else:
                local_path = Path(local_path)
                local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download the object
            self.client.fget_object(bucket_name, object_name, str(local_path))
            
            logger.info(f"Downloaded {object_name} to {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading object {object_name}: {e}")
            raise
    
    def download_pdf_objects(self, 
                           bucket_name: str, 
                           object_names: List[str],
                           download_dir: Optional[Path] = None) -> List[Tuple[str, Path]]:
        """
        Download multiple PDF objects
        
        Args:
            bucket_name: Name of the bucket
            object_names: List of object names to download
            download_dir: Directory to download files to
            
        Returns:
            List of tuples (object_name, local_path)
        """
        if download_dir is None:
            download_dir = Path(config.temp_dir)
        
        download_dir = Path(download_dir)
        download_dir.mkdir(exist_ok=True)
        
        downloaded_files = []
        
        for object_name in object_names:
            try:
                local_path = self.download_object(
                    bucket_name, 
                    object_name, 
                    download_dir / Path(object_name).name
                )
                downloaded_files.append((object_name, local_path))
            except Exception as e:
                logger.error(f"Failed to download {object_name}: {e}")
        
        logger.info(f"Downloaded {len(downloaded_files)} out of {len(object_names)} PDF files")
        return downloaded_files
    
    def get_object_info(self, bucket_name: str, object_name: str) -> Dict[str, Any]:
        """
        Get detailed object information
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            
        Returns:
            Dictionary with object information
        """
        if not self.client:
            raise RuntimeError("MinIO client not initialized")
        
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            
            return {
                'name': object_name,
                'size': stat.size,
                'size_str': self._format_size(stat.size),
                'last_modified': stat.last_modified,
                'last_modified_str': stat.last_modified.strftime('%Y-%m-%d %H:%M:%S') if stat.last_modified else 'Unknown',
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata or {},
                'is_pdf': object_name.lower().endswith('.pdf')
            }
        except Exception as e:
            logger.error(f"Error getting object info for {object_name}: {e}")
            raise
    
    def upload_object(self, 
                     bucket_name: str, 
                     object_name: str, 
                     local_path: Path,
                     metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload local file to MinIO
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name for the object
            local_path: Path to local file
            metadata: Optional metadata dictionary
            
        Returns:
            bool: True if upload successful
        """
        if not self.client:
            raise RuntimeError("MinIO client not initialized")
        
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        try:
            # Determine content type
            content_type = self._guess_content_type(str(local_path))
            
            # Upload the file
            result = self.client.fput_object(
                bucket_name, 
                object_name, 
                str(local_path),
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"Uploaded {local_path} to {bucket_name}/{object_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading {local_path}: {e}")
            return False
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete object from bucket
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            
        Returns:
            bool: True if deletion successful
        """
        if not self.client:
            raise RuntimeError("MinIO client not initialized")
        
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Deleted object {bucket_name}/{object_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting object {object_name}: {e}")
            return False
    
    def get_bucket_stats(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket statistics
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            Dictionary with bucket statistics
        """
        try:
            objects = self.list_objects(bucket_name, include_metadata=False)
            pdf_objects = [obj for obj in objects if obj['is_pdf']]
            
            total_size = sum(obj['size'] for obj in objects)
            pdf_size = sum(obj['size'] for obj in pdf_objects)
            
            return {
                'total_objects': len(objects),
                'pdf_objects': len(pdf_objects),
                'total_size': total_size,
                'total_size_str': self._format_size(total_size),
                'pdf_size': pdf_size,
                'pdf_size_str': self._format_size(pdf_size),
                'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"Error getting bucket stats for {bucket_name}: {e}")
            return {
                'error': str(e),
                'total_objects': 0,
                'pdf_objects': 0,
                'total_size': 0,
                'total_size_str': '0 B',
                'pdf_size': 0,
                'pdf_size_str': '0 B',
                'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def cleanup_temp_files(self, temp_dir: Optional[Path] = None):
        """
        Clean up temporary downloaded files
        
        Args:
            temp_dir: Directory to clean (defaults to config temp_dir)
        """
        if temp_dir is None:
            temp_dir = Path(config.temp_dir)
        
        try:
            if temp_dir.exists():
                for file_path in temp_dir.glob("*.pdf"):
                    file_path.unlink()
                logger.info(f"Cleaned up temporary files in {temp_dir}")
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {e}")


# Convenience function for getting a configured MinIO client
def get_minio_client() -> MinIOClient:
    """
    Get a configured MinIO client instance
    
    Returns:
        MinIOClient: Configured client instance
    """
    return MinIOClient()
