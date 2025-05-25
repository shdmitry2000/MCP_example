# Enhanced Database Generator with Dual Naming System
# database_generator_enhanced.py

from typing import Dict, Any, Optional
from syntetic_data_create.database_generator import DatabaseGenerator, ISRAELI_CREDIT_CARD_SCHEMA
from syntetic_data_create.field_mapper import HebrewEnglishFieldMapper


class EnhancedDatabaseGenerator(DatabaseGenerator):
    """Enhanced generator with dual naming support."""
    
    def __init__(self, strategy: GenerationStrategy, db_url: Optional[str] = None, 
                 use_english_columns: bool = True, preserve_hebrew_metadata: bool = True):
        super().__init__(strategy, db_url)
        self.use_english_columns = use_english_columns
        self.preserve_hebrew_metadata = preserve_hebrew_metadata
        self.field_mapper = HebrewEnglishFieldMapper()
    
    def _convert_schema_fields(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema to use English field names while preserving Hebrew metadata."""
        converted_schema = {}
        
        for table_name, table_config in schema.items():
            converted_table = {
                'fields': {},
                'metadata': table_config.get('metadata', {})
            }
            
            # Convert field names
            for field_name, field_config in table_config.get('fields', {}).items():
                if self.use_english_columns:
                    # Use English name for database column
                    english_name = self.field_mapper.get_english_name(field_name)
                    converted_field = field_config.copy()
                    
                    if self.preserve_hebrew_metadata:
                        # Preserve Hebrew name in metadata
                        converted_field['hebrew_name'] = field_name
                        converted_field['display_name'] = self.field_mapper.get_display_name(english_name)
                    
                    converted_table['fields'][english_name] = converted_field
                else:
                    # Keep Hebrew names
                    converted_table['fields'][field_name] = field_config
            
            converted_schema[table_name] = converted_table
        
        return converted_schema
    
    def generate_and_store(self, schema: Dict[str, Any], num_records: int = 1000) -> Dict[str, Any]:
        """Generate and store data with field name conversion."""
        
        # Convert schema field names
        converted_schema = self._convert_schema_fields(schema)
        
        # Generate data using parent method
        result = super().generate_and_store(converted_schema, num_records)
        
        # Add field mapping information to result
        result['field_mappings'] = {
            'hebrew_to_english': self.field_mapper.hebrew_to_english,
            'english_to_hebrew': self.field_mapper.english_to_hebrew,
            'use_english_columns': self.use_english_columns,
            'preserve_hebrew_metadata': self.preserve_hebrew_metadata
        }
        
        return result
    
    def export_with_hebrew_headers(self, output_dir: str = "exported_data", 
                                 use_hebrew_headers: bool = True) -> Dict[str, str]:
        """Export data with option to use Hebrew column headers."""
        
        # First export normally
        exported_files = self.export_to_csv(output_dir)
        
        if use_hebrew_headers and self.use_english_columns:
            # Create Hebrew header versions
            hebrew_files = {}
            
            for table_name, file_path in exported_files.items():
                # Read the CSV
                import pandas as pd
                df = pd.read_csv(file_path)
                
                # Map column names back to Hebrew
                hebrew_columns = {}
                for col in df.columns:
                    hebrew_name = self.field_mapper.get_hebrew_name(col)
                    hebrew_columns[col] = hebrew_name
                
                # Rename columns and save Hebrew version
                hebrew_df = df.rename(columns=hebrew_columns)
                hebrew_file = file_path.replace('.csv', '_hebrew.csv')
                hebrew_df.to_csv(hebrew_file, index=False, encoding='utf-8-sig')
                
                hebrew_files[f"{table_name}_hebrew"] = hebrew_file
            
            # Combine results
            exported_files.update(hebrew_files)
        
        return exported_files
    
    def get_field_info(self, table_name: str) -> Dict[str, Dict[str, str]]:
        """Get comprehensive field information for a table."""
        if not hasattr(self, '_table_field_info'):
            return {}
        
        table_info = {}
        
        # Get database columns
        inspector = sa.inspect(self.engine)
        columns = inspector.get_columns(table_name)
        
        for column in columns:
            col_name = column['name']
            hebrew_name = self.field_mapper.get_hebrew_name(col_name)
            display_name = self.field_mapper.get_display_name(col_name)
            
            table_info[col_name] = {
                'database_name': col_name,
                'hebrew_name': hebrew_name,
                'display_name': display_name,
                'data_type': str(column['type'])
            }
        
        return table_info


# Enhanced factory function
def create_enhanced_generator(strategy: str = "faker", db_url: str = None, 
                            use_english_columns: bool = True,
                            preserve_hebrew_metadata: bool = True,
                            locale: str = 'he_IL') -> EnhancedDatabaseGenerator:
    """
    Create enhanced database generator with dual naming support.
    
    Args:
        strategy: Generation strategy ('faker', 'sdv', etc.)
        db_url: Database URL
        use_english_columns: Use English column names in database
        preserve_hebrew_metadata: Keep Hebrew names in metadata
        locale: Locale for data generation
    
    Returns:
        Enhanced database generator
    """
    strategy_mapping = {
        'faker': FakerSQLAlchemyStrategy,
    }
    
    if strategy not in strategy_mapping:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    strategy_class = strategy_mapping[strategy]
    if strategy == 'faker':
        strategy_instance = strategy_class(locale=locale)
    else:
        strategy_instance = strategy_class()
    
    return EnhancedDatabaseGenerator(
        strategy_instance, 
        db_url=db_url,
        use_english_columns=use_english_columns,
        preserve_hebrew_metadata=preserve_hebrew_metadata
    )


# Usage example
if __name__ == "__main__":
    # Create enhanced generator
    generator = create_enhanced_generator(
        strategy='faker',
        db_url='sqlite:///israeli_banking_enhanced.db',
        use_english_columns=True,  # Database uses English column names
        preserve_hebrew_metadata=True  # Keep Hebrew names in metadata
    )
    
    # Generate data
    result = generator.generate_and_store(ISRAELI_CREDIT_CARD_SCHEMA, num_records=100)
    
    print("Field Mappings:")
    for hebrew, english in result['field_mappings']['hebrew_to_english'].items():
        print(f"  {hebrew} -> {english}")
    
    # Export with both English and Hebrew headers
    exported_files = generator.export_with_hebrew_headers(
        output_dir="dual_language_exports",
        use_hebrew_headers=True
    )
    
    print("\nExported Files:")
    for file_type, file_path in exported_files.items():
        print(f"  {file_type}: {file_path}")
    
    # Get field information
    field_info = generator.get_field_info('users')
    print("\nUsers Table Field Info:")
    for field, info in field_info.items():
        print(f"  {field}: {info}")