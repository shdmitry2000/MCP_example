#!/usr/bin/env python3
# test_create_generator_fix.py

"""
Test script to verify that the create_generator function works correctly
"""

import sys
from pathlib import Path

# Add project to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_standalone_create_generator():
    """Test the standalone create_generator function."""
    print("🧪 Testing standalone create_generator function...")
    
    try:
        # This simulates what the fixed function should look like
        from database_generator import DatabaseGenerator, FakerSQLAlchemyStrategy
        
        def create_generator_fixed(strategy: str = "faker", db_url: str = None, locale: str = 'he_IL'):
            """Fixed version of create_generator function."""
            strategy_mapping = {
                'faker': FakerSQLAlchemyStrategy,
            }
            
            if strategy not in strategy_mapping:
                raise ValueError(f"Unknown strategy: {strategy}. Available strategies: {list(strategy_mapping.keys())}")
            
            strategy_class = strategy_mapping[strategy]
            if strategy == 'faker':
                strategy_instance = strategy_class(locale=locale)
            else:
                strategy_instance = strategy_class()
            
            return DatabaseGenerator(strategy_instance, db_url=db_url)
        
        # Test the function
        test_db_url = "sqlite:///test_generator.db"
        generator = create_generator_fixed('faker', db_url=test_db_url)
        
        print(f"✅ Successfully created generator with strategy: faker")
        print(f"   Database URL: {generator.db_url}")
        print(f"   Strategy: {generator.strategy.get_name()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_generation_engine():
    """Test the DataGenerationEngine with the fix."""
    print("\n🧪 Testing DataGenerationEngine with create_generator fix...")
    
    try:
        from data_generator import DataGenerationEngine
        
        # Create a test definition
        test_definition = {
            "schema_info": {
                "name": "Test Schema",
                "target_system": "faker",
                "locale": "he_IL"
            },
            "tables": {
                "test_table": {
                    "description": "Test table",
                    "primary_key": "id",
                    "fields": {
                        "id": {"type": "integer", "constraints": {"min": 1, "max": 100}},
                        "name": {"type": "string", "constraints": {"max_length": 50}}
                    }
                }
            }
        }
        
        # Save test definition
        import json
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_definition, f, indent=2)
            definition_file = f.name
        
        # Test the engine
        engine = DataGenerationEngine("test_db_folder")
        
        # Test step by step
        print("   1. Loading definition...")
        definition = engine.load_definition_file(definition_file)
        print(f"      ✅ Loaded definition with {len(definition.get('tables', {}))} tables")
        
        print("   2. Preparing database URL...")
        db_url = engine.prepare_database_url(db_name="test.db")
        print(f"      ✅ Database URL: {db_url}")
        
        print("   3. Creating generator...")
        # This is where the fix should work
        generator = engine.create_generator("faker")
        print(f"      ✅ Generator created successfully")
        
        # Clean up
        import os
        os.unlink(definition_file)
        
        return True
        
    except Exception as e:
        print(f"❌ DataGenerationEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING CREATE_GENERATOR FUNCTION FIX")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Standalone function
    if test_standalone_create_generator():
        tests_passed += 1
    
    # Test 2: DataGenerationEngine integration
    if test_data_generation_engine():
        tests_passed += 1
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The create_generator fix should work.")
        print("\n📋 Next steps:")
        print("1. Apply the fix to database_generator.py")
        print("2. Test with the simplified usage script")
        print("3. Run the complete integration")
    else:
        print("🚨 Some tests failed. Check the errors above.")
    
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)