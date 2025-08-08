                      task: asyncio.Task,
                      callback: Optional[Callable] = None):
        """Handle job completion"""
        try:
            if task.exception():
                result = {'success': False, 'error': str(task.exception())}
                logger.error(f"Job {job_id} failed: {task.exception()}")
            else:
                result = task.result()
                logger.info(f"Job {job_id} completed successfully")
            
            self._job_results[job_id] = result
            
            # Call completion callback if provided
            if callback:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(job_id, result))
                    else:
                        callback(job_id, result)
                except Exception as e:
                    logger.warning(f"Error in job completion callback: {e}")
        
        except Exception as e:
            logger.error(f"Error handling job completion for {job_id}: {e}")
            self._job_results[job_id] = {'success': False, 'error': str(e)}
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if job was cancelled
        """
        async with self._lock:
            if job_id not in self.jobs:
                return False
            
            task = self.jobs[job_id]
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled job: {job_id}")
                return True
            
            return False
    
    async def wait_for_job(self, job_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for a job to complete
        
        Args:
            job_id: Job identifier
            timeout: Optional timeout in seconds
            
        Returns:
            Job result
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        task = self.jobs[job_id]
        
        try:
            if timeout:
                result = await asyncio.wait_for(task, timeout=timeout)
            else:
                result = await task
            
            return result
        
        except asyncio.TimeoutError:
            logger.warning(f"Job {job_id} timed out after {timeout} seconds")
            raise
        
        except asyncio.CancelledError:
            logger.info(f"Job {job_id} was cancelled")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[str]:
        """
        Get job status
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status string or None
        """
        if job_id not in self.jobs:
            return None
        
        task = self.jobs[job_id]
        
        if task.done():
            if task.cancelled():
                return 'cancelled'
            elif task.exception():
                return 'failed'
            else:
                return 'completed'
        else:
            return 'running'
    
    def get_job_result(self, job_id: str) -> Optional[Any]:
        """
        Get job result
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job result or None
        """
        return self._job_results.get(job_id)
    
    def list_jobs(self) -> Dict[str, str]:
        """
        List all jobs and their statuses
        
        Returns:
            Dict mapping job IDs to statuses
        """
        job_statuses = {}
        
        for job_id in self.jobs:
            job_statuses[job_id] = self.get_job_status(job_id)
        
        return job_statuses
    
    async def cleanup_completed_jobs(self):
        """Clean up completed job tasks"""
        async with self._lock:
            completed_jobs = []
            
            for job_id, task in self.jobs.items():
                if task.done():
                    completed_jobs.append(job_id)
            
            for job_id in completed_jobs:
                del self.jobs[job_id]
            
            if completed_jobs:
                logger.info(f"Cleaned up {len(completed_jobs)} completed jobs")


async def run_with_timeout(coro: Awaitable, timeout: float) -> Any:
    """
    Run coroutine with timeout
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        
    Returns:
        Coroutine result
        
    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    return await asyncio.wait_for(coro, timeout=timeout)


async def gather_with_concurrency(coroutines: List[Awaitable], 
                                 max_concurrent: int = 10) -> List[Any]:
    """
    Run coroutines with concurrency limit
    
    Args:
        coroutines: List of coroutines to run
        max_concurrent: Maximum concurrent coroutines
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro
    
    wrapped_coroutines = [run_with_semaphore(coro) for coro in coroutines]
    return await asyncio.gather(*wrapped_coroutines)


def run_async_in_thread(coro: Awaitable) -> Any:
    """
    Run async coroutine in a separate thread with its own event loop
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Coroutine result
    """
    def run_in_new_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop)
        return future.result()


class AsyncFileManager:
    """Async file operations manager"""
    
    @staticmethod
    async def read_file(file_path: Path) -> str:
        """Read file content asynchronously"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            return await f.read()
    
    @staticmethod
    async def write_file(file_path: Path, content: str) -> bool:
        """Write file content asynchronously"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    @staticmethod
    async def copy_file(src: Path, dest: Path) -> bool:
        """Copy file asynchronously"""
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(src, 'rb') as src_file:
                async with aiofiles.open(dest, 'wb') as dest_file:
                    while True:
                        chunk = await src_file.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        await dest_file.write(chunk)
            
            return True
        except Exception as e:
            logger.error(f"Error copying file {src} to {dest}: {e}")
            return False
    
    @staticmethod
    async def delete_file(file_path: Path) -> bool:
        """Delete file asynchronously"""
        try:
            await asyncio.get_event_loop().run_in_executor(None, file_path.unlink)
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False


# Export commonly used classes and functions
__all__ = [
    'AsyncProgressTracker',
    'AsyncBatchProcessor',
    'async_download_file',
    'async_process_pdf',
    'async_add_to_vector_store',
    'async_process_minio_pdf',
    'AsyncJobManager',
    'run_with_timeout',
    'gather_with_concurrency',
    'run_async_in_thread',
    'AsyncFileManager'
]
