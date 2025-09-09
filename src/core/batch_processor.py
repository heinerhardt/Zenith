"""
Batch PDF Processor for MinIO Integration
Handles batch processing of PDFs from MinIO buckets with progress tracking
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue
import time
import traceback

from langchain.schema import Document

from .config import config
from .minio_client import MinIOClient
from .pdf_processor import PDFProcessor
from .vector_store import VectorStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingJob:
    """Data class for processing job information"""
    job_id: str
    bucket_name: str
    object_names: List[str]
    total_objects: int
    processed_objects: int = 0
    failed_objects: int = 0
    status: str = 'pending'  # pending, running, completed, failed, cancelled
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_callback: Optional[Callable] = None
    results: Dict[str, Any] = field(default_factory=dict)


class BatchPDFProcessor:
    """
    Batch processor for PDF files from MinIO storage
    Handles job creation, execution, and monitoring
    """
    
    def __init__(self, 
                 minio_client: MinIOClient,
                 vector_store: Optional[VectorStore] = None,
                 max_workers: int = 3,
                 batch_size: int = 10):
        """
        Initialize batch processor
        
        Args:
            minio_client: MinIO client instance
            vector_store: Vector store instance (optional)
            max_workers: Maximum number of worker threads
            batch_size: Number of PDFs to process in each batch
        """
        self.minio_client = minio_client
        self.vector_store = vector_store or VectorStore()
        self.pdf_processor = PDFProcessor()
        self.max_workers = max_workers
        self.batch_size = batch_size
        
        # Job management
        self.jobs: Dict[str, ProcessingJob] = {}
        self.is_processing = False
        self.current_job_id: Optional[str] = None
        
        # Threading
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_processing = False
        
        logger.info(f"BatchPDFProcessor initialized with {max_workers} workers, batch size {batch_size}")
    
    def create_job(self, 
                   bucket_name: str, 
                   object_names: Optional[List[str]] = None,
                   filter_pattern: Optional[str] = None,
                   progress_callback: Optional[Callable] = None) -> str:
        """
        Create a new processing job
        
        Args:
            bucket_name: MinIO bucket name
            object_names: Specific object names to process (optional)
            filter_pattern: Pattern to filter objects (e.g., "*.pdf")
            progress_callback: Callback function for progress updates
            
        Returns:
            str: Job ID
        """
        try:
            job_id = str(uuid.uuid4())[:8]
            
            # Get object names if not provided
            if object_names is None:
                # List all PDF objects in bucket
                objects = self.minio_client.list_objects(bucket_name, prefix="", suffix=".pdf")
                object_names = [obj['name'] for obj in objects]
                
                # Apply filter pattern if provided
                if filter_pattern:
                    import fnmatch
                    object_names = [name for name in object_names if fnmatch.fnmatch(name, filter_pattern)]
            
            # Create job
            job = ProcessingJob(
                job_id=job_id,
                bucket_name=bucket_name,
                object_names=object_names,
                total_objects=len(object_names),
                processed_objects=0,
                failed_objects=0,
                status='pending',
                progress_callback=progress_callback
            )
            
            self.jobs[job_id] = job
            logger.info(f"Created job {job_id} with {len(object_names)} PDFs from bucket '{bucket_name}'")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            raise
    
    def start_job(self, job_id: str) -> bool:
        """
        Start processing a job
        
        Args:
            job_id: Job ID to start
            
        Returns:
            bool: True if job started successfully
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        
        if self.is_processing:
            logger.warning(f"Another job is already running. Cannot start job {job_id}")
            return False
        
        if job.status != 'pending':
            logger.warning(f"Job {job_id} is not in pending state (current: {job.status})")
            return False
        
        try:
            # Update job status
            job.status = 'running'
            job.start_time = datetime.now()
            self.is_processing = True
            self.current_job_id = job_id
            
            # Start processing in background thread
            self._processing_thread = threading.Thread(
                target=self._process_job_worker,
                args=(job,),
                daemon=True
            )
            self._processing_thread.start()
            
            logger.info(f"Started job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting job {job_id}: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            self.is_processing = False
            self.current_job_id = None
            return False
    
    def _process_job_worker(self, job: ProcessingJob):
        """
        Worker method to process a job
        
        Args:
            job: ProcessingJob instance
        """
        try:
            logger.info(f"Processing job {job.job_id} with {job.total_objects} PDFs")
            
            # Process PDFs in batches
            for i in range(0, len(job.object_names), self.batch_size):
                if self._stop_processing:
                    logger.info(f"Job {job.job_id} cancelled")
                    job.status = 'cancelled'
                    break
                
                batch = job.object_names[i:i + self.batch_size]
                self._process_batch(job, batch)
            
            # Update final status
            if job.status != 'cancelled':
                if job.failed_objects == 0:
                    job.status = 'completed'
                    logger.info(f"Job {job.job_id} completed successfully")
                else:
                    job.status = 'completed'  # Partially completed
                    logger.warning(f"Job {job.job_id} completed with {job.failed_objects} failures")
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)
        
        finally:
            job.end_time = datetime.now()
            self.is_processing = False
            self.current_job_id = None
            
            # Cleanup temp files
            self._cleanup_temp_files()
    
    def _process_batch(self, job: ProcessingJob, batch: List[str]):
        """
        Process a batch of PDF files
        
        Args:
            job: ProcessingJob instance
            batch: List of object names to process
        """
        futures = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(batch), self.max_workers)) as executor:
            for object_name in batch:
                if self._stop_processing:
                    break
                
                future = executor.submit(self._process_single_pdf, job, object_name)
                futures.append(future)
            
            # Wait for all futures to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in batch processing: {e}")
    
    def _process_single_pdf(self, job: ProcessingJob, object_name: str):
        """
        Process a single PDF file
        
        Args:
            job: ProcessingJob instance
            object_name: MinIO object name
        """
        try:
            logger.debug(f"Processing {object_name} from job {job.job_id}")
            
            # Download PDF to temp file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Download from MinIO
                self.minio_client.download_object(job.bucket_name, object_name, temp_path)
                
                # Process PDF
                chunks = self.pdf_processor.process_pdf(temp_path)
                
                # Store in vector store
                if chunks and self.vector_store:
                    metadata = {
                        'source': f"minio://{job.bucket_name}/{object_name}",
                        'bucket': job.bucket_name,
                        'object_name': object_name,
                        'job_id': job.job_id,
                        'processed_at': datetime.now().isoformat()
                    }
                    
                    self.vector_store.add_documents(chunks, metadata=metadata)
                
                # Update job progress
                job.processed_objects += 1
                
                # Call progress callback if provided
                if job.progress_callback:
                    try:
                        job.progress_callback(job.processed_objects, job.total_objects)
                    except Exception as cb_error:
                        logger.warning(f"Progress callback error: {cb_error}")
                
                logger.debug(f"Successfully processed {object_name}")
                
        except Exception as e:
            logger.error(f"Error processing {object_name}: {e}")
            job.failed_objects += 1
            
            if object_name not in job.results:
                job.results[object_name] = {}
            job.results[object_name]['error'] = str(e)
        
        finally:
            # Clean up temp file
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up temp file: {cleanup_error}")
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            bool: True if job cancelled successfully
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        
        if job.status != 'running':
            logger.warning(f"Job {job_id} is not running (current: {job.status})")
            return False
        
        try:
            self._stop_processing = True
            job.status = 'cancelled'
            logger.info(f"Cancelled job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status and progress
        
        Args:
            job_id: Job ID
            
        Returns:
            Dict with job information
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        
        progress_percent = 0
        if job.total_objects > 0:
            progress_percent = round((job.processed_objects / job.total_objects) * 100, 2)
        
        return {
            'job_id': job.job_id,
            'bucket_name': job.bucket_name,
            'status': job.status,
            'total_objects': job.total_objects,
            'processed_objects': job.processed_objects,
            'failed_objects': job.failed_objects,
            'progress_percent': progress_percent,
            'start_time': job.start_time,
            'end_time': job.end_time,
            'error_message': job.error_message
        }
    
    def get_all_jobs(self) -> Dict[str, ProcessingJob]:
        """
        Get all jobs
        
        Returns:
            Dict of job_id -> ProcessingJob
        """
        return self.jobs.copy()
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from memory
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            bool: True if job deleted successfully
        """
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        # Don't delete running jobs
        if job.status == 'running':
            logger.warning(f"Cannot delete running job {job_id}")
            return False
        
        del self.jobs[job_id]
        logger.info(f"Deleted job {job_id}")
        return True
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics
        
        Returns:
            Dict with processing stats
        """
        total_jobs = len(self.jobs)
        completed_jobs = len([j for j in self.jobs.values() if j.status == 'completed'])
        failed_jobs = len([j for j in self.jobs.values() if j.status == 'failed'])
        running_jobs = len([j for j in self.jobs.values() if j.status == 'running'])
        
        total_processed = sum(j.processed_objects for j in self.jobs.values())
        total_failed = sum(j.failed_objects for j in self.jobs.values())
        
        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'total_processed_objects': total_processed,
            'total_failed_objects': total_failed,
            'is_currently_processing': self.is_processing,
            'current_job_id': self.current_job_id
        }
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dir = tempfile.gettempdir()
            for file in os.listdir(temp_dir):
                if file.startswith('tmp') and file.endswith('.pdf'):
                    try:
                        os.unlink(os.path.join(temp_dir, file))
                    except:
                        pass
        except Exception as e:
            logger.warning(f"Error cleaning temp files: {e}")
    
    def shutdown(self):
        """
        Shutdown the batch processor
        """
        try:
            # Stop any running processing
            self._stop_processing = True
            
            # Wait for processing thread to finish
            if self._processing_thread and self._processing_thread.is_alive():
                self._processing_thread.join(timeout=30)
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            # Cleanup temp files
            self._cleanup_temp_files()
            
            logger.info("BatchPDFProcessor shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")