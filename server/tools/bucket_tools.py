from google.cloud import storage
from typing import Dict, Any, Optional, List
import logging
from google.cloud.exceptions import GoogleCloudError
from google.auth import default
import os

logger = logging.getLogger(__name__)

class BucketTools:
    """Tools for interacting with Google Cloud Storage buckets."""
    
    def __init__(self):
        # Get project ID from environment or use default
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'me-sb-dgcp-dpoc-pocyosh-pr')
        credentials, _ = default()
        self.storage_client = storage.Client(credentials=credentials, project=project_id)
    
    @staticmethod
    def list_bucket_contents(bucket_name: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List contents of a GCS bucket.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Optional prefix to filter objects
            
        Returns:
            List of objects in the bucket
        """
        try:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'me-sb-dgcp-dpoc-pocyosh-pr')
            credentials, _ = default()
            storage_client = storage.Client(credentials=credentials, project=project_id)
            bucket = storage_client.bucket(bucket_name)
            
            # List objects with optional prefix
            blobs = bucket.list_blobs(prefix=prefix)
            
            contents = []
            for blob in blobs:
                contents.append({
                    'key': blob.name,
                    'size': blob.size,
                    'last_modified': blob.updated.isoformat(),
                    'storage_class': blob.storage_class,
                    'content_type': blob.content_type
                })
            
            return contents
        except GoogleCloudError as e:
            logger.error(f"Error listing bucket contents: {e}")
            raise
    
    @staticmethod
    def read_bucket_file(bucket_name: str, file_key: str) -> str:
        """
        Read a file from a GCS bucket.
        
        Args:
            bucket_name: Name of the bucket
            file_key: Key of the file to read
            
        Returns:
            File contents
        """
        try:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'me-sb-dgcp-dpoc-pocyosh-pr')
            credentials, _ = default()
            storage_client = storage.Client(credentials=credentials, project=project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(file_key)
            
            return blob.download_as_text()
        except GoogleCloudError as e:
            logger.error(f"Error reading bucket file: {e}")
            raise
    
    @staticmethod
    def write_bucket_file(bucket_name: str, file_key: str, content: str) -> Dict[str, Any]:
        """
        Write a file to a GCS bucket.
        
        Args:
            bucket_name: Name of the bucket
            file_key: Key for the file
            content: Content to write
            
        Returns:
            Status information
        """
        try:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'me-sb-dgcp-dpoc-pocyosh-pr')
            credentials, _ = default()
            storage_client = storage.Client(credentials=credentials, project=project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(file_key)
            
            blob.upload_from_string(
                content,
                content_type='text/plain'
            )
            
            return {
                'success': True,
                'bucket': bucket_name,
                'key': file_key,
                'size': len(content),
                'content_type': blob.content_type
            }
        except GoogleCloudError as e:
            logger.error(f"Error writing bucket file: {e}")
            raise 