# Schema Usage Guide - Swagger and Definition Files

## 🎯 Overview

Your Israeli Banking Data Generator now supports multiple schema sources:

1. **📄 Swagger/OpenAPI files** - Industry standard API documentation format
2. **📋 Definition files** - Simplified database schema format 
3. **🔄 Format conversion** - Convert between Swagger and Definition formats
4. **🏗️ Default schemas** - Built-in Israeli banking schemas

## 🚀 Quick Start

### Create Default Schema Files

```bash
# Create both Swagger and Definition files from your current default schema
python complete_integration.py --create-schemas
```

This creates:
- `schemas/israeli_banking_swagger.json` - Full Swagger/OpenAPI 3.0 schema
- `schemas/israeli_banking_definition.json` - Simplified definition schema

### Generate Database from Swagger File

```bash
# Use default Swagger file
python complete_integration.py --schema-source swagger --records 1000

# Use custom Swagger file
python complete_integration.py --schema-source path/to/your/swagger.json --records 1000
```

### Generate Database from Definition File

```bash
# Use default Definition file
python complete_integration.py --schema-source definition --records 1000

# Use custom Definition file
python complete_integration.py --schema-source path/to/your/definition.json --records 1000
```

## 📁 Schema File Formats

### Swagger/OpenAPI Format

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Israeli Banking Data Generator API",
    "version": "1.0.0"
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
            "pattern": "^[0-9]{9}$",
            "example": "123456782"
          },
          "שם_פרטי": {
            "type": "string",
            "description": "שם פרטי בעברית",
            "maxLength": 50,
            "example": "דוד"
          }
        }
      }
    }
  }
}
```

### Definition Format

```json
{
  "schema_info": {
    "name": "Israeli Banking Database Schema",
    "version": "1.0.0",
    "locale": "he_IL"
  },
  "tables": {
    "users": {
      "description": "לקוחות הבנק",
      "primary_key": "תעודת_זהות",
      "fields": {
        "תעודת_זהות": {
          "type": "string",
          "constraints": {"max_length": 9},
          "description": "מספר תעודת זהות ישראלית",
          "generator": "israeli_id"
        },
        "שם_פרטי": {
          "type": "string",
          "constraints": {"max_length": 50},
          "description": "שם פרטי בעברית",
          "generator": "hebrew_first_name"
        }
      }
    }
  }
}
```

## 🔄 Format Conversion

### Convert Swagger to Definition

```bash
python complete_integration.py --convert-schema swagger-to-definition
```

### Convert Definition to Swagger

```bash
python complete_integration.py --convert-schema definition-to-swagger
```

### Using Schema Manager Directly

```python
from schema_manager import SchemaManager

manager = SchemaManager()

# Load and convert Swagger to Definition
swagger_schema = manager.load_swagger_schema("my_swagger.json")
definition_schema = manager.convert_swagger_to_definition(swagger_schema)

# Load and convert Definition to Swagger
definition_schema = manager.load_definition_schema("my_definition.json")
swagger_schema = manager.convert_definition_to_swagger(definition_schema)
```

## 📋 Available Commands

### List Available Schema Files

```bash
python complete_integration.py --list-schemas
```

Output:
```
📁 Available Schema Files:
   Swagger files: 2
      • israeli_banking_swagger.json
      • custom_banking_api.json
   Definition files: 1
      • israeli_banking_definition.json
```

### Generate with Different Sources

```bash
# Use built-in default schema
python complete_integration.py --schema-source default

# Use Swagger file
python complete_integration.py --schema-source swagger

# Use Definition file  
python complete_integration.py --schema-source definition

# Use custom file
python complete_integration.py --schema-source /path/to/custom/schema.json
```

## 🛠️ Programmatic Usage

### Using Schema Manager

```python
from schema_manager import SchemaManager

# Initialize
manager = SchemaManager()

# Create default files
created_files = manager.create_default_files()
print(f"Swagger file: {created_files['swagger_file']}")
print(f"Definition file: {created_files['definition_file']}")

# Generate database from Swagger
result = manager.generate_database_from_swagger(
    swagger_file="schemas/israeli_banking_swagger.json",
    num_records=1000,
    db_url="sqlite:///from_swagger.db"
)

