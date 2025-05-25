#!/usr/bin/env python3
# complete_integration.py

"""
Complete integration script that demonstrates the full workflow:
Fixed version with proper imports and error handling
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import argparse

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent if current_dir.name == 'syntetic_data_create' else current_dir
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import with error handling
try:
    from database_generator import create_generator, ISRAELI_CREDIT_CARD_SCHEMA
except ImportError as e:
    logger.error(f"Failed to import database_generator: {e}")
    sys.exit(1)

try:
    from swagger_db_integration import EnhancedSwaggerSchemaGenerator
except ImportError as e:
    logger.warning(f"swagger_db_integration not available: {e}")
    EnhancedSwaggerSchemaGenerator = None

try:
    from schema_manager import SchemaManager
except ImportError as e:
    logger.warning(f"schema_manager not available: {e}")
    SchemaManager = None

# Import config with fallback
try:
    from config.config import config
    DATABASE_URL = config.DATABASE_URL
    DB_FOLDER = getattr(config, 'DB_FOLDER', 'database_files')
    # Ensure DB folder exists
    Path(DB_FOLDER).mkdir(parents=True, exist_ok=True)
except ImportError:
    logger.warning("Config not found, using default database settings")
    DB_FOLDER = "database_files"
    Path(DB_FOLDER).mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{DB_FOLDER}/israeli_banking_data.db"

# Configure logging to use DB_FOLDER
log_file = Path(DB_FOLDER) / "logs" / "database_generation.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

# Update logging configuration
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IsraeliBankingDataGenerator:
    """
    Complete Israeli banking data generation system with multiple strategies
    and integration with existing MCP tools. All files stored in DB_FOLDER.
    """
    
    def __init__(self, db_url: Optional[str] = None, strategy: str = 'faker', schema_source: str = 'default'):
        """
        Initialize the complete data generation system.
        
        Args:
            db_url: Database URL (defaults to config or SQLite in DB_FOLDER)
            strategy: Generation strategy ('faker', 'sdv', 'mimesis')
            schema_source: Schema source ('default', 'swagger', 'definition', or file path)
        """
        # Use DB_FOLDER for all file operations
        self.db_folder = Path(DB_FOLDER)
        self.schemas_folder = self.db_folder / "schemas"
        self.exports_folder = self.db_folder / "exports"
        self.logs_folder = self.db_folder / "logs"
        
        # Create all necessary folders
        for folder in [self.db_folder, self.schemas_folder, self.exports_folder, self.logs_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Set database URL to use DB_FOLDER if not absolute
        if db_url:
            self.db_url = db_url
        else:
            self.db_url = DATABASE_URL if DATABASE_URL.startswith(('postgresql://', 'mysql://', 'sqlite:///')) else f"sqlite:///{self.db_folder}/israeli_banking_data.db"
        
        self.strategy = strategy
        self.schema_source = schema_source
        self.generator = None
        self.schema_manager = SchemaManager(str(self.schemas_folder)) if SchemaManager else None
        self.results = {}
        
        logger.info(f"Initializing Israeli Banking Data Generator")
        logger.info(f"DB Folder: {self.db_folder}")
        logger.info(f"Database: {self.db_url}")
        logger.info(f"Strategy: {self.strategy}")
        logger.info(f"Schema Source: {self.schema_source}")
    
    def setup(self) -> Dict[str, Any]:
        """Setup the enhanced generator and test the connection."""
        try:
            # Create default schema files if they don't exist and schema manager is available
            if self.schema_source == 'default' and self.schema_manager:
                try:
                    created_files = self.schema_manager.create_default_files()
                    logger.info(f"Created default schema files: {created_files}")
                except Exception as e:
                    logger.warning(f"Could not create schema files: {e}")
            
            # Initialize generator based on schema source
            if EnhancedSwaggerSchemaGenerator and (self.schema_source == 'swagger' or 
                                                 (os.path.exists(self.schema_source) and 
                                                  self.schema_source.endswith(('.json', '.yaml', '.yml')))):
                # Use Swagger-based generator
                if self.schema_manager:
                    swagger_file = self.schema_source if os.path.exists(self.schema_source) else self.schema_manager.swagger_file
                else:
                    swagger_file = self.schemas_folder / "israeli_banking_swagger.json"
                
                self.generator = EnhancedSwaggerSchemaGenerator(
                    schema_file_path=str(swagger_file),
                    db_url=self.db_url
                )
            else:
                # Use basic database generator
                self.generator = create_generator(self.strategy, db_url=self.db_url)
            
            logger.info("Generator setup completed successfully")
            return {"status": "success", "message": "Setup completed successfully"}
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def generate_complete_database(self, num_records: int = 1000) -> Dict[str, Any]:
        """
        Generate a complete Israeli banking database with all tables and relationships.
        
        Args:
            num_records: Number of records to generate per table
            
        Returns:
            Generation results with statistics
        """
        logger.info(f"Starting complete database generation with {num_records} records")
        logger.info(f"Using schema source: {self.schema_source}")
        
        try:
            # Generate based on schema source type
            if (self.schema_source == 'definition' or 
                (os.path.exists(self.schema_source) and 'definition' in self.schema_source)):
                
                if self.schema_manager:
                    # Generate from definition file
                    definition_file = self.schema_source if os.path.exists(self.schema_source) else self.schema_manager.definition_file
                    result = self.schema_manager.generate_database_from_definition(
                        definition_file=str(definition_file),
                        num_records=num_records,
                        db_url=self.db_url
                    )
                else:
                    # Fallback to basic generation
                    result = self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records)
                    
            elif (self.schema_source == 'swagger' or 
                  (os.path.exists(self.schema_source) and 
                   self.schema_source.endswith(('.json', '.yaml', '.yml')))):
                
                if self.schema_manager:
                    # Generate from swagger file
                    swagger_file = self.schema_source if os.path.exists(self.schema_source) else self.schema_manager.swagger_file
                    result = self.schema_manager.generate_database_from_swagger(
                        swagger_file=str(swagger_file),
                        num_records=num_records,
                        db_url=self.db_url
                    )
                else:
                    # Fallback to enhanced generator if available
                    if hasattr(self.generator, 'generate_database'):
                        result = self.generator.generate_database(
                            num_records=num_records, 
                            strategy=self.strategy
                        )
                    else:
                        result = self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records)
            else:
                # Default generation
                if hasattr(self.generator, 'generate_database'):
                    result = self.generator.generate_database(
                        num_records=num_records, 
                        strategy=self.strategy
                    )
                else:
                    result = self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records)
            
            # Get detailed statistics
            if hasattr(self.generator, 'get_database_stats'):
                stats = self.generator.get_database_stats()
            elif hasattr(self.generator, 'get_table_stats'):
                stats = self.generator.get_table_stats()
            else:
                stats = {}
            
            # Store results
            self.results = {
                'generation_result': result,
                'database_stats': stats,
                'timestamp': datetime.now().isoformat(),
                'strategy_used': self.strategy,
                'schema_source': self.schema_source,
                'total_records': sum(table_stats.get('record_count', 0) for table_stats in stats.values()) if stats else result.get('total_records', num_records * 2)  # Estimate
            }
            
            logger.info(f"Database generation completed successfully")
            logger.info(f"Total records created: {self.results['total_records']}")
            
            return self.results
            
        except Exception as e:
            logger.error(f"Database generation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the generated database."""
        try:
            if hasattr(self.generator, 'get_database_stats'):
                return self.generator.get_database_stats()
            elif hasattr(self.generator, 'get_table_stats'):
                return self.generator.get_table_stats()
            else:
                return {"message": "Statistics not available"}
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    def export_data(self, formats: list = ['csv']) -> Dict[str, Any]:
        """
        Export generated data in multiple formats to DB_FOLDER/exports.
        
        Args:
            formats: List of export formats ('csv', 'json', 'excel')
            
        Returns:
            Export results with file paths
        """
        logger.info(f"Exporting data in formats: {formats}")
        
        export_results = {}
        
        try:
            # Get the database URL from our generator
            if hasattr(self.generator, 'db_url'):
                db_url = self.generator.db_url
            else:
                db_url = self.db_url
            
            # CSV Export
            if 'csv' in formats:
                csv_export_dir = self.exports_folder / "csv"
                csv_export_dir.mkdir(parents=True, exist_ok=True)
                
                csv_files = self._export_csv(db_url, csv_export_dir)
                
                export_results['csv'] = {
                    'files': csv_files,
                    'count': len(csv_files) if isinstance(csv_files, dict) else 0,
                    'export_dir': str(csv_export_dir)
                }
                logger.info(f"CSV export: {export_results['csv']['count']} files created in {csv_export_dir}")
            
            # JSON Export
            if 'json' in formats:
                json_export_dir = self.exports_folder / "json"
                json_export_dir.mkdir(parents=True, exist_ok=True)
                
                json_files = self._export_json(db_url, json_export_dir)
                
                export_results['json'] = {
                    'files': json_files,
                    'count': len(json_files) if isinstance(json_files, dict) else 0,
                    'export_dir': str(json_export_dir)
                }
                logger.info(f"JSON export: {export_results['json']['count']} files created in {json_export_dir}")
            
            # Excel Export
            if 'excel' in formats:
                excel_export_dir = self.exports_folder / "excel"
                excel_export_dir.mkdir(parents=True, exist_ok=True)
                
                excel_files = self._export_excel(db_url, excel_export_dir)
                
                export_results['excel'] = {
                    'files': excel_files,
                    'count': len(excel_files) if isinstance(excel_files, dict) else 0,
                    'export_dir': str(excel_export_dir)
                }
                logger.info(f"Excel export: {export_results['excel']['count']} files created in {excel_export_dir}")
            
            return export_results
            
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _export_csv(self, db_url: str, output_dir: Path) -> Dict[str, str]:
        """Export to CSV format."""
        try:
            # Try using generator's export method first
            if hasattr(self.generator, 'export_to_csv'):
                return self.generator.export_to_csv(str(output_dir))
            
            # Fallback to manual export
            import pandas as pd
            from sqlalchemy import create_engine, inspect
            
            engine = create_engine(db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            csv_files = {}
            for table_name in table_names:
                df = pd.read_sql_table(table_name, engine)
                csv_file = output_dir / f"{table_name}.csv"
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                csv_files[table_name] = str(csv_file)
                logger.info(f"Exported {table_name}: {len(df)} rows to CSV")
            
            return csv_files
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return {"error": str(e)}
    
    def _export_json(self, db_url: str, output_dir: Path) -> Dict[str, str]:
        """Export to JSON format."""
        try:
            import pandas as pd
            from sqlalchemy import create_engine, inspect
            
            engine = create_engine(db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            json_files = {}
            
            # Export each table as separate JSON file
            for table_name in table_names:
                df = pd.read_sql_table(table_name, engine)
                json_file = output_dir / f"{table_name}.json"
                
                # Convert to records and save with UTF-8 encoding
                records = df.to_dict('records')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2, default=str)
                
                json_files[table_name] = str(json_file)
                logger.info(f"Exported {table_name}: {len(df)} rows to JSON")
            
            # Create combined JSON file
            combined_file = output_dir / "combined_data.json"
            combined_data = {}
            
            for table_name in table_names:
                df = pd.read_sql_table(table_name, engine)
                combined_data[table_name] = df.to_dict('records')
            
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2, default=str)
            
            json_files['combined'] = str(combined_file)
            
            return json_files
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return {"error": str(e)}
    
    def _export_excel(self, db_url: str, output_dir: Path) -> Dict[str, str]:
        """Export to Excel format."""
        try:
            import pandas as pd
            from sqlalchemy import create_engine, inspect
            
            engine = create_engine(db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            excel_files = {}
            
            # Export each table as separate Excel file
            for table_name in table_names:
                df = pd.read_sql_table(table_name, engine)
                excel_file = output_dir / f"{table_name}.xlsx"
                df.to_excel(excel_file, index=False, engine='openpyxl')
                excel_files[table_name] = str(excel_file)
                logger.info(f"Exported {table_name}: {len(df)} rows to Excel")
            
            # Create combined Excel file with multiple sheets
            combined_file = output_dir / "combined_data.xlsx"
            
            with pd.ExcelWriter(combined_file, engine='openpyxl') as writer:
                for table_name in table_names:
                    df = pd.read_sql_table(table_name, engine)
                    sheet_name = table_name[:31]  # Excel sheet name limit
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            excel_files['combined'] = str(combined_file)
            
            return excel_files
            
        except ImportError:
            logger.error("openpyxl not installed. Install with: pip install openpyxl")
            return {"error": "openpyxl not installed"}
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return {"error": str(e)}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report and save to DB_FOLDER."""
        logger.info("Generating comprehensive report")
        
        report = {
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "database_url": self.db_url,
                "db_folder": str(self.db_folder),
                "strategy_used": self.strategy,
                "schema_source": self.schema_source,
                "generator_version": "1.0.0"
            },
            "database_info": self.results.get('database_stats', {}),
            "generation_summary": {
                "total_tables": len(self.results.get('database_stats', {})),
                "total_records": self.results.get('total_records', 0),
                "generation_strategy": self.strategy,
                "schema_source": self.schema_source
            },
            "file_locations": {
                "database_folder": str(self.db_folder),
                "schemas_folder": str(self.schemas_folder),
                "exports_folder": str(self.exports_folder),
                "logs_folder": str(self.logs_folder)
            }
        }
        
        # Save report to DB_FOLDER
        report_file = self.db_folder / "israeli_banking_generation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Report saved to {report_file}")
        
        return report


def create_schema_files_only():
    """Create default schema files only in DB_FOLDER/schemas."""
    if not SchemaManager:
        print("❌ Schema Manager not available. Please ensure schema_manager.py is in the same directory.")
        return False
    
    try:
        schemas_dir = Path(DB_FOLDER) / "schemas"
        schemas_dir.mkdir(parents=True, exist_ok=True)
        
        manager = SchemaManager(str(schemas_dir))
        created_files = manager.create_default_files()
        
        print("✅ Created default schema files:")
        for file_type, file_path in created_files.items():
            file_size = Path(file_path).stat().st_size / 1024  # KB
            print(f"   • {file_type}: {file_path} ({file_size:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema files: {e}")
        return False


def list_available_schemas():
    """List available schema files in DB_FOLDER/schemas."""
    if not SchemaManager:
        print("❌ Schema Manager not available.")
        return
    
    try:
        schemas_dir = Path(DB_FOLDER) / "schemas"
        schemas_dir.mkdir(parents=True, exist_ok=True)
        
        manager = SchemaManager(str(schemas_dir))
        available_schemas = manager.list_available_schemas()
        
        print("📁 Available Schema Files:")
        print(f"   Location: {schemas_dir}")
        
        if available_schemas["swagger_files"]:
            print(f"   📄 Swagger files ({len(available_schemas['swagger_files'])}):")
            for file_info in available_schemas['swagger_files']:
                file_size = Path(file_info['path']).stat().st_size / 1024  # KB
                print(f"      • {file_info['name']} ({file_size:.1f} KB)")
        
        if available_schemas["definition_files"]:
            print(f"   📋 Definition files ({len(available_schemas['definition_files'])}):")
            for file_info in available_schemas['definition_files']:
                file_size = Path(file_info['path']).stat().st_size / 1024  # KB
                print(f"      • {file_info['name']} ({file_size:.1f} KB)")
        
        if not available_schemas["swagger_files"] and not available_schemas["definition_files"]:
            print("   No schema files found. Run with --create-schemas to create default files.")
            
    except Exception as e:
        print(f"❌ Error listing schemas: {e}")


def main():
    """Main function demonstrating the complete workflow with schema file support."""
    print("=" * 80)
    print("ISRAELI BANKING DATA GENERATOR - COMPLETE WORKFLOW")
    print("=" * 80)
    
    # Configuration
    app_config = {
        'db_url': DATABASE_URL,
        'strategy': 'faker',
        'num_records': 500,
        'schema_source': 'default'
    }
    
    # Show DB folder location
    print(f"\n📁 DB Folder: {DB_FOLDER}")
    print(f"   All files will be stored in this location")
    
    # Initialize generator
    print("\n1. Initializing Generator...")
    generator = IsraeliBankingDataGenerator(
        db_url=app_config['db_url'],
        strategy=app_config['strategy'],
        schema_source=app_config['schema_source']
    )
    
    # Setup
    setup_result = generator.setup()
    if setup_result['status'] != 'success':
        print(f"❌ Setup failed: {setup_result['message']}")
        return False
    
    print("✅ Generator initialized successfully")
    print(f"   Database: {generator.db_url}")
    print(f"   Schemas: {generator.schemas_folder}")
    print(f"   Exports: {generator.exports_folder}")
    
    # Generate database
    print(f"\n2. Generating Database ({app_config['num_records']} records per table)...")
    generation_result = generator.generate_complete_database(app_config['num_records'])
    
    if 'error' in generation_result:
        print(f"❌ Generation failed: {generation_result['message']}")
        return False
    
    print(f"✅ Database generated: {generation_result['total_records']} total records")
    if generation_result.get('database_stats'):
        print(f"   Tables created: {list(generation_result['database_stats'].keys())}")
    
    # Export data
    print("\n3. Exporting Data...")
    export_result = generator.export_data(['csv'])
    
    if 'error' not in export_result:
        for format_name, format_info in export_result.items():
            print(f"✅ {format_name.upper()} Export: {format_info['count']} files created")
            if 'export_dir' in format_info:
                print(f"   Location: {format_info['export_dir']}")
    
    # Generate report
    print("\n4. Generating Report...")
    report = generator.generate_report()
    print(f"✅ Report saved to: {generator.db_folder}/israeli_banking_generation_report.json")
    
    # Summary
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"📁 DB Folder: {DB_FOLDER}")
    print(f"📊 Database: {app_config['db_url']}")
    print(f"📈 Total Records: {generation_result.get('total_records', 'N/A')}")
    
    print(f"\n📂 Generated Files Structure:")
    print(f"   {DB_FOLDER}/")
    print(f"   ├── israeli_banking_data.db           # Database file")
    print(f"   ├── israeli_banking_generation_report.json  # Report")
    print(f"   ├── schemas/                          # Schema files")
    print(f"   │   ├── israeli_banking_swagger.json")
    print(f"   │   └── israeli_banking_definition.json")
    print(f"   ├── exports/                          # Export files")
    print(f"   │   └── csv_data/                     # CSV exports")
    print(f"   └── logs/                             # Log files")
    print(f"       └── database_generation.log")
    
    print("\n🚀 Next Steps:")
    print("   1. Install DBeaver to explore your database")
    print(f"   2. Open database file: {generator.db_url}")
    print(f"   3. Check exports in: {generator.exports_folder}")
    print(f"   4. Review logs in: {generator.logs_folder}")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Israeli Banking Data Generator')
    parser.add_argument('--records', type=int, default=500, help='Number of records per table')
    parser.add_argument('--db-url', type=str, default=DATABASE_URL, help='Database URL')
    parser.add_argument('--strategy', type=str, default='faker', choices=['faker'], help='Generation strategy')
    parser.add_argument('--schema-source', type=str, default='default', 
                       help='Schema source: "default", "swagger", "definition", or file path')
    parser.add_argument('--create-schemas', action='store_true', help='Create default schema files only')
    parser.add_argument('--list-schemas', action='store_true', help='List available schema files')
    
    args = parser.parse_args()
    
    if args.create_schemas:
        # Create default schema files
        success = create_schema_files_only()
        sys.exit(0 if success else 1)
    
    elif args.list_schemas:
        # List available schema files
        list_available_schemas()
        sys.exit(0)
    
    else:
        # Run the main workflow
        try:
            generator = IsraeliBankingDataGenerator(
                db_url=args.db_url,
                strategy=args.strategy,
                schema_source=args.schema_source
            )
            
            # Setup
            setup_result = generator.setup()
            if setup_result['status'] != 'success':
                print(f"❌ Setup failed: {setup_result['message']}")
                sys.exit(1)
            
            # Generate
            generation_result = generator.generate_complete_database(args.records)
            if 'error' in generation_result:
                print(f"❌ Generation failed: {generation_result['message']}")
                sys.exit(1)
            
            print("✅ Generation completed successfully!")
            print(f"Database: {args.db_url}")
            print(f"Records: {generation_result.get('total_records', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)