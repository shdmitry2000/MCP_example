# Modular Israeli Banking Data Generator - Usage Guide

## 🎯 Overview

Your system is now modular with two independent processes:

1. **🔄 Schema Converter** - Convert Swagger files to Definition files
2. **🚀 Data Generator** - Generate databases from Definition files  
3. **🖥️ Streamlit GUI** - User-friendly interface for both processes

## 📁 File Structure

```
your-project/
├── schema_converter.py          # Process 1: Swagger → Definition
├── data_generator.py           # Process 2: Definition → Database  
├── streamlit_gui.py            # GUI for both processes
├── db/                         # Your DB_FOLDER (from .env)
│   ├── definitions/            # Definition files
│   ├── exports/                # CSV/JSON exports
│   ├── logs/                   # Process logs
│   ├── *.db                    # Generated databases
│   └── reports/                # Generation reports
└── config/
    └── config.py              # Your existing config
```

## 🚀 Usage Methods

### Method 1: Command Line (Separate Processes)

#### Step 1: Convert Swagger to Definition
```bash
# Convert your existing Swagger file
python schema_converter.py your_swagger.json --target-system faker --output-dir db/definitions

# Or create from built-in Israeli banking schema
python schema_converter.py --create-sample israeli_banking.json --target-system faker
```

#### Step 2: Generate Database from Definition
```bash
# Generate database from definition file
python data_generator.py db/definitions/israeli_banking_faker_definition.json --records 1000 --strategy faker

# With custom database
python data_generator.py db/definitions/custom_definition.json --records 5000 --db-url "postgresql://user:pass@localhost/mydb"

# Export to multiple formats
python data_generator.py definition.json --records 1000 --export csv json
```

### Method 2: Streamlit GUI (Recommended)

```bash
# Install Streamlit if you haven't
pip install streamlit

# Launch the GUI
streamlit run streamlit_gui.py
```

Then use the web interface:
1. **🔄 Schema Conversion Tab**: Upload Swagger → Generate Definition
2. **🚀 Data Generation Tab**: Select Definition → Generate Database
3. **📁 File Manager Tab**: Browse generated files

### Method 3: Python API

```python
# Process 1: Schema Conversion
from schema_converter import SchemaConverter

converter = SchemaConverter()
swagger_schema = converter.load_swagger_file("my_api.json")
definition = converter.convert_swagger_to_definition(swagger_schema, "faker")
converter.save_definition_file(definition, "output_definition.json")

# Process 2: Data Generation  
from data_generator import DataGenerationEngine

engine = DataGenerationEngine("my_db_folder")
result = engine.generate_database(
    definition_file="output_definition.json",
    num_records=1000,
    strategy="faker"
)
```

## 🔧 Creating Custom Definitions

### For Faker Strategy

```json
{
  "schema_info": {
    "name": "My Custom Schema",
    "target_system": "faker",
    "locale": "he_IL"
  },
  "tables": {
    "customers": {
      "description": "Customer table",
      "primary_key": "customer_id",
      "fields": {
        "customer_id": {
          "type": "string",
          "constraints": {"max_length": 10},
          "generation": {"generator": "uuid"}
        },
        "שם_פרטי": {
          "type": "string", 
          "constraints": {"max_length": 50},
          "generation": {"generator": "hebrew_first_name", "locale": "he_IL"}
        },
        "תעודת_זהות": {
          "type": "string",
          "constraints": {"max_length": 9},
          "generation": {"generator": "israeli_id"}
        }
      }
    }
  }
}
```

### For SDV Strategy (Future)

```json
{
  "schema_info": {
    "target_system": "sdv"
  },
  "generation_settings": {
    "sdv_options": {
      "model_type": "GaussianCopula",
      "privacy_level": "high"
    }
  },
  "tables": {
    "users": {
      "fields": {
        "age": {
          "type": "integer",
          "generation": {
            "sdv_options": {
              "distribution": "normal",
              "anonymization": "auto"
            }
          }
        }
      }
    }
  }
}
```

## 🎯 Target Systems Support

