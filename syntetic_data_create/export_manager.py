#!/usr/bin/env python3
# export_manager.py

"""
Export Manager - Handles exporting generated data in various formats
Independent module for export functionality
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExportManager:
    """
    Manages exports of generated data in various formats.
    Handles database exports in a modular way.
    """
    
    def __init__(self, db_url: str, exports_folder: Path):
        """
        Initialize the export manager.
        
        Args:
            db_url: Database URL to export from
            exports_folder: Base folder for exports
        """
        self.db_url = db_url
        self.exports_folder = Path(exports_folder)
        self.exports_folder.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Log initialization
        self.logger.info(f"Export Manager initialized for {db_url}")
        self.logger.info(f"Exports folder: {self.exports_folder}")
    
    def export_data(self, formats: List[str]) -> Dict[str, Any]:
        """
        Export data in specified formats.
        
        Args:
            formats: List of export formats ('csv', 'json', 'excel', 'sql')
            
        Returns:
            Dictionary with export results by format
        """
        if not formats:
            return {}
            
        # Ensure formats is a list
        if isinstance(formats, str):
            formats = [formats]
        
        self.logger.info(f"Exporting data in formats: {formats}")
        
        export_results = {}
        for format_name in formats:
            try:
                format_dir = self.exports_folder / format_name
                format_dir.mkdir(parents=True, exist_ok=True)
                
                export_func = getattr(self, f"_export_to_{format_name.lower()}", None)
                if export_func:
                    self.logger.info(f"Exporting to {format_name} format...")
                    result = export_func(format_dir)
                    export_results[format_name] = result
                else:
                    self.logger.warning(f"Export format not supported: {format_name}")
                    export_results[format_name] = {
                        "error": f"Format not supported: {format_name}",
                        "location": str(format_dir),
                        "file_count": 0
                    }
            except Exception as e:
                self.logger.error(f"Error exporting to {format_name}: {e}", exc_info=True)
                export_results[format_name] = {
                    "error": str(e),
                    "location": str(self.exports_folder / format_name),
                    "file_count": 0
                }
        
        self.logger.info(f"Export completed with results: {list(export_results.keys())}")
        return export_results
    
    def _export_to_csv(self, output_dir: Path) -> Dict[str, Any]:
        """Export to CSV format."""
        import pandas as pd
        from sqlalchemy import create_engine, inspect
        
        csv_files = {}
        try:
            self.logger.info(f"Starting CSV export to {output_dir}")
            engine = create_engine(self.db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                try:
                    df = pd.read_sql_table(table_name, engine)
                    csv_file = output_dir / f"{table_name}.csv"
                    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                    csv_files[table_name] = str(csv_file)
                    self.logger.info(f"Exported {table_name}: {len(df)} rows to CSV")
                except Exception as e:
                    self.logger.error(f"Error exporting {table_name} to CSV: {e}")
            
            return {
                "files": csv_files,
                "location": str(output_dir),
                "file_count": len(csv_files)
            }
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "location": str(output_dir),
                "file_count": 0
            }
    
    def _export_to_json(self, output_dir: Path) -> Dict[str, Any]:
        """Export to JSON format."""
        import pandas as pd
        from sqlalchemy import create_engine, inspect
        
        json_files = {}
        try:
            self.logger.info(f"Starting JSON export to {output_dir}")
            engine = create_engine(self.db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            combined_data = {}
            
            for table_name in table_names:
                try:
                    df = pd.read_sql_table(table_name, engine)
                    json_file = output_dir / f"{table_name}.json"
                    records = df.to_dict('records')
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(records, f, ensure_ascii=False, indent=2, default=str)
                    json_files[table_name] = str(json_file)
                    combined_data[table_name] = records
                    self.logger.info(f"Exported {table_name}: {len(df)} rows to JSON")
                except Exception as e:
                    self.logger.error(f"Error exporting {table_name} to JSON: {e}")
            
            # Create combined JSON file
            combined_file = output_dir / "combined_data.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2, default=str)
            json_files['combined'] = str(combined_file)
            
            return {
                "files": json_files,
                "location": str(output_dir),
                "file_count": len(json_files)
            }
            
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "location": str(output_dir),
                "file_count": 0
            }
    
    def _export_to_excel(self, output_dir: Path) -> Dict[str, Any]:
        """Export to Excel format."""
        import pandas as pd
        from sqlalchemy import create_engine, inspect
        
        excel_files = {}
        try:
            self.logger.info(f"Starting Excel export to {output_dir}")
            engine = create_engine(self.db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            # Create combined Excel file with multiple sheets
            combined_file = output_dir / "combined_data.xlsx"
            
            try:
                with pd.ExcelWriter(combined_file, engine='openpyxl') as writer:
                    for table_name in table_names:
                        df = pd.read_sql_table(table_name, engine)
                        sheet_name = table_name[:31]  # Excel sheet name limit
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                excel_files['combined'] = str(combined_file)
                self.logger.info(f"Exported combined Excel file: {combined_file}")
            except ImportError:
                return {
                    "error": "openpyxl not installed. Install with: pip install openpyxl",
                    "location": str(output_dir),
                    "file_count": 0
                }
            
            return {
                "files": excel_files,
                "location": str(output_dir),
                "file_count": len(excel_files)
            }
            
        except Exception as e:
            self.logger.error(f"Excel export failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "location": str(output_dir),
                "file_count": 0
            }
    
    def _export_to_sql(self, output_dir: Path) -> Dict[str, Any]:
        """Export database tables to SQL DDL (CREATE TABLE) and DML (INSERT) statements."""
        import pandas as pd
        from sqlalchemy import create_engine, inspect, MetaData, Table
        from sqlalchemy.schema import CreateTable
        
        sql_files = {}
        try:
            self.logger.info(f"Starting SQL export to {output_dir}")
            engine = create_engine(self.db_url)
            inspector = inspect(engine)
            metadata = MetaData()
            
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                self.logger.info(f"Exporting table {table_name} schema and data to SQL...")
                
                # Create SQL file path
                sql_file = os.path.join(output_dir, f"{table_name}.sql")
                
                try:
                    # Get table object
                    table = Table(table_name, metadata, autoload_with=engine)
                    
                    # Generate CREATE TABLE statement
                    create_table_sql = str(CreateTable(table).compile(engine))
                    
                    # Get table data
                    df = pd.read_sql_table(table_name, engine)
                    
                    # Generate INSERT statements
                    insert_statements = []
                    for _, row in df.iterrows():
                        values = []
                        for value in row:
                            values.append(self._sql_value_formatter(value))
                        
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(values)});"
                        insert_statements.append(insert_sql)
                    
                    # Write SQL file
                    with open(sql_file, 'w', encoding='utf-8') as f:
                        f.write(create_table_sql + ';\n\n')
                        f.write('\n'.join(insert_statements))
                    
                    sql_files[table_name] = sql_file
                    
                except Exception as e:
                    self.logger.error(f"Error exporting {table_name} to sql: {str(e)}")
            
            return {
                'files': sql_files,
                'location': str(output_dir),
                'file_count': len(sql_files)
            }
                
        except Exception as e:
            self.logger.error(f"Error exporting to SQL: {str(e)}")
            return {
                'error': str(e),
                'files': {},
                'location': str(output_dir),
                'file_count': 0
            }
    
    def _sql_value_formatter(self, value: Any) -> str:
        """Format a value for SQL INSERT statement."""
        import pandas as pd
        
        if value is None or (hasattr(pd, 'isna') and pd.isna(value)):
            return 'NULL'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (datetime, date)):
            return f"'{value}'"
        elif isinstance(value, str):
            # Escape single quotes in strings
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"
        else:
            # For any other types, convert to string and escape quotes
            escaped_value = str(value).replace("'", "''")
            return f"'{escaped_value}'"


def test_export_manager():
    """Test the ExportManager functionality."""
    import tempfile
    
    # Create a temporary SQLite database for testing
    import sqlite3
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple test database
        db_file = os.path.join(temp_dir, "test.db")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute('''
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL,
            date TEXT
        )
        ''')
        
        # Insert some test data
        test_data = [
            (1, "Test 1", 10.5, "2025-01-01"),
            (2, "Test 2", 20.5, "2025-01-02"),
            (3, "Test 3", 30.5, "2025-01-03"),
            (4, "Test's with quote", 40.5, "2025-01-04"),
            (5, "Test with NULL", None, None)
        ]
        cursor.executemany("INSERT INTO test_table VALUES (?, ?, ?, ?)", test_data)
        conn.commit()
        conn.close()
        
        # Create export manager
        db_url = f"sqlite:///{db_file}"
        exports_folder = Path(temp_dir) / "exports"
        manager = ExportManager(db_url, exports_folder)
        
        # Test exports
        print("\nTesting Export Manager...")
        print(f"Database: {db_url}")
        print(f"Exports folder: {exports_folder}")
        
        formats_to_test = ["csv", "json", "sql"]
        results = manager.export_data(formats_to_test)
        
        for format_name, result in results.items():
            print(f"\n{format_name.upper()} Export:")
            if "error" in result:
                print(f"  Error: {result['error']}")
            else:
                print(f"  Files: {result['file_count']}")
                print(f"  Location: {result['location']}")
                
                # Show file sizes
                for table_name, file_path in result.get('files', {}).items():
                    file_size = Path(file_path).stat().st_size / 1024 if Path(file_path).exists() else 0
                    print(f"  - {table_name}: {file_size:.1f} KB")
                    
                    # For SQL, show a snippet
                    if format_name == "sql":
                        with open(file_path, 'r') as f:
                            lines = f.readlines()[:5]  # First 5 lines
                            print(f"    First 5 lines:")
                            for line in lines:
                                print(f"      {line.strip()}")
        
        print("\nExport Manager test completed!")


if __name__ == "__main__":
    test_export_manager()