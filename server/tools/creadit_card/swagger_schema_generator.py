# swagger_schema_generator.py

"""
Swagger Schema Generator for MCP Server - generates user data based on Swagger schema
without the need for a running FastAPI server.
"""

import json
import os
import random
import pickle
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("swagger_schema_generator")

class SwaggerSchemaGenerator:
    """
    Generates data according to a Swagger/OpenAPI schema without requiring a running server.
    """
    
    def __init__(self, schema_file_path: str = None, data_storage_path: str = "user_data_cache.pkl"):
        """
        Initialize the generator.
        
        Args:
            schema_file_path: Path to the Swagger/OpenAPI schema JSON file
            data_storage_path: Path to store generated user data
        """
        self.data_storage_path = data_storage_path
        
        # Define the schema inline if no file is provided
        self.schema = self._load_schema(schema_file_path) if schema_file_path else self._create_default_schema()
        
        # Load cached user data if it exists
        self.user_data_cache = self._load_user_data_cache()
        
        logger.info("Swagger Schema Generator initialized")
    
    def _load_schema(self, schema_file_path: str) -> Dict[str, Any]:
        """
        Load Swagger/OpenAPI schema from JSON file.
        
        Args:
            schema_file_path: Path to the schema file
            
        Returns:
            The loaded schema
        """
        try:
            with open(schema_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schema file: {e}")
            logger.info("Using default schema instead")
            return self._create_default_schema()
    
    def _create_default_schema(self) -> Dict[str, Any]:
        """
        Create a default Swagger/OpenAPI schema for Discount Bank credit card system.
        
        Returns:
            Default schema
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Discount Bank MCP Server API",
                "description": "API for managing credit card data for Discount Bank agents",
                "version": "1.0.0"
            },
            "components": {
                "schemas": {
                    "LastPayment": {
                        "type": "object",
                        "required": ["amount", "date"],
                        "properties": {
                            "amount": {
                                "type": "number",
                                "format": "float",
                                "description": "סכום התשלום האחרון"
                            },
                            "date": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך התשלום האחרון (YYYY-MM-DD)"
                            }
                        }
                    },
                    "CreditCard": {
                        "type": "object",
                        "required": ["type", "last_four", "expiry", "status"],
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "סוג כרטיס האשראי"
                            },
                            "last_four": {
                                "type": "string",
                                "description": "4 ספרות אחרונות של הכרטיס"
                            },
                            "expiry": {
                                "type": "string",
                                "description": "תאריך תפוגה (MM/YY)"
                            },
                            "status": {
                                "type": "string",
                                "description": "סטטוס הכרטיס (פעיל, חסום, וכו')"
                            }
                        }
                    },
                    "Transaction": {
                        "type": "object",
                        "required": ["date", "merchant", "amount", "status"],
                        "properties": {
                            "date": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך העסקה (YYYY-MM-DD)"
                            },
                            "merchant": {
                                "type": "string",
                                "description": "שם בית העסק"
                            },
                            "amount": {
                                "type": "number",
                                "format": "float",
                                "description": "סכום העסקה"
                            },
                            "status": {
                                "type": "string",
                                "description": "סטטוס העסקה (נרשם, ממתין, וכו')"
                            }
                        }
                    },
                    "SavingsDeposit": {
                        "type": "object",
                        "required": ["amount", "date", "merchant"],
                        "properties": {
                            "amount": {
                                "type": "number",
                                "format": "float",
                                "description": "סכום ההפקדה"
                            },
                            "date": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך ההפקדה (YYYY-MM-DD)"
                            },
                            "merchant": {
                                "type": "string",
                                "description": "מקור ההפקדה (בית עסק)"
                            }
                        }
                    },
                    "SavingsProgram": {
                        "type": "object",
                        "required": ["balance", "last_deposit"],
                        "properties": {
                            "balance": {
                                "type": "number",
                                "format": "float",
                                "description": "יתרת החיסכון"
                            },
                            "last_deposit": {
                                "type": "object",
                                "$ref": "#/components/schemas/SavingsDeposit",
                                "description": "פרטי ההפקדה האחרונה"
                            }
                        }
                    },
                    "TravelInsurance": {
                        "type": "object",
                        "required": ["status", "coverage", "expiry"],
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "סטטוס הביטוח (פעיל, לא פעיל)"
                            },
                            "coverage": {
                                "type": "string",
                                "description": "רמת הכיסוי (בסיסי, מורחב)"
                            },
                            "expiry": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך תפוגה (YYYY-MM-DD)"
                            }
                        }
                    },
                    "FrequentFlyerLastEarned": {
                        "type": "object",
                        "required": ["amount", "date", "source"],
                        "properties": {
                            "amount": {
                                "type": "integer",
                                "description": "כמות הנקודות שנצברו"
                            },
                            "date": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך צבירת הנקודות (YYYY-MM-DD)"
                            },
                            "source": {
                                "type": "string",
                                "description": "מקור צבירת הנקודות"
                            }
                        }
                    },
                    "FrequentFlyer": {
                        "type": "object",
                        "required": ["program", "points", "last_earned"],
                        "properties": {
                            "program": {
                                "type": "string",
                                "description": "שם תוכנית הנוסע המתמיד"
                            },
                            "points": {
                                "type": "integer",
                                "description": "סך נקודות נוסע מתמיד"
                            },
                            "last_earned": {
                                "type": "object",
                                "$ref": "#/components/schemas/FrequentFlyerLastEarned",
                                "description": "פרטי הצבירה האחרונה"
                            }
                        }
                    },
                    "UserData": {
                        "type": "object",
                        "required": [
                            "account_id", "name", "balance", "credit_limit", 
                            "available_credit", "payment_due_date", "last_payment",
                            "cards", "transactions"
                        ],
                        "properties": {
                            "account_id": {
                                "type": "string",
                                "description": "מזהה חשבון"
                            },
                            "name": {
                                "type": "string",
                                "description": "שם הלקוח"
                            },
                            "balance": {
                                "type": "number",
                                "format": "float",
                                "description": "יתרת החיוב בכרטיס"
                            },
                            "credit_limit": {
                                "type": "number",
                                "format": "float",
                                "description": "מסגרת האשראי"
                            },
                            "available_credit": {
                                "type": "number",
                                "format": "float",
                                "description": "אשראי זמין"
                            },
                            "payment_due_date": {
                                "type": "string",
                                "format": "date",
                                "description": "תאריך החיוב הבא (YYYY-MM-DD)"
                            },
                            "last_payment": {
                                "type": "object",
                                "$ref": "#/components/schemas/LastPayment",
                                "description": "פרטי התשלום האחרון"
                            },
                            "cards": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/CreditCard"
                                },
                                "description": "רשימת כרטיסי האשראי"
                            },
                            "transactions": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/Transaction"
                                },
                                "description": "רשימת עסקאות אחרונות"
                            },
                            "savings_program": {
                                "type": "object",
                                "$ref": "#/components/schemas/SavingsProgram",
                                "description": "תוכנית חיסכון (אם קיימת)",
                                "nullable": "true"
                            },
                            "travel_insurance": {
                                "type": "object",
                                "$ref": "#/components/schemas/TravelInsurance",
                                "description": "ביטוח נסיעות (אם קיים)",
                                "nullable": "true"
                            },
                            "frequent_flyer": {
                                "type": "object",
                                "$ref": "#/components/schemas/FrequentFlyer",
                                "description": "נקודות נוסע מתמיד (אם קיימות)",
                                "nullable": "true"  
                            }
                        }
                    }
                }
            },
            "examples": {
                "UserData": {
                    "account_id": "ACC12345",
                    "name": "ישראל ישראלי",
                    "balance": 2450.75,
                    "credit_limit": 5000.00,
                    "available_credit": 2549.25,
                    "payment_due_date": "2025-04-25",
                    "last_payment": {
                        "amount": 500.00,
                        "date": "2025-03-15"
                    },
                    "cards": [
                        {
                            "type": "מפתח דיסקונט רגיל",
                            "last_four": "1234",
                            "expiry": "12/28",
                            "status": "פעיל"
                        }
                    ],
                    "transactions": [
                        {
                            "date": "2025-04-02",
                            "merchant": "סופרמרקט",
                            "amount": 85.43,
                            "status": "נרשם"
                        },
                        {
                            "date": "2025-04-01",
                            "merchant": "תחנת דלק",
                            "amount": 45.25,
                            "status": "נרשם"
                        }
                    ],
                    "savings_program": {
                        "balance": 324.55,
                        "last_deposit": {
                            "amount": 12.50,
                            "date": "2025-04-01",
                            "merchant": "רשת מזון"
                        }
                    }
                }
            }
        }
    
    def _load_user_data_cache(self) -> Dict[str, Dict[str, Any]]:
        """
        Load previously cached user data if it exists.
        
        Returns:
            Dictionary of cached user data by user ID
        """
        try:
            if os.path.exists(self.data_storage_path):
                with open(self.data_storage_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    logger.info(f"Loaded {len(cached_data)} cached user profiles")
                    return cached_data
        except Exception as e:
            logger.error(f"Error loading cached user data: {e}")
        
        return {}
    
    def _save_user_data_cache(self):
        """Save the current user data cache."""
        try:
            with open(self.data_storage_path, 'wb') as f:
                pickle.dump(self.user_data_cache, f)
            logger.info(f"Saved {len(self.user_data_cache)} user profiles to cache")
        except Exception as e:
            logger.error(f"Error saving user data cache: {e}")
    
    def save_schema_to_file(self, file_path: str = "discount_bank_schema.json"):
        """
        Save the current schema to a JSON file.
        
        Args:
            file_path: Path to save the schema
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.schema, f, ensure_ascii=False, indent=2)
            logger.info(f"Schema saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving schema to file: {e}")
    
    def generate_user_data(self, user_id: str) -> Dict[str, Any]:
        """Generate realistic user data."""
        # Generate a random account ID
        account_id = f"ACC{random.randint(10000, 99999)}"
        
        # Generate random balance and credit
        balance = round(random.uniform(1000, 30000), 2)
        available_credit = round(random.uniform(5000, 25000), 2)
        
        # Generate card data
        card_types = [
            "מפתח דיסקונט רגיל",
            "ויזה רגיל",
            "ויזה זהב",
            "ויזה פלטינום",
            "מסטרקארד רגיל",
            "מסטרקארד זהב/פלטינום",
            "דיינרס קלאב רגיל",
            "FLY CARD מפתח דיסקונט",
            "FLY CARD PREMIUM מפתח דיסקונט",
            "דביט רגיל"
        ]
        
        # Generate 1-2 cards for the user
        num_cards = random.randint(1, 2)
        cards = []
        for _ in range(num_cards):
            card = {
                "type": random.choice(card_types),
                "last_four": str(random.randint(1000, 9999)),
                "expiry": f"{random.randint(1,12):02d}/{random.randint(24,30)}",
                "status": "פעיל"
            }
            cards.append(card)
        
        # Generate transaction history
        num_transactions = random.randint(5, 15)
        transactions = []
        merchants = ["סופרמרקט", "חנות אונליין", "תחנת דלק", "מסעדה", "חנות בגדים"]
        
        for _ in range(num_transactions):
            amount = round(random.uniform(50, 1000), 2)
            days_ago = random.randint(0, 365)
            date = (datetime.now() + timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            transaction = {
                "date": date,
                "amount": amount,
                "merchant": random.choice(merchants),
                "status": "נרשם",
                "description": f"עסקה ב{random.choice(merchants)}"
            }
            transactions.append(transaction)
        
        # Sort transactions by date
        transactions.sort(key=lambda x: x["date"], reverse=True)
        
        # Generate rewards data
        rewards = {
            "points": random.randint(1000, 50000),
            "cash_value": round(random.uniform(100, 5000), 2),
            "last_earned": {
                "amount": round(random.uniform(10, 100), 2),
                "date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            }
        }
        
        # Generate account info
        account_info = {
            "account_number": account_id,
            "branch": f"{random.randint(1, 999):03d}",
            "type": "חשבון פרטי",
            "status": "פעיל",
            "balance": balance,
            "available_credit": available_credit
        }

        # Generate name and email
        first_names = ["ישראל", "דוד", "משה", "יעקב", "שרה", "רחל", "לאה", "רבקה"]
        last_names = ["כהן", "לוי", "ישראלי", "דוידוב", "יעקובי", "אברהמי"]
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.replace(' ', '.').lower()}@example.com"
        
        # Create the complete user data structure
        user_data = {
            "user_id": user_id,
            "account_id": account_id,
            "name": name,
            "email": email,
            "account_info": account_info,
            "balance": balance,
            "available_credit": available_credit,
            "cards": cards,
            "transactions": transactions,
            "rewards": rewards,
            "error": None
        }
        
        # Cache the generated data
        self.user_data_cache[user_id] = user_data
        self._save_user_data_cache()
        
        return user_data
    
    def get_user_data(self, user_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get user data for the specified user ID.
        
        Args:
            user_id: The user ID
            fields: Optional list of specific fields to retrieve
            
        Returns:
            User data
        """
        # Check if user exists in cache
        if user_id not in self.user_data_cache:
            # Generate data for new user
            logger.info(f"User {user_id} not found, generating new data")
            self.generate_user_data(user_id)
        
        user_data = self.user_data_cache[user_id]
        
        # If specific fields are requested, filter the data
        if fields:
            result = {}
            for field in fields:
                if field in user_data:
                    result[field] = user_data[field]
                elif "." in field:
                    # Handle nested fields (e.g., "last_payment.amount")
                    parts = field.split(".")
                    current = user_data
                    valid = True
                    for part in parts:
                        if part in current:
                            current = current[part]
                        else:
                            valid = False
                            break
                    if valid:
                        result[field] = current
            return result
        
        # Otherwise return all data
        return user_data
    
    def generate_multiple_users(self, count: int) -> Dict[str, Dict[str, Any]]:
        """
        Generate data for multiple users.
        
        Args:
            count: Number of users to generate
            
        Returns:
            Dictionary of generated user data, keyed by user ID
        """
        result = {}
        for _ in range(count):
            user_id = f"user{uuid.uuid4().hex[:8]}"
            result[user_id] = self.generate_user_data(user_id)
        
        return result
    
    def validate_against_schema(self, data: Dict[str, Any], schema_ref: str) -> bool:
        """
        Validate data against a specific schema reference.
        
        Args:
            data: The data to validate
            schema_ref: The schema reference (e.g., "#/components/schemas/UserData")
            
        Returns:
            True if valid, False otherwise
        """
        # This is a simplified validation. In a real implementation,
        # you would use a proper JSON Schema validator.
        try:
            # Parse the schema reference
            parts = schema_ref.split("/")
            if len(parts) < 4 or parts[0] != "#" or parts[1] != "components" or parts[2] != "schemas":
                raise ValueError(f"Invalid schema reference: {schema_ref}")
            
            schema_name = parts[3]
            schema = self.schema["components"]["schemas"].get(schema_name)
            if not schema:
                raise ValueError(f"Schema not found: {schema_name}")
            
            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Basic type checking for properties
            properties = schema.get("properties", {})
            for field, field_schema in properties.items():
                if field in data:
                    # Check nested objects
                    if field_schema.get("type") == "object" and "$ref" in field_schema:
                        nested_schema_ref = field_schema["$ref"]
                        if not self.validate_against_schema(data[field], nested_schema_ref):
                            return False
                    
                    # Check arrays
                    elif field_schema.get("type") == "array" and "items" in field_schema:
                        item_schema = field_schema["items"]
                        if "$ref" in item_schema:
                            item_schema_ref = item_schema["$ref"]
                            for item in data[field]:
                                if not self.validate_against_schema(item, item_schema_ref):
                                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


class MCPServerWithSwagger:
    """
    MCP Server implementation that uses Swagger schema to generate and validate data.
    """
    
    def __init__(self, data_storage_path: str = "user_data_cache.pkl"):
        """
        Initialize the MCP server with Swagger schema generator.
        
        Args:
            data_storage_path: Path to store dynamically generated user data
        """
        self.schema_generator = SwaggerSchemaGenerator(data_storage_path=data_storage_path)
        self.private_data = self.schema_generator.user_data_cache
        self.public_data = {}  # Would load public card data here
        logger.info("MCP Server initialized with Swagger schema generator")
    
    async def get_private_data(self, user_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get private data for a specific user.
        
        Args:
            user_id: The user identifier
            fields: Optional list of specific fields to retrieve
            
        Returns:
            User data dictionary
        """
        logger.info(f"Getting private data for user {user_id}, fields: {fields}")
        
        return self.schema_generator.get_user_data(user_id, fields)
    
    
    def generate_user_data(self, user_id: str = None) -> Dict[str, Any]:
        """
        Generate user data based on the Swagger schema.
        
        Args:
            user_id: Optional user ID
            
        Returns:
            Generated user data
        """
        return self.schema_generator.generate_user_data(user_id)


# Example usage
def main():
    # Create the schema generator
    generator = SwaggerSchemaGenerator()
    
    # Save the schema to a file
    generator.save_schema_to_file()
    
    # Generate a user
    user_data = generator.generate_user_data()
    print(f"Generated user data: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
    
    # Create MCP server with Swagger schema
    server = MCPServerWithSwagger()
    
    # Generate data for 5 users
    users = generator.generate_multiple_users(5)
    print(f"Generated {len(users)} users")
    
    # Validate a user against the schema
    is_valid = generator.validate_against_schema(user_data, "#/components/schemas/UserData")
    print(f"User data is valid: {is_valid}")


if __name__ == "__main__":
    main()