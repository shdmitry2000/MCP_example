# database_generator.py

"""
Generic Database Generator with multiple implementation strategies.
Currently supports Faker + SQLAlchemy with plans for SDV, Mimesis, and other generators.
"""

import os
import random
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Union
from datetime import datetime, timedelta
from pathlib import Path

# Database imports
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.sqlite import TEXT as SQLiteText

# Data generation imports
from faker import Faker
import pandas as pd

# Configuration
from config.config import config
from syntetic_data_create.data_generator import FieldGeneratorFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class GenerationStrategy(ABC):
    """Abstract base class for different data generation strategies."""
    
    @abstractmethod
    def generate_data(self, schema: Dict[str, Any], num_records: int) -> Dict[str, List[Dict[str, Any]]]:
        """Generate data based on the provided schema."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this generation strategy."""
        pass

class FakerSQLAlchemyStrategy(GenerationStrategy):
    """Faker + SQLAlchemy implementation of data generation."""
    
    def __init__(self, locale: str = 'he_IL'):
        self.fake = Faker(locale)
        self.locale = locale
        self.generator_factory = FieldGeneratorFactory(self.fake, locale)
        
    def get_name(self) -> str:
        return "Faker + SQLAlchemy"
    
    def generate_data(self, schema: Dict[str, Any], num_records: int) -> Dict[str, List[Dict[str, Any]]]:
        """Generate data based on schema using Faker."""
        result = {}
        
        # Process each table in the schema
        for table_name, table_config in schema.items():
            records = []
            fields = table_config.get('fields', {})
            
            # Create generators for each field
            field_generators = {}
            for field_name, field_config in fields.items():
                field_generators[field_name] = self.generator_factory.create_generator(
                    field_name, field_config
                )
            
            # Generate records
            for _ in range(num_records):
                record = {}
                # Generate value for each field
                for field_name, generator in field_generators.items():
                    record[field_name] = generator()
                records.append(record)
            
            result[table_name] = records
        
        return result
    
    
