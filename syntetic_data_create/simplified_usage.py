#!/usr/bin/env python3
# simplified_usage.py

"""
Simplified example showing how to use the DataGenerationEngine
with a focus on SQL export functionality.
"""

import os
import sys
from pathlib import Path
import json
import argparse

# Add project root to Python path if needed
current_dir = Path(__file__).parent
project_root = current_dir.parent if current_dir.name == 'syntetic_data_create' else current_dir
sys.path.insert(0, str(project_root))

# Import the DataGenerationEngine
from data_generator import DataGenerationEngine


def create_sample_definition():
    """Create a sample definition file for testing."""
    # Create output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Create definitions folder
    definitions_dir = output_dir / "definitions"
    definitions_dir.mkdir(exist_ok=True)
    
    # Create a simple definition file
    definition = {
        "schema_info": {
            "name": "Test Schema",
            "version": "1.0.0",
            "target_system": "faker",
            "locale": "he_IL"
        },
        "tables": {
            "users": {
                "description": "Users table",
                "primary_key": "id",
                "fields": {
                    "id": {
                        "type": "integer",
                        "constraints": {"primary_key": True, "autoincrement": True}
                    },
                    "name": {
                        "type": "string",
                        "constraints": {"max_length": 50}
                    },
                    "email": {
                        "type": "string",
                        "constraints": {"max_length": 100}
                    },
                    "active": {
                        "type": "boolean"
                    }
                }
            },
            "orders": {
                "description": "Orders table",
                "primary_key": "id",
                "fields": {
                    "id": {
                        "type": "integer",
                        "constraints": {"primary_key": True, "autoincrement": True}
                    },
                    "user_id": {
                        "type": "integer",
                        "constraints": {"foreign_key": "users.id"}
                    },
                    "amount": {
                        "type": "float",
                        "constraints": {"min": 10, "max": 1000}
                    },
                    "order_date": {
                        "type": "date"
                    },
                    "notes": {
                        "type": "string",
                        "constraints": {"max_length": 200, "nullable": True}
                    }
                }
            }
        }
    }
    
    # Save to file
    definition_file = definitions_dir / "test_definition.json"
    with open(definition_file, 'w', encoding='utf-8') as f:
        json.dump(definition, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Created sample definition file: {definition_file}")
    return str(definition_file)


def run_step_by_step(definition_file, output_dir, num_records=50):
    """Run the data generation process step by step."""
    print("\n" + "=" * 60)
    print("STEP-BY-STEP WORKFLOW")
    print("=" * 60)
    
    # Create DataGenerationEngine
    engine = DataGenerationEngine(str(output_dir))
    print(f"✅ Engine initialized with output folder: {output_dir}")
    
    # Step 1: Load definition file
    print("\nSTEP 1: Loading definition file...")
    definition = engine.load_definition_file(definition_file)
    print(f"✅ Definition loaded with {len(definition.get('tables', {}))} tables")
    
    # Step 2: Prepare database URL
    print("\nSTEP 2: Preparing database URL...")
    db_url = engine.prepare_database_url(db_name="step_by_step.db")
    print(f"✅ Database URL prepared: {db_url}")
    
    # Step 3: Create generator
    print("\nSTEP 3: Creating generator...")
    generator = engine.create_generator(strategy="faker")
    print(f"✅ Generator created with strategy: faker")
    
    # Step 4: Convert definition
    print("\nSTEP 4: Converting definition to generator schema...")
    generator_schema = engine.convert_definition_to_generator_schema()
    print(f"✅ Definition converted with tables: {list(generator_schema.keys())}")
    
    # Step 5: Generate database
    print("\nSTEP 5: Generating database...")
    gen_result = engine.generate_database_data(generator_schema, num_records)
    print(f"✅ Database generated with {gen_result.get('total_records', 0)} total records")
    
    # Step 6: Export data
    print("\nSTEP 6: Exporting data...")
    export_result = engine.export_data(["csv", "json", "sql"])
    
    # Print export results
    for format_name, format_info in export_result.items():
        if "error" not in format_info:
            print(f"✅ {format_name.upper()} export: {format_info.get('file_count', 0)} files")
            print(f"   📁 Location: {format_info.get('location', 'N/A')}")
        else:
            print(f"❌ {format_name.upper()} export failed: {format_info.get('error', 'Unknown error')}")
    
    # Step 7: Generate report
    print("\nSTEP 7: Generating report...")
    report_result = engine.generate_report()
    print(f"✅ Report generated: {report_result.get('report_file', 'N/A')}")
    
    print("\n✅ Step-by-step workflow completed successfully!")
    return engine


def run_complete_workflow(definition_file, output_dir, num_records=50):
    """Run the complete data generation workflow."""
    print("\n" + "=" * 60)
    print("COMPLETE WORKFLOW")
    print("=" * 60)
    
    # Create DataGenerationEngine
    engine = DataGenerationEngine(str(output_dir))
    print(f"✅ Engine initialized with output folder: {output_dir}")
    
    # Run complete workflow
    print("\nGenerating database, exporting data, and creating report...")
    result = engine.generate_complete_database(
        definition_file=definition_file,
        num_records=num_records,
        strategy="faker",
        export_formats=["csv", "json", "sql"]
    )
    
    # Check result
    if result.get("status") == "success":
        print(f"\n✅ Complete workflow succeeded!")
        print(f"📊 Database URL: {result.get('database_url', 'N/A')}")
        print(f"📊 Total records: {result.get('total_records', 0)}")
        print(f"📊 Tables created: {result.get('tables_created', [])}")
        
        # Print export information
        print("\nExport results:")
        for format_name, format_info in result.get("export_results", {}).items():
            if "error" not in format_info:
                print(f"✅ {format_name.upper()}: {format_info.get('file_count', 0)} files")
                print(f"   📁 Location: {format_info.get('location', 'N/A')}")
            else:
                print(f"❌ {format_name.upper()}: {format_info.get('error', 'Unknown error')}")
        
        # Print report information
        print(f"\n📄 Report file: {result.get('report_file', 'N/A')}")
    else:
        print(f"\n❌ Complete workflow failed: {result.get('message', 'Unknown error')}")
    
    return engine


def main():
    """Main function to run examples."""
    parser = argparse.ArgumentParser(description="Test DataGenerationEngine with SQL export")
    parser.add_argument("--records", type=int, default=50, help="Number of records per table")
    parser.add_argument("--workflow", choices=["step", "complete", "both"], default="both", 
                      help="Workflow to run (step-by-step, complete, or both)")
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("DATA GENERATION ENGINE EXAMPLE")
    print("=" * 60)
    
    # Create sample definition file
    definition_file = create_sample_definition()
    
    # Run requested workflow
    if args.workflow in ["step", "both"]:
        engine1 = run_step_by_step(definition_file, output_dir, args.records)
    
    if args.workflow in ["complete", "both"]:
        engine2 = run_complete_workflow(definition_file, output_dir, args.records)
    
    # Show folder structure
    print("\n" + "=" * 60)
    print("FOLDER STRUCTURE")
    print("=" * 60)
    
    def print_folder_structure(path, prefix=""):
        for item in sorted(path.iterdir()):
            if item.is_dir():
                print(f"{prefix}📁 {item.name}/")
                print_folder_structure(item, prefix + "  ")
            else:
                size = item.stat().st_size / 1024  # KB
                print(f"{prefix}📄 {item.name} ({size:.1f} KB)")
    
    print_folder_structure(output_dir)
    
    # Cleanup option
    cleanup = input("\nClean up test files? (y/n): ").lower() == 'y'
    if cleanup:
        import shutil
        shutil.rmtree(output_dir)
        print("✅ Test files cleaned up")


if __name__ == "__main__":
    main()