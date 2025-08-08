        else:
            pattern_lower = pattern
        
        if fnmatch.fnmatch(obj_name, pattern_lower if not case_sensitive else pattern):
            filtered.append(obj)
    
    return filtered


def filter_objects_by_size(objects: List[Dict[str, Any]], 
                          min_size_bytes: int = 0, 
                          max_size_bytes: int = None) -> List[Dict[str, Any]]:
    """
    Filter objects by size range
    
    Args:
        objects: List of object dictionaries
        min_size_bytes: Minimum size in bytes
        max_size_bytes: Maximum size in bytes (None for no limit)
        
    Returns:
        List of objects within size range
    """
    filtered = []
    
    for obj in objects:
        size = obj.get('size', 0)
        
        if size < min_size_bytes:
            continue
        
        if max_size_bytes is not None and size > max_size_bytes:
            continue
        
        filtered.append(obj)
    
    return filtered


def filter_objects_by_date(objects: List[Dict[str, Any]], 
                          min_age_days: int = 0, 
                          max_age_days: int = None) -> List[Dict[str, Any]]:
    """
    Filter objects by modification date
    
    Args:
        objects: List of object dictionaries
        min_age_days: Minimum age in days
        max_age_days: Maximum age in days (None for no limit)
        
    Returns:
        List of objects within age range
    """
    filtered = []
    current_time = datetime.now()
    
    for obj in objects:
        last_modified = obj.get('last_modified')
        
        if not last_modified:
            continue  # Skip objects without modification date
        
        # Calculate age in days
        if last_modified.tzinfo:
            current_time = current_time.replace(tzinfo=last_modified.tzinfo)
        
        age_days = (current_time - last_modified).days
        
        if age_days < min_age_days:
            continue
        
        if max_age_days is not None and age_days > max_age_days:
            continue
        
        filtered.append(obj)
    
    return filtered


def group_objects_by_path(objects: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group objects by their parent path
    
    Args:
        objects: List of object dictionaries
        
    Returns:
        Dict mapping parent paths to lists of objects
    """
    groups = {}
    
    for obj in objects:
        path_info = parse_object_path(obj['name'])
        parent = path_info['parent'] or 'root'
        
        if parent not in groups:
            groups[parent] = []
        
        groups[parent].append(obj)
    
    return groups


def calculate_processing_estimate(objects: List[Dict[str, Any]], 
                                avg_processing_time_per_mb: float = 2.0) -> Dict[str, Any]:
    """
    Calculate processing time and resource estimates
    
    Args:
        objects: List of objects to process
        avg_processing_time_per_mb: Average processing time per MB in seconds
        
    Returns:
        Dict with processing estimates
    """
    if not objects:
        return {
            'total_objects': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'estimated_time_seconds': 0,
            'estimated_time_minutes': 0,
            'estimated_time_human': '0 minutes'
        }
    
    total_size_bytes = sum(obj.get('size', 0) for obj in objects)
    total_size_mb = total_size_bytes / (1024 * 1024)
    
    # Base time estimate
    estimated_seconds = total_size_mb * avg_processing_time_per_mb
    
    # Add overhead for each file (startup, cleanup, etc.)
    file_overhead_seconds = len(objects) * 5  # 5 seconds per file overhead
    estimated_seconds += file_overhead_seconds
    
    # Add network overhead (download time estimate)
    network_overhead_seconds = total_size_mb * 0.5  # Assume 2MB/s download speed
    estimated_seconds += network_overhead_seconds
    
    estimated_minutes = estimated_seconds / 60
    
    # Human readable time
    if estimated_minutes < 1:
        time_human = f"{int(estimated_seconds)} seconds"
    elif estimated_minutes < 60:
        time_human = f"{int(estimated_minutes)} minutes"
    else:
        hours = int(estimated_minutes // 60)
        minutes = int(estimated_minutes % 60)
        time_human = f"{hours}h {minutes}m"
    
    return {
        'total_objects': len(objects),
        'total_size_bytes': total_size_bytes,
        'total_size_mb': round(total_size_mb, 2),
        'estimated_time_seconds': round(estimated_seconds, 1),
        'estimated_time_minutes': round(estimated_minutes, 1),
        'estimated_time_human': time_human
    }


def format_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} EB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def create_temp_directory(prefix: str = "minio_") -> Path:
    """
    Create a temporary directory for MinIO operations
    
    Args:
        prefix: Directory name prefix
        
    Returns:
        Path to created temporary directory
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    logger.info(f"Created temporary directory: {temp_dir}")
    return temp_dir


def cleanup_temp_directory(temp_dir: Path, force: bool = False) -> bool:
    """
    Clean up temporary directory
    
    Args:
        temp_dir: Path to temporary directory
        force: Force deletion even if directory contains files
        
    Returns:
        bool: True if cleanup successful
    """
    try:
        if temp_dir.exists():
            if force:
                shutil.rmtree(temp_dir)
            else:
                temp_dir.rmdir()  # Only removes if empty
            
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
            return True
    except Exception as e:
        logger.warning(f"Error cleaning up temporary directory {temp_dir}: {e}")
        return False
    
    return True


def validate_pdf_file(file_path: Path) -> Dict[str, Any]:
    """
    Validate a PDF file
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Dict with validation results
    """
    result = {
        'is_valid': False,
        'file_exists': False,
        'is_pdf': False,
        'is_readable': False,
        'size_bytes': 0,
        'page_count': 0,
        'error_message': None
    }
    
    try:
        # Check if file exists
        if not file_path.exists():
            result['error_message'] = "File does not exist"
            return result
        
        result['file_exists'] = True
        result['size_bytes'] = file_path.stat().st_size
        
        # Check file extension
        if not file_path.suffix.lower() == '.pdf':
            result['error_message'] = "File is not a PDF (wrong extension)"
            return result
        
        result['is_pdf'] = True
        
        # Try to read with pdfplumber
        try:
            import pdfplumber
            
            with pdfplumber.open(file_path) as pdf:
                result['page_count'] = len(pdf.pages)
                
                # Try to extract text from first page
                if pdf.pages:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text()
                    result['is_readable'] = True
                else:
                    result['error_message'] = "PDF has no pages"
                    return result
            
        except Exception as e:
            result['error_message'] = f"PDF reading error: {str(e)}"
            return result
        
        result['is_valid'] = True
        
    except Exception as e:
        result['error_message'] = f"Validation error: {str(e)}"
    
    return result


def generate_object_report(objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive report for a list of objects
    
    Args:
        objects: List of object dictionaries
        
    Returns:
        Dict with report data
    """
    if not objects:
        return {
            'total_objects': 0,
            'total_size': 0,
            'pdf_objects': 0,
            'size_distribution': {},
            'type_distribution': {},
            'date_range': None,
            'largest_object': None,
            'smallest_object': None
        }
    
    # Basic counts
    total_objects = len(objects)
    pdf_objects = len([obj for obj in objects if obj.get('is_pdf', False)])
    total_size = sum(obj.get('size', 0) for obj in objects)
    
    # Size distribution
    size_ranges = {
        'small': 0,      # < 1MB
        'medium': 0,     # 1MB - 10MB
        'large': 0,      # 10MB - 100MB
        'very_large': 0  # > 100MB
    }
    
    for obj in objects:
        size_mb = obj.get('size', 0) / (1024 * 1024)
        if size_mb < 1:
            size_ranges['small'] += 1
        elif size_mb < 10:
            size_ranges['medium'] += 1
        elif size_mb < 100:
            size_ranges['large'] += 1
        else:
            size_ranges['very_large'] += 1
    
    # Type distribution
    type_dist = {}
    for obj in objects:
        obj_name = obj.get('name', '')
        ext = Path(obj_name).suffix.lower()
        type_dist[ext] = type_dist.get(ext, 0) + 1
    
    # Date range
    dates = [obj.get('last_modified') for obj in objects if obj.get('last_modified')]
    date_range = None
    if dates:
        date_range = {
            'oldest': min(dates),
            'newest': max(dates),
            'span_days': (max(dates) - min(dates)).days
        }
    
    # Largest and smallest objects
    objects_with_size = [obj for obj in objects if obj.get('size', 0) > 0]
    largest_object = max(objects_with_size, key=lambda x: x.get('size', 0)) if objects_with_size else None
    smallest_object = min(objects_with_size, key=lambda x: x.get('size', 0)) if objects_with_size else None
    
    return {
        'total_objects': total_objects,
        'total_size': total_size,
        'total_size_formatted': format_size(total_size),
        'pdf_objects': pdf_objects,
        'pdf_percentage': (pdf_objects / total_objects * 100) if total_objects > 0 else 0,
        'size_distribution': size_ranges,
        'type_distribution': type_dist,
        'date_range': date_range,
        'largest_object': largest_object,
        'smallest_object': smallest_object,
        'average_size': total_size / total_objects if total_objects > 0 else 0,
        'average_size_formatted': format_size(total_size // total_objects) if total_objects > 0 else '0 B'
    }


def create_processing_manifest(objects: List[Dict[str, Any]], 
                             bucket_name: str,
                             job_id: str) -> Dict[str, Any]:
    """
    Create a processing manifest for a list of objects
    
    Args:
        objects: List of objects to process
        bucket_name: MinIO bucket name
        job_id: Processing job ID
        
    Returns:
        Dict with manifest data
    """
    manifest = {
        'job_id': job_id,
        'bucket_name': bucket_name,
        'created_at': datetime.now().isoformat(),
        'total_objects': len(objects),
        'objects': [],
        'processing_estimate': calculate_processing_estimate(objects),
        'report': generate_object_report(objects)
    }
    
    for obj in objects:
        manifest['objects'].append({
            'name': obj.get('name'),
            'size': obj.get('size', 0),
            'size_formatted': format_size(obj.get('size', 0)),
            'last_modified': obj.get('last_modified').isoformat() if obj.get('last_modified') else None,
            'is_pdf': obj.get('is_pdf', False),
            'content_type': obj.get('content_type', ''),
            'etag': obj.get('etag', '')
        })
    
    return manifest


# Convenience functions for common operations
def get_pdf_objects_from_bucket(client, bucket_name: str, prefix: str = '') -> List[Dict[str, Any]]:
    """Get all PDF objects from a bucket"""
    try:
        return client.list_pdf_objects(bucket_name, prefix=prefix)
    except Exception as e:
        logger.error(f"Error getting PDF objects from bucket {bucket_name}: {e}")
        return []


def estimate_download_time(objects: List[Dict[str, Any]], 
                          bandwidth_mbps: float = 10.0) -> float:
    """
    Estimate download time for objects
    
    Args:
        objects: List of objects
        bandwidth_mbps: Available bandwidth in Mbps
        
    Returns:
        Estimated download time in seconds
    """
    total_size_mb = sum(obj.get('size', 0) for obj in objects) / (1024 * 1024)
    return (total_size_mb * 8) / bandwidth_mbps  # Convert to seconds


def create_batch_groups(objects: List[Dict[str, Any]], 
                       batch_size: int = 10) -> List[List[Dict[str, Any]]]:
    """
    Group objects into batches for processing
    
    Args:
        objects: List of objects to group
        batch_size: Size of each batch
        
    Returns:
        List of object batches
    """
    batches = []
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        batches.append(batch)
    
    return batches


# Export commonly used functions
__all__ = [
    'validate_bucket_name',
    'validate_object_name',
    'sanitize_object_name',
    'parse_object_path',
    'filter_objects_by_pattern',
    'filter_objects_by_size',
    'filter_objects_by_date',
    'group_objects_by_path',
    'calculate_processing_estimate',
    'format_size',
    'format_duration',
    'create_temp_directory',
    'cleanup_temp_directory',
    'validate_pdf_file',
    'generate_object_report',
    'create_processing_manifest',
    'get_pdf_objects_from_bucket',
    'estimate_download_time',
    'create_batch_groups'
]
