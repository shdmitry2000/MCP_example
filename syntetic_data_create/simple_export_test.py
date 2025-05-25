#!/usr/bin/env python3
# simple_export_test.py

"""
Simple test to verify exports folder functionality
"""

import sys
import json
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent if current_dir.name == 'syntetic_data_create' else current_dir
sys.path.insert(0, str(project_root))

def test_basic_export():
    """Test basic export functionality."""
    print("🧪 Testing basic export functionality...")
    
    try:
        # Generate a small database first
        print("1. Generating small test database...")
        result = subprocess.run([
            sys.executable, 
            "syntetic_data_create/complete_integration.py", 
            "--records", "50"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Database generation failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        
        print("✅ Database generated successfully")
        
        # Check if exports folder exists
        db_folder = Path("db")
        exports_folder = db_folder / "exports"
        
        if not exports_folder.exists():
            print(f"❌ Exports folder doesn't exist: {exports_folder}")
            return False
        
        print(f"✅ Exports folder exists: {exports_folder}")
        
        # Check for CSV exports
        csv_folder = exports_folder / "csv"
        if csv_folder.exists():
            csv_files = list(csv_folder.glob("*.csv"))
            print(f"✅ CSV folder found with {len(csv_files)} files:")
            for file in csv_files:
                size = file.stat().st_size / 1024
                print(f"   • {file.name} ({size:.1f} KB)")
        else:
            print("❌ CSV folder not found")
        
        # Check for JSON exports
        json_folder = exports_folder / "json"
        if json_folder.exists():
            json_files = list(json_folder.glob("*.json"))
            print(f"✅ JSON folder found with {len(json_files)} files:")
            for file in json_files:
                size = file.stat().st_size / 1024
                print(f"   • {file.name} ({size:.1f} KB)")
        else:
            print("❌ JSON folder not found")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run simple export test."""
    print("=" * 50)
    print("SIMPLE EXPORT TEST")
    print("=" * 50)
    
    # Import subprocess here to avoid issues if not available
    global subprocess
    import subprocess
    
    if test_basic_export():
        print("\n✅ Export functionality is working!")
        
        # Show folder structure
        db_folder = Path("db")
        if db_folder.exists():
            print(f"\n📁 Generated folder structure:")
            for item in sorted(db_folder.rglob("*")):
                if item.is_file():
                    relative_path = item.relative_to(db_folder)
                    size = item.stat().st_size / 1024
                    print(f"   📄 {relative_path} ({size:.1f} KB)")
                elif item.is_dir() and item != db_folder:
                    relative_path = item.relative_to(db_folder)
                    print(f"   📁 {relative_path}/")
    else:
        print("\n❌ Export functionality test failed")
    
    # Cleanup option
    cleanup = input("\n🧹 Clean up test files? (y/n): ").lower().strip()
    if cleanup == 'y':
        import shutil
        if Path("db").exists():
            shutil.rmtree("db")
            print("✅ Cleaned up test files")


if __name__ == "__main__":
    main()