class DatabaseGenerator:
    """Main class for generating databases with different strategies."""
    
    def __init__(self, strategy: GenerationStrategy, db_url: Optional[str] = None):
        self.strategy = strategy
        self.db_folder = Path(config.DB_FOLDER)
        self.db_folder.mkdir(parents=True, exist_ok=True)
        
        # If db_url is provided, use it; otherwise get from config or default
        self.db_url = db_url if db_url else self._get_default_db_url()
        self.engine = None
        self.Session = None
        self._setup_database()
        
    def _get_default_db_url(self) -> str:
        """Get default database URL from config or create SQLite."""
        if hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
            return config.DATABASE_URL
            
        # Create SQLite database in the configured folder
        db_path = self.db_folder / f"{config.DEFAULT_DB_NAME}.db"
        return f"sqlite:///{db_path}"
    
    def _setup_database(self):
        """Setup database connection."""
        try:
            self.engine = create_engine(self.db_url, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"Database connection established: {self.db_url}")
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    def generate_and_store(self, schema: Dict[str, Any], num_records: int = 1000) -> Dict[str, Any]:
        """Generate data and store it in the database."""
        logger.info(f"Generating {num_records} records using {self.strategy.get_name()}")
        
        # Generate data using the strategy
        generated_data = self.strategy.generate_data(schema, num_records)
        
        # Create database tables and store data
        self._create_tables_from_schema(schema)
        self._store_data(generated_data, schema)
        
        return {
            'strategy': self.strategy.get_name(),
            'records_generated': num_records,
            'tables_created': list(schema.keys()),
            'database_url': self.db_url,
            'total_records': sum(len(records) for records in generated_data.values())
        }
    
    def _create_tables_from_schema(self, schema: Dict[str, Any]):
        """Create SQLAlchemy tables from schema definition."""
        # Clear existing table definitions
        Base.metadata.clear()
        
        # Create table classes dynamically
        table_classes = {}
        
        for table_name, table_config in schema.items():
            # Define columns based on schema
            columns = {'__tablename__': table_name}
            
            # Get metadata if available
            metadata = table_config.get('metadata', {})
            primary_key = metadata.get('primary_key')
            
            # Check if any field is marked as primary key in the fields themselves
            fields = table_config.get('fields', {})
            if not primary_key:
                # Look for a field that should be primary key
                for field_name, field_config in fields.items():
                    if field_name.lower() in ['id', 'תעודת_זהות', 'מספר_כרטיס', 'מספר_חשבון']:
                        primary_key = field_name
                        break
            
            # Add auto-incrementing ID if no primary key found
            if not primary_key:
                columns['id'] = Column(Integer, primary_key=True, autoincrement=True)
                logger.info(f"Added auto-increment primary key 'id' to table {table_name}")
            
            # Add fields based on schema
            for field_name, field_config in fields.items():
                field_type = field_config.get('type', 'string')
                constraints = field_config.get('constraints', {})
                
                # Determine if this field is the primary key
                is_primary_key = (field_name == primary_key)
                
                if field_type == 'string':
                    max_length = constraints.get('max_length', 255)
                    if max_length > 1000:
                        columns[field_name] = Column(Text, primary_key=is_primary_key)
                    else:
                        columns[field_name] = Column(String(max_length), primary_key=is_primary_key)
                elif field_type == 'integer':
                    columns[field_name] = Column(Integer, primary_key=is_primary_key, autoincrement=is_primary_key)
                elif field_type == 'float':
                    columns[field_name] = Column(Float, primary_key=is_primary_key)
                elif field_type == 'date':
                    columns[field_name] = Column(Date, primary_key=is_primary_key)
                elif field_type == 'datetime':
                    columns[field_name] = Column(DateTime, primary_key=is_primary_key)
                elif field_type == 'boolean':
                    columns[field_name] = Column(Boolean, primary_key=is_primary_key)
                elif field_type == 'choice':
                    columns[field_name] = Column(String(100), primary_key=is_primary_key)
                else:
                    columns[field_name] = Column(String(255), primary_key=is_primary_key)
            
            # Create the table class
            table_class = type(table_name.capitalize(), (Base,), columns)
            table_classes[table_name] = table_class
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Created {len(table_classes)} tables")
        
        return table_classes
    
    def _store_data(self, data: Dict[str, List[Dict[str, Any]]], schema: Dict[str, Any]):
        """Store generated data in the database."""
        session = self.Session()
        
        try:
            for table_name, records in data.items():
                # Get the table class
                table_class = Base.metadata.tables[table_name]
                
                # Insert records
                for record in records:
                    session.execute(table_class.insert().values(**record))
                
                logger.info(f"Stored {len(records)} records in {table_name}")
            
            session.commit()
            logger.info("All data committed to database")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing data: {e}")
            raise
        finally:
            session.close()
    
    def get_table_stats(self) -> Dict[str, Any]:
        """Get statistics about the generated tables."""
        stats = {}
        session = self.Session()
        
        try:
            # Get all table names
            inspector = sa.inspect(self.engine)
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                # Count records
                result = session.execute(sa.text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                
                # Get table info
                columns = inspector.get_columns(table_name)
                column_info = [{'name': col['name'], 'type': str(col['type'])} for col in columns]
                
                stats[table_name] = {
                    'record_count': count,
                    'columns': column_info
                }
            
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
        finally:
            session.close()
        
        return stats
    
    def export_to_csv(self, output_dir: str = "exported_data") -> Dict[str, str]:
        """Export all tables to CSV files."""
        result = self.export_data(['csv'], output_dir)
        
        # Convert the new format to the old format for backward compatibility
        if 'csv' in result and 'files' in result['csv']:
            return result['csv']['files']
        return {}

    def export_data(self, export_formats: List[str], output_dir: str = "exports") -> Dict[str, Dict[str, str]]:
        """Export data in multiple formats.
        
        Args:
            export_formats: List of formats to export ('csv', 'json', 'excel')
            output_dir: Directory to store exported files
            
        Returns:
            Dictionary with results for each format
        """
        # Ensure export_formats is a list
        if isinstance(export_formats, str):
            export_formats = [export_formats]
            
        # Create export directory inside db_folder
        output_path = Path(self.db_folder) / str(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        session = self.Session()
        
        try:
            inspector = sa.inspect(self.engine)
            table_names = inspector.get_table_names()
            
            for format_name in export_formats:
                format_results = {}
                
                for table_name in table_names:
                    try:
                        # Read data into pandas DataFrame
                        df = pd.read_sql_table(table_name, self.engine)
                        
                        if format_name == 'csv':
                            file_path = output_path / f"{table_name}.csv"
                            df.to_csv(file_path, index=False, encoding='utf-8-sig')
                        elif format_name == 'json':
                            file_path = output_path / f"{table_name}.json"
                            df.to_json(file_path, orient='records', force_ascii=False)
                        elif format_name == 'excel':
                            file_path = output_path / f"{table_name}.xlsx"
                            df.to_excel(file_path, index=False)
                        
                        format_results[table_name] = str(file_path)
                        logger.info(f"Exported {table_name} to {file_path}")
                        
                    except Exception as e:
                        format_results[table_name] = {'error': str(e)}
                        logger.error(f"Error exporting {table_name} to {format_name}: {e}")
                
                results[format_name] = {
                    'location': str(output_path),
                    'files': format_results
                }
        
        except Exception as e:
            logger.error(f"Error during export: {e}")
            results['error'] = str(e)
        finally:
            session.close()
        
        return results

    def generate_database(self, definition_file: str, num_records: int = 1000, db_url: Optional[str] = None) -> Dict[str, Any]:
        """Generate database from definition file."""
        # Update db_url if provided
        if db_url:
            self.db_url = db_url
            self._setup_database()
            
        # Load the schema from the definition file
        with open(definition_file, 'r', encoding='utf-8') as f:
            schema = json.loads(f.read())
            
        # Use the schema's tables section if it exists
        if 'tables' in schema:
            schema = schema['tables']
            
        return self.generate_and_store(schema, num_records)

# Pre-defined schemas for common use cases
ISRAELI_CREDIT_CARD_SCHEMA = {
    'users': {
        'fields': {
            'id_number': {'type': 'string', 'constraints': {'max_length': 9}, 'hebrew_name': 'תעודת_זהות'},
            'first_name': {'type': 'string', 'constraints': {'max_length': 50}, 'hebrew_name': 'שם_פרטי'},
            'last_name': {'type': 'string', 'constraints': {'max_length': 50}, 'hebrew_name': 'שם_משפחה'},
            'address': {'type': 'string', 'constraints': {'max_length': 200}, 'hebrew_name': 'כתובת'},
            'city': {'type': 'string', 'constraints': {'max_length': 50}, 'hebrew_name': 'עיר'},
            'phone': {'type': 'string', 'constraints': {'max_length': 15}, 'hebrew_name': 'טלפון'},
            'email': {'type': 'string', 'constraints': {'max_length': 100}, 'hebrew_name': 'דואר_אלקטרוני'},
            'creation_date': {'type': 'date', 'hebrew_name': 'תאריך_יצירה'},
            'status': {'type': 'choice', 'constraints': {'choices': ['פעיל', 'לא פעיל', 'מושעה']}, 'hebrew_name': 'סטטוס'}
        }
    },
    'accounts': {
        'fields': {
            'account_number': {'type': 'string', 'constraints': {'max_length': 15}, 'hebrew_name': 'מספר_חשבון'},
            'id_number': {'type': 'string', 'constraints': {'max_length': 9}, 'hebrew_name': 'תעודת_זהות'},
            'account_type': {'type': 'choice', 'constraints': {'choices': ['חשבון פרטי', 'חשבון עסקי', 'חשבון חיסכון']}, 'hebrew_name': 'סוג_חשבון'},
            'balance': {'type': 'float', 'constraints': {'min': 0, 'max': 1000000}, 'hebrew_name': 'יתרה'},
            'credit_limit': {'type': 'integer', 'constraints': {'min': 0, 'max': 100000}, 'hebrew_name': 'מסגרת_אשראי'},
            'available_credit': {'type': 'float', 'constraints': {'min': 0, 'max': 100000}, 'hebrew_name': 'אשראי_זמין'},
            'bank_branch': {'type': 'integer', 'constraints': {'min': 1, 'max': 999}, 'hebrew_name': 'סניף_בנק'},
            'opening_date': {'type': 'date', 'hebrew_name': 'תאריך_פתיחה'},
            'status': {'type': 'choice', 'constraints': {'choices': ['פעיל', 'חסום', 'סגור']}, 'hebrew_name': 'סטטוס'}
        }
    },
    'credit_cards': {
        'fields': {
            'card_number': {'type': 'string', 'constraints': {'max_length': 19}, 'hebrew_name': 'מספר_כרטיס'},
            'id_number': {'type': 'string', 'constraints': {'max_length': 9}, 'hebrew_name': 'תעודת_זהות'},
            'card_type': {'type': 'choice', 'constraints': {
                'choices': ['ויזה רגיל', 'ויזה זהב', 'ויזה פלטינום',
                          'מאסטרקארד רגיל', 'מאסטרקארד זהב', 'מאסטרקארד פלטינום',
                          'אמריקן אקספרס', 'ישראכרט', 'דביט רגיל']
            }, 'hebrew_name': 'סוג_כרטיס'},
            'expiry_date': {'type': 'string', 'constraints': {'max_length': 5}, 'hebrew_name': 'תוקף'},
            'credit_limit': {'type': 'integer', 'constraints': {'min': 1000, 'max': 100000}, 'hebrew_name': 'מסגרת_אשראי'},
            'balance': {'type': 'float', 'constraints': {'min': 0, 'max': 100000}, 'hebrew_name': 'יתרה'},
            'last_payments': {'type': 'float', 'constraints': {'min': 0, 'max': 10000}, 'hebrew_name': 'תשלומים_אחרונים'},
            'issue_date': {'type': 'date', 'hebrew_name': 'תאריך_הנפקה'},
            'credit_score': {'type': 'integer', 'constraints': {'min': 300, 'max': 850}, 'hebrew_name': 'דירוג_אשראי'},
            'status': {'type': 'choice', 'constraints': {'choices': ['פעיל', 'חסום', 'מושעה', 'בוטל']}, 'hebrew_name': 'סטטוס'}
        }
    },
    'transactions': {
        'fields': {
            'card_number': {'type': 'string', 'constraints': {'max_length': 19}, 'hebrew_name': 'מספר_כרטיס'},
            'transaction_date': {'type': 'date', 'hebrew_name': 'תאריך_עסקה'},
            'amount': {'type': 'float', 'constraints': {'min': 1, 'max': 10000}, 'hebrew_name': 'סכום'},
            'category': {'type': 'choice', 'constraints': {
                'choices': ['מזון ומשקאות', 'קניות ואופנה', 'בידור ותרבות',
                          'דלק ותחבורה', 'חשמל ומים', 'תקשורת',
                          'בריאות ורפואה', 'חינוך', 'ביטוח', 'אחר']
            }, 'hebrew_name': 'קטגוריה'},
            'business_name': {'type': 'string', 'constraints': {'max_length': 100}, 'hebrew_name': 'שם_עסק'},
            'transaction_type': {'type': 'choice', 'constraints': {'choices': ['רגילה', 'תשלומים', 'קרדיט', 'החזר']}, 'hebrew_name': 'סוג_עסקה'},
            'installments': {'type': 'choice', 'constraints': {'choices': [1, 3, 6, 12, 24, 36]}, 'hebrew_name': 'מספר_תשלומים'},
            'status': {'type': 'choice', 'constraints': {'choices': ['נרשם', 'ממתין', 'מאושר', 'נדחה', 'בוטל']}, 'hebrew_name': 'סטטוס'},
            'description': {'type': 'string', 'constraints': {'max_length': 200}, 'hebrew_name': 'תיאור'}
        }
    }
}

# Factory function to create generators
def create_generator(self, strategy: str = "faker") -> Any:
    """
    Create database generator with specified strategy.
    
    Args:
        strategy: Generation strategy name
        
    Returns:
        Database generator instance
    """
    self.logger.info(f"STEP 3: Creating generator with strategy: {strategy}")
    
    try:
        if not self.db_url:
            raise ValueError("Database URL not prepared. Call prepare_database_url() first.")
        
        # Use the standalone create_generator function (this is the key fix!)
        self.generator = create_generator(strategy, db_url=self.db_url)
        self.logger.info(f"Generator created with strategy: {strategy}")
        
        return self.generator
        
    except Exception as e:
        self.logger.error(f"Failed to create generator: {e}", exc_info=True)
        raise
    
def _create_custom_generator(self, strategy: str):
    """Create a simple generator if importing fails."""
    # This is a fallback in case the import fails
    from sqlalchemy import create_engine
    
    class SimpleGenerator:
        def __init__(self, db_url):
            self.db_url = db_url
            self.engine = create_engine(db_url)
            self.strategy = SimpleStrategy()
            
        def generate_and_store(self, schema, num_records):
            # Implement a simple generation method
            return {
                "strategy": strategy,
                "records_generated": num_records,
                "tables_created": list(schema.keys()),
                "database_url": self.db_url,
                "total_records": num_records * len(schema)
            }
            
        def get_table_stats(self):
            # Simple implementation
            return {}
    
    class SimpleStrategy:
        def get_name(self):
            return f"Simple {strategy}"
            
    return SimpleGenerator(self.db_url)

def create_generator(strategy: str = "faker", db_url: str = None, locale: str = 'he_IL') -> DatabaseGenerator:
    """
    Factory function to create database generators with different strategies.
    
    Args:
        strategy: Generation strategy name ('faker', 'sdv', 'mimesis')
        db_url: Database URL (optional)
        locale: Locale for data generation (default: 'he_IL')
        
    Returns:
        DatabaseGenerator instance
    """
    # Map strategy names to strategy classes
    strategy_mapping = {
        'faker': FakerSQLAlchemyStrategy,
        # Future strategies can be added here:
        # 'sdv': SDVStrategy,
        # 'mimesis': MimesisStrategy,
    }
    
    if strategy not in strategy_mapping:
        raise ValueError(f"Unknown strategy: {strategy}. Available strategies: {list(strategy_mapping.keys())}")
    
    # Create the strategy instance
    strategy_class = strategy_mapping[strategy]
    if strategy == 'faker':
        strategy_instance = strategy_class(locale=locale)
    else:
        strategy_instance = strategy_class()
    
    # Create and return the database generator
    return DatabaseGenerator(strategy_instance, db_url=db_url)


# Example usage and testing
if __name__ == "__main__":
    # Create generator with Faker strategy
    generator = create_generator('faker', locale='he_IL')
    
    # Generate Israeli credit card data
    result = generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=1000)
    
    print("Generation Results:")
    print(f"Strategy: {result['strategy']}")
    print(f"Records Generated: {result['records_generated']}")
    print(f"Tables Created: {result['tables_created']}")
    print(f"Database URL: {result['database_url']}")
    
    # Get statistics
    stats = generator.get_table_stats()
    print("\nTable Statistics:")
    for table_name, table_stats in stats.items():
        print(f"{table_name}: {table_stats['record_count']} records")
    
    # Export to CSV
    exported = generator.export_to_csv()
    print(f"\nExported files: {exported}")




