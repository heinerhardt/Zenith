"""
Batch Processor UI Component for Streamlit
Provides interface for managing PDF processing jobs
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.core.minio_client import MinIOClient
from src.core.batch_processor import BatchPDFProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BatchProcessorUI:
    """Batch processor UI component"""
    
    def __init__(self):
        """Initialize batch processor UI"""
        self._processor = None
    
    def get_batch_processor(self) -> Optional[BatchPDFProcessor]:
        """
        Get or create batch processor instance
        
        Returns:
            BatchPDFProcessor instance or None
        """
        client = st.session_state.get('minio_client')
        if not client:
            return None
        
        if self._processor is None:
            try:
                self._processor = BatchPDFProcessor(client)
            except Exception as e:
                logger.error(f"Error creating batch processor: {e}")
                return None
        
        return self._processor
    
    def render_job_creator(self, client: MinIOClient) -> Optional[str]:
        """
        Render job creation interface
        
        Args:
            client: MinIO client instance
            
        Returns:
            Created job ID or None
        """
        st.subheader("📝 Create Processing Job")
        
        processor = self.get_batch_processor()
        if not processor:
            st.error("❌ Failed to initialize batch processor")
            return None
        
        # Job configuration form
        with st.form("create_job_form"):
            # Bucket selection
            try:
                buckets = client.list_buckets()
                if not buckets:
                    st.error("No buckets available")
                    return None
                
                bucket_names = [bucket['name'] for bucket in buckets]
                selected_bucket = st.selectbox(
                    "Select Bucket",
                    options=bucket_names,
                    help="Choose a bucket to process PDFs from"
                )
            except Exception as e:
                st.error(f"Error loading buckets: {str(e)}")
                return None
            
            # Processing options
            col1, col2 = st.columns(2)
            
            with col1:
                process_all = st.radio(
                    "Processing Scope",
                    options=["All PDFs in bucket", "Filtered PDFs"],
                    help="Choose whether to process all PDFs or apply filters"
                )
                
                if process_all == "Filtered PDFs":
                    prefix_filter = st.text_input(
                        "Path Prefix Filter",
                        placeholder="e.g., documents/",
                        help="Only process PDFs with this path prefix"
                    )
                    
                    pattern_filter = st.text_input(
                        "Name Pattern Filter",
                        placeholder="e.g., *.pdf or report_*.pdf",
                        help="Only process PDFs matching this pattern"
                    )
                else:
                    prefix_filter = ""
                    pattern_filter = ""
            
            with col2:
                batch_size = st.number_input(
                    "Batch Size",
                    min_value=1,
                    max_value=50,
                    value=10,
                    help="Number of PDFs to process in each batch"
                )
                
                max_workers = st.number_input(
                    "Max Workers",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Maximum number of concurrent workers"
                )
            
            # Job description
            job_description = st.text_area(
                "Job Description (Optional)",
                placeholder="Describe this processing job...",
                help="Optional description for this job"
            )
            
            # Create job button
            create_job = st.form_submit_button(
                "🚀 Create Job",
                type="primary",
                use_container_width=True
            )
            
            if create_job:
                try:
                    # Update processor settings
                    processor.batch_size = batch_size
                    processor.max_workers = max_workers
                    
                    # Create job with filters
                    filter_pattern = pattern_filter if pattern_filter else None
                    
                    job_id = processor.create_job(
                        bucket_name=selected_bucket,
                        filter_pattern=filter_pattern,
                        progress_callback=self._job_progress_callback
                    )
                    
                    if job_id:
                        # Store job description if provided
                        if job_description:
                            st.session_state[f'job_desc_{job_id}'] = job_description
                        
                        logger.info(f"Created job {job_id}")
                        return job_id
                    
                except Exception as e:
                    st.error(f"Error creating job: {str(e)}")
                    logger.error(f"Error creating job: {e}")
                    return None
        
        return None
    
    def render_job_monitor(self) -> Optional[str]:
        """
        Render job monitoring interface
        
        Returns:
            Selected job ID or None
        """
        st.subheader("📊 Job Monitor")
        
        processor = self.get_batch_processor()
        if not processor:
            st.error("❌ Batch processor not available")
            return None
        
        # Get all jobs
        jobs = processor.get_all_jobs()
        
        if not jobs:
            st.info("No processing jobs created yet")
            return None
        
        # Job selection
        job_options = []
        for job_id, job in jobs.items():
            status_icon = self._get_status_icon(job.status)
            job_display = f"{job_id} {status_icon} - {job.bucket_name} ({job.total_objects} PDFs)"
            job_options.append((job_display, job_id))
        
        if job_options:
            selected_display, selected_job_id = st.selectbox(
                "Select Job",
                options=job_options,
                format_func=lambda x: x[0] if isinstance(x, tuple) else x,
                help="Choose a job to monitor"
            )
            
            # Job control buttons
            col1, col2, col3, col4 = st.columns(4)
            
            job = jobs[selected_job_id]
            
            with col1:
                if job.status == 'pending':
                    if st.button("▶️ Start Job", use_container_width=True, type="primary"):
                        if processor.start_job(selected_job_id):
                            st.success("Job started!")
                            st.rerun()
                        else:
                            st.error("Failed to start job")
                elif job.status == 'running':
                    if st.button("⏹️ Cancel Job", use_container_width=True):
                        if processor.cancel_job(selected_job_id):
                            st.success("Job cancelled!")
                            st.rerun()
                        else:
                            st.error("Failed to cancel job")
            
            with col2:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            
            with col3:
                if job.status in ['completed', 'failed', 'cancelled']:
                    if st.button("🗑️ Delete Job", use_container_width=True):
                        if processor.delete_job(selected_job_id):
                            st.success("Job deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete job")
            
            with col4:
                # Export job results button (placeholder)
                st.button("📊 Export Results", use_container_width=True, disabled=True)
            
            return selected_job_id
        
        return None
    
    def render_job_details(self, job_id: str):
        """
        Render detailed job information
        
        Args:
            job_id: Job ID to display details for
        """
        processor = self.get_batch_processor()
        if not processor:
            return
        
        try:
            job_status = processor.get_job_status(job_id)
            jobs = processor.get_all_jobs()
            job = jobs.get(job_id)
            
            if not job:
                st.error(f"Job {job_id} not found")
                return
            
            st.subheader(f"📋 Job Details: {job_id}")
            
            # Job description if available
            job_desc = st.session_state.get(f'job_desc_{job_id}')
            if job_desc:
                st.write(f"**Description:** {job_desc}")
                st.divider()
            
            # Status and progress
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_color = {
                    'pending': 'orange',
                    'running': 'blue',
                    'completed': 'green',
                    'failed': 'red',
                    'cancelled': 'gray'
                }.get(job.status, 'gray')
                
                st.markdown(f"**Status:** :{status_color}[{job.status.title()}]")
            
            with col2:
                st.metric("Progress", f"{job.processed_objects}/{job.total_objects}")
            
            with col3:
                if job.total_objects > 0:
                    progress_percent = (job.processed_objects / job.total_objects) * 100
                    st.metric("Completion", f"{progress_percent:.1f}%")
            
            # Progress bar
            if job.total_objects > 0:
                progress = job.processed_objects / job.total_objects
                st.progress(progress)
            
            # Time information
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Bucket:**", job.bucket_name)
            
            with col2:
                if job.start_time:
                    st.write(f"**Started:** {job.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col3:
                if job.end_time:
                    st.write(f"**Ended:** {job.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Calculate duration
                    if job.start_time:
                        duration = job.end_time - job.start_time
                        st.write(f"**Duration:** {str(duration).split('.')[0]}")
            
            # Error information
            if job.error_message:
                st.error(f"**Error:** {job.error_message}")
            
            # Processing statistics
            if job.processed_objects > 0 or job.failed_objects > 0:
                st.divider()
                st.subheader("📈 Processing Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Objects", job.total_objects)
                
                with col2:
                    st.metric("Processed", job.processed_objects, 
                             delta=None if job.failed_objects == 0 else f"+{job.processed_objects}")
                
                with col3:
                    st.metric("Failed", job.failed_objects,
                             delta=None if job.failed_objects == 0 else f"{job.failed_objects}")
                
                with col4:
                    success_rate = 0
                    if job.processed_objects + job.failed_objects > 0:
                        success_rate = (job.processed_objects / (job.processed_objects + job.failed_objects)) * 100
                    st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Object results (if available)
            if hasattr(job, 'results') and job.results:
                st.divider()
                st.subheader("📄 Object Results")
                
                # Show failed objects
                failed_objects = {k: v for k, v in job.results.items() if 'error' in v}
                if failed_objects:
                    with st.expander(f"❌ Failed Objects ({len(failed_objects)})", expanded=False):
                        for obj_name, result in failed_objects.items():
                            st.write(f"**{obj_name}:** {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"Error loading job details: {str(e)}")
            logger.error(f"Error in job details: {e}")
    
    def render_batch_operations(self):
        """Render batch operations interface"""
        st.subheader("🔧 Batch Operations")
        
        processor = self.get_batch_processor()
        if not processor:
            st.error("❌ Batch processor not available")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⏹️ Cancel All Jobs", use_container_width=True):
                try:
                    jobs = processor.get_all_jobs()
                    cancelled_count = 0
                    
                    for job_id, job in jobs.items():
                        if job.status == 'running':
                            if processor.cancel_job(job_id):
                                cancelled_count += 1
                    
                    if cancelled_count > 0:
                        st.success(f"Cancelled {cancelled_count} running jobs")
                    else:
                        st.info("No running jobs to cancel")
                        
                except Exception as e:
                    st.error(f"Error cancelling jobs: {str(e)}")
        
        with col2:
            if st.button("🗑️ Clear Completed", use_container_width=True):
                try:
                    jobs = processor.get_all_jobs()
                    deleted_count = 0
                    
                    for job_id, job in jobs.items():
                        if job.status in ['completed', 'failed', 'cancelled']:
                            if processor.delete_job(job_id):
                                deleted_count += 1
                    
                    if deleted_count > 0:
                        st.success(f"Deleted {deleted_count} completed jobs")
                        st.rerun()
                    else:
                        st.info("No completed jobs to delete")
                        
                except Exception as e:
                    st.error(f"Error deleting jobs: {str(e)}")
        
        with col3:
            if st.button("📊 Processing Stats", use_container_width=True):
                try:
                    stats = processor.get_processing_stats()
                    
                    st.json({
                        "Total Jobs": stats['total_jobs'],
                        "Completed Jobs": stats['completed_jobs'],
                        "Failed Jobs": stats['failed_jobs'],
                        "Running Jobs": stats['running_jobs'],
                        "Total Processed Objects": stats['total_processed_objects'],
                        "Total Failed Objects": stats['total_failed_objects'],
                        "Currently Processing": stats['is_currently_processing'],
                        "Current Job": stats.get('current_job_id', 'None')
                    })
                    
                except Exception as e:
                    st.error(f"Error getting stats: {str(e)}")
    
    def _get_status_icon(self, status: str) -> str:
        """
        Get status icon for job status
        
        Args:
            status: Job status
            
        Returns:
            Status icon
        """
        icons = {
            'pending': '🟡',
            'running': '🔵',
            'completed': '🟢',
            'failed': '🔴',
            'cancelled': '🟠'
        }
        return icons.get(status, '⚪')
    
    def _job_progress_callback(self, processed: int, total: int):
        """
        Progress callback for job processing
        
        Args:
            processed: Number of processed objects
            total: Total number of objects
        """
        # This could be used to update progress in real-time
        # For now, it's just a placeholder
        logger.debug(f"Job progress: {processed}/{total}")
        pass