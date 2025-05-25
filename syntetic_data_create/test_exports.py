#!/usr/bin/env python3
# test_exports.py

"""
Test script to verify exports folder functionality
"""

import sys
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent if current_dir.name == 'syntetic_data_create' else current_dir
sys.path.insert(0, str(project_root))

def test_exports_with_complete_integration():
    """Test exports using the complete integration script."""
    print("🧪 Testing exports with complete integration...")
    
    try:
        from syntetic_data_create.complete_integration import IsraeliBankingDataGenerator
        
        # Use the same DB folder as the generator expects
        generator = IsraeliBankingDataGenerator(
            db_url="sqlite:///test_banking.db",  # Simple SQLite file in current directory
            strategy='faker',
            schema_source='default'
        )
        
        print(f"✅ Generator initialized with DB folder: {generator.db_folder}")
        print(f"   Exports folder: {generator.exports_folder}")
        
        # Setup
        setup_result = generator.setup()
        if setup_result['status'] != 'success':
            print(f"❌ Setup failed: {setup_result['message']}")
            return False
        
        print("✅ Generator setup completed")
        
        # Generate small dataset
        print("🚀 Generating test database...")
        generation_result = generator.generate_complete_database(num_records=50)
        
        if 'error' in generation_result:
            print(f"❌ Generation failed: {generation_result['message']}")
            return False
        
        print(f"✅ Database generated: {generation_result['total_records']} records")
        
        # Test exports
        print("📤 Testing exports...")
        export_result = generator.export_data(['csv', 'json'])  # Remove excel for now to avoid openpyxl dependency
        
        if 'error' in export_result:
            print(f"❌ Export failed: {export_result}")
            return False
        
        # Verify exports
        print("🔍 Verifying exports...")
        
        for format_name, format_info in export_result.items():
            print(f"\n📋 {format_name.upper()} Export:")
            print(f"   Location: {format_info.get('export_dir', 'N/A')}")
            print(f"   Files created: {format_info.get('count', 0)}")
            
            # Check if files actually exist
            export_dir = Path(format_info.get('export_dir', ''))
            if export_dir.exists():
                files = list(export_dir.glob('*'))
                print(f"   Actual files: {len(files)}")
                for file in files:
                    file_size = file.stat().st_size / 1024  # KB
                    print(f"     • {file.name} ({file_size:.1f} KB)")
            else:
                print(f"   ❌ Export directory doesn't exist: {export_dir}")
        
        # Show folder structure
        print(f"\n📁 Complete folder structure in {generator.db_folder}:")
        show_folder_structure(generator.db_folder)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exports_with_data_generator():
    """Test exports using the data generator process."""
    print("\n🧪 Testing exports with data generator process...")
    
    try:
        from syntetic_data_create.data_generator import DataGenerationEngine
        
        # Create a simple definition file for testing with proper primary keys
        test_definition = {
            "schema_info": {
                "name": "Test Schema",
                "target_system": "faker",
                "locale": "he_IL"
            },
            "tables": {
                "test_users": {
                    "description": "Test users table",
                    "primary_key": "id",  # Add primary key
                    "fields": {
                        "id": {"type": "integer", "constraints": {"min": 1, "max": 100000}},
                        "name": {"type": "string", "constraints": {"max_length": 50}},
                        "email": {"type": "string", "constraints": {"max_length": 100}}
                    }
                },
                "test_orders": {
                    "description": "Test orders table",
                    "primary_key": "order_id",  # Add primary key
                    "fields": {
                        "order_id": {"type": "integer", "constraints": {"min": 1, "max": 100000}},
                        "amount": {"type": "float", "constraints": {"min": 10, "max": 1000}},
                        "status": {"type": "choice", "constraints": {"choices": ["pending", "completed", "cancelled"]}}
                    }
                }
            }
        }
        
        # Save test definition
        test_folder = Path("test_data_generator")
        test_folder.mkdir(exist_ok=True)
        
        definition_file = test_folder / "test_definition.json"
        import json
        with open(definition_file, 'w', encoding='utf-8') as f:
            json.dump(test_definition, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Created test definition: {definition_file}")
        
        # Initialize engine
        engine = DataGenerationEngine(str(test_folder))
        
        print(f"✅ Engine initialized with folder: {test_folder}")
        print(f"   Exports folder: {engine.exports_folder}")
        
        # Generate database
        result = engine.generate_database(
            definition_file=str(definition_file),
            num_records=25,
            strategy="faker"
        )
        
        print(f"✅ Database generated: {result.get('database_url', 'N/A')}")
        
        # Test exports (skip excel to avoid openpyxl dependency issues)
        export_result = engine.export_data(result['database_url'], ['csv', 'json'])
        
        # Verify exports
        print("🔍 Verifying data generator exports...")
        
        for format_name, format_info in export_result.items():
            if 'error' not in format_info:
                print(f"\n📋 {format_name.upper()} Export:")
                print(f"   Location: {format_info.get('location', 'N/A')}")
                print(f"   Files: {format_info.get('file_count', 0)}")
                
                # Check actual files
                export_dir = Path(format_info.get('location', ''))
                if export_dir.exists():
                    files = list(export_dir.glob('*'))
                    for file in files:
                        file_size = file.stat().st_size / 1024  # KB
                        print(f"     • {file.name} ({file_size:.1f} KB)")
                        
                        # Show a sample of the content for verification
                        if file.suffix == '.csv':
                            print(f"       Sample CSV content:")
                            with open(file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()[:3]  # First 3 lines
                                for line in lines:
                                    print(f"         {line.strip()}")
                        elif file.suffix == '.json':
                            print(f"       Sample JSON content:")
                            with open(file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, list) and len(data) > 0:
                                    sample = data[0] if len(data) > 0 else {}
                                    print(f"         First record: {sample}")
                                elif isinstance(data, dict):
                                    for key, value in list(data.items())[:2]:
                                        sample_count = len(value) if isinstance(value, list) else 'N/A'
                                        print(f"         {key}: {sample_count} records")
            else:
                print(f"❌ {format_name.upper()} export failed: {format_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_folder_structure(folder_path: Path, max_depth: int = 3, current_depth: int = 0):
    """Show folder structure."""
    if current_depth >= max_depth:
        return
        
    try:
        folder = Path(folder_path)
        if not folder.exists():
            return
            
        items = sorted(folder.iterdir())
        
        for item in items:
            indent = "  " * current_depth
            if item.is_file():
                size = item.stat().st_size / 1024  # KB
                print(f"{indent}📄 {item.name} ({size:.1f} KB)")
            elif item.is_dir():
                print(f"{indent}📁 {item.name}/")
                show_folder_structure(item, max_depth, current_depth + 1)
                
    except Exception as e:
        print(f"Error showing folder structure: {e}")


def cleanup_test_files():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    import shutil
    
    test_files_and_folders = [
        "test_data_generator",
        "test_banking.db",
        "db"  # Clean up the db folder created by the test
    ]
    
    for item in test_files_and_folders:
        item_path = Path(item)
        if item_path.exists():
            if item_path.is_file():
                item_path.unlink()
                print(f"✅ Removed file {item}")
            elif item_path.is_dir():
                shutil.rmtree(item_path)
                print(f"✅ Removed folder {item}")
        else:
            print(f"ℹ️ {item} doesn't exist, skipping")


def main():
    """Run all export tests."""
    print("=" * 60)
    print("EXPORTS FOLDER FUNCTIONALITY TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Complete Integration exports
    if test_exports_with_complete_integration():
        tests_passed += 1
        print("✅ Complete Integration exports test PASSED")
    else:
        print("❌ Complete Integration exports test FAILED")
    
    # Test 2: Data Generator exports
    if test_exports_with_data_generator():
        tests_passed += 1
        print("✅ Data Generator exports test PASSED")
    else:
        print("❌ Data Generator exports test FAILED")
    
    # Results
    print("\n" + "=" * 60)
    print(f"EXPORTS TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All exports tests passed! Exports folder functionality is working correctly.")
    else:
        print("🚨 Some exports tests failed. Check the errors above.")
    
    # Ask about cleanup
    cleanup = input("\n🧹 Clean up test files? (y/n): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_files()
    
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)