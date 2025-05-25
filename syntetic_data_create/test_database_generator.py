# test_database_generator.py

"""
Comprehensive test suite for the database generator and integration functionality.
Includes unit tests, integration tests, and performance tests.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime
import json
from sqlalchemy import create_engine, inspect, text



from .database_generator import ISRAELI_CREDIT_CARD_SCHEMA, DatabaseGenerator, FakerSQLAlchemyStrategy, create_generator
from .swagger_db_integration import EnhancedSwaggerSchemaGenerator, DatabaseTestSuite
from .schema_manager import SchemaManager

class TestFakerSQLAlchemyStrategy(unittest.TestCase):
    """Test the Faker + SQLAlchemy strategy."""
    
    def setUp(self):
        self.strategy = FakerSQLAlchemyStrategy(locale='he_IL')
        self.test_schema = {
            'test_table': {
                'fields': {
                    'תעודת_זהות': {'type': 'string', 'constraints': {'max_length': 9}},
                    'שם_פרטי': {'type': 'string', 'constraints': {'max_length': 50}},
                    'גיל': {'type': 'integer', 'constraints': {'min': 18, 'max': 120}},
                    'יתרה': {'type': 'float', 'constraints': {'min': 0, 'max': 100000}},
                    'תאריך_יצירה': {'type': 'date'},
                    'פעיל': {'type': 'boolean'},
                    'סטטוס': {'type': 'choice', 'constraints': {'choices': ['פעיל', 'לא פעיל']}}
                }
            }
        }
    
    def test_strategy_name(self):
        """Test strategy name."""
        self.assertEqual(self.strategy.get_name(), "Faker + SQLAlchemy")
    
    def test_israeli_id_generation(self):
        """Test Israeli ID generation."""
        israeli_id = self.strategy._generate_israeli_id()
        self.assertEqual(len(israeli_id), 9)
        self.assertTrue(israeli_id.isdigit())
        
        # Test that different calls generate different IDs
        israeli_id2 = self.strategy._generate_israeli_id()
        self.assertNotEqual(israeli_id, israeli_id2)
    
    def test_credit_card_generation(self):
        """Test credit card number generation."""
        card_number = self.strategy._generate_credit_card_number()
        self.assertIsInstance(card_number, str)
        self.assertTrue(len(card_number) >= 13)  # Minimum credit card length
    
    def test_phone_number_generation(self):
        """Test Israeli phone number generation."""
        phone = self.strategy._generate_phone_number()
        self.assertTrue(phone.startswith(('050', '052', '053', '054', '055', '057', '058')))
        self.assertIn('-', phone)
    
    def test_data_generation(self):
        """Test data generation with schema."""
        data = self.strategy.generate_data(self.test_schema, num_records=10)
        
        # Check structure
        self.assertIn('test_table', data)
        self.assertEqual(len(data['test_table']), 10)
        
        # Check field types and constraints
        for record in data['test_table']:
            self.assertIn('תעודת_זהות', record)
            self.assertIn('שם_פרטי', record)
            self.assertIn('גיל', record)
            self.assertIn('יתרה', record)
            self.assertIn('תאריך_יצירה', record)
            self.assertIn('פעיל', record)
            self.assertIn('סטטוס', record)
            
            # Test constraints
            self.assertTrue(18 <= record['גיל'] <= 120)
            self.assertTrue(0 <= record['יתרה'] <= 100000)
            self.assertIn(record['סטטוס'], ['פעיל', 'לא פעיל'])
            self.assertIsInstance(record['פעיל'], bool)


class TestDatabaseGenerator(unittest.TestCase):
    """Test the main DatabaseGenerator class."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        self.generator = create_generator('faker', db_url=self.db_url)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_connection(self):
        """Test database connection setup."""
        self.assertIsNotNone(self.generator.engine)
        self.assertIsNotNone(self.generator.Session)
    
    def test_generate_and_store(self):
        """Test data generation and storage."""
        result = self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=50)
        
        # Check results
        self.assertEqual(result['records_generated'], 50)
        self.assertEqual(result['strategy'], "Faker + SQLAlchemy")
        self.assertIn('credit_cards', result['tables_created'])
        self.assertIn('transactions', result['tables_created'])
        
        # Verify data was actually stored
        stats = self.generator.get_table_stats()
        self.assertGreater(stats['credit_cards']['record_count'], 0)
        self.assertGreater(stats['transactions']['record_count'], 0)
    
    def test_table_stats(self):
        """Test table statistics functionality."""
        # Generate some data first
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=25)
        
        stats = self.generator.get_table_stats()
        
        # Check stats structure
        self.assertIn('credit_cards', stats)
        self.assertIn('transactions', stats)
        
        for table_name, table_stats in stats.items():
            self.assertIn('record_count', table_stats)
            self.assertIn('columns', table_stats)
            self.assertGreater(table_stats['record_count'], 0)
    
    def test_csv_export(self):
        """Test CSV export functionality."""
        # Generate data
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=20)
        
        # Export to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = self.generator.export_to_csv(temp_dir)
            
            # Check that files were created
            self.assertGreater(len(exported_files), 0)
            
            for table_name, file_path in exported_files.items():
                self.assertTrue(os.path.exists(file_path))
                
                # Check that CSV contains data
                df = pd.read_csv(file_path)
                self.assertGreater(len(df), 0)

    def test_export_data_multiple_formats(self):
        """Test exporting data in multiple formats."""
        # Generate data first
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=20)
        
        # Export in multiple formats
        with tempfile.TemporaryDirectory() as temp_dir:
            export_formats = ['csv', 'json', 'excel']
            results = self.generator.export_data(export_formats, temp_dir)
            
            # Check results structure
            for format_name in export_formats:
                self.assertIn(format_name, results)
                self.assertIn('location', results[format_name])
                self.assertIn('files', results[format_name])
                
                # Check that files were created
                for table_name, file_path in results[format_name]['files'].items():
                    self.assertTrue(os.path.exists(file_path))
                    
                    # Verify file contents based on format
                    if format_name == 'csv':
                        df = pd.read_csv(file_path)
                    elif format_name == 'json':
                        df = pd.read_json(file_path)
                    elif format_name == 'excel':
                        df = pd.read_excel(file_path)
                    
                    self.assertGreater(len(df), 0)

    def test_export_data_single_format(self):
        """Test exporting data in a single format."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=20)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with string input instead of list
            results = self.generator.export_data('csv', temp_dir)
            
            self.assertIn('csv', results)
            self.assertIn('location', results['csv'])
            self.assertIn('files', results['csv'])

    def test_export_to_csv_backward_compatibility(self):
        """Test that export_to_csv maintains backward compatibility."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=20)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = self.generator.export_to_csv(temp_dir)
            
            # Check old format is maintained
            self.assertIsInstance(exported_files, dict)
            for table_name, file_path in exported_files.items():
                self.assertTrue(os.path.exists(file_path))
                df = pd.read_csv(file_path)
                self.assertGreater(len(df), 0)

    def test_sql_export(self):
        """Test SQL file generation functionality."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=20)
        
        # Export to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.generator.export_data(['sql'], temp_dir)
            
            # Check that export was successful
            self.assertIn('sql', result)
            self.assertIn('files', result['sql'])
            self.assertIn('location', result['sql'])
            
            # Check that files were created
            sql_files = result['sql']['files']
            for table_name, file_path in sql_files.items():
                self.assertTrue(os.path.exists(file_path),
                              f"SQL file not found for table {table_name}")
                
                # Check file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.assertIn('CREATE TABLE', content)
                    self.assertIn('INSERT INTO', content)

    def test_schema_table_conversion(self):
        """Test that all tables from schema are properly converted and generated."""
        # Define a test schema with multiple tables
        test_schema = {
            'users': {
                'fields': {
                    'id': {'type': 'integer', 'constraints': {'primary_key': True, 'autoincrement': True}},
                    'first_name': {'type': 'string', 'constraints': {'max_length': 50}},
                    'last_name': {'type': 'string', 'constraints': {'max_length': 50}},
                    'email': {'type': 'string', 'constraints': {'max_length': 100}}
                }
            },
            'orders': {
                'fields': {
                    'id': {'type': 'integer', 'constraints': {'primary_key': True, 'autoincrement': True}},
                    'user_id': {'type': 'integer', 'constraints': {'foreign_key': 'users.id'}},
                    'order_date': {'type': 'date'},
                    'total_amount': {'type': 'float'}
                }
            },
            'products': {
                'fields': {
                    'id': {'type': 'integer', 'constraints': {'primary_key': True, 'autoincrement': True}},
                    'name': {'type': 'string', 'constraints': {'max_length': 100}},
                    'price': {'type': 'float'},
                    'description': {'type': 'string', 'constraints': {'max_length': 500}}
                }
            }
        }
        
        # Generate database with test schema
        self.generator.generate_and_store(test_schema, num_records=10)
        
        # Connect to database and verify schema
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        try:
            # Check users table
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            column_names = {col[1] for col in columns}  # Get column names
            expected_names = {'id', 'first_name', 'last_name', 'email'}
            self.assertEqual(column_names, expected_names,
                           f"Mismatch in columns for table users")
            
            # Check orders table
            cursor.execute("PRAGMA table_info(orders)")
            columns = cursor.fetchall()
            column_names = {col[1] for col in columns}
            expected_names = {'id', 'user_id', 'order_date', 'total_amount'}
            self.assertEqual(column_names, expected_names,
                           f"Mismatch in columns for table orders")
            
            # Check products table
            cursor.execute("PRAGMA table_info(products)")
            columns = cursor.fetchall()
            column_names = {col[1] for col in columns}
            expected_names = {'id', 'name', 'price', 'description'}
            self.assertEqual(column_names, expected_names,
                           f"Mismatch in columns for table products")
            
        finally:
            cursor.close()
            conn.close()


class TestEnhancedSwaggerSchemaGenerator(unittest.TestCase):
    """Test the enhanced Swagger schema generator with database integration."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        
        self.temp_cache = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        self.temp_cache.close()
        
        self.generator = EnhancedSwaggerSchemaGenerator(
            db_url=self.db_url,
            data_storage_path=self.temp_cache.name
        )
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        if os.path.exists(self.temp_cache.name):
            os.unlink(self.temp_cache.name)
    
    def test_schema_conversion(self):
        """Test Swagger to database schema conversion."""
        db_schema = self.generator.create_database_schema_from_swagger()
        
        # Check that required tables are present
        expected_tables = ['users', 'accounts', 'credit_cards', 'transactions']
        for table in expected_tables:
            self.assertIn(table, db_schema)
        
        # Check table structure
        users_table = db_schema['users']
        self.assertIn('fields', users_table)
        self.assertIn('תעודת_זהות', users_table['fields'])
        self.assertIn('שם_פרטי', users_table['fields'])
    
    def test_database_generation(self):
        """Test full database generation."""
        result = self.generator.generate_database(num_records=30, strategy='faker')
        
        # Check results
        self.assertEqual(result['records_generated'], 30)
        self.assertIn('database_url', result)
        self.assertIn('tables_created', result)
        self.assertIn('db_schema', result)
        
        # Verify database connection is established
        connection = self.generator.get_database_connection()
        self.assertIsNotNone(connection)
    
    def test_query_functionality(self):
        """Test database query functionality."""
        # Generate test data
        self.generator.generate_database(num_records=20)
        
        # Test basic query
        result = self.generator.query_generated_data("SELECT COUNT(*) as count FROM users")
        row = result.fetchone()
        self.assertEqual(row.count, 20)
        
        # Test more complex query
        result = self.generator.query_generated_data(
            "SELECT * FROM users WHERE תעודת_זהות IS NOT NULL LIMIT 5"
        )
        rows = result.fetchall()
        self.assertGreater(len(rows), 0)
        self.assertLessEqual(len(rows), 5)
    
    def test_integration_with_tools(self):
        """Test integration with existing credit card tools."""
        # Generate database
        self.generator.generate_database(num_records=15, strategy='faker')
        
        # Get a user for testing
        users = self.generator.get_table_sample('users', limit=1)
        if users:
            user_id = users[0]['תעודת_זהות']
            
            # Test integration
            integrated_data = self.generator.integrate_with_existing_tools(user_id)
            
            # Check integration results
            required_fields = ['user_id', 'account_id', 'name', 'balance', 'cards', 'transactions']
            for field in required_fields:
                self.assertIn(field, integrated_data)
            
            # Check that data is in expected format
            self.assertIsInstance(integrated_data['cards'], list)
            self.assertIsInstance(integrated_data['transactions'], list)


