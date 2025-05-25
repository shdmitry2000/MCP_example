#!/usr/bin/env python3
# schema_converter.py

"""
Schema Converter - Process 1: Convert Swagger files to Definition files
Completely independent process that handles schema conversion only
"""

import json
import yaml
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from syntetic_data_create.field_mapper import HebrewEnglishFieldMapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaConverter:
    """
    Converts Swagger/OpenAPI schemas to standardized Definition format.
    Completely independent of data generation.
    """
    
    def __init__(self):
        self.conversion_log = []
        self.field_mapper = HebrewEnglishFieldMapper()
        
    def load_swagger_file(self, file_path: str) -> Dict[str, Any]:
        """Load Swagger/OpenAPI file (JSON or YAML)."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Swagger file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
        
        logger.info(f"Loaded Swagger schema from: {file_path}")
        return schema
    
    def convert_swagger_to_definition(self, swagger_schema: Dict[str, Any], 
                                    target_system: str = "faker") -> Dict[str, Any]:
        """
        Convert Swagger schema to Definition format.
        
        Args:
            swagger_schema: Loaded Swagger schema
            target_system: Target generation system (faker, sdv, mimesis, etc.)
            
        Returns:
            Definition schema dictionary
        """
        logger.info(f"Converting Swagger schema to definition format for {target_system}")
        
        # Extract basic info
        info = swagger_schema.get("info", {})
        
        definition_schema = {
            "schema_info": {
                "name": info.get("title", "Converted Schema"),
                "version": info.get("version", "1.0.0"),
                "description": info.get("description", "Converted from Swagger schema"),
                "created": datetime.now().isoformat(),
                "locale": "he_IL",
                "source": "swagger_conversion",
                "target_system": target_system
            },
            "tables": {},
            "generation_settings": {
                "target_system": target_system,
                "default_records_per_table": 1000,
                "relationships": {},
                "constraints": {}
            }
        }
        
        # Process components/schemas
        components = swagger_schema.get("components", {})
        schemas = components.get("schemas", {})
        
        for schema_name, schema_def in schemas.items():
            if schema_def.get("type") != "object":
                continue
                
            table_name = self._schema_name_to_table_name(schema_name)
            table_definition = self._convert_schema_to_table(
                schema_name, schema_def, target_system
            )
            
            if table_definition:
                definition_schema["tables"][table_name] = table_definition
                self.conversion_log.append(f"Converted {schema_name} -> {table_name}")
        
        # Add system-specific optimizations
        definition_schema = self._optimize_for_target_system(definition_schema, target_system)
        
        logger.info(f"Conversion completed: {len(definition_schema['tables'])} tables created")
        return definition_schema
    
    def _schema_name_to_table_name(self, schema_name: str) -> str:
        """Convert schema name to table name."""
        name_mapping = {
            'User': 'users',
            'Account': 'accounts',
            'CreditCard': 'credit_cards',
            'Transaction': 'transactions',
            'Customer': 'customers',
            'Product': 'products',
            'Order': 'orders'
        }
        return name_mapping.get(schema_name, schema_name.lower() + 's')
    
    def _convert_schema_to_table(self, schema_name: str, schema_def: Dict[str, Any], 
                               target_system: str) -> Dict[str, Any]:
        """Convert individual schema to table definition."""
        table_def = {
            "description": schema_def.get("description", f"Table for {schema_name}"),
            "source_schema": schema_name,
            "fields": {},
            "constraints": {},
            "relationships": {}
        }
        
        # Process properties
        properties = schema_def.get("properties", {})
        required_fields = schema_def.get("required", [])
        
        # Determine primary key
        primary_key = self._determine_primary_key(properties)
        if primary_key:
            table_def["primary_key"] = primary_key
        
        # Convert each property to field
        for prop_name, prop_def in properties.items():
            # Convert Hebrew field name to English for database
            english_name = self._convert_hebrew_to_english(prop_name)
            
            field_def = self._convert_property_to_field(
                english_name, prop_def, target_system, prop_name in required_fields
            )
            
            # Mark as primary key if this is the primary key field
            if english_name == primary_key:
                field_def["constraints"]["primary_key"] = True
            
            # Preserve Hebrew name in metadata
            field_def['hebrew_name'] = prop_name
            field_def['display_name'] = self._get_display_name(english_name)
            
            table_def["fields"][english_name] = field_def
        
        return table_def
    
    def _determine_primary_key(self, properties: Dict[str, Any]) -> Optional[str]:
        """Determine primary key from properties."""
        # Priority order for primary key detection
        pk_candidates = [
            "תעודת_זהות", "id", "uuid", "מספר_כרטיס", "מספר_חשבון",
            "customer_id", "user_id", "account_number", "card_number"
        ]
        
        for candidate in pk_candidates:
            if candidate in properties:
                return candidate
        
        # Return first field as fallback
        return list(properties.keys())[0] if properties else None
    
    def _convert_property_to_field(self, prop_name: str, prop_def: Dict[str, Any], 
                                 target_system: str, is_required: bool) -> Dict[str, Any]:
        """Convert Swagger property to field definition."""
        field_def = {
            "type": self._map_swagger_type(prop_def.get("type", "string")),
            "description": prop_def.get("description", ""),
            "required": is_required,
            "constraints": {},
            "generation": {}
        }
        
        # Handle constraints
        constraints = {}
        if "maxLength" in prop_def:
            constraints["max_length"] = prop_def["maxLength"]
        if "minLength" in prop_def:
            constraints["min_length"] = prop_def["minLength"]
        if "minimum" in prop_def:
            constraints["min"] = prop_def["minimum"]
        if "maximum" in prop_def:
            constraints["max"] = prop_def["maximum"]
        if "enum" in prop_def:
            field_def["type"] = "choice"
            constraints["choices"] = prop_def["enum"]
        if "pattern" in prop_def:
            constraints["pattern"] = prop_def["pattern"]
        
        if constraints:
            field_def["constraints"] = constraints
        
        # Add generation strategy based on field name and target system
        generation_config = self._get_generation_config(prop_name, prop_def, target_system)
        if generation_config:
            field_def["generation"] = generation_config
        
        return field_def
    
    def _map_swagger_type(self, swagger_type: str) -> str:
        """Map Swagger types to definition types."""
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "number": "float",
            "boolean": "boolean",
            "array": "array",
            "object": "object"
        }
        return type_mapping.get(swagger_type, "string")
    
    def _get_generation_config(self, prop_name: str, prop_def: Dict[str, Any], 
                             target_system: str) -> Dict[str, Any]:
        """Get generation configuration based on target system."""
        config = {}
        
        # Common configurations
        if "תעודת_זהות" in prop_name:
            config["generator"] = "israeli_id"
            config["locale"] = "he_IL"
        elif "טלפון" in prop_name or "phone" in prop_name.lower():
            config["generator"] = "israeli_phone"
        elif "שם_פרטי" in prop_name or "first_name" in prop_name.lower():
            config["generator"] = "hebrew_first_name"
            config["locale"] = "he_IL"
        elif "שם_משפחה" in prop_name or "last_name" in prop_name.lower():
            config["generator"] = "hebrew_last_name"
            config["locale"] = "he_IL"
        elif "כתובת" in prop_name or "address" in prop_name.lower():
            config["generator"] = "hebrew_address"
            config["locale"] = "he_IL"
        elif "מספר_כרטיס" in prop_name or "card_number" in prop_name.lower():
            config["generator"] = "credit_card_number"
        elif prop_def.get("format") == "email":
            config["generator"] = "email"
        elif prop_def.get("format") == "date":
            config["generator"] = "past_date"
        elif prop_def.get("format") == "date-time":
            config["generator"] = "past_datetime"
        
        # System-specific configurations
        if target_system == "sdv":
            config["sdv_options"] = {
                "distribution": "auto",
                "anonymization": "auto" if "sensitive" in prop_name.lower() else "none"
            }
        elif target_system == "mimesis":
            config["mimesis_provider"] = self._get_mimesis_provider(prop_name, prop_def)
        
        return config
    
    def _get_mimesis_provider(self, prop_name: str, prop_def: Dict[str, Any]) -> str:
        """Get Mimesis provider for field."""
        if "name" in prop_name.lower():
            return "person.full_name"
        elif "email" in prop_name.lower():
            return "person.email"
        elif "phone" in prop_name.lower():
            return "person.telephone"
        elif "address" in prop_name.lower():
            return "address.address"
        elif "company" in prop_name.lower():
            return "finance.company"
        else:
            return "text.word"
    
    def _optimize_for_target_system(self, definition_schema: Dict[str, Any], 
                                  target_system: str) -> Dict[str, Any]:
        """Add system-specific optimizations."""
        if target_system == "faker":
            definition_schema["generation_settings"]["faker_options"] = {
                "locale": "he_IL",
                "seed": None,
                "providers": ["faker.providers.bank", "faker.providers.credit_card"]
            }
        elif target_system == "sdv":
            definition_schema["generation_settings"]["sdv_options"] = {
                "model_type": "GaussianCopula",
                "privacy_level": "medium",
                "enforce_relationships": True
            }
        elif target_system == "mimesis":
            definition_schema["generation_settings"]["mimesis_options"] = {
                "locale": "he",
                "seed": None
            }
        
        return definition_schema
    
    def save_definition_file(self, definition_schema: Dict[str, Any], 
                           output_path: str) -> str:
        """Save definition schema to file."""
        output_file = Path(output_path)
        
        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(definition_schema, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Definition schema saved to: {output_file}")
        return str(output_file)
    
    def get_conversion_report(self) -> Dict[str, Any]:
        """Get conversion report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "conversions": self.conversion_log,
            "total_conversions": len(self.conversion_log)
        }
    
    def _convert_hebrew_to_english(self, hebrew_name: str) -> str:
        """Convert Hebrew field name to English."""
        return self.field_mapper.get_english_name(hebrew_name)
    
    def _get_display_name(self, field_name: str) -> str:
        """Generate a human-readable display name from field name."""
        return self.field_mapper.get_display_name(field_name)


