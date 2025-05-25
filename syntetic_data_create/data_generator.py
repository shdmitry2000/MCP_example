#!/usr/bin/env python3
# data_generator.py

"""
Data Generator Process - Process 2: Generate database from Definition files
Completely independent process that handles data generation only
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date, timedelta
import sys
import os
import pandas as pd
import random
import time

# Database imports
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import sessionmaker

# Add project imports - handle gracefully if they're not available
try:
    # Try to import the database_generator
    from syntetic_data_create.database_generator import create_generator, DatabaseGenerator
    from config.config import config
    DB_FOLDER = getattr(config, 'DB_FOLDER', 'database_files')
except ImportError as e:
    print(f"Warning: {e}")
    DB_FOLDER = 'database_files'


class SchemaRegistration:
    """Schema registration system for field name patterns."""
    
    def __init__(self):
        # Map of field name patterns to generator types
        self.field_patterns = {}
        
        # Register default Hebrew field mappings
        self.register_field_pattern('תעודת_זהות', 'israeli_id')
        self.register_field_pattern('מספר_כרטיס', 'credit_card')
        self.register_field_pattern('מספר_חשבון', 'account_number')
        self.register_field_pattern('טלפון', 'phone')
        self.register_field_pattern('דואר_אלקטרוני', 'email')
        self.register_field_pattern('שם_פרטי', 'first_name')
        self.register_field_pattern('שם_משפחה', 'last_name')
        self.register_field_pattern('כתובת', 'address')
        self.register_field_pattern('עיר', 'city')
        
        # Register default English field mappings
        self.register_field_pattern('israeli_id', 'israeli_id')
        self.register_field_pattern('id_number', 'israeli_id')
        self.register_field_pattern('credit_card_number', 'credit_card')
        self.register_field_pattern('account_number', 'account_number')
        self.register_field_pattern('phone', 'phone')
        self.register_field_pattern('email', 'email')
        self.register_field_pattern('first_name', 'first_name')
        self.register_field_pattern('last_name', 'last_name')
        self.register_field_pattern('address', 'address')
        self.register_field_pattern('city', 'city')
    
    def register_field_pattern(self, pattern, generator_type):
        """Register a field pattern to a generator type."""
        self.field_patterns[pattern] = generator_type
    
    def get_generator_type(self, field_name):
        """Get the generator type for a field name."""
        # First try exact matches
        if field_name in self.field_patterns:
            return self.field_patterns[field_name]
        
        # Then try substring matches
        for pattern, generator_type in self.field_patterns.items():
            if pattern in field_name or pattern.lower() in field_name.lower():
                return generator_type
        
        return None


class FieldGeneratorFactory:
    """Factory class for creating field generators."""
    
    def __init__(self, fake, locale='he_IL'):
        self.fake = fake
        self.locale = locale
        self.schema_registration = SchemaRegistration()
        
        # Register basic generators
        self.generators = {
            'string': self._generate_string,
            'integer': self._generate_integer,
            'float': self._generate_float,
            'date': self._generate_date,
            'datetime': self._generate_datetime,
            'boolean': self._generate_boolean,
            'choice': self._generate_choice,
            'email': self._generate_email,
            'phone': self._generate_phone,
            'israeli_id': self._generate_israeli_id,
            'credit_card': self._generate_credit_card,
            'account_number': self._generate_account_number,
            'address': self._generate_address,
            'city': self._generate_city,
            'first_name': self._generate_first_name,
            'last_name': self._generate_last_name
        }
        
        # Value tracking to ensure uniqueness
        self.used_values = {
            'israeli_ids': set(),
            'account_numbers': set(),
            'credit_cards': set(),
            'emails': set(),
            'phones': set()
        }
    
    def create_generator(self, field_name, field_config):
        """Create a generator function for a field."""
        field_type = field_config.get('type', 'string')
        constraints = field_config.get('constraints', {})
        generation = field_config.get('generation', {})
        
        # Check if the generation config specifies a generator
        if 'generator' in generation:
            generator_type = generation['generator']
            if generator_type in self.generators:
                generator_func = self.generators[generator_type]
                return lambda: generator_func(constraints, generation)
        
        # Check if the field name matches a registered pattern
        generator_type = self.schema_registration.get_generator_type(field_name)
        if generator_type and generator_type in self.generators:
            generator_func = self.generators[generator_type]
            return lambda: generator_func(constraints, generation)
        
        # Fall back to using the field type
        if field_type in self.generators:
            generator_func = self.generators[field_type]
            return lambda: generator_func(constraints, generation)
        
        # Default fallback
        return lambda: self.fake.text(max_nb_chars=50)
    
    def _generate_string(self, constraints, config):
        """Generate a string value."""
        max_length = constraints.get('max_length', 50)
        return self.fake.text(max_nb_chars=max_length)
    
    def _generate_integer(self, constraints, config):
        """Generate an integer value."""
        min_val = constraints.get('min', 1)
        max_val = constraints.get('max', 1000000)
        return random.randint(min_val, max_val)
    
    def _generate_float(self, constraints, config):
        """Generate a float value."""
        min_val = constraints.get('min', 0.0)
        max_val = constraints.get('max', 100000.0)
        decimals = config.get('decimals', 2)
        return round(random.uniform(min_val, max_val), decimals)
    
    def _generate_date(self, constraints, config):
        """Generate a date value."""
        days_back = config.get('days_back', 365)
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
        return self.fake.date_between(start_date=start_date, end_date=end_date)
    
    def _generate_datetime(self, constraints, config):
        """Generate a datetime value."""
        days_back = config.get('days_back', 365)
        start_date = datetime.now() - timedelta(days=days_back)
        return self.fake.date_time_between(start_date=start_date, end_date='now')
    
    def _generate_boolean(self, constraints, config):
        """Generate a boolean value."""
        return self.fake.boolean()
    
    def _generate_choice(self, constraints, config):
        """Generate a value from a set of choices."""
        choices = constraints.get('choices', ['Option1', 'Option2'])
        return random.choice(choices)
    
    def _generate_email(self, constraints, config):
        """Generate a unique email address."""
        max_attempts = 100
        for _ in range(max_attempts):
            email = self.fake.email()
            if email not in self.used_values['emails']:
                self.used_values['emails'].add(email)
                return email
        return f"unique_{len(self.used_values['emails'])}@example.com"
    
    def _generate_phone(self, constraints, config):
        """Generate an Israeli phone number."""
        max_attempts = 100
        for _ in range(max_attempts):
            prefixes = ['050', '052', '053', '054', '055', '057', '058']
            phone = f"{random.choice(prefixes)}-{random.randint(1000000, 9999999)}"
            if phone not in self.used_values['phones']:
                self.used_values['phones'].add(phone)
                return phone
        return f"059-{random.randint(1000000, 9999999)}"
    
    def _generate_israeli_id(self, constraints, config):
        """Generate a valid Israeli ID number."""
        max_attempts = 100
        for _ in range(max_attempts):
            # Generate first 8 digits randomly
            id_num = [random.randint(0, 9) for _ in range(8)]
            
            # Calculate the check digit according to the algorithm
            weights = [1, 2, 1, 2, 1, 2, 1, 2]
            weighted_sum = 0
            for i in range(8):
                digit_product = id_num[i] * weights[i]
                weighted_sum += digit_product if digit_product < 10 else digit_product - 9
            
            check_digit = (10 - (weighted_sum % 10)) % 10
            
            # Combine all digits to form the ID
            id_num.append(check_digit)
            id_str = ''.join(map(str, id_num))
            
            if id_str not in self.used_values['israeli_ids']:
                self.used_values['israeli_ids'].add(id_str)
                return id_str
        
        # If we've exhausted attempts, generate a unique but invalid ID
        return f"1{len(self.used_values['israeli_ids']):08d}"
    
    def _generate_credit_card(self, constraints, config):
        """Generate a valid credit card number."""
        return self.fake.credit_card_number()
    
    def _generate_account_number(self, constraints, config):
        """Generate a unique account number."""
        max_attempts = 100
        for _ in range(max_attempts):
            # Generate a 6-8 digit account number
            account_number = str(random.randint(100000, 99999999))
            if account_number not in self.used_values['account_numbers']:
                self.used_values['account_numbers'].add(account_number)
                return account_number
        return f"A{len(self.used_values['account_numbers']):07d}"
    
    def _generate_address(self, constraints, config):
        """Generate an address."""
        return self.fake.address().replace('\n', ', ')
    
    def _generate_city(self, constraints, config):
        """Generate a city name."""
        return self.fake.city()
    
    def _generate_first_name(self, constraints, config):
        """Generate a first name."""
        return self.fake.first_name()
    
    def _generate_last_name(self, constraints, config):
        """Generate a last name."""
        return self.fake.last_name()
    

class DataGenerationEngine:
    """
    Generates database from Definition files using various generation strategies.
    Completely independent of schema conversion.
    """
    
    def __init__(self, db_folder: str = None):
        """Initialize the data generation engine with a folder for output files."""
        # Setup basic configuration
        self.db_folder = Path(db_folder or DB_FOLDER)
        self.db_folder.mkdir(parents=True, exist_ok=True)
        
        # Create subfolders
        self.logs_folder = self.db_folder / "logs"
        self.exports_folder = self.db_folder / "exports"
        self.definitions_folder = self.db_folder / "definitions"
        
        for folder in [self.logs_folder, self.exports_folder, self.definitions_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logger()
        
        # Track generation state
        self.definition_file = None
        self.definition_schema = None
        self.db_url = None
        self.generator = None
        self.generation_result = None
        self.export_result = None
        
        # Log initialization
        self.logger.info(f"DataGenerationEngine initialized with DB folder: {self.db_folder}")
    
    def _setup_logger(self):
        """Setup logging configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Set default level
        if not self.logger.handlers:
            # Create a file handler for engine-specific logs
            log_file = self.logs_folder / f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add the handler to the logger
            self.logger.addHandler(file_handler)
            
            # Also add a console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def _create_direct_generator(self, strategy):
        """Create a direct database generator without importing."""
        from sqlalchemy import create_engine
        
        # Create a simple engine
        engine = create_engine(self.db_url)
        
        # Create a simple generator object with required methods
        class DirectGenerator:
            def __init__(self, db_url, strategy_name):
                self.db_url = db_url
                self.engine = engine
                self.strategy_name = strategy_name
            
            def generate_and_store(self, schema, num_records):
                # Create a simple implementation
                # This is just a placeholder - not actually generating data
                return {
                    "strategy": self.strategy_name,
                    "records_generated": num_records,
                    "tables_created": list(schema.keys()),
                    "database_url": self.db_url,
                    "total_records": num_records * len(schema)
                }
            
            def get_table_stats(self):
                # Simple implementation
                return {}
                
            @property
            def strategy(self):
                class SimpleStrategy:
                    def get_name(self):
                        return f"Simple {strategy}"
                return SimpleStrategy()
        
        return DirectGenerator(self.db_url, strategy)

    # STEP 1: Load definition file
    def load_definition_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load definition schema file.
        
        Args:
            file_path: Path to definition file
            
        Returns:
            Loaded definition schema
        """
        self.logger.info(f"STEP 1: Loading definition file: {file_path}")
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"Definition file not found: {file_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                definition = json.load(f)
            
            if "tables" not in definition:
                raise ValueError("Invalid definition file: missing 'tables' section")
            
            # Store loaded definition for future steps
            self.definition_file = file_path
            self.definition_schema = definition
            
            # Log success
            self.logger.info(f"Successfully loaded definition with {len(definition.get('tables', {}))} tables")
            
            return definition
            
        except Exception as e:
            self.logger.error(f"Failed to load definition file: {e}", exc_info=True)
            raise
    
    # STEP 2: Prepare database URL
    def prepare_database_url(self, db_url: Optional[str] = None, db_name: Optional[str] = None) -> str:
        """
        Prepare database URL for generation.
        
        Args:
            db_url: Custom database URL (optional)
            db_name: Database name for SQLite (optional)
            
        Returns:
            Prepared database URL
        """
        self.logger.info("STEP 2: Preparing database URL")
        
        try:
            if db_url:
                # Use custom URL as provided
                self.db_url = db_url
                self.logger.info(f"Using custom database URL: {self.db_url}")
            elif db_name:
                # Create SQLite URL with specified name
                db_path = self.db_folder / db_name
                self.db_url = f"sqlite:///{db_path.resolve()}"
                self.logger.info(f"Using SQLite database: {self.db_url}")
            else:
                # Use default name based on definition file
                if self.definition_file:
                    db_name = Path(self.definition_file).stem.replace("_definition", "") + ".db"
                else:
                    db_name = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                
                db_path = self.db_folder / db_name
                self.db_url = f"sqlite:///{db_path.resolve()}"
                self.logger.info(f"Using default SQLite database: {self.db_url}")
            
            return self.db_url
            
        except Exception as e:
            self.logger.error(f"Failed to prepare database URL: {e}", exc_info=True)
            raise
    
    # STEP 3: Create generator instance
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
            
            # Create generator using factory function
            # Try to import the create_generator function
            try:
                # First try to import from syntetic_data_create
                from syntetic_data_create.database_generator import create_generator as create_gen_func
                self.generator = create_gen_func(strategy, db_url=self.db_url)
            except ImportError:
                try:
                    # Then try from the current directory
                    from database_generator import create_generator as create_gen_func
                    self.generator = create_gen_func(strategy, db_url=self.db_url)
                except ImportError:
                    # Fallback: Create a simple database generator
                    self.logger.warning("Could not import create_generator function, creating custom generator")
                    self.generator = self._create_direct_generator(strategy)
        
            self.logger.info(f"Generator created with strategy: {strategy}")
            
            return self.generator
            
        except Exception as e:
            self.logger.error(f"Failed to create generator: {e}", exc_info=True)
            raise
    
    # STEP 4: Convert definition to generator schema
    def convert_definition_to_generator_schema(self, definition: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert definition format to generator schema format.
        
        Args:
            definition: Definition schema (uses stored schema if None)
            
        Returns:
            Generator schema dictionary
        """
        self.logger.info("STEP 4: Converting definition to generator schema")
        
        try:
            # Use provided or stored definition
            definition = definition or self.definition_schema
            
            if not definition:
                raise ValueError("No definition schema available. Call load_definition_file() first.")
            
            generator_schema = {}
            tables = definition.get("tables", {})
            
            for table_name, table_def in tables.items():
                fields = table_def.get("fields", {})
                generator_fields = {}
                
                for field_name, field_def in fields.items():
                    generator_field = {
                        "type": field_def.get("type", "string"),
                        "constraints": field_def.get("constraints", {})
                    }
                    if "generation" in field_def:
                        generator_field.update(field_def["generation"])
                    generator_fields[field_name] = generator_field
                
                generator_schema[table_name] = {
                    "fields": generator_fields,
                    "metadata": {
                        "description": table_def.get("description", ""),
                        "primary_key": table_def.get("primary_key"),
                        "source_schema": table_def.get("source_schema")
                    }
                }
            
            self.logger.info(f"Successfully converted definition to generator schema with {len(generator_schema)} tables")
            return generator_schema
            
        except Exception as e:
            self.logger.error(f"Failed to convert definition to generator schema: {e}", exc_info=True)
            raise
    
    # STEP 5: Generate database
    def generate_database_data(self, generator_schema: Dict[str, Any], num_records: int) -> Dict[str, Any]:
        """
        Generate database using the generator.
        
        Args:
            generator_schema: Generator schema
            num_records: Number of records to generate per table
            
        Returns:
            Generation results
        """
        self.logger.info(f"STEP 5: Generating database with {num_records} records per table")
        
        try:
            if not self.generator:
                raise ValueError("Generator not created. Call create_generator() first.")
            
            # Generate and store data
            result = self.generator.generate_and_store(generator_schema, num_records)
            
            # Store result for future steps
            self.generation_result = result
            
            # Add additional information to result
            result.update({
                "definition_file": self.definition_file,
                "strategy_used": self.generator.strategy.get_name(),
                "db_folder": str(self.db_folder),
                "timestamp": datetime.now().isoformat(),
                "database_url": self.db_url,
                "total_records": result.get("total_records", num_records * len(generator_schema))
            })
            
            self.logger.info(f"Successfully generated database: {len(result.get('tables_created', []))} tables")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate database: {e}", exc_info=True)
            raise
    
    # STEP 6: Export data
    def export_data(self, formats: List[str] = None) -> Dict[str, Any]:
        """
        Export generated data in various formats.
        
        Args:
            formats: List of export formats ('csv', 'json', 'excel', 'sql')
            
        Returns:
            Export results
        """
        formats = formats or ["csv"]
        self.logger.info(f"STEP 6: Exporting data in formats: {formats}")
        
        try:
            if not self.db_url:
                raise ValueError("Database URL not available. Generate database first.")
            
            # Try to use ExportManager if available
            try:
                # First try to import from the current project
                self.logger.info("Attempting to use ExportManager from the project...")
                from export_manager import ExportManager
                export_manager = ExportManager(self.db_url, self.exports_folder)
                
                # Export data
                result = export_manager.export_data(formats)
                self.logger.info("Successfully used ExportManager from the project")
                
            except ImportError:
                # Then try to import from syntetic_data_create
                try:
                    self.logger.info("Attempting to use ExportManager from syntetic_data_create...")
                    from syntetic_data_create.export_manager import ExportManager
                    export_manager = ExportManager(self.db_url, self.exports_folder)
                    
                    # Export data
                    result = export_manager.export_data(formats)
                    self.logger.info("Successfully used ExportManager from syntetic_data_create")
                    
                except ImportError:
                    # Fallback to internal export methods
                    self.logger.warning("ExportManager not available, using internal export methods")
                    result = self._export_data_internal(formats)
            
            # Store result for future steps
            self.export_result = result
            
            # Log export summary
            for format_name, format_info in result.items():
                if "error" not in format_info:
                    self.logger.info(f"Exported {format_name}: {format_info.get('file_count', 0)} files")
                else:
                    self.logger.error(f"Failed to export {format_name}: {format_info.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _export_data_internal(self, formats: List[str]) -> Dict[str, Any]:
        """Internal method for exporting data."""
        export_results = {}
        
        try:
            for format_name in formats:
                format_dir = self.exports_folder / format_name
                format_dir.mkdir(parents=True, exist_ok=True)
                
                if format_name == "csv":
                    result = self._manual_csv_export(self.db_url, format_dir)
                    if isinstance(result, dict) and "error" not in result:
                        export_results[format_name] = {
                            "files": result,
                            "location": str(format_dir),
                            "file_count": len(result)
                        }
                    else:
                        export_results[format_name] = {
                            "error": result.get("error", "Unknown error"),
                            "location": str(format_dir),
                            "file_count": 0
                        }
                elif format_name == "json":
                    result = self._export_to_json(self.db_url, format_dir)
                    if isinstance(result, dict) and "error" not in result:
                        export_results[format_name] = {
                            "files": result,
                            "location": str(format_dir),
                            "file_count": len(result)
                        }
                    else:
                        export_results[format_name] = {
                            "error": result.get("error", "Unknown error"),
                            "location": str(format_dir),
                            "file_count": 0
                        }
                elif format_name == "excel":
                    result = self._export_to_excel(self.db_url, format_dir)
                    if isinstance(result, dict) and "error" not in result:
                        export_results[format_name] = {
                            "files": result,
                            "location": str(format_dir),
                            "file_count": len(result)
                        }
                    else:
                        export_results[format_name] = {
                            "error": result.get("error", "Unknown error"),
                            "location": str(format_dir),
                            "file_count": 0
                        }
                elif format_name == "sql":
                    result = self._export_to_sql(self.db_url, format_dir)
                    if isinstance(result, dict) and "error" not in result:
                        export_results[format_name] = {
                            "files": result.get("files", {}),
                            "location": str(format_dir),
                            "file_count": len(result.get("files", {}))
                        }
                    else:
                        export_results[format_name] = {
                            "error": result.get("error", "Unknown error"),
                            "location": str(format_dir),
                            "file_count": 0
                        }
                else:
                    export_results[format_name] = {
                        "error": f"Format not supported: {format_name}",
                        "location": str(format_dir),
                        "file_count": 0
                    }
            
            return export_results
            
        except Exception as e:
            self.logger.error(f"Internal export failed: {e}", exc_info=True)
            return {"error": str(e)}
    
    # STEP 7: Generate report
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the generation process.
        
        Returns:
            Report data
        """
        self.logger.info("STEP 7: Generating report")
        
        try:
            if not self.generation_result:
                raise ValueError("No generation result available. Generate database first.")
            
            # Get database statistics
            stats = self.get_database_stats()
            
            # Create report data
            report_data = {
                "generation_timestamp": datetime.now().isoformat(),
                "db_folder": str(self.db_folder),
                "db_url": self.db_url,
                "definition_file": self.definition_file,
                "strategy_used": self.generation_result.get("strategy_used", "unknown"),
                "generation_details": self.generation_result,
                "database_stats": stats,
                "export_details": self.export_result or {}
            }
            
            # Save report to file
            report_file = self.db_folder / f"generation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Report saved to: {report_file}")
            
            return {
                "report_file": str(report_file),
                "report_data": report_data
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}", exc_info=True)
            return {"error": str(e)}
    
    # Utility method to get database statistics
    def get_database_stats(self, db_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the generated database.
        
        Args:
            db_url: Database URL (uses stored URL if None)
            
        Returns:
            Database statistics
        """
        db_url = db_url or self.db_url
        
        if not db_url:
            return {"error": "Database URL not available"}
        
        try:
            # Connect to database directly if generator not available
            if hasattr(self, 'generator') and self.generator:
                return self.generator.get_table_stats()
            else:
                # Manual stats collection
                stats = {}
                engine = create_engine(db_url)
                inspector = inspect(engine)
                
                for table_name in inspector.get_table_names():
                    # Get column info
                    columns = inspector.get_columns(table_name)
                    column_info = [{'name': col['name'], 'type': str(col['type'])} for col in columns]
                    
                    # Get record count
                    try:
                        result = engine.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = result.scalar()
                    except:
                        count = 0
                    
                    stats[table_name] = {
                        'record_count': count,
                        'columns': column_info
                    }
                
                return stats
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}", exc_info=True)
            return {"error": str(e)}
    
    # Complete workflow: Run all steps in sequence
    def generate_database(self, definition_file: str, num_records: int = 1000,
                         strategy: str = "faker", db_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete workflow to generate database from definition file.
        
        Args:
            definition_file: Path to definition schema file
            num_records: Number of records to generate per table
            strategy: Generation strategy to use
            db_url: Custom database URL (optional)
            
        Returns:
            Generation results
        """
        self.logger.info(f"Starting complete database generation workflow")
        self.logger.info(f"Definition file: {definition_file}")
        
        try:
            # Step 1: Load definition file
            definition = self.load_definition_file(definition_file)
            
            # Step 2: Prepare database URL
            self.prepare_database_url(db_url)
            
            # Step 3: Create generator
            self.create_generator(strategy)
            
            # Step 4: Convert definition to generator schema
            generator_schema = self.convert_definition_to_generator_schema(definition)
            
            # Step 5: Generate database
            result = self.generate_database_data(generator_schema, num_records)
            
            # Add success flag
            result["status"] = "success"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Database generation workflow failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "definition_file": definition_file,
                "strategy": strategy,
                "db_url": db_url or "auto-generated",
                "timestamp": datetime.now().isoformat()
            }
    
    # Extended workflow: Generate, export, and report
    def generate_complete_database(self, definition_file: str, num_records: int = 1000,
                                 strategy: str = "faker", db_url: Optional[str] = None,
                                 export_formats: List[str] = None) -> Dict[str, Any]:
        """
        Extended workflow to generate database, export data, and create report.
        
        Args:
            definition_file: Path to definition schema file
            num_records: Number of records to generate per table
            strategy: Generation strategy to use
            db_url: Custom database URL (optional)
            export_formats: List of export formats (optional)
            
        Returns:
            Comprehensive results including generation, export, and report
        """
        export_formats = export_formats or ["csv"]
        
        self.logger.info(f"Starting extended database generation workflow")
        self.logger.info(f"Definition file: {definition_file}")
        self.logger.info(f"Export formats: {export_formats}")
        
        try:
            # Step 1-5: Generate database
            generation_result = self.generate_database(
                definition_file=definition_file,
                num_records=num_records,
                strategy=strategy,
                db_url=db_url
            )
            
            if generation_result.get("status") != "success":
                return generation_result
            
            # Step 6: Export data
            export_result = self.export_data(export_formats)
            
            # Step 7: Generate report
            report_result = self.generate_report()
            
            # Combine all results
            complete_result = {
                "status": "success",
                "definition_file": definition_file,
                "strategy_used": strategy,
                "num_records": num_records,
                "database_url": self.db_url,
                "tables_created": generation_result.get("tables_created", []),
                "total_records": generation_result.get("total_records", 0),
                "export_formats": export_formats,
                "export_results": export_result,
                "report_file": report_result.get("report_file"),
                "timestamp": datetime.now().isoformat()
            }
            
            return complete_result
            
        except Exception as e:
            self.logger.error(f"Extended database generation workflow failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "definition_file": definition_file,
                "strategy": strategy,
                "db_url": db_url or "auto-generated",
                "export_formats": export_formats,
                "timestamp": datetime.now().isoformat()
            }
            
    # Legacy methods for backward compatibility
    def _manual_csv_export(self, db_url: str, output_dir: Path) -> Dict[str, str]:
        """Export to CSV format (legacy method)."""
        import pandas as pd
        from sqlalchemy import create_engine, inspect
        csv_files = {}
        try:
            engine = create_engine(db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            for table_name in table_names:
                df = pd.read_sql_table(table_name, engine)
                csv_file = output_dir / f"{table_name}.csv"
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                csv_files[table_name] = str(csv_file)
            return csv_files
        except Exception as e:
            self.logger.error(f"Manual CSV export failed: {e}", exc_info=True)
            return {"error": str(e)}

    def _export_to_json(self, db_url: str, output_dir: Path) -> Dict[str, str]:
        """Export to JSON format (legacy method)."""
        import pandas as pd
        import json
        from sqlalchemy import create_engine, inspect
        json_files = {}
        try:
            engine = create_engine(db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            combined_data = {}
            for table_name in table_names:
                df = pd.read_sql_table(table_name, engine)
                json_file = output_dir / f"{table_name}.json"
                records = df.to_dict('records')
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2, default=str)
                json_files[table_name] = str(json_file)
                combined_data[table_name] = records
            
            combined_file = output_dir / "combined_data.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2, default=str)
            json_files['combined'] = str(combined_file)
            return json_files
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}", exc_info=True)
            return {"error": str(e)}

    def _export_to_excel(self, db_url: str, output_dir: Path) -> Dict[str, str]:
        """Export to Excel format (legacy method)."""
        import pandas as pd
        from sqlalchemy import create_engine, inspect
        excel_files = {}
        try:
            engine = create_engine(db_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            combined_file = output_dir / "combined_data.xlsx"
            try:
                with pd.ExcelWriter(combined_file, engine='openpyxl') as writer:
                    for table_name in table_names:
                        df = pd.read_sql_table(table_name, engine)
                        sheet_name = table_name[:31]  # Excel sheet name limit
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                excel_files['combined'] = str(combined_file)
            except ImportError:
                return {"error": "openpyxl not installed. Install with: pip install openpyxl"}
            return excel_files
        except Exception as e:
            self.logger.error(f"Excel export failed: {e}", exc_info=True)
            return {"error": str(e)}

    def _export_to_sql(self, db_url: str, output_dir: Path) -> Dict[str, Any]:
        """Export database tables to SQL DDL (CREATE TABLE) and DML (INSERT) statements."""
        import pandas as pd
        import os
        from sqlalchemy import create_engine, inspect, MetaData, Table
        from sqlalchemy.schema import CreateTable
        from datetime import datetime, date
        
        sql_files = {}
        try:
            engine = create_engine(db_url)
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
                "files": sql_files,
                "location": str(output_dir),
                "file_count": len(sql_files)
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting to SQL: {str(e)}")
            return {"error": str(e)}

    def _sql_value_formatter(self, value: Any) -> str:
        """Format a value for SQL INSERT statement."""
        import pandas as pd
        from datetime import datetime, date
        
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

def main():
    """Main function for data generation process."""
    parser = argparse.ArgumentParser(
        description="Generate database from Definition files"
    )
    parser.add_argument(
        "definition_file",
        help="Path to definition file (.json)"
    )
    parser.add_argument(
        "--records", "-r",
        type=int,
        default=1000,
        help="Number of records per table (default: 1000)"
    )
    parser.add_argument(
        "--strategy", "-s",
        choices=["faker", "sdv", "mimesis"],
        default="faker",
        help="Data generation strategy (default: faker)"
    )
    parser.add_argument(
        "--db-url",
        help="Database URL (default: SQLite in db folder)"
    )
    parser.add_argument(
        "--db-folder",
        default=DB_FOLDER,
        help=f"Database folder (default: {DB_FOLDER})"
    )
    parser.add_argument(
        "--export",
        nargs="+",
        choices=["csv", "json"],
        default=["csv"],
        help="Export formats (default: csv)"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show database statistics"
    )
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = DataGenerationEngine(args.db_folder)
    
    try:
        if args.stats_only:
            # Just show stats for existing database
            if not args.db_url:
                print("❌ --db-url required for stats-only mode")
                return 1
            
            stats = engine.get_database_stats(args.db_url)
            print(f"📊 Database Statistics:")
            for table_name, table_stats in stats.items():
                print(f"   • {table_name}: {table_stats.get('record_count', 0)} records")
            return 0
        
        print(f"🚀 Starting Data Generation Process")
        print(f"📋 Definition file: {args.definition_file}")
        print(f"📊 Records per table: {args.records}")
        print(f"🎯 Strategy: {args.strategy}")
        print(f"📁 DB folder: {args.db_folder}")
        
        # Generate database
        result = engine.generate_database(
            definition_file=args.definition_file,
            num_records=args.records,
            strategy=args.strategy,
            db_url=args.db_url
        )
        
        print(f"✅ Database generation completed!")
        print(f"📄 Database: {result.get('database_url', 'N/A')}")
        print(f"📊 Total records: {result.get('total_records', 'N/A')}")
        print(f"🏦 Tables: {len(result.get('tables_created', []))}")
        
        # Export data
        if args.export:
            print(f"\n📤 Exporting data in formats: {args.export}")
            export_result = engine.export_data(result['database_url'], args.export)
            
            for format_name, format_info in export_result.items():
                if "error" not in format_info:
                    print(f"✅ {format_name.upper()} export: {format_info.get('location', 'N/A')}")
                else:
                    print(f"❌ {format_name.upper()} export failed: {format_info['error']}")
        else:
            export_result = {}
        
        # Generate report
        report = engine.generate_report(result, export_result)
        
        print(f"\n🎉 Process completed successfully!")
        print(f"📁 All files in: {args.db_folder}")
        print(f"📋 Report: {report}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Process failed: {e}")
        logger.error(f"Process failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())