### Current Support
- ✅ **Faker**: Full support with Hebrew locale
- ⏳ **SDV**: Framework ready (implementation needed)
- ⏳ **Mimesis**: Framework ready (implementation needed)

### Adding New Systems

1. **Extend SchemaConverter**:
```python
def _optimize_for_target_system(self, definition_schema, target_system):
    if target_system == "my_new_system":
        definition_schema["generation_settings"]["my_system_options"] = {
            "custom_config": "value"
        }
```

2. **Extend DataGenerationEngine**:
```python  
def _create_my_system_generator(self, schema, db_url, definition):
    # Implement your generator
    return MySystemGenerator(schema, db_url)
```

## 🖥️ Streamlit GUI Features

### Schema Conversion Tab
- 📤 Upload Swagger files (JSON/YAML)
- 📋 Use built-in Israeli banking schema
- ✏️ Paste Swagger JSON directly
- 🎯 Select target system (Faker, SDV, Mimesis)
- 👀 Preview generated table structure

### Data Generation Tab  
- 📋 Select from converted definition files
- 📊 Configure record count (10-100,000)
- 🎯 Choose generation strategy
- 📤 Multi-format export (CSV, JSON, Excel)
- 📈 View generation statistics
- 🔗 Custom database URL support

### File Manager Tab
- 📁 Browse definition files
- 🗄️ View database files with sizes
- 📤 Check export files
- 🗂️ Organized folder structure

## 🚀 Quick Start Examples

### Example 1: Israeli Banking Data
```bash
# Step 1: Create definition from built-in schema
python schema_converter.py --create-israeli-banking --target-system faker

# Step 2: Generate 5000 records
python data_generator.py db/definitions/israeli_banking_faker_definition.json --records 5000

# Result: SQLite database with Hebrew names, Israeli IDs, credit cards, transactions
```

### Example 2: Custom E-commerce Schema
```bash
# Step 1: Convert your e-commerce API schema  
python schema_converter.py ecommerce_api.json --target-system faker --output-dir db/definitions

# Step 2: Generate test data
python data_generator.py db/definitions/ecommerce_api_faker_definition.json --records 2000 --export csv

# Result: Database with products, orders, customers + CSV exports
```

### Example 3: Multiple Target Systems
```bash
# Create different definitions for different systems
python schema_converter.py banking_api.json --target-system faker
python schema_converter.py banking_api.json --target-system sdv  
python schema_converter.py banking_api.json --target-system mimesis

# Generate with different strategies
python data_generator.py banking_api_faker_definition.json --strategy faker --records 1000
python data_generator.py banking_api_sdv_definition.json --strategy sdv --records 1000
```

## 🔧 Configuration Options

### Environment Variables (.env)
```env
DATABASE_URL=sqlite:///israeli_banking_data.db
DB_FOLDER=db
GENERATION_LOCALE=he_IL
DEFAULT_RECORDS=1000
```

### Command Line Arguments

#### Schema Converter
```bash
python schema_converter.py INPUT_FILE [OPTIONS]

Options:
  --output, -o              Output definition file path
  --target-system, -t       Target system (faker, sdv, mimesis, custom)
  --output-dir              Output directory for definition files
  --create-israeli-banking  Create built-in Israeli banking schema
```

#### Data Generator  
```bash
python data_generator.py DEFINITION_FILE [OPTIONS]

Options:
  --records, -r             Number of records per table (default: 1000)
  --strategy, -s            Generation strategy (faker, sdv, mimesis)
  --db-url                  Custom database URL
  --db-folder               Database folder path
  --export                  Export formats (csv, json, excel)
  --stats-only              Only show database statistics
```

## 🎨 GUI Customization

### Custom CSS for Hebrew
The Streamlit GUI includes built-in Hebrew support with RTL text direction and proper fonts.

### Adding New Generation Systems to GUI
1. Update the strategy selectbox in `streamlit_gui.py`:
```python
strategy = st.selectbox(
    "Generation Strategy:",
    ["faker", "sdv", "mimesis", "my_new_system"],  # Add your system
    key="gen_strategy"
)
```

