# database_connected_credit_cards_tools.py

"""
Enhanced Credit Card Tools that connect to the generated Israeli banking database
instead of using mock data. This provides real Hebrew banking data with proper relationships.
"""

from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
import random
import uuid
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import pandas as pd

# Import your existing models
from server.tools.creadit_card.creadit_cards_tools import Card, Transaction, SavingsDeposit, UserPreferences, TransactionFilter, RewardsCalculation

# Configuration
from config.config import config

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectedCreditCardsTools:
    """
    Enhanced Credit Card Tools that work with the generated Israeli banking database.
    Provides real Hebrew data with authentic Israeli banking information.
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize with database connection.
        
        Args:
            db_url: Database URL. If None, will try to find generated database.
        """
        self.db_url = db_url or self._find_database()
        self.engine = None
        self.Session = None
        self._setup_database_connection()
        self._validate_database_schema()
        
        logger.info(f"Database-Connected Credit Card Tools initialized with DB: {self.db_url}")
    
    def _find_database(self) -> str:
        """Find the database file."""
        # First try to use the database URL from config
        if hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
            db_url = config.DATABASE_URL
            # If the URL points to israeli_banking_data.db, replace it with israeli_banking_swagger_faker.db
            if db_url.endswith('israeli_banking_data.db'):
                db_url = db_url.replace('israeli_banking_data.db', 'israeli_banking_swagger_faker.db')
            logger.info(f"Using database URL from config: {db_url}")
            return db_url

        # If no config or invalid URL, try to find the database in common locations
        common_locations = [
            "db/israeli_banking_swagger_faker.db",
            "israeli_banking_swagger_faker.db",
            "../db/israeli_banking_swagger_faker.db",
            "../../db/israeli_banking_swagger_faker.db"
        ]

        for location in common_locations:
            if os.path.exists(location):
                logger.info(f"Found database at: {location}")
                return f"sqlite:///{location}"

        raise FileNotFoundError("Could not find the database file. Please ensure it exists in one of the common locations.")
    
    def _setup_database_connection(self):
        """Setup SQLAlchemy connection to the database."""
        try:
            self.engine = create_engine(self.db_url)
            self.Session = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Database connection established successfully")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _validate_database_schema(self):
        """Validate that the required tables exist in the database."""
        required_tables = ['users', 'accounts', 'credit_cards', 'transactions']
        
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.warning(f"⚠️  Missing tables: {missing_tables}")
                logger.info("Available tables:", existing_tables)
            else:
                logger.info("✅ All required tables found in database")
                
        except Exception as e:
            logger.error(f"❌ Schema validation failed: {e}")
    
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user data from the database.
        
        Args:
            user_id: Israeli ID number (תעודת זהות)
            
        Returns:
            Complete user data with account, cards, and transactions
        """
        logger.info(f"Getting database user data for: {user_id}")
        
        try:
            session = self.Session()
            
            # Get user information
            user_query = text("""
                SELECT * FROM users 
                WHERE israeli_id = :user_id
                LIMIT 1
            """)
            user_result = session.execute(user_query, {"user_id": user_id}).fetchone()
            
            if not user_result:
                logger.warning(f"User {user_id} not found in database")
                return {"error": f"User {user_id} not found"}
            
            # Convert to dict (handle different SQLAlchemy versions)
            if hasattr(user_result, '_asdict'):
                user_data = user_result._asdict()
            else:
                user_data = dict(user_result._mapping)
            
            # Get account information
            account_query = text("""
                SELECT * FROM accounts 
                WHERE israeli_id = :user_id
            """)
            account_results = session.execute(account_query, {"user_id": user_id}).fetchall()
            accounts = [dict(row._mapping) if hasattr(row, '_mapping') else row._asdict() for row in account_results]
            
            # Get credit cards
            cards_query = text("""
                SELECT * FROM credit_cards 
                WHERE israeli_id = :user_id
            """)
            card_results = session.execute(cards_query, {"user_id": user_id}).fetchall()
            cards = [dict(row._mapping) if hasattr(row, '_mapping') else row._asdict() for row in card_results]
            
            # Get recent transactions (limit to last 20)
            transactions_query = text("""
                SELECT t.* FROM transactions t
                JOIN credit_cards c ON t.card_number = c.card_number
                WHERE c.israeli_id = :user_id
                ORDER BY t.transaction_date DESC
                LIMIT 20
            """)
            transaction_results = session.execute(transactions_query, {"user_id": user_id}).fetchall()
            transactions = [dict(row._mapping) if hasattr(row, '_mapping') else row._asdict() for row in transaction_results]
            
            # Get default account if none exists
            default_account = {
                'account_number': f"ACC{user_id}",
                'balance': 0,
                'available_credit': 0,
                'bank_branch': 1
            }
            
            # Format response to match MCP tools API
            response_data = {
                "user_id": user_id,
                "account_id": accounts[0].get('account_number', default_account['account_number']) if accounts else default_account['account_number'],
                "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
                "email": user_data.get('email', ''),
                "balance": accounts[0].get('balance', default_account['balance']) if accounts else default_account['balance'],
                "available_credit": accounts[0].get('available_credit', default_account['available_credit']) if accounts else default_account['available_credit'],
                "cards": [
                    {
                        "type": card.get('card_type', 'Unknown'),
                        "last_four": str(card.get('card_number', '0000'))[-4:],
                        "expiry": str(card.get('expiry_date', '12/28')),
                        "status": card.get('status', 'active')
                    } for card in cards
                ] if cards else [],
                "transactions": [
                    {
                        "date": str(trans.get('transaction_date', '')),
                        "merchant": trans.get('merchant_name', 'Unknown Merchant'),
                        "amount": float(trans.get('amount', 0)),
                        "status": trans.get('status', 'pending'),
                        "description": trans.get('description', f"Transaction at {trans.get('merchant_name', 'business')}")
                    } for trans in transactions
                ] if transactions else [],
                "account_info": {
                    "account_number": accounts[0].get('account_number', default_account['account_number']) if accounts else default_account['account_number'],
                    "branch": f"{accounts[0].get('bank_branch', default_account['bank_branch']):03d}" if accounts else f"{default_account['bank_branch']:03d}",
                    "type": accounts[0].get('account_type', 'checking') if accounts else 'checking',
                    "status": accounts[0].get('status', 'active') if accounts else 'active'
                }
            }
            
            logger.info(f"✅ Retrieved data for user {user_id} from database")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error getting user data: {e}")
            return {"error": f"Failed to get user data: {str(e)}"}
        finally:
            session.close()
    
    def get_user_fields(self, user_id: str, fields: List[str]) -> Dict[str, Any]:
        """Get specific fields for a user from database."""
        logger.info(f"Getting specific fields for user {user_id}: {fields}")
        
        # Get full user data first
        user_data = self.get_user_data(user_id)
        
        if "error" in user_data:
            return user_data
        
        # Filter to requested fields
        result = {}
        for field in fields:
            if field in user_data:
                result[field] = user_data[field]
            elif "." in field:
                # Handle nested fields (e.g., "account_info.balance")
                parts = field.split(".")
                current = user_data
                valid = True
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        valid = False
                        break
                if valid:
                    result[field] = current
        
        return result
    
    def check_balance(self, user_id: str) -> Dict[str, Any]:
        """Check account balance from database."""
        logger.info(f"Checking balance for user {user_id}")
        
        user_data = self.get_user_data(user_id)
        
        if "error" in user_data:
            return user_data
        
        return {
            "balance": user_data.get("balance", 0),
            "available_credit": user_data.get("available_credit", 0),
            "account_info": user_data.get("account_info", {})
        }
    
    def get_transactions(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get transaction history from database."""
        logger.info(f"Getting transactions for user {user_id}")
        
        user_data = self.get_user_data(user_id)
        
        if "error" in user_data:
            return user_data
        
        return {"transactions": user_data.get("transactions", [])}
    
    def filter_transactions(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter: Optional[TransactionFilter] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Filter transactions by date range."""
        logger.info(f"Filtering transactions for user {user_id}")
        
        # Get all transactions first
        result = self.get_transactions(user_id)
        
        if "error" in result:
            return result
        
        transactions = result.get("transactions", [])
        
        # Use filter object if provided
        if filter:
            start_date = filter.start_date
            end_date = filter.end_date
        
        # Apply date filters
        if start_date or end_date:
            filtered_transactions = []
            for transaction in transactions:
                transaction_date = transaction.get("date", "")
                
                if start_date and transaction_date < start_date:
                    continue
                
                if end_date and transaction_date > end_date:
                    continue
                
                filtered_transactions.append(transaction)
            
            return {"transactions": filtered_transactions}
        
        return result
    
    def get_savings_program(self, user_id: str) -> Dict[str, Any]:
        """Get savings program info (mock implementation for now)."""
        logger.info(f"Getting savings program for user {user_id}")
        
        # This would be extended with actual savings data from database
        return {
            "balance": random.uniform(100, 5000),
            "last_deposit": {
                "amount": random.uniform(10, 500),
                "date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                "merchant": "הפקדה אוטומטית"
            },
            "status": "פעיל"
        }
    
    def get_travel_insurance(self, user_id: str) -> Dict[str, Any]:
        """Get travel insurance info (mock implementation)."""
        return {
            "status": "פעיל",
            "coverage": "מורחב",
            "expiry": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        }
    
    def get_frequent_flyer(self, user_id: str) -> Dict[str, Any]:
        """Get frequent flyer info (mock implementation)."""
        return {
            "program": "אל על מטוס משאלות",
            "points": random.randint(1000, 50000),
            "status": "פעיל",
            "last_earned": {
                "amount": random.randint(100, 1000),
                "date": (datetime.now() - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
                "source": "טיסה לאירופה"
            }
        }
    
    def search_cards(self, query: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for credit cards (uses existing implementation)."""
        # This can remain the same as the original implementation
        card_types = [
            {
                "cardType": "מפתח דיסקונט רגיל",
                "cardBrand": "Visa",
                "cardIssuer": "Discount Bank",
                "features": ["כניסה לטרקלין דן", "ביטוח נסיעות בסיסי", "הנחות ברשתות נבחרות"],
                "benefits": ["צבירת נקודות מפתח", "אפשרות לפריסת תשלומים", "אבטחה מתקדמת"],
                "fees": {"annual": 120, "international": "2.5%", "minFee": 10}
            },
            {
                "cardType": "FLY CARD מפתח דיסקונט",
                "cardBrand": "MasterCard", 
                "cardIssuer": "Discount Bank",
                "features": ["צבירת נקודות טיסה", "ביטוח נסיעות מורחב", "כניסה לטרקליני VIP"],
                "benefits": ["הנחות בטיסות", "צבירה מוגברת על הוצאות בחו״ל", "שירות קונסיירז'"],
                "fees": {"annual": 250, "international": "2.0%", "minFee": 8}
            }
        ]
        
        # Filter by query
        if query:
            query = query.lower()
            card_types = [card for card in card_types if query in card["cardType"].lower() or 
                        query in card["cardBrand"].lower() or
                        any(query in feature.lower() for feature in card["features"])]
        
        return {
            "matching_cards": card_types,
            "matching_faqs": [],
            "matching_services": {}
        }
    
    def get_card_recommendations(self, preferences: Union[str, UserPreferences]) -> List[Dict[str, Any]]:
        """Get card recommendations (uses existing logic)."""
        # Can use the existing implementation from the original tools
        if isinstance(preferences, str):
            card_type = preferences.upper()
            cards = [
                {
                    "cardType": "מפתח דיסקונט רגיל",
                    "cardBrand": "Visa",
                    "score": 85 if "VISA" in card_type else 70
                },
                {
                    "cardType": "FLY CARD מפתח דיסקונט", 
                    "cardBrand": "MasterCard",
                    "score": 85 if "MASTER" in card_type else 70
                }
            ]
            return [card for card in cards if card["score"] >= 80]
        
        return []
    
    def calculate_rewards(self, calculation: RewardsCalculation) -> Dict[str, Any]:
        """Calculate rewards (uses existing logic)."""
        points_multiplier = 1.0
        if "premium" in calculation.card_type.lower():
            points_multiplier = 2.0
        elif "platinum" in calculation.card_type.lower():
            points_multiplier = 3.0
        elif "fly card" in calculation.card_type.lower():
            points_multiplier = 2.5
            
        points = calculation.spending_amount * points_multiplier
        
        return {
            "rewards": {
                "points": points,
                "cash_value": points / 100,
                "card_type": calculation.card_type,
                "points_multiplier": points_multiplier
            }
        }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the connected database."""
        try:
            session = self.Session()
            
            stats = {}
            
            # Count records in each table
            tables = ['users', 'accounts', 'credit_cards', 'transactions']
            
            for table in tables:
                try:
                    count_query = text(f"SELECT COUNT(*) as count FROM {table}")
                    result = session.execute(count_query).fetchone()
                    stats[table] = result.count if result else 0
                except Exception as e:
                    logger.warning(f"Could not count {table}: {e}")
                    stats[table] = "Unknown"
            
            session.close()
            return {
                "database_url": self.db_url,
                "table_counts": stats,
                "status": "connected"
            }
            
        except Exception as e:
            return {
                "database_url": self.db_url,
                "error": str(e),
                "status": "error"
            }
    
    def list_sample_users(self, limit: int = 3) -> List[Dict[str, Any]]:
        """List sample users from the database."""
        try:
            with self.Session() as session:
                result = session.execute(text("""
                    SELECT 
                        israeli_id as user_id,
                        first_name,
                        last_name,
                        email
                    FROM users 
                    LIMIT :limit
                """), {"limit": limit})
                users = [dict(row._mapping) for row in result]
                return users
        except Exception as e:
            logger.error(f"Error listing sample users: {e}")
            return []


# Create the enhanced tools instance
def create_database_connected_tools(db_url: str = None) -> DatabaseConnectedCreditCardsTools:
    """
    Factory function to create database-connected credit card tools.
    
    Args:
        db_url: Optional database URL. If None, will auto-detect.
        
    Returns:
        DatabaseConnectedCreditCardsTools instance
    """
    return DatabaseConnectedCreditCardsTools(db_url=db_url)


# Example usage and testing
if __name__ == "__main__":
    # Test the database connection
    tools = create_database_connected_tools()
    
    # Get database stats
    stats = tools.get_database_stats()
    print("Database Stats:", stats)
    
    # List sample users
    users = tools.list_sample_users(5)
    print(f"Sample users: {len(users)}")
    
    if users:
        # Test with first user
        test_user_id = users[0]["user_id"]
        print(f"Testing with user: {test_user_id}")
        
        # Get user data
        user_data = tools.get_user_data(test_user_id)
        print(f"User data keys: {list(user_data.keys())}")
        
        # Check balance
        balance = tools.check_balance(test_user_id)
        print(f"Balance: {balance}")
        
        # Get transactions
        transactions = tools.get_transactions(test_user_id)
        print(f"Transactions: {len(transactions.get('transactions', []))}")