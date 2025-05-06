import json
import pandas as pd
from typing import List, Dict, Any, Optional
import numpy as np

class DataTools:
    """Tools for data analysis and transformation."""
    
    @staticmethod
    def analyze_data(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze data and provide statistical summary.
        
        Args:
            data: List of dictionaries containing data
            columns: Optional list of columns to analyze (analyzes all if None)
            
        Returns:
            Statistical summary
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Filter columns if specified
        if columns and all(col in df.columns for col in columns):
            df = df[columns]
        
        # Generate statistics
        stats = {}
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                stats[column] = {
                    "mean": float(df[column].mean()),
                    "median": float(df[column].median()),
                    "std": float(df[column].std()),
                    "min": float(df[column].min()),
                    "max": float(df[column].max()),
                }
            elif pd.api.types.is_string_dtype(df[column]):
                stats[column] = {
                    "unique_values": df[column].nunique(),
                    "most_common": df[column].value_counts().index[0] if not df[column].empty else None,
                    "null_count": int(df[column].isna().sum()),
                }
            
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "statistics": stats
        }
    
    @staticmethod
    def filter_data(data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter data based on criteria.
        
        Args:
            data: List of dictionaries containing data
            filters: Dictionary of filter criteria (column_name: value)
            
        Returns:
            Filtered data
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Apply filters
        for column, value in filters.items():
            if column in df.columns:
                if isinstance(value, list):
                    df = df[df[column].isin(value)]
                else:
                    df = df[df[column] == value]
        
        # Convert back to list of dictionaries
        return df.to_dict(orient="records")

    @staticmethod
    def summarize_dataset(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Provide a comprehensive summary of the dataset.
        
        Args:
            data: List of dictionaries containing data
            
        Returns:
            Dataset summary
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Basic dataset information
        info = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_types": {col: str(df[col].dtype) for col in df.columns},
            "missing_values": {col: int(df[col].isna().sum()) for col in df.columns},
            "memory_usage": df.memory_usage(deep=True).sum(),
        }
        
        # Sample data (first 5 rows)
        sample = df.head(5).to_dict(orient="records")
        
        return {
            "info": info,
            "sample": sample
        }