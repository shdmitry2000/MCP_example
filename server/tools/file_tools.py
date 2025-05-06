import os
import json
from typing import List, Dict, Any, Optional
import csv
import tempfile

class FileTools:
    """Tools for file manipulation."""
    
    @staticmethod
    def read_file(file_path: str, max_size: int = 1024 * 1024) -> str:
        """
        Read content from a file safely.
        
        Args:
            file_path: Path to the file
            max_size: Maximum file size to read (default: 1MB)
            
        Returns:
            File content
        """
        # Security checks
        abs_path = os.path.abspath(file_path)
        
        # Check if file exists
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        # Check if file is too large
        if os.path.getsize(abs_path) > max_size:
            raise ValueError(f"File is too large: {os.path.getsize(abs_path)} bytes (max: {max_size})")
        
        # Read file content
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    @staticmethod
    def write_file(file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Write content to a file safely.
        
        Args:
            file_path: Path to the file
            content: Content to write
            overwrite: Whether to overwrite existing file
            
        Returns:
            Status information
        """
        # Security checks
        abs_path = os.path.abspath(file_path)
        
        # Check if file exists and overwrite is not allowed
        if os.path.exists(abs_path) and not overwrite:
            raise FileExistsError(f"File already exists: {abs_path}")
        
        # Write content to file
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "path": abs_path,
            "size": len(content)
        }
    
    @staticmethod
    def list_directory(directory_path: str, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in a directory.
        
        Args:
            directory_path: Path to the directory
            pattern: Optional glob pattern to filter files
            
        Returns:
            List of file information
        """
        import glob
        
        # Security checks
        abs_path = os.path.abspath(directory_path)
        
        # Check if directory exists
        if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
            raise NotADirectoryError(f"Directory not found: {abs_path}")
        
        # List files
        files = []
        
        if pattern:
            file_list = glob.glob(os.path.join(abs_path, pattern))
        else:
            file_list = [os.path.join(abs_path, f) for f in os.listdir(abs_path)]
        
        for file_path in file_list:
            stat = os.stat(file_path)
            files.append({
                "name": os.path.basename(file_path),
                "path": file_path,
                "size": stat.st_size,
                "last_modified": stat.st_mtime,
                "is_directory": os.path.isdir(file_path)
            })
        
        return files