# Generate database from Definition
result = manager.generate_database_from_definition(
    definition_file="schemas/israeli_banking_definition.json", 
    num_records=1000,
    db_url="sqlite:///from_definition.db"
)
```

### Using Complete Integration

```python
from complete_integration import IsraeliBankingDataGenerator

# Initialize with Swagger source
generator = IsraeliBankingDataGenerator(
    db_url="sqlite:///my_bank.db",
    strategy="faker",
    schema_source="swagger"  # or "definition" or file path
)

# Setup and generate
generator.setup()
result = generator.generate_complete_database(num_records=1000)
```

## 📊 Schema File Structure

### Created Files Directory Structure

```
schemas/
├── israeli_banking_swagger.json          # Full Swagger/OpenAPI schema
├── israeli_banking_definition.json       # Simplified definition schema
├── converted_swagger_to_definition.json  # Converted files
├── converted_definition_to_swagger.json
└── custom_schemas/                       # Your custom schemas
    ├── banking_v2.json
    └── retail_banking.yaml
```

## 🎯 Use Cases

### 1. API Documentation Team

Use **Swagger files** when you need:
- Industry standard API documentation
- Integration with API tools (Postman, Insomnia)
- Detailed validation rules and examples
- OpenAPI ecosystem compatibility

```bash
python complete_integration.py --schema-source swagger --records 5000
```

### 2. Database Design Team

Use **Definition files** when you need:
- Simple database-focused schemas
- Custom data generation rules
- Quick prototyping
- Non-API database projects

```bash
python complete_integration.py --schema-source definition --records 5000
```

### 3. Testing Different Schemas

```bash
# Test with minimal data
python complete_integration.py --schema-source swagger --records 100

# Test with production-like data
python complete_integration.py --schema-source definition --records 10000

# Compare results
python complete_integration.py --list-schemas
```

## 🔧 Customization

### Create Custom Swagger Schema

1. Copy the default Swagger file:
   ```bash
   cp schemas/israeli_banking_swagger.json schemas/my_custom_banking.json
   ```

2. Edit your custom schema with additional fields or tables

3. Use your custom schema:
   ```bash
   python complete_integration.py --schema-source schemas/my_custom_banking.json
   ```

### Create Custom Definition Schema

1. Copy the default Definition file:
   ```bash
   cp schemas/israeli_banking_definition.json schemas/my_banking_definition.json
   ```

2. Modify tables, fields, or add new generators

3. Generate database:
   ```bash
   python complete_integration.py --schema-source schemas/my_banking_definition.json
   ```

## 🧪 Testing Schema Files

### Validate Your Schema

```python
from schema_manager import SchemaManager

manager = SchemaManager()

# Test loading your schema
try:
    schema = manager.load_swagger_schema("my_schema.json")
    print("✅ Schema loaded successfully")
except Exception as e:
    print(f"❌ Schema error: {e}")

# Test generation with small dataset
result = manager.generate_database_from_swagger(
    swagger_file="my_schema.json",
    num_records=10,  # Small test
    db_url="sqlite:///test.db"
)
```

## 📈 Performance Comparison

| Schema Source | Loading Speed | Generation Speed | File Size | Complexity |
|---------------|---------------|------------------|-----------|------------|
| **Default** | Fastest | Fastest | N/A | Low |
| **Definition** | Fast | Fast | Small | Medium |
| **Swagger** | Medium | Medium | Large | High |
| **Custom File** | Depends on size | Depends on complexity | Variable | Variable |

## 🎉 Examples

### Complete Workflow with Schema

```bash
# 1. Create default schema files
python complete_integration.py --create-schemas

# 2. List available schemas
python complete_integration.py --list-schemas

# 3. Generate from Swagger
python complete_integration.py --schema-source swagger --records 1000 --db-url "sqlite:///swagger_bank.db"

# 4. Generate from Definition  
python complete_integration.py --schema-source definition --records 1000 --db-url "sqlite:///definition_bank.db"

# 5. Convert between formats
python complete_integration.py --convert-schema swagger-to-definition

# 6. Use your .env DATABASE_URL with custom schema
python complete_integration.py --schema-source schemas/israeli_banking_swagger.json --records 2000
```

This gives you maximum flexibility to work with different schema formats while maintaining the same powerful data generation capabilities! 🚀