def main():
    """Main function for schema conversion process."""
    parser = argparse.ArgumentParser(
        description="Convert Swagger/OpenAPI schemas to Definition format"
    )
    parser.add_argument(
        "swagger_file", 
        nargs='?',  # Make it optional
        help="Path to Swagger/OpenAPI file (.json or .yaml)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output definition file path",
        default=None
    )
    parser.add_argument(
        "--target-system", "-t",
        choices=["faker", "sdv", "mimesis", "custom"],
        default="faker",
        help="Target data generation system"
    )
    parser.add_argument(
        "--output-dir",
        default="db/definitions",
        help="Output directory for definition files"
    )
    parser.add_argument(
        "--create-israeli-banking",
        action="store_true",
        help="Create built-in Israeli banking schema"
    )
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = SchemaConverter()
    
    try:
        if args.create_israeli_banking:
            # Create built-in Israeli banking schema
            print(f"🏦 Creating built-in Israeli banking schema...")
            print(f"🎯 Target system: {args.target_system}")
            
            # Create default Israeli banking Swagger schema
            swagger_schema = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Israeli Banking API",
                    "version": "1.0.0",
                    "description": "Israeli banking system with Hebrew support"
                },
                "components": {
                    "schemas": {
                        "User": {
                            "type": "object",
                            "required": ["תעודת_זהות", "שם_פרטי", "שם_משפחה"],
                            "properties": {
                                "תעודת_זהות": {
                                    "type": "string",
                                    "description": "מספר תעודת זהות ישראלית",
                                    "pattern": "^[0-9]{9}$"
                                },
                                "שם_פרטי": {
                                    "type": "string",
                                    "description": "שם פרטי בעברית",
                                    "maxLength": 50
                                },
                                "שם_משפחה": {
                                    "type": "string",
                                    "description": "שם משפחה בעברית", 
                                    "maxLength": 50
                                },
                                "טלפון": {
                                    "type": "string",
                                    "description": "מספר טלפון ישראלי",
                                    "pattern": "^05[0-9]-[0-9]{7}$"
                                }
                            }
                        },
                        "CreditCard": {
                            "type": "object",
                            "required": ["מספר_כרטיס", "תעודת_זהות", "סוג_כרטיס"],
                            "properties": {
                                "מספר_כרטיס": {
                                    "type": "string",
                                    "description": "מספר כרטיס האשראי",
                                    "maxLength": 19
                                },
                                "תעודת_זהות": {
                                    "type": "string",
                                    "pattern": "^[0-9]{9}$"
                                },
                                "סוג_כרטיס": {
                                    "type": "string",
                                    "enum": ["ויזה", "מאסטרקארד", "ישראכרט"]
                                },
                                "מסגרת_אשראי": {
                                    "type": "integer",
                                    "minimum": 1000,
                                    "maximum": 100000
                                }
                            }
                        }
                    }
                }
            }
            
            # Convert to definition
            definition_schema = converter.convert_swagger_to_definition(swagger_schema, args.target_system)
            
            # Save definition file
            output_path = f"{args.output_dir}/israeli_banking_{args.target_system}_definition.json"
            saved_path = converter.save_definition_file(definition_schema, output_path)
            
            print(f"✅ Israeli banking schema created!")
            print(f"📋 Output: {saved_path}")
            print(f"🎯 Target system: {args.target_system}")
            print(f"📊 Tables: {len(definition_schema['tables'])}")
            
            return 0
        
        elif args.swagger_file:
            # Convert provided Swagger file
            print(f"🔄 Converting Swagger schema: {args.swagger_file}")
            print(f"🎯 Target system: {args.target_system}")
            
            # Load Swagger file
            swagger_schema = converter.load_swagger_file(args.swagger_file)
            
            # Convert to definition
            definition_schema = converter.convert_swagger_to_definition(
                swagger_schema, args.target_system
            )
            
            # Determine output path
            if args.output:
                output_path = args.output
            else:
                swagger_name = Path(args.swagger_file).stem
                output_path = f"{args.output_dir}/{swagger_name}_{args.target_system}_definition.json"
            
            # Save definition file
            saved_path = converter.save_definition_file(definition_schema, output_path)
            
            # Get conversion report
            report = converter.get_conversion_report()
            
            print(f"✅ Conversion completed successfully!")
            print(f"📄 Input: {args.swagger_file}")
            print(f"📋 Output: {saved_path}")
            print(f"📊 Tables converted: {len(definition_schema['tables'])}")
            print(f"🎯 Target system: {args.target_system}")
            
            # Show table summary
            print(f"\n📋 Converted Tables:")
            for table_name, table_def in definition_schema['tables'].items():
                field_count = len(table_def.get('fields', {}))
                pk = table_def.get('primary_key', 'N/A')
                print(f"   • {table_name}: {field_count} fields (PK: {pk})")
            
            print(f"\n🚀 Next step: Use this definition file with data generation process")
            print(f"   python data_generator.py {saved_path} --records 1000")
            
        else:
            print("❌ Please provide a Swagger file or use --create-israeli-banking")
            parser.print_help()
            return 1
        
    except Exception as e:
        print(f"❌ Process failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())