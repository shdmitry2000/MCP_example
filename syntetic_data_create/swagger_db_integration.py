# swagger_db_integration.py

"""
Enhanced Swagger Schema Generator with Database Integration
Connects the existing Swagger schema generator with the new database generator
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from syntetic_data_create.database_generator import DatabaseGenerator, FakerSQLAlchemyStrategy, create_generator
from syntetic_data_create.swagger_schema_generator import SwaggerSchemaGenerator
import sqlalchemy as sa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from config.config import config

class EnhancedSwaggerSchemaGenerator(SwaggerSchemaGenerator):
    """
    Enhanced version of SwaggerSchemaGenerator with database integration capabilities.
    """
    
    

    def __init__(self, schema_file_path: str = None, data_storage_path: str = "user_data_cache.pkl", db_url: str = None):
        super().__init__(schema_file_path, data_storage_path)
        self.db_url = db_url or config.DATABASE_URL  # Use config if no URL provided
        self.db_generator = None
        
    def create_database_schema_from_swagger(self) -> Dict[str, Any]:
        """
        Convert Swagger/OpenAPI schema to database schema format.
        
        Returns:
            Database schema dictionary
        """
        db_schema = {}
        
        # Extract schemas from the Swagger definition
        schemas = self.schema.get('components', {}).get('schemas', {})
        
        for schema_name, schema_def in schemas.items():
            # Skip schemas that are not meant to be tables
            if schema_name in ['UserData', 'LastPayment']:  # These are composite objects
                continue
                
            table_name = self._schema_name_to_table_name(schema_name)
            db_schema[table_name] = {
                'fields': self._convert_schema_properties(schema_def.get('properties', {}))
            }
        
        # Add additional tables based on your specific schema
        self._add_custom_tables(db_schema)
        
        return db_schema
    
    def _schema_name_to_table_name(self, schema_name: str) -> str:
        """Convert schema name to table name."""
        name_mapping = {
            'CreditCard': 'credit_cards',
            'Transaction': 'transactions',
            'SavingsProgram': 'savings_programs',
            'SavingsDeposit': 'savings_deposits',
            'TravelInsurance': 'travel_insurance',
            'FrequentFlyer': 'frequent_flyer',
            'FrequentFlyerLastEarned': 'frequent_flyer_earnings',
        }
        return name_mapping.get(schema_name, schema_name.lower())
    
    def _convert_schema_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Swagger properties to database schema fields."""
        fields = {}
        
        for prop_name, prop_def in properties.items():
            field_type = prop_def.get('type', 'string')
            field_format = prop_def.get('format')
            
            # Convert Swagger types to database types
            if field_type == 'string':
                if field_format == 'date':
                    db_type = 'date'
                elif field_format == 'date-time':
                    db_type = 'datetime'
                else:
                    db_type = 'string'
            elif field_type == 'number':
                if field_format == 'float':
                    db_type = 'float'
                else:
                    db_type = 'float'
            elif field_type == 'integer':
                db_type = 'integer'
            elif field_type == 'boolean':
                db_type = 'boolean'
            else:
                db_type = 'string'
            
            # Add constraints based on description and field name
            constraints = self._get_field_constraints(prop_name, prop_def)
            
            fields[prop_name] = {
                'type': db_type,
                'constraints': constraints
            }
        
        return fields
    
    def _get_field_constraints(self, field_name: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """Get field constraints based on field name and definition."""
        constraints = {}
        
        # Set max length for string fields
        if field_def.get('type') == 'string':
            if 'כתובת' in field_name or 'address' in field_name:
                constraints['max_length'] = 200
            elif 'תיאור' in field_name or 'description' in field_name:
                constraints['max_length'] = 500
            elif 'תעודת_זהות' in field_name:
                constraints['max_length'] = 9
            elif 'טלפון' in field_name or 'phone' in field_name:
                constraints['max_length'] = 15
            elif 'מספר_כרטיס' in field_name:
                constraints['max_length'] = 19
            else:
                constraints['max_length'] = 100
        
        # Set ranges for numeric fields
        elif field_def.get('type') in ['number', 'integer']:
            if 'מסגרת_אשראי' in field_name or 'credit_limit' in field_name:
                constraints.update({'min': 5000, 'max': 100000})
            elif 'יתרה' in field_name or 'balance' in field_name:
                constraints.update({'min': 0, 'max': 50000})
            elif 'סכום' in field_name or 'amount' in field_name:
                constraints.update({'min': 10, 'max': 10000})
            elif 'דירוג_אשראי' in field_name:
                constraints.update({'min': 300, 'max': 850})
        
        # Add choices for specific fields
        if 'סוג_כרטיס' in field_name:
            constraints['choices'] = ['ויזה', 'מאסטרקארד', 'אמריקן אקספרס', 'ישראכרט']
        elif 'סטטוס' in field_name and 'status' in field_name:
            constraints['choices'] = ['פעיל', 'חסום', 'מושעה', 'לא פעיל']
        elif 'קטגוריה' in field_name:
            constraints['choices'] = ['מזון', 'קניות', 'בידור', 'דלק', 'חשמל', 'תקשורת']
        
        return constraints
    
    def _add_custom_tables(self, db_schema: Dict[str, Any]):
        """Add custom tables specific to Israeli banking system."""
        # Add users table to link everything together
        db_schema['users'] = {
            'fields': {
                'id': {'type': 'integer', 'constraints': {'primary_key': True, 'autoincrement': True}},
                'תעודת_זהות': {'type': 'string', 'constraints': {'max_length': 9, 'unique': True}},
                'שם_פרטי': {'type': 'string', 'constraints': {'max_length': 50}},
                'שם_משפחה': {'type': 'string', 'constraints': {'max_length': 50}},
                'כתובת': {'type': 'string', 'constraints': {'max_length': 200}},
                'עיר': {'type': 'string', 'constraints': {'max_length': 50}},
                'טלפון': {'type': 'string', 'constraints': {'max_length': 15}},
                'דואר_אלקטרוני': {'type': 'string', 'constraints': {'max_length': 100}},
                'תאריך_יצירה': {'type': 'datetime'},
                'סטטוס': {'type': 'choice', 'constraints': {'choices': ['פעיל', 'לא פעיל', 'מושעה']}}
            }
        }
        
        # Add accounts table
        db_schema['accounts'] = {
            'fields': {
                'id': {'type': 'integer', 'constraints': {'primary_key': True, 'autoincrement': True}},
                'מספר_חשבון': {'type': 'string', 'constraints': {'max_length': 15, 'unique': True}},
                'user_id': {'type': 'integer', 'constraints': {'foreign_key': 'users.id'}},
                'סוג_חשבון': {'type': 'choice', 'constraints': {'choices': ['חשבון פרטי', 'חשבון עסקי']}},
                'יתרה': {'type': 'float', 'constraints': {'min': 0, 'max': 1000000}},
                'מסגרת_אשראי': {'type': 'integer', 'constraints': {'min': 0, 'max': 100000}},
                'אשראי_זמין': {'type': 'float', 'constraints': {'min': 0, 'max': 100000}},
                'סניף_בנק': {'type': 'integer', 'constraints': {'min': 1, 'max': 200}},
                'תאריך_פתיחה': {'type': 'date'},
                'סטטוס': {'type': 'choice', 'constraints': {'choices': ['פעיל', 'חסום', 'סגור']}}
            }
        }
        
        # Add credit cards table
        db_schema['credit_cards'] = {
            'fields': {
                'id': {'type': 'integer', 'constraints': {'primary_key': True, 'autoincrement': True}},
                'מספר_כרטיס': {'type': 'string', 'constraints': {'max_length': 16, 'unique': True}},
                'user_id': {'type': 'integer', 'constraints': {'foreign_key': 'users.id'}},
                'account_id': {'type': 'integer', 'constraints': {'foreign_key': 'accounts.id'}},
                'סוג_כרטיס': {'type': 'choice', 'constraints': {'choices': ['ויזה', 'מאסטרקארד', 'אמריקן אקספרס', 'ישראכרט']}},
                'תוקף': {'type': 'date'},
                'סטטוס': {'type': 'choice', 'constraints': {'choices': ['פעיל', 'חסום', 'מבוטל']}}
            }
        }
        
        # Add transactions table
        db_schema['transactions'] = {
            'fields': {
                'id': {'type': 'integer', 'constraints': {'primary_key': True, 'autoincrement': True}},
                'credit_card_id': {'type': 'integer', 'constraints': {'foreign_key': 'credit_cards.id'}},
                'תאריך_עסקה': {'type': 'datetime'},
                'סכום': {'type': 'float', 'constraints': {'min': -10000, 'max': 10000}},
                'שם_עסק': {'type': 'string', 'constraints': {'max_length': 100}},
                'קטגוריה': {'type': 'choice', 'constraints': {'choices': ['מזון', 'קניות', 'בידור', 'דלק', 'חשמל', 'תקשורת']}},
                'סטטוס': {'type': 'choice', 'constraints': {'choices': ['מאושר', 'בהמתנה', 'נדחה']}}
            }
        }
    
    def generate_database(self, num_records: int = 1000, strategy: str = 'faker') -> Dict[str, Any]:
        """
        Generate a complete database based on the Swagger schema.
        
        Args:
            num_records: Number of records to generate per table
            strategy: Generation strategy to use ('faker', 'sdv', etc.)
            
        Returns:
            Generation results
        """
        logger.info(f"Generating database with {num_records} records using {strategy} strategy")
        
        # Convert Swagger schema to database schema
        db_schema = self.create_database_schema_from_swagger()
        
        # Create database generator
        self.db_generator = create_generator(strategy, db_url=self.db_url)
        
        # Generate and store data
        result = self.db_generator.generate_and_store(db_schema, num_records)
        
        # Store connection info for later use
        result['db_schema'] = db_schema
        result['swagger_schema'] = self.schema
        
        logger.info(f"Database generation completed: {result['database_url']}")
        return result
    
    def get_database_connection(self):
        """Get the database connection from the generator."""
        if self.db_generator:
            return self.db_generator.engine
        return None
    
    def query_generated_data(self, query: Union[str, sa.text]) -> Any:
        """Execute a query on the generated data."""
        if not self.db_generator:
            raise ValueError("Database not generated yet. Call generate_database() first.")
            
        session = self.db_generator.Session()
        try:
            # Convert string query to SQLAlchemy text object if needed
            sql_query = sa.text(query) if isinstance(query, str) else query
            result = session.execute(sql_query)
            return result
        except Exception as e:
            logger.error(f"Query error: {e}")
            raise
        finally:
            session.close()
    
    def get_table_sample(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get a sample of records from a table."""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        result = self.query_generated_data(query)
        return [dict(zip(result.keys(), row)) for row in result]
    
    def export_database_to_csv(self, output_dir: str = "exported_data") -> Dict[str, str]:
        """Export the generated database to CSV files."""
        if not self.db_generator:
            raise ValueError("Database not generated yet. Call generate_database() first.")
        
        return self.db_generator.export_to_csv(output_dir)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the generated database."""
        if not self.db_generator:
            raise ValueError("Database not generated yet. Call generate_database() first.")
        
        return self.db_generator.get_table_stats()
    
    def integrate_with_existing_tools(self, user_id: str) -> Dict[str, Any]:
        """
        Integrate generated database with existing credit card tools.
        Updates the existing user data cache with database-generated data.
        
        Args:
            user_id: User ID to integrate data for
            
        Returns:
            Integration results
        """
        if not self.db_generator:
            raise ValueError("Database not generated yet. Call generate_database() first.")
        
        try:
            # Get user data from database
            user_query = f"SELECT * FROM users WHERE תעודת_זהות = '{user_id}' LIMIT 1"
            user_result = self.query_generated_data(user_query)
            user_data = [dict(zip(user_result.keys(), row)) for row in user_result]
            
            if not user_data:
                logger.warning(f"User {user_id} not found in database, generating new data")
                return self.generate_user_data(user_id)
            
            user_record = user_data[0]
            israeli_id = user_record['תעודת_זהות']
            
            # Get related data
            accounts_query = f"""
                SELECT a.* 
                FROM accounts a
                JOIN users u ON a.user_id = u.id
                WHERE u.תעודת_זהות = '{israeli_id}'
            """
            accounts_result = self.query_generated_data(accounts_query)
            accounts = [dict(zip(accounts_result.keys(), row)) for row in accounts_result]
            
            cards_query = f"""
                SELECT cc.* 
                FROM credit_cards cc
                JOIN users u ON cc.user_id = u.id
                WHERE u.תעודת_זהות = '{israeli_id}'
            """
            cards_result = self.query_generated_data(cards_query)
            cards = [dict(zip(cards_result.keys(), row)) for row in cards_result]
            
            transactions_query = f"""
                SELECT t.* 
                FROM transactions t
                JOIN credit_cards cc ON t.credit_card_id = cc.id
                JOIN users u ON cc.user_id = u.id
                WHERE u.תעודת_זהות = '{israeli_id}'
                ORDER BY t.תאריך_עסקה DESC 
                LIMIT 20
            """
            transactions_result = self.query_generated_data(transactions_query)
            transactions = [dict(zip(transactions_result.keys(), row)) for row in transactions_result]
            
            # Convert to the format expected by the existing tools
            integrated_data = {
                "user_id": user_id,
                "account_id": accounts[0]['מספר_חשבון'] if accounts else f"ACC{user_id}",
                "name": f"{user_record['שם_פרטי']} {user_record['שם_משפחה']}",
                "email": user_record['דואר_אלקטרוני'],
                "balance": accounts[0]['יתרה'] if accounts else 0,
                "available_credit": accounts[0]['אשראי_זמין'] if accounts else 0,
                "cards": [
                    {
                        "type": card['סוג_כרטיס'],
                        "last_four": card['מספר_כרטיס'][-4:],
                        "expiry": card['תוקף'],
                        "status": "פעיל"
                    } for card in cards
                ],
                "transactions": [
                    {
                        "date": str(trans['תאריך_עסקה']),
                        "merchant": trans['שם_עסק'],
                        "amount": trans['סכום'],
                        "status": trans['סטטוס'],
                        "description": f"עסקה ב{trans['שם_עסק']}"
                    } for trans in transactions
                ],
                "account_info": {
                    "account_number": accounts[0]['מספר_חשבון'] if accounts else f"ACC{user_id}",
                    "branch": f"{accounts[0]['סניף_בנק']:03d}" if accounts else "001",
                    "type": accounts[0]['סוג_חשבון'] if accounts else "חשבון פרטי",
                    "status": accounts[0]['סטטוס'] if accounts else "פעיל",
                    "balance": accounts[0]['יתרה'] if accounts else 0,
                    "available_credit": accounts[0]['אשראי_זמין'] if accounts else 0,
                    "currency": "ILS"
                },
                "error": None
            }
            
            # Update the user data cache
            self.user_data_cache[user_id] = integrated_data
            self._save_user_data_cache()
            
            logger.info(f"Successfully integrated database data for user {user_id}")
            return integrated_data
            
        except Exception as e:
            logger.error(f"Error integrating database data: {e}")
            return {"error": f"Integration failed: {str(e)}"}


class DatabaseTestSuite:
    """Test suite for the database generation and integration functionality."""
    
    def __init__(self, generator: EnhancedSwaggerSchemaGenerator):
        self.generator = generator
        self.test_results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        logger.info("Starting database test suite")
        
        tests = [
            self.test_schema_conversion,
            self.test_database_generation,
            self.test_data_integrity,
            self.test_integration_with_tools,
            self.test_query_functionality,
            self.test_export_functionality
        ]
        
        for test in tests:
            try:
                test_name = test.__name__
                logger.info(f"Running test: {test_name}")
                result = test()
                self.test_results[test_name] = {"status": "PASSED", "result": result}
            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}")
                self.test_results[test_name] = {"status": "FAILED", "error": str(e)}
        
        # Summary
        passed = sum(1 for result in self.test_results.values() if result["status"] == "PASSED")
        total = len(self.test_results)
        
        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed/total)*100:.1f}%",
            "test_results": self.test_results
        }
        
        logger.info(f"Test suite completed: {passed}/{total} tests passed")
        return summary
    
    def test_schema_conversion(self) -> Dict[str, Any]:
        """Test Swagger to database schema conversion."""
        db_schema = self.generator.create_database_schema_from_swagger()
        
        # Verify required tables exist
        required_tables = ['users', 'accounts', 'credit_cards', 'transactions']
        for table in required_tables:
            assert table in db_schema, f"Missing required table: {table}"
        
        # Verify table structure
        assert 'fields' in db_schema['users'], "Users table missing fields"
        assert 'תעודת_זהות' in db_schema['users']['fields'], "Users table missing Israeli ID field"
        
        return {
            "tables_created": len(db_schema),
            "table_names": list(db_schema.keys()),
            "sample_table_fields": len(db_schema['users']['fields'])
        }
    
    def test_database_generation(self) -> Dict[str, Any]:
        """Test database generation functionality."""
        result = self.generator.generate_database(num_records=100, strategy='faker')
        
        # Verify generation results
        assert 'database_url' in result, "Missing database URL in results"
        assert 'tables_created' in result, "Missing tables created info"
        assert result['records_generated'] == 100, "Incorrect number of records generated"
        
        return {
            "generation_successful": True,
            "database_url": result['database_url'],
            "tables_created": result['tables_created'],
            "records_per_table": result['records_generated']
        }
    
    def test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and relationships."""
        stats = self.generator.get_database_stats()
        
        integrity_checks = {}
        
        # Check that all tables have data
        for table_name, table_stats in stats.items():
            integrity_checks[f"{table_name}_has_data"] = table_stats['record_count'] > 0
        
        # Check Israeli ID format (should be 9 digits)
        try:
            users_sample = self.generator.get_table_sample('users', limit=5)
            for user in users_sample:
                israeli_id = user.get('תעודת_זהות', '')
                integrity_checks['israeli_id_format'] = len(israeli_id) == 9 and israeli_id.isdigit()
                break  # Just check first user
        except Exception as e:
            integrity_checks['israeli_id_format'] = False
        
        return {
            "table_stats": stats,
            "integrity_checks": integrity_checks,
            "all_checks_passed": all(integrity_checks.values())
        }
    
    def test_integration_with_tools(self) -> Dict[str, Any]:
        """Test integration with existing credit card tools."""
        # Get a sample user from the database
        users_sample = self.generator.get_table_sample('users', limit=1)
        if not users_sample:
            raise ValueError("No users found in database")
        
        user_id = users_sample[0]['תעודת_זהות']
        
        # Test integration
        integrated_data = self.generator.integrate_with_existing_tools(user_id)
        
        # Verify integration results
        required_fields = ['user_id', 'account_id', 'name', 'balance', 'cards', 'transactions']
        for field in required_fields:
            assert field in integrated_data, f"Missing required field in integrated data: {field}"
        
        return {
            "integration_successful": True,
            "user_id": user_id,
            "integrated_fields": list(integrated_data.keys()),
            "cards_count": len(integrated_data['cards']),
            "transactions_count": len(integrated_data['transactions'])
        }
    
    def test_query_functionality(self) -> Dict[str, Any]:
        """Test database query functionality."""
        # Test basic query
        result = self.generator.query_generated_data("SELECT COUNT(*) as count FROM users")
        assert len(result) > 0, "Query returned no results"
        
        user_count = result[0]['count']
        
        # Test more complex query
        complex_query = """
        SELECT u.שם_פרטי, u.שם_משפחה, COUNT(c.מספר_כרטיס) as card_count
        FROM users u
        LEFT JOIN credit_cards c ON u.תעודת_זהות = c.תעודת_זהות
        GROUP BY u.תעודת_זהות, u.שם_פרטי, u.שם_משפחה
        LIMIT 5
        """
        complex_result = self.generator.query_generated_data(complex_query)
        
        return {
            "basic_query_successful": True,
            "user_count": user_count,
            "complex_query_successful": len(complex_result) > 0,
            "sample_complex_result": complex_result[:2] if complex_result else []
        }
    
    def test_export_functionality(self) -> Dict[str, Any]:
        """Test CSV export functionality."""
        export_dir = "test_export"
        exported_files = self.generator.export_database_to_csv(export_dir)
        
        # Verify files were created
        for table_name, file_path in exported_files.items():
            assert os.path.exists(file_path), f"Export file not found: {file_path}"
        
        return {
            "export_successful": True,
            "exported_files": exported_files,
            "files_created": len(exported_files)
        }


# Example usage and main function
def main():
    """Main function demonstrating the enhanced functionality."""
    
    # Initialize enhanced generator
    generator = EnhancedSwaggerSchemaGenerator(
        db_url="sqlite:///israeli_banking_test.db"
    )
    
    print("=== Enhanced Swagger Schema Generator with Database Integration ===")
    print()
    
    # Generate database
    print("1. Generating database...")
    result = generator.generate_database(num_records=500, strategy='faker')
    print(f"   Database created: {result['database_url']}")
    print(f"   Tables: {result['tables_created']}")
    print(f"   Records per table: {result['records_generated']}")
    print()
    
    # Get database statistics
    print("2. Database statistics...")
    stats = generator.get_database_stats()
    for table_name, table_stats in stats.items():
        print(f"   {table_name}: {table_stats['record_count']} records")
    print()
    
    # Test integration
    print("3. Testing integration with existing tools...")
    users_sample = generator.get_table_sample('users', limit=1)
    if users_sample:
        user_id = users_sample[0]['תעודת_זהות']
        integrated_data = generator.integrate_with_existing_tools(user_id)
        print(f"   Integrated data for user {user_id}")
        print(f"   Cards: {len(integrated_data.get('cards', []))}")
        print(f"   Transactions: {len(integrated_data.get('transactions', []))}")
    print()
    
    # Run test suite
    print("4. Running test suite...")
    test_suite = DatabaseTestSuite(generator)
    test_results = test_suite.run_all_tests()
    print(f"   Tests passed: {test_results['passed']}/{test_results['total_tests']}")
    print(f"   Success rate: {test_results['success_rate']}")
    print()
    
    # Export to CSV
    print("5. Exporting to CSV...")
    exported_files = generator.export_database_to_csv("exported_israeli_banking_data")
    print(f"   Exported {len(exported_files)} files:")
    for table_name, file_path in exported_files.items():
        print(f"     {table_name} -> {file_path}")
    print()
    
    print("=== Integration Complete ===")
    return generator, test_results


if __name__ == "__main__":
    generator, results = main()