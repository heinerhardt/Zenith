"""
Bucket Browser Component for Streamlit UI
Provides interface for browsing MinIO buckets and objects
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import fnmatch

from src.core.minio_client import MinIOClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BucketBrowserUI:
    """Bucket browser UI component"""
    
    def __init__(self):
        """Initialize bucket browser"""
        pass
    
    def render_bucket_selector(self, client: MinIOClient) -> Optional[str]:
        """
        Render bucket selection interface
        
        Args:
            client: MinIO client instance
            
        Returns:
            Selected bucket name or None
        """
        try:
            # Get available buckets
            buckets = client.list_buckets()
            
            if not buckets:
                st.warning("No buckets available")
                return None
            
            # Bucket selection
            bucket_names = [bucket['name'] for bucket in buckets]
            
            selected_bucket = st.selectbox(
                "Select Bucket",
                options=bucket_names,
                index=0,
                help="Choose a MinIO bucket to browse"
            )
            
            if selected_bucket:
                # Show bucket information
                bucket_info = next((b for b in buckets if b['name'] == selected_bucket), None)
                if bucket_info:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Created", bucket_info.get('creation_date_str', 'Unknown'))
                    
                    # Get bucket stats
                    try:
                        stats = client.get_bucket_stats(selected_bucket)
                        if 'error' not in stats:
                            with col2:
                                st.metric("Total Objects", stats.get('total_objects', 0))
                            with col3:
                                st.metric("PDF Objects", stats.get('pdf_objects', 0))
                    except Exception as e:
                        logger.warning(f"Could not get bucket stats: {e}")
            
            return selected_bucket
            
        except Exception as e:
            st.error(f"Error loading buckets: {str(e)}")
            logger.error(f"Error in bucket selector: {e}")
            return None
    
    def render_object_filter(self) -> Dict[str, Any]:
        """
        Render object filtering interface
        
        Returns:
            Dictionary with filter settings
        """
        st.subheader("🔍 Object Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            prefix_filter = st.text_input(
                "Path Prefix",
                value=st.session_state.get('object_prefix', ''),
                help="Filter objects by path prefix (e.g., 'documents/', 'pdfs/2024')"
            )
            
            name_pattern = st.text_input(
                "Name Pattern",
                value=st.session_state.get('object_pattern', '*.pdf'),
                help="Filter objects by name pattern (e.g., '*.pdf', 'report_*.pdf')"
            )
            
            only_pdfs = st.checkbox(
                "PDF Files Only",
                value=True,
                help="Show only PDF files"
            )
        
        with col2:
            min_size_mb = st.number_input(
                "Min Size (MB)",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help="Filter objects by minimum size"
            )
            
            max_size_mb = st.number_input(
                "Max Size (MB)",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help="Filter objects by maximum size (0 = no limit)"
            )
            
            date_filter = st.selectbox(
                "Date Range",
                options=["All", "Last 7 days", "Last 30 days", "Last 90 days"],
                help="Filter objects by last modified date"
            )
        
        # Store filter values in session state
        st.session_state['object_prefix'] = prefix_filter
        st.session_state['object_pattern'] = name_pattern
        
        return {
            'prefix': prefix_filter,
            'pattern': name_pattern,
            'only_pdfs': only_pdfs,
            'min_size_mb': min_size_mb,
            'max_size_mb': max_size_mb,
            'date_filter': date_filter
        }
    
    def render_object_browser(self, 
                            client: MinIOClient, 
                            bucket_name: str, 
                            filters: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Render object browser with selection
        
        Args:
            client: MinIO client instance
            bucket_name: Selected bucket name
            filters: Filter settings
            
        Returns:
            List of selected objects or None
        """
        try:
            st.subheader(f"📁 Objects in '{bucket_name}'")
            
            # List objects with filters
            objects = client.list_objects(
                bucket_name=bucket_name,
                prefix=filters.get('prefix', ''),
                suffix='.pdf' if filters.get('only_pdfs', True) else None
            )
            
            if not objects:
                st.info("No objects found matching the filters")
                return None
            
            # Apply additional filters
            filtered_objects = self._apply_filters(objects, filters)
            
            if not filtered_objects:
                st.info("No objects found matching the filters")
                return None
            
            # Convert to DataFrame for display
            df_data = []
            for obj in filtered_objects:
                df_data.append({
                    'Select': False,
                    'Name': obj['name'],
                    'Size': obj.get('size_str', 'Unknown'),
                    'Modified': obj.get('last_modified_str', 'Unknown'),
                    'Type': self._get_object_type(obj['name'])
                })
            
            df = pd.DataFrame(df_data)
            
            # Object selection interface
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"Found {len(filtered_objects)} objects")
            
            with col2:
                select_all = st.button("Select All", use_container_width=True)
            
            with col3:
                clear_all = st.button("Clear All", use_container_width=True)
            
            # Handle select/clear all
            if select_all:
                for i in range(len(df)):
                    df.at[i, 'Select'] = True
            
            if clear_all:
                for i in range(len(df)):
                    df.at[i, 'Select'] = False
            
            # Display objects table with selection
            edited_df = st.data_editor(
                df,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select objects for processing",
                        default=False,
                    ),
                    "Name": st.column_config.TextColumn(
                        "Object Name",
                        help="Name of the object in MinIO",
                        width="large"
                    ),
                    "Size": st.column_config.TextColumn(
                        "Size",
                        help="Object size"
                    ),
                    "Modified": st.column_config.TextColumn(
                        "Last Modified",
                        help="Last modification date"
                    ),
                    "Type": st.column_config.TextColumn(
                        "Type",
                        help="File type"
                    )
                },
                disabled=["Name", "Size", "Modified", "Type"],
                hide_index=True,
                height=400,
                use_container_width=True
            )
            
            # Get selected objects
            selected_objects = []
            if edited_df['Select'].any():
                selected_indices = edited_df[edited_df['Select']].index.tolist()
                selected_objects = [filtered_objects[i] for i in selected_indices]
                
                st.success(f"Selected {len(selected_objects)} objects")
            
            return selected_objects
            
        except Exception as e:
            st.error(f"Error browsing objects: {str(e)}")
            logger.error(f"Error in object browser: {e}")
            return None
    
    def render_batch_actions(self, 
                           selected_objects: List[Dict[str, Any]], 
                           bucket_name: str) -> Optional[Dict[str, Any]]:
        """
        Render batch action buttons
        
        Args:
            selected_objects: List of selected objects
            bucket_name: Selected bucket name
            
        Returns:
            Dictionary with action information or None
        """
        if not selected_objects:
            return None
        
        st.divider()
        st.subheader("🚀 Batch Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        action_result = None
        
        with col1:
            if st.button(
                f"📄 Process Selected ({len(selected_objects)})",
                use_container_width=True,
                type="primary"
            ):
                action_result = {
                    'process_selected': {
                        'bucket_name': bucket_name,
                        'object_names': [obj['name'] for obj in selected_objects],
                        'total_count': len(selected_objects)
                    }
                }
        
        with col2:
            if st.button("📦 Process All in Bucket", use_container_width=True):
                action_result = {
                    'process_all_bucket': {
                        'bucket_name': bucket_name
                    }
                }
        
        with col3:
            if st.button("📋 Download List", use_container_width=True):
                object_list = "\n".join([obj['name'] for obj in selected_objects])
                action_result = {
                    'download_list': object_list
                }
        
        with col4:
            if st.button("📊 Export Metadata", use_container_width=True):
                # Create metadata DataFrame
                metadata_rows = []
                for obj in selected_objects:
                    metadata_rows.append({
                        'object_name': obj['name'],
                        'bucket': bucket_name,
                        'size_bytes': obj.get('size', 0),
                        'size_human': obj.get('size_str', 'Unknown'),
                        'last_modified': obj.get('last_modified_str', 'Unknown'),
                        'type': self._get_object_type(obj['name'])
                    })
                
                metadata_df = pd.DataFrame(metadata_rows)
                action_result = {
                    'export_metadata': metadata_df
                }
        
        return action_result
    
    def render_bucket_stats(self, client: MinIOClient, bucket_name: str):
        """
        Render bucket statistics
        
        Args:
            client: MinIO client instance
            bucket_name: Bucket name
        """
        try:
            st.divider()
            st.subheader("📊 Bucket Statistics")
            
            # Get detailed stats
            stats = client.get_bucket_stats(bucket_name)
            
            if 'error' in stats:
                st.error(f"Error getting stats: {stats['error']}")
                return
            
            # Display stats in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Objects",
                    stats.get('total_objects', 0),
                    help="Total number of objects in bucket"
                )
            
            with col2:
                st.metric(
                    "PDF Objects",
                    stats.get('pdf_objects', 0),
                    help="Number of PDF files"
                )
            
            with col3:
                st.metric(
                    "Total Size",
                    stats.get('total_size_str', '0 B'),
                    help="Total size of all objects"
                )
            
            with col4:
                st.metric(
                    "PDF Size",
                    stats.get('pdf_size_str', '0 B'),
                    help="Total size of PDF files"
                )
            
            # Additional stats
            if stats.get('largest_object'):
                st.write("**Largest Object:**", stats['largest_object'])
            
            if stats.get('most_recent'):
                st.write("**Most Recent:**", stats['most_recent'])
                
        except Exception as e:
            st.error(f"Error loading bucket stats: {str(e)}")
            logger.error(f"Error in bucket stats: {e}")
    
    def _apply_filters(self, objects: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply filters to object list
        
        Args:
            objects: List of objects
            filters: Filter settings
            
        Returns:
            Filtered list of objects
        """
        filtered = objects
        
        # Apply name pattern filter
        if filters.get('pattern') and filters['pattern'] != '*':
            pattern = filters['pattern']
            filtered = [obj for obj in filtered if fnmatch.fnmatch(obj['name'], pattern)]
        
        # Apply size filters
        min_size = filters.get('min_size_mb', 0) * 1024 * 1024  # Convert to bytes
        max_size = filters.get('max_size_mb', 0) * 1024 * 1024  # Convert to bytes
        
        if min_size > 0:
            filtered = [obj for obj in filtered if obj.get('size', 0) >= min_size]
        
        if max_size > 0:
            filtered = [obj for obj in filtered if obj.get('size', 0) <= max_size]
        
        # Apply date filter
        date_filter = filters.get('date_filter', 'All')
        if date_filter != 'All':
            # Implement date filtering based on last_modified
            # This would require parsing the date and comparing
            pass
        
        return filtered
    
    def _get_object_type(self, object_name: str) -> str:
        """
        Get object type based on file extension
        
        Args:
            object_name: Object name
            
        Returns:
            Object type string
        """
        if object_name.lower().endswith('.pdf'):
            return 'PDF'
        elif object_name.lower().endswith(('.txt', '.md')):
            return 'Text'
        elif object_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            return 'Image'
        elif object_name.lower().endswith(('.doc', '.docx')):
            return 'Document'
        else:
            return 'Other'