class TestPerformance(unittest.TestCase):
    """Performance tests for the database generator."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_large_dataset_generation(self):
        """Test generation of larger datasets."""
        generator = create_generator('faker', db_url=self.db_url)
        
        start_time = datetime.now()
        result = generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=1000)
        end_time = datetime.now()
        
        generation_time = (end_time - start_time).total_seconds()
        
        # Check that generation completed successfully
        self.assertEqual(result['records_generated'], 1000)
        
        # Log performance metrics
        print(f"\nPerformance Test Results:")
        print(f"Records generated: {result['records_generated']}")
        print(f"Tables created: {len(result['tables_created'])}")
        print(f"Generation time: {generation_time:.2f} seconds")
        print(f"Records per second: {result['records_generated'] / generation_time:.2f}")
        
        # Basic performance assertion (should generate at least 100 records per second)
        self.assertGreater(result['records_generated'] / generation_time, 100)
    
    def test_memory_usage(self):
        """Test memory usage during generation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        generator = create_generator('faker', db_url=self.db_url)
        generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=2000)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\nMemory Usage Test:")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Memory increase should be reasonable (less than 100MB for 2000 records)
        self.assertLess(memory_increase, 100)


class TestDataQuality(unittest.TestCase):
    """Test data quality and constraints."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        self.generator = create_generator('faker', db_url=self.db_url)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def _is_valid_israeli_id(self, id_num: str) -> bool:
        """Validate Israeli ID number using the Luhn algorithm."""
        if not id_num.isdigit() or len(id_num) != 9:
            return False
        
        # Calculate check digit
        total = 0
        for i, digit in enumerate(id_num[:-1]):
            num = int(digit)
            if i % 2 == 0:
                total += num
            else:
                doubled = num * 2
                total += doubled if doubled < 10 else doubled - 9
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(id_num[-1])
    
    def test_israeli_id_validity(self):
        """Test that generated Israeli IDs are valid."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=100)
        
        # Connect to database and check IDs
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id_number FROM credit_cards LIMIT 10")
            ids = cursor.fetchall()
            for id_num in ids:
                self.assertTrue(self._is_valid_israeli_id(id_num[0]))
        finally:
            cursor.close()
            conn.close()

    def test_data_uniqueness(self):
        """Test that generated data has appropriate uniqueness."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=100)
        
        # Connect to database and check uniqueness
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        try:
            # Check ID uniqueness
            cursor.execute("SELECT COUNT(DISTINCT id_number) as unique_ids, COUNT(*) as total FROM credit_cards")
            unique_ids, total = cursor.fetchone()
            self.assertEqual(unique_ids, total, "Duplicate IDs found")
            
            # Check email uniqueness
            cursor.execute("SELECT COUNT(DISTINCT email) as unique_emails, COUNT(*) as total FROM users")
            unique_emails, total = cursor.fetchone()
            self.assertEqual(unique_emails, total, "Duplicate emails found")
            
            # Check phone number uniqueness
            cursor.execute("SELECT COUNT(DISTINCT phone) as unique_phones, COUNT(*) as total FROM users")
            unique_phones, total = cursor.fetchone()
            self.assertEqual(unique_phones, total, "Duplicate phone numbers found")
        finally:
            cursor.close()
            conn.close()

    def test_data_ranges(self):
        """Test that generated data falls within expected ranges."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=100)
        
        # Connect to database and check ranges
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        try:
            # Check credit limit range
            cursor.execute("SELECT MIN(credit_limit) as min_limit, MAX(credit_limit) as max_limit FROM credit_cards")
            min_limit, max_limit = cursor.fetchone()
            self.assertGreaterEqual(min_limit, 1000, "Credit limit too low")
            self.assertLessEqual(max_limit, 100000, "Credit limit too high")
            
            # Check transaction amounts
            cursor.execute("SELECT MIN(amount) as min_amount, MAX(amount) as max_amount FROM transactions")
            min_amount, max_amount = cursor.fetchone()
            self.assertGreaterEqual(min_amount, 0, "Transaction amount cannot be negative")
            self.assertLessEqual(max_amount, 50000, "Transaction amount too high")
            
            # Check phone number format
            cursor.execute("SELECT phone FROM users LIMIT 10")
            phones = cursor.fetchall()
            for phone in phones:
                # Remove any hyphens or spaces from phone number
                clean_phone = phone[0].replace('-', '').replace(' ', '')
                self.assertTrue(clean_phone.startswith(('02', '03', '04', '08', '09', '050', '052', '053', '054', '055', '058')),
                              f"Invalid phone number format: {phone[0]}")
                self.assertTrue(len(clean_phone) >= 9 and len(clean_phone) <= 10,
                              f"Invalid phone number length: {phone[0]}")
        finally:
            cursor.close()
            conn.close()
    
    def test_hebrew_text_quality(self):
        """Test that Hebrew text fields contain appropriate content."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=100)
        
        # Connect to database and check content
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        try:
            # Check first and last names
            cursor.execute("SELECT first_name, last_name FROM users LIMIT 5")
            names = cursor.fetchall()
            for first_name, last_name in names:
                # Check that names contain Hebrew characters
                self.assertTrue(any(ord('\u0590') <= ord(c) <= ord('\u05FF') for c in first_name),
                              f"First name {first_name} doesn't contain Hebrew characters")
                self.assertTrue(any(ord('\u0590') <= ord(c) <= ord('\u05FF') for c in last_name),
                              f"Last name {last_name} doesn't contain Hebrew characters")
            
            # Check addresses
            cursor.execute("SELECT address FROM users LIMIT 5")
            addresses = cursor.fetchall()
            for address in addresses:
                self.assertTrue(any(ord('\u0590') <= ord(c) <= ord('\u05FF') for c in address[0]),
                              f"Address {address[0]} doesn't contain Hebrew characters")
        finally:
            cursor.close()
            conn.close()

    def test_unique_values(self):
        """Test that certain fields have unique values."""
        # Generate data
        schema = {
            'accounts': {
                'fields': {
                    'מספר_חשבון': {'type': 'string'},
                    'תעודת_זהות': {'type': 'string'},
                }
            }
        }
        
        strategy = FakerSQLAlchemyStrategy()
        data = strategy.generate_data(schema, num_records=1000)
        
        # Check account numbers are unique
        account_numbers = [record['מספר_חשבון'] for record in data['accounts']]
        self.assertEqual(len(account_numbers), len(set(account_numbers)), "Account numbers should be unique")
        
        # Check IDs are unique
        ids = [record['תעודת_זהות'] for record in data['accounts']]
        self.assertEqual(len(ids), len(set(ids)), "IDs should be unique")

    def test_israeli_id_validation(self):
        """Test that generated Israeli IDs are valid."""
        self.generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=100)
        
        # Connect to database and check IDs
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id_number FROM users")
            ids = cursor.fetchall()
            for id_num in ids:
                self.assertTrue(self._is_valid_israeli_id(id_num[0]))
        finally:
            cursor.close()
            conn.close()


class TestSchemaManager(unittest.TestCase):
    """Test the SchemaManager class."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.schema_manager = SchemaManager(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_definition_to_db_schema_conversion(self):
        """Test that all tables from definition schema are properly converted."""
        # Test definition schema with multiple tables and relationships
        definition_schema = {
            "schema_info": {
                "name": "Test Schema",
                "version": "1.0.0",
                "locale": "he_IL"
            },
            "tables": {
                "customers": {
                    "description": "Customer information",
                    "primary_key": "customer_id",
                    "fields": {
                        "customer_id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "created_at": {"type": "datetime"}
                    }
                },
                "orders": {
                    "description": "Order information",
                    "primary_key": "order_id",
                    "fields": {
                        "order_id": {"type": "integer"},
                        "customer_id": {"type": "integer"},
                        "total": {"type": "float"},
                        "order_date": {"type": "datetime"}
                    },
                    "foreign_keys": {
                        "customer_id": {"references": "customers.customer_id"}
                    }
                },
                "order_items": {
                    "description": "Order items",
                    "primary_key": "item_id",
                    "fields": {
                        "item_id": {"type": "integer"},
                        "order_id": {"type": "integer"},
                        "product_name": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "price": {"type": "float"},
                        "created_at": {"type": "datetime"}
                    },
                    "foreign_keys": {
                        "order_id": {"references": "orders.order_id"}
                    }
                }
            }
        }
        
        # Convert schema
        db_schema = self.schema_manager._convert_definition_to_db_schema(definition_schema)
        
        # Verify all tables were converted
        expected_tables = {'customers', 'orders', 'order_items'}
        self.assertEqual(set(db_schema.keys()), expected_tables)
        
        # Check table structure preservation
        for table_name, table_def in definition_schema['tables'].items():
            converted_table = db_schema[table_name]
            
            # Check fields were preserved
            self.assertEqual(
                set(converted_table['fields'].keys()),
                set(table_def['fields'].keys())
            )
            
            # Check metadata was preserved
            self.assertEqual(
                converted_table['metadata']['description'],
                table_def['description']
            )
            self.assertEqual(
                converted_table['metadata']['primary_key'],
                table_def['primary_key']
            )
            
            # Check foreign keys if present
            if 'foreign_keys' in table_def:
                self.assertEqual(
                    converted_table['metadata']['foreign_keys'],
                    table_def['foreign_keys']
                )
            
            # Check datetime fields
            for field_name, field_def in table_def['fields'].items():
                if field_def['type'] == 'datetime':
                    self.assertEqual(
                        converted_table['fields'][field_name]['type'],
                        'datetime'
                    )
    
    def test_generate_database_from_definition(self):
        """Test database generation from definition schema."""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test definition file
            test_definition = {
                "schema_info": {
                    "name": "Test Schema",
                    "version": "1.0.0",
                    "locale": "he_IL"
                },
                "tables": {
                    "departments": {
                        "description": "Department information",
                        "fields": {
                            "id": {"type": "integer", "constraints": {"primary_key": True, "autoincrement": True}},
                            "name": {"type": "string", "constraints": {"max_length": 100}},
                            "location": {"type": "string", "constraints": {"max_length": 200}}
                        }
                    },
                    "employees": {
                        "description": "Employee information",
                        "fields": {
                            "id": {"type": "integer", "constraints": {"primary_key": True, "autoincrement": True}},
                            "department_id": {"type": "integer", "constraints": {"foreign_key": "departments.id"}},
                            "first_name": {"type": "string", "constraints": {"max_length": 50}},
                            "last_name": {"type": "string", "constraints": {"max_length": 50}},
                            "hire_date": {"type": "date"}
                        }
                    }
                }
            }
            
            # Write test definition to file
            definition_path = os.path.join(temp_dir, 'test_definition.json')
            with open(definition_path, 'w', encoding='utf-8') as f:
                json.dump(test_definition, f, indent=2)
            
            # Initialize SchemaManager with temp directory
            schema_manager = SchemaManager(temp_dir)
            
            # Generate database from definition
            db_url = schema_manager.generate_database_from_definition('test_definition.json', num_records=10)
            
            # Verify database was created
            self.assertIsNotNone(db_url)
            self.assertTrue(db_url.startswith('sqlite:///'))
            
            # Export data to verify it was generated correctly
            generator = DatabaseGenerator(db_url)
            with tempfile.TemporaryDirectory() as export_dir:
                result = generator.export_data(['sql'], export_dir)
                
                # Check that export was successful
                self.assertIn('sql', result)
                self.assertIn('files', result['sql'])
                self.assertIn('location', result['sql'])
                
                # Check that files were created
                sql_files = result['sql']['files']
                for table_name, file_path in sql_files.items():
                    self.assertTrue(os.path.exists(file_path),
                                  f"SQL file not found for table {table_name}")
                    
                    # Check file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.assertIn('CREATE TABLE', content)
                        self.assertIn('INSERT INTO', content)


def run_comprehensive_tests():
    """Run all test suites and generate a comprehensive report."""
    import sys
    from io import StringIO
    
    # Capture test output
    test_output = StringIO()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestFakerSQLAlchemyStrategy,
        TestDatabaseGenerator,
        TestEnhancedSwaggerSchemaGenerator,
        TestPerformance,
        TestDataQuality,
        TestSchemaManager
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(stream=test_output, verbosity=2)
    result = runner.run(test_suite)
    
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': f"{((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%",
        'test_output': test_output.getvalue(),
        'successful': len(result.failures) == 0 and len(result.errors) == 0
    }
    
    # Print summary
    print("=" * 60)
    print("COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Failures: {report['failures']}")
    print(f"Errors: {report['errors']}")
    print(f"Success Rate: {report['success_rate']}")
    print(f"Overall Status: {'PASSED' if report['successful'] else 'FAILED'}")
    print("=" * 60)
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback.split('Error:')[-1].strip()}")
    
    return report


def demo_full_workflow():
    """Demonstrate the complete workflow with both strategies."""
    print("=" * 60)
    print("FULL WORKFLOW DEMONSTRATION")
    print("=" * 60)
    
    # Step 1: Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_url = f"sqlite:///{temp_db.name}"
    
    try:
        print(f"\n1. Creating database: {db_url}")
        
        # Step 2: Create enhanced generator
        print("2. Initializing Enhanced Swagger Schema Generator...")
        generator = EnhancedSwaggerSchemaGenerator(db_url=db_url)
        
        # Step 3: Generate database
        print("3. Generating Israeli banking database...")
        result = generator.generate_database(num_records=200, strategy='faker')
        print(f"   Created {len(result['tables_created'])} tables with {result['records_generated']} records each")
        
        # Step 4: Show database statistics
        print("4. Database statistics:")
        stats = generator.get_database_stats()
        for table_name, table_stats in stats.items():
            print(f"   {table_name}: {table_stats['record_count']} records, {len(table_stats['columns'])} columns")
        
        # Step 5: Test integration
        print("5. Testing integration with existing tools...")
        users_sample = generator.get_table_sample('users', limit=1)
        if users_sample:
            user_id = users_sample[0]['תעודת_זהות']
            integrated_data = generator.integrate_with_existing_tools(user_id)
            print(f"   Successfully integrated data for user {user_id}")
            print(f"   User has {len(integrated_data.get('cards', []))} cards and {len(integrated_data.get('transactions', []))} transactions")
        
        # Step 6: Run automated tests
        print("6. Running automated test suite...")
        test_suite = DatabaseTestSuite(generator)
        test_results = test_suite.run_all_tests()
        print(f"   Tests: {test_results['passed']}/{test_results['total_tests']} passed ({test_results['success_rate']})")
        
        # Step 7: Export data
        print("7. Exporting data to CSV...")
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = generator.export_database_to_csv(temp_dir)
            print(f"   Exported {len(exported_files)} CSV files:")
            for table_name, file_path in exported_files.items():
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"     {table_name}.csv ({file_size:.1f} KB)")
        
        # Step 8: Query examples
        print("8. Sample queries:")
        
        # Count users by city
        city_query = """
        SELECT עיר, COUNT(*) as user_count 
        FROM users 
        GROUP BY עיר 
        ORDER BY user_count DESC 
        LIMIT 5
        """
        city_results = generator.query_generated_data(city_query)
        print("   Top cities by user count:")
        for result in city_results:
            print(f"     {result['עיר']}: {result['user_count']} users")
        
        # Average credit limit by card type
        credit_query = """
        SELECT סוג_כרטיס, AVG(מסגרת_אשראי) as avg_limit, COUNT(*) as card_count
        FROM credit_cards 
        GROUP BY סוג_כרטיס 
        ORDER BY avg_limit DESC
        """
        credit_results = generator.query_generated_data(credit_query)
        print("   Average credit limit by card type:")
        for result in credit_results:
            print(f"     {result['סוג_כרטיס']}: ₪{result['avg_limit']:,.0f} ({result['card_count']} cards)")
        
        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        return generator, result, test_results
        
    finally:
        # Cleanup
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)


def test_improved_faker_strategy():
    """Test the improved FakerSQLAlchemyStrategy implementation."""
    # Create schema
    schema = {
        'users': {
            'fields': {
                'תעודת_זהות': {'type': 'string', 'constraints': {'max_length': 9}},
                'שם_פרטי': {'type': 'string', 'constraints': {'max_length': 50}},
                'email': {
                    'type': 'string', 
                    'constraints': {'max_length': 100},
                    'generation': {'generator': 'email'}
                },
                'balance': {
                    'type': 'float',
                    'constraints': {'min': 100, 'max': 10000},
                    'generation': {'decimals': 2}
                }
            }
        }
    }
    
    # Generate data
    strategy = FakerSQLAlchemyStrategy(locale='he_IL')
    data = strategy.generate_data(schema, num_records=3)
    
    # Print result
    for table_name, records in data.items():
        print(f"Table: {table_name}")
        for record in records:
            print(record)

# Run the test
if __name__ == "__main__":
    test_improved_faker_strategy()
    
    exit(0)
# if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run full demonstration
        demo_full_workflow()
    elif len(sys.argv) > 1 and sys.argv[1] == "--performance":
        # Run only performance tests
        suite = unittest.TestSuite()
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPerformance))
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    else:
        # Run comprehensive test suite
        report = run_comprehensive_tests()
        
        # Exit with appropriate code
        sys.exit(0 if report['successful'] else 1)