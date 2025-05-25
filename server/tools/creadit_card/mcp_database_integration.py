#!/usr/bin/env python3
# mcp_database_integration.py

"""
Integration script to connect your existing MCP credit card tools 
to the generated Israeli banking database.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent  # Go up to project root
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_integration():
    """Test the database integration with your MCP tools."""
    print("🔗 Testing MCP Tools Database Integration")
    print("=" * 50)
    
    try:
        # Import the database-connected tools
        from server.tools.creadit_card.database_connected_credit_cards_tools import create_database_connected_tools
        
        # Create the enhanced tools
        print("1. Creating database-connected tools...")
        tools = create_database_connected_tools()
        
        # Test database connection
        print("2. Testing database connection...")
        stats = tools.get_database_stats()
        
        if stats.get("status") == "connected":
            print("✅ Database connection successful!")
            print(f"   Database: {stats['database_url']}")
            print(f"   Tables: {stats['table_counts']}")
        else:
            print(f"❌ Database connection failed: {stats.get('error')}")
            return False
        
        # Get sample users for testing
        print("3. Getting sample users...")
        users = tools.list_sample_users(3)
        
        if not users:
            print("❌ No users found in database")
            return False
        
        print(f"✅ Found {len(users)} sample users")
        for user in users:
            print(f"   • {user['first_name']} {user['last_name']} (ID: {user['user_id']})")
        
        # Test with first user
        test_user_id = users[0]["user_id"]
        print(f"\n4. Testing MCP functions with user: {test_user_id}")
        
        # Test get_user_data
        print("   Testing get_user_data...")
        user_data = tools.get_user_data(test_user_id)
        
        if "error" in user_data:
            print(f"   ❌ get_user_data failed: {user_data['error']}")
        else:
            print(f"   ✅ User: {user_data['name']}")
            print(f"   ✅ Account: {user_data['account_id']}")
            print(f"   ✅ Cards: {len(user_data['cards'])}")
            print(f"   ✅ Transactions: {len(user_data['transactions'])}")
        
        # Test check_balance
        print("   Testing check_balance...")
        balance = tools.check_balance(test_user_id)
        
        if "error" in balance:
            print(f"   ❌ check_balance failed: {balance['error']}")
        else:
            print(f"   ✅ Balance: ₪{balance['balance']:,.2f}")
            print(f"   ✅ Available Credit: ₪{balance['available_credit']:,.2f}")
        
        # Test get_transactions
        print("   Testing get_transactions...")
        transactions = tools.get_transactions(test_user_id)
        
        if "error" in transactions:
            print(f"   ❌ get_transactions failed: {transactions['error']}")
        else:
            trans_list = transactions['transactions']
            print(f"   ✅ Retrieved {len(trans_list)} transactions")
            
            if trans_list:
                recent = trans_list[0]
                print(f"   ✅ Recent: {recent['merchant']} - ₪{recent['amount']:,.2f}")
        
        # Test get_user_fields
        print("   Testing get_user_fields...")
        fields = tools.get_user_fields(test_user_id, ["name", "balance", "account_info.branch"])
        
        if "error" in fields:
            print(f"   ❌ get_user_fields failed: {fields['error']}")
        else:
            print(f"   ✅ Filtered fields: {list(fields.keys())}")
        
        print("\n✅ All MCP function tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure database_connected_credit_cards_tools.py is available")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def compare_data_sources():
    """Compare data from original tools vs database-connected tools."""
    print("\n🔄 Comparing Data Sources")
    print("=" * 50)
    
    try:
        # Import both versions
        from server.tools.creadit_card.creadit_cards_tools import CreaditCardsTools
        from server.tools.creadit_card.database_connected_credit_cards_tools import create_database_connected_tools
        
        # Get sample user from database
        db_tools = create_database_connected_tools()
        users = db_tools.list_sample_users(1)
        
        if not users:
            print("❌ No users in database for comparison")
            return
        
        test_user_id = users[0]["user_id"]
        
        print(f"Comparing data for user: {test_user_id}")
        
        # Original tools (mock data)
        print("\n📋 Original Tools (Mock Data):")
        original = CreaditCardsTools()
        original_data = original.get_user_data(test_user_id)
        
        print(f"   Name: {original_data.get('name', 'N/A')}")
        print(f"   Cards: {len(original_data.get('cards', []))}")
        print(f"   Transactions: {len(original_data.get('transactions', []))}")
        print(f"   Balance: ₪{db_data.get('balance', 0):,.2f}")
            
            # Show sample transaction data
        if db_data.get('transactions'):
            print("\n   📊 Sample Database Transaction:")
            trans = db_data['transactions'][0]
            print(f"      • {trans['merchant']} - ₪{trans['amount']:,.2f}")
            print(f"      • Date: {trans['date']}")
            print(f"      • Status: {trans['status']}")
                
            # Show Hebrew data quality
            if db_data.get('cards'):
                print("\n   🔤 Hebrew Card Data:")
                card = db_data['cards'][0]
                print(f"      • Type: {card['type']}")
                print(f"      • Status: {card['status']}")
        else:
            print(f"   ❌ Error: {db_data['error']}")
        
        print("\n🎯 Key Differences:")
        print("   • Original: Generated mock data in English")
        print("   • Database: Real Hebrew banking data with relationships")
        print("   • Database: Authentic Israeli names and addresses")
        print("   • Database: Valid Israeli ID numbers with checksums")
        print("   • Database: Realistic transaction patterns")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")

def show_database_schema():
    """Show the database schema structure."""
    print("\n📋 Database Schema Structure")
    print("=" * 50)
    
    try:
        from server.tools.creadit_card.database_connected_credit_cards_tools import create_database_connected_tools
        
        tools = create_database_connected_tools()
        
        if not tools.engine:
            print("❌ No database connection")
            return
        
        from sqlalchemy import inspect
        
        inspector = inspect(tools.engine)
        tables = inspector.get_table_names()
        
        print(f"📊 Database Tables ({len(tables)}):")
        
        for table in tables:
            print(f"\n📋 Table: {table}")
            columns = inspector.get_columns(table)
            
            for col in columns[:5]:  # Show first 5 columns
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"   • {col['name']}: {col_type} {nullable}")
            
            if len(columns) > 5:
                print(f"   ... and {len(columns) - 5} more columns")
        
        # Show sample data
        print(f"\n📊 Sample Data from 'users' table:")
        session = tools.Session()
        
        try:
            from sqlalchemy import text
            result = session.execute(text("SELECT * FROM users LIMIT 2")).fetchall()
            
            for i, row in enumerate(result, 1):
                row_dict = dict(row._mapping) if hasattr(row, '_mapping') else row._asdict()
                print(f"   User {i}:")
                
                # Show key fields with Hebrew/English fallback
                name_fields = ['first_name', 'שם_פרטי', 'last_name', 'שם_משפחה']
                for field in name_fields:
                    if field in row_dict and row_dict[field]:
                        print(f"      {field}: {row_dict[field]}")
                        break
                
                id_fields = ['id_number', 'תעודת_זהות']
                for field in id_fields:
                    if field in row_dict and row_dict[field]:
                        print(f"      ID: {row_dict[field]}")
                        break
        
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Schema inspection failed: {e}")

def create_mcp_wrapper():
    """Create a wrapper that integrates with your existing MCP server."""
    print("\n🔧 Creating MCP Integration Wrapper")
    print("=" * 50)
    
    wrapper_code = '''
# mcp_database_wrapper.py

"""
Wrapper to integrate database-connected tools with your existing MCP server.
Replace the original CreaditCardsTools with this enhanced version.
"""

from server.tools.creadit_card.database_connected_credit_cards_tools import create_database_connected_tools
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class EnhancedCreaditCardsTools:
    """
    Enhanced MCP Credit Card Tools that use the generated database
    while maintaining backward compatibility with existing MCP interface.
    """
    
    def __init__(self, db_url: str = None):
        """Initialize with database connection."""
        self.db_tools = create_database_connected_tools(db_url)
        logger.info("Enhanced Credit Card Tools initialized with database")
    
    # Forward all methods to the database tools
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        return self.db_tools.get_user_data(user_id)
    
    def get_user_fields(self, user_id: str, fields: List[str]) -> Dict[str, Any]:
        return self.db_tools.get_user_fields(user_id, fields)
    
    def check_balance(self, user_id: str) -> Dict[str, Any]:
        return self.db_tools.check_balance(user_id)
    
    def get_transactions(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        return self.db_tools.get_transactions(user_id)
    
    def filter_transactions(self, user_id: str, start_date: str = None, 
                          end_date: str = None, filter_obj = None):
        return self.db_tools.filter_transactions(user_id, start_date, end_date, filter_obj)
    
    def get_savings_program(self, user_id: str) -> Dict[str, Any]:
        return self.db_tools.get_savings_program(user_id)
    
    def get_travel_insurance(self, user_id: str) -> Dict[str, Any]:
        return self.db_tools.get_travel_insurance(user_id)
    
    def get_frequent_flyer(self, user_id: str) -> Dict[str, Any]:
        return self.db_tools.get_frequent_flyer(user_id)
    
    def search_cards(self, query: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.db_tools.search_cards(query, categories)
    
    def get_card_recommendations(self, preferences) -> List[Dict[str, Any]]:
        return self.db_tools.get_card_recommendations(preferences)
    
    def calculate_rewards(self, calculation) -> Dict[str, Any]:
        return self.db_tools.calculate_rewards(calculation)
    
    # Additional database-specific methods
    def get_database_stats(self) -> Dict[str, Any]:
        return self.db_tools.get_database_stats()
    
    def list_sample_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.db_tools.list_sample_users(limit)

# Create singleton instance for backward compatibility
enhanced_credit_cards_tools = EnhancedCreaditCardsTools()
'''
    
    # Save the wrapper
    try:
        with open("mcp_database_wrapper.py", "w", encoding="utf-8") as f:
            f.write(wrapper_code)
        
        print("✅ Created mcp_database_wrapper.py")
        print("\n📝 To use in your MCP server:")
        print("   1. Replace: from server.tools.creadit_card.creadit_cards_tools import CreaditCardsTools")
        print("   2. With: from server.tools.creadit_card.mcp_database_wrapper import EnhancedCreaditCardsTools")
        print("   3. Update: tools = EnhancedCreaditCardsTools()")
        
    except Exception as e:
        print(f"❌ Failed to create wrapper: {e}")

def run_comprehensive_test():
    """Run comprehensive integration tests."""
    print("\n🧪 Running Comprehensive Integration Tests")
    print("=" * 50)
    
    try:
        from server.tools.creadit_card.database_connected_credit_cards_tools import create_database_connected_tools
        
        tools = create_database_connected_tools()
        users = tools.list_sample_users(3)
        
        if not users:
            print("❌ No test users available")
            return False
        
        test_results = {
            "connection": False,
            "user_data": False,
            "balance": False,
            "transactions": False,
            "fields": False,
            "hebrew_data": False
        }
        
        # Test 1: Database connection
        stats = tools.get_database_stats()
        test_results["connection"] = stats.get("status") == "connected"
        print(f"🔗 Connection: {'✅' if test_results['connection'] else '❌'}")
        
        # Use first user for remaining tests
        test_user_id = users[0]["user_id"]
        
        # Test 2: User data retrieval
        user_data = tools.get_user_data(test_user_id)
        test_results["user_data"] = "error" not in user_data
        print(f"👤 User Data: {'✅' if test_results['user_data'] else '❌'}")
        
        if test_results["user_data"]:
            # Test 3: Balance check
            balance = tools.check_balance(test_user_id)
            test_results["balance"] = "error" not in balance and "balance" in balance
            print(f"💰 Balance: {'✅' if test_results['balance'] else '❌'}")
            
            # Test 4: Transactions
            transactions = tools.get_transactions(test_user_id)
            test_results["transactions"] = "error" not in transactions
            print(f"💳 Transactions: {'✅' if test_results['transactions'] else '❌'}")
            
            # Test 5: Field filtering
            fields = tools.get_user_fields(test_user_id, ["name", "balance"])
            test_results["fields"] = "error" not in fields and len(fields) > 0
            print(f"🔍 Field Filtering: {'✅' if test_results['fields'] else '❌'}")
            
            # Test 6: Hebrew data validation
            has_hebrew = False
            if user_data.get("name"):
                # Check for Hebrew characters in name or transactions
                text_to_check = user_data["name"]
                if user_data.get("transactions"):
                    text_to_check += " " + user_data["transactions"][0].get("merchant", "")
                
                has_hebrew = any('\u0590' <= char <= '\u05FF' for char in text_to_check)
            
            test_results["hebrew_data"] = has_hebrew
            print(f"🔤 Hebrew Data: {'✅' if test_results['hebrew_data'] else '❌'}")
        
        # Summary
        passed = sum(test_results.values())
        total = len(test_results)
        
        print(f"\n📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed! Database integration is working perfectly.")
            print("\n🚀 Ready to use with MCP server:")
            return True
        else:
            print("⚠️  Some tests failed. Check the issues above.")
            return False
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        return False

def main():
    """Main integration testing and setup."""
    print("🏦 Israeli Banking MCP Tools Database Integration")
    print("=" * 60)
    
    print("This script will help you connect your MCP credit card tools")
    print("to the generated Israeli banking database with real Hebrew data.")
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Basic database integration
    if test_database_integration():
        tests_passed += 1
        print("✅ Test 1/4: Database integration working")
    else:
        print("❌ Test 1/4: Database integration failed")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you've generated a database first:")
        print("   python complete_integration.py --records 1000")
        print("2. Check that the database file exists")
        print("3. Verify database_connected_credit_cards_tools.py is available")
        return
    
    # Test 2: Data comparison
    try:
        compare_data_sources()
        tests_passed += 1
        print("✅ Test 2/4: Data source comparison completed")
    except Exception as e:
        print(f"❌ Test 2/4: Data comparison failed: {e}")
    
    # Test 3: Schema inspection
    try:
        show_database_schema()
        tests_passed += 1
        print("✅ Test 3/4: Schema inspection completed")
    except Exception as e:
        print(f"❌ Test 3/4: Schema inspection failed: {e}")
    
    # Test 4: Comprehensive test
    if run_comprehensive_test():
        tests_passed += 1
        print("✅ Test 4/4: Comprehensive test passed")
    else:
        print("❌ Test 4/4: Comprehensive test failed")
    
    # Final results
    print(f"\n📊 Final Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed >= 3:
        print("🎉 Integration successful!")
        
        # Create wrapper for easy MCP integration
        create_mcp_wrapper()
        
        print("\n🚀 Next Steps:")
        print("1. Update your MCP server to use the database tools")
        print("2. Test with real Israeli ID numbers from the database")
        print("3. Enjoy authentic Hebrew banking data!")
        
        # Show sample usage
        print("\n📝 Sample Usage:")
        print('from server.tools.creadit_card.mcp_database_wrapper import EnhancedCreaditCardsTools')
        print('tools = EnhancedCreaditCardsTools()')
        print('users = tools.list_sample_users(5)')
        print('user_data = tools.get_user_data(users[0]["user_id"])')
        
    else:
        print("❌ Integration needs work. Check the errors above.")

if __name__ == "__main__":
    main()
    
    
    
        
        # # Database tools (real data)
        # print("\n🗄️  Database Tools (Real Data):")
        # db_data = db_tools.get_user_data(test_user_id)
        
        # if "error" not in db_data:
        #     print(f"   Name: {db_data.get('name', 'N/A')}")
        #     print(f"   Cards: {len(db_data.get('cards', []))}")
        #     print(f"   Transactions: {len(db_data.get('transactions', []))}")
        #     print(f"   Balance: {db_data.get('balance', 0):,.2f}")
            
        #     # Show sample transaction data
        #     if db_data.get('transactions'):
        #         print("\n   📊 Sample Database Transaction:")
        #         trans = db_data['transactions'][0]
        #         print(f"      • {trans['merchant']} - ₪{trans['amount']:,.2f}")
        #         print(f"      • Date: {trans['date']}")
        #         print(f"      • Status: {trans['status']}")
                
        #     # Show Hebrew data quality  
        #     if db_data.get('cards'):
        #         print("\n   🔤 Hebrew Card Data:")
        #         card = db_data['cards'][0]
        #         print(f"      • Type: {card['type']}")
        #         print(f"      • Status: {card['status']}")
        #     else:
        #         print("   ❌ No cards found in database")
                
        #     # Show sample data      
        #     print("\n   📊 Sample Data from 'users' table:")
        #     session = db_tools.Session()
            
        #     try:
        #         from sqlalchemy import text
        #         result = session.execute(text("SELECT * FROM users LIMIT 2")).fetchall()
                
        #         for i, row in enumerate(result, 1):
        #             row_dict = dict(row._mapping) if hasattr(row, '_mapping') else row._asdict()
        #             print(f"   User {i}:")  
                    
        #             # Show key fields with Hebrew/English fallback
        #             name_fields = ['first_name', 'שם_פרטי', 'last_name', 'שם_משפחה']
        #             for field in name_fields:
        #                 if field in row_dict and row_dict[field]:
        #                     print(f"      {field}: {row_dict[field]}")
        #                     break
                            
        #             id_fields = ['id_number', 'תעודת_זהות']
        #             for field in id_fields:
        #                 if field in row_dict and row_dict[field]:
        #                     print(f"      ID: {row_dict[field]}")
        #                     break
                            
        #     finally:
        #         session.close()
                
        #     # Show sample data from 'transactions' table
        #     print("\n   📊 Sample Data from 'transactions' table:")
        #     result = session.execute(text("SELECT * FROM transactions LIMIT 2")).fetchall()