2. Add system-specific options:
```python
if strategy == "my_new_system":
    st.write("My System Options:")
    option1 = st.slider("Custom Option", 0, 100, 50)
```

## 📊 Output Examples

### Generated Files Structure
```
db/
├── israeli_banking_data.db              # SQLite database (2.5 MB)
├── definitions/
│   ├── israeli_banking_faker_definition.json    # Faker-optimized schema
│   ├── israeli_banking_sdv_definition.json      # SDV-optimized schema  
│   └── custom_schema_definition.json            # Your custom schema
├── exports/
│   ├── csv/
│   │   ├── users.csv                   # 1000 Hebrew users
│   │   ├── accounts.csv                # 1000 bank accounts
│   │   ├── credit_cards.csv            # 1000 credit cards
│   │   └── transactions.csv            # 10000 transactions
│   └── json/
│       └── combined_data.json          # All data in JSON format
├── logs/
│   └── generation_20240522_143022.log  # Detailed process logs
└── reports/
    └── generation_report_20240522_143022.json  # Comprehensive report
```

### Sample Generated Data (Hebrew)
```csv
# users.csv
תעודת_זהות,שם_פרטי,שם_משפחה,כתובת,עיר,טלפון,דואר_אלקטרוני
123456782,דוד,כהן,"רחוב הרצל 15, תל אביב",תל אביב,050-1234567,david.cohen@example.com
234567893,שרה,לוי,"שדרות בן גוריון 42, חיפה",חיפה,052-9876543,sarah.levi@example.com

# credit_cards.csv  
מספר_כרטיס,תעודת_זהות,סוג_כרטיס,תוקף,מסגרת_אשראי,יתרה
4532123456789012,123456782,ויזה זהב,12/28,25000,3250.75
5555444433332222,234567893,מאסטרקארד פלטינום,06/29,50000,12450.30
```

## 🔍 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure all files are in the same directory
ls -la schema_converter.py data_generator.py streamlit_gui.py

# Check Python path
python -c "import sys; print(sys.path)"
```

**2. Hebrew Text Issues**
```bash
# Ensure UTF-8 encoding
export PYTHONIOENCODING=utf-8

# Check locale
locale
```

**3. Database Connection Issues**
```bash
# Test with SQLite first
python data_generator.py definition.json --db-url "sqlite:///test.db" --records 10

# Then try PostgreSQL
python data_generator.py definition.json --db-url "postgresql://user:pass@localhost/db" --records 10
```

**4. Streamlit Import Issues**
```bash
# Install Streamlit
pip install streamlit pandas

# Run with full path
python -m streamlit run streamlit_gui.py
```

## 🚀 Next Steps

### Immediate Actions
1. **Test the modular system**:
   ```bash
   python schema_converter.py --create-israeli-banking
   python data_generator.py db/definitions/israeli_banking_faker_definition.json --records 100
   ```

2. **Launch the GUI**:
   ```bash
   streamlit run streamlit_gui.py
   ```

3. **Explore your data**:
   - Open DBeaver and connect to `db/israeli_banking_data.db`
   - Check CSV exports in `db/exports/csv/`

### Future Enhancements
1. **Add SDV support** in `data_generator.py`
2. **Add Mimesis support** for alternative fake data
3. **Create custom definition templates** for different industries
4. **Add data validation** and quality checks
5. **Implement incremental data generation**

## 🎉 Benefits of This Modular Approach

### ✅ **Flexibility**
- Use any combination of processes
- Easy to add new generation systems
- Swap strategies without changing schemas

### ✅ **Maintainability**  
- Clear separation of concerns
- Independent testing of each process
- Easy debugging and troubleshooting

### ✅ **Scalability**
- Process large schemas in steps
- Generate multiple databases from one definition
- Batch processing capabilities

### ✅ **User Experience**
- GUI for non-technical users
- Command line for automation
- API for integration

Your modular system is now ready for production use with Israeli banking data, Hebrew support, and extensibility for future data generation systems! 🎯