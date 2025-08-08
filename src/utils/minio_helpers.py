"""
MinIO helper utilities for Zenith PDF Chatbot
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional
import uuid

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

class MinIOClient:
    """MinIO client for document processing"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        """Initialize MinIO client"""
        if not MINIO_AVAILABLE:
            raise ImportError("MinIO not available. Install with: pip install minio>=7.2.0")
        
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
    
    def list_buckets(self) -> List[str]:
        """List all available buckets"""
        try:
            buckets = self.client.list_buckets()
            return [bucket.name for bucket in buckets]
        except S3Error as e:
            raise Exception(f"Failed to list buckets: {e}")
    
    def list_pdf_files(self, bucket_name: str, prefix: str = "") -> List[str]:
        """List all PDF files in a bucket"""
        try:
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            pdf_files = []
            for obj in objects:
                if obj.object_name.lower().endswith('.pdf'):
                    pdf_files.append(obj.object_name)
            
            return sorted(pdf_files)
        
        except S3Error as e:
            raise Exception(f"Failed to list objects in bucket {bucket_name}: {e}")
    
    def download_file(self, bucket_name: str, object_name: str) -> Path:
        """Download a file from MinIO to temporary location"""
        try:
            # Create temporary file
            temp_dir = Path(tempfile.gettempdir()) / "zenith_minio"
            temp_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            file_extension = Path(object_name).suffix
            temp_filename = f"{uuid.uuid4()}{file_extension}"
            temp_path = temp_dir / temp_filename
            
            # Download file
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=str(temp_path)
            )
            
            return temp_path
        
        except S3Error as e:
            raise Exception(f"Failed to download {object_name} from {bucket_name}: {e}")
    
    def upload_file(self, bucket_name: str, object_name: str, file_path: Path) -> bool:
        """Upload a file to MinIO"""
        try:
            self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=str(file_path)
            )
            return True
        
        except S3Error as e:
            raise Exception(f"Failed to upload {file_path} to {bucket_name}/{object_name}: {e}")
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """Check if a file exists in MinIO"""
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_info(self, bucket_name: str, object_name: str) -> dict:
        """Get file information"""
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type
            }
        except S3Error as e:
            raise Exception(f"Failed to get file info for {object_name}: {e}")

def test_minio_connection(endpoint: str, access_key: str, secret_key: str, secure: bool = False) -> tuple[bool, str]:
    """Test MinIO connection"""
    try:
        client = MinIOClient(endpoint, access_key, secret_key, secure)
        buckets = client.list_buckets()
        return True, f"Connection successful! Found {len(buckets)} buckets."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
