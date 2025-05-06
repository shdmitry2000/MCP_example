from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import random
import uuid
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import sys
from pathlib import Path



from .swagger_schema_generator import SwaggerSchemaGenerator
from config.config import config

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# Pydantic models for request/response validation
class Card(BaseModel):
    type: str = Field(..., description="סוג כרטיס האשראי")
    last_four: str = Field(..., description="4 ספרות אחרונות של הכרטיס") 
    expiry: str = Field(..., description="תאריך תפוגה (MM/YY)")
    status: str = Field(..., description="סטטוס הכרטיס (פעיל, חסום, וכו')")
    
class Transaction(BaseModel):
    date: str = Field(..., description="תאריך העסקה (YYYY-MM-DD)")
    merchant: str = Field(..., description="שם בית העסק")
    amount: float = Field(..., description="סכום העסקה")
    status: str = Field(..., description="סטטוס העסקה (נרשם, ממתין, וכו')")
    description: Optional[str] = Field(None, description="תיאור העסקה")

class SavingsDeposit(BaseModel):
    amount: float = Field(..., description="סכום ההפקדה")
    date: str = Field(..., description="תאריך ההפקדה (YYYY-MM-DD)")
    merchant: str = Field(..., description="מקור ההפקדה (בית עסק)")

class UserPreferences(BaseModel):
    travel_frequency: Optional[str] = Field(None, description="How often the user travels")
    savings_focus: Optional[str] = Field(None, description="User's interest in savings")
    premium_benefits: Optional[str] = Field(None, description="User's interest in premium benefits")
    budget_control: Optional[str] = Field(None, description="User's need for budget control")

class TransactionFilter(BaseModel):
    start_date: Optional[str] = Field(None, description="Start date for filtering transactions (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for filtering transactions (YYYY-MM-DD)")

class RewardsCalculation(BaseModel):
    spending_amount: float = Field(..., description="Amount spent in currency")
    card_type: str = Field(..., description="Type of credit card")

class CreaditCardsTools:
    DATA_STORAGE_PATH = "user_data_cache.pkl"
    # Initialize Schema Generator for data
    schema_generator = SwaggerSchemaGenerator(data_storage_path=DATA_STORAGE_PATH)

    # Load or initialize user data cache
    private_data = schema_generator.user_data_cache

    def __init__(self):
        pass

    # Utility functions
    @staticmethod
    def ensure_user_exists(user_id: str) -> Dict[str, Any]:
        """Ensure user exists in the database, create if not"""
        if user_id not in credit_cards_tools.private_data:
            logger.info(f"Generating data for new user {user_id}")
            user_data = credit_cards_tools.schema_generator.generate_user_data(user_id)
            credit_cards_tools.private_data[user_id] = user_data
            return user_data
        return credit_cards_tools.private_data[user_id]

    @staticmethod
    def filter_user_fields(user_data: Dict[str, Any], fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Filter user data to include only requested fields"""
        if not fields:
            return user_data
        
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

    @staticmethod
    def get_user_data(user_id: str) -> Dict[str, Any]:
        """
        Get user data for a specific user ID
    
        Args:
            user_id: User identifier
            
        Returns:
            User data dictionary
        """
        logger.info(f"Getting data for user {user_id}")
        
        try:
            # Handle sensitive queries
            sensitive_keywords = ["pin", "password", "social security", "ssn"]
            if any(keyword in user_id.lower() for keyword in sensitive_keywords):
                logger.error(f"Sensitive information requested for user {user_id}")
                return {"error": "Cannot provide sensitive information"}

            # Ensure user exists using the singleton instance
            user_data = CreaditCardsTools.ensure_user_exists(user_id)
            
            # Add standard fields if missing
            if "account_info" not in user_data:
                user_data["account_info"] = {
                    "account_number": user_data["account_id"],
                    "branch": f"{random.randint(1, 999):03d}",
                    "type": "חשבון פרטי",
                    "status": "פעיל",
                    "balance": user_data.get("balance", 0),
                    "available_credit": user_data.get("available_credit", 0),
                    "currency": "ILS"
                }
            
            # Add description to transactions if missing
            if "transactions" in user_data:
                for transaction in user_data["transactions"]:
                    if "description" not in transaction:
                        transaction["description"] = f"עסקה ב{transaction['merchant']}"

            # Remove error field if not needed
            if "error" in user_data and user_data["error"] is None:
                del user_data["error"]
            
            logger.info(f"Successfully retrieved data for user {user_id}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error in get_user_data: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def get_user_fields(user_id: str, fields: List[str]) -> Dict[str, Any]:
        """
        Get specific fields for a user
        
        Args:
            user_id: User identifier
            fields: List of specific fields to retrieve
            
        Returns:
            User data filtered to requested fields
        """
        logger.info(f"Getting fields for user {user_id}: {fields}")
        
        try:
            # Validate input parameters
            if not user_id:
                logger.error("User ID is required")
                return {"error": "User ID is required"}
                
            if not fields:
                logger.error("Fields list is required")
                return {"error": "Fields list is required"}
                
            if not isinstance(fields, list):
                logger.error(f"Fields must be a list, got {type(fields)}")
                return {"error": "Fields must be a list"}
                
            # Get full user data first
            user_data = CreaditCardsTools.get_user_data(user_id)
            
            if "error" in user_data:
                logger.error(f"Error getting user data: {user_data['error']}")
                return user_data
                
            # Then filter the fields
            result = CreaditCardsTools.filter_user_fields(user_data, fields)
            logger.info(f"Successfully retrieved {len(result)} fields for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_user_fields: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def check_balance(user_id: str) -> Dict[str, Any]:
        """
        Check account balance and available credit
        
        Args:
            user_id: User identifier
            
        Returns:
            Balance information including current balance, available credit, and account details
        """
        logger.info(f"Checking balance for user {user_id}")
        
        try:
            # Get user data
            user_data = CreaditCardsTools.get_user_data(user_id)
            
            if "error" in user_data:
                logger.error(f"Error getting user data: {user_data['error']}")
                return user_data
                
            # Extract balance information
            balance_info = {
                "balance": user_data.get("balance", 0),
                "available_credit": user_data.get("available_credit", 0),
                "account_info": user_data.get("account_info", {})
            }
            
            logger.info(f"Successfully retrieved balance for user {user_id}")
            return balance_info
            
        except Exception as e:
            logger.error(f"Error in check_balance: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def get_transactions(user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get transaction history for a user with optional date filtering
        
        Args:
            user_id: User identifier
            start_date: Optional start date for filtering (YYYY-MM-DD)
            end_date: Optional end date for filtering (YYYY-MM-DD)
            
        Returns:
            Filtered transaction list
        """
        user_data = CreaditCardsTools.get_user_data(user_id)
        
        if "error" in user_data:
            return user_data
            
        if "transactions" in user_data:
            return {"transactions": user_data["transactions"]}
        
        return {"transactions": []}

    @staticmethod
    def get_filtered_transactions(
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get transaction history for a user with date filtering
        
        Args:
            user_id: User identifier
            start_date: Optional start date for filtering (YYYY-MM-DD)
            end_date: Optional end date for filtering (YYYY-MM-DD)
            
        Returns:
            Filtered transaction list
        """
        # Get all transactions first
        result = CreaditCardsTools.get_transactions(user_id)
        
        if "error" in result:
            return result
            
        if "transactions" in result:
            transactions = result["transactions"]
            
            if start_date or end_date:
                filtered_transactions = []
                for transaction in transactions:
                    transaction_date = transaction.get("date")
                    
                    if start_date and transaction_date < start_date:
                        continue
                    
                    if end_date and transaction_date > end_date:
                        continue
                    
                    filtered_transactions.append(transaction)
                
                return {"transactions": filtered_transactions}
        
        return result

    @staticmethod
    def filter_transactions(
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter: Optional[TransactionFilter] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter transactions with parameters
        
        Args:
            user_id: User identifier
            start_date: Optional start date for filtering (YYYY-MM-DD)
            end_date: Optional end date for filtering (YYYY-MM-DD)
            filter: Optional TransactionFilter object
            
        Returns:
            Filtered transaction list
        """
        logger.info(f"Filtering transactions for user {user_id} with dates: {start_date} to {end_date}")
        
        try:
            # Get all transactions first
            result = CreaditCardsTools.get_transactions(user_id)
            
            if "error" in result:
                logger.error(f"Error getting transactions: {result['error']}")
                return result
                
            if "transactions" in result:
                transactions = result["transactions"]
                
                # Use filter object if provided, otherwise use direct date parameters
                if filter:
                    start_date = filter.start_date
                    end_date = filter.end_date
                
                # Apply date filters if provided
                if start_date or end_date:
                    filtered_transactions = []
                    for transaction in transactions:
                        transaction_date = transaction.get("date")
                        
                        if start_date and transaction_date < start_date:
                            continue
                        
                        if end_date and transaction_date > end_date:
                            continue
                        
                        filtered_transactions.append(transaction)
                    
                    return {"transactions": filtered_transactions}
            
            logger.info(f"Successfully filtered transactions for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in filter_transactions: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def get_savings_program(user_id: str) -> Dict[str, Any]:
        """
        Get savings program information
        
        Args:
            user_id: User identifier
            
        Returns:
            Savings program details including balance and last deposit
        """
        logger.info(f"Getting savings program info for user {user_id}")
        
        try:
            # Get user data
            user_data = CreaditCardsTools.get_user_data(user_id)
            
            if "error" in user_data:
                logger.error(f"Error getting user data: {user_data['error']}")
                return user_data
                
            # Extract savings program information
            savings_program_info = user_data.get("savings_program", {})
            
            # If no savings program info exists, return default structure
            if not savings_program_info:
                savings_program_info = {
                    "balance": 0.0,
                    "last_deposit": {
                        "amount": 0.0,
                        "date": None,
                        "merchant": None
                    },
                    "status": "לא פעיל"
                }
            
            logger.info(f"Successfully retrieved savings program info for user {user_id}")
            return savings_program_info
            
        except Exception as e:
            logger.error(f"Error in get_savings_program: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def get_travel_insurance(user_id: str) -> Dict[str, Any]:
        """
        Get travel insurance information
        
        Args:
            user_id: User identifier
            
        Returns:
            Travel insurance details including status and coverage
        """
        logger.info(f"Getting travel insurance info for user {user_id}")
        
        try:
            # Get user data
            user_data = CreaditCardsTools.get_user_data(user_id)
            
            if "error" in user_data:
                logger.error(f"Error getting user data: {user_data['error']}")
                return user_data
                
            # Extract travel insurance information
            travel_insurance_info = user_data.get("travel_insurance", {})
            
            # If no travel insurance info exists, return default structure
            if not travel_insurance_info:
                travel_insurance_info = {
                    "status": "לא פעיל",
                    "coverage": "אין",
                    "expiry": None
                }
            
            logger.info(f"Successfully retrieved travel insurance info for user {user_id}")
            return travel_insurance_info
            
        except Exception as e:
            logger.error(f"Error in get_travel_insurance: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def get_frequent_flyer(user_id: str) -> Dict[str, Any]:
        """
        Get frequent flyer program information
        
        Args:
            user_id: User identifier
            
        Returns:
            Frequent flyer program details including points and status
        """
        logger.info(f"Getting frequent flyer info for user {user_id}")
        
        try:
            # Get user data
            user_data = CreaditCardsTools.get_user_data(user_id)
            
            if "error" in user_data:
                logger.error(f"Error getting user data: {user_data['error']}")
                return user_data
                
            # Extract frequent flyer information
            frequent_flyer_info = user_data.get("frequent_flyer", {})
            
            # If no frequent flyer info exists, return default structure
            if not frequent_flyer_info:
                frequent_flyer_info = {
                    "program": "אל על",
                    "points": 0,
                    "status": "לא פעיל",
                    "last_earned": {
                        "amount": 0,
                        "date": None,
                        "source": None
                    }
                }
            
            logger.info(f"Successfully retrieved frequent flyer info for user {user_id}")
            return frequent_flyer_info
            
        except Exception as e:
            logger.error(f"Error in get_frequent_flyer: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def search_cards(query: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for credit cards based on query and optional categories
        
        Args:
            query: Search query
            categories: Optional list of categories to filter by
            
        Returns:
            Search results
        """
        # Sample implementation - replace with actual database query
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
        
        faq_items = [
            {
                "question": "איך אני מפעיל את כרטיס האשראי החדש שלי?",
                "answer": "להפעלת הכרטיס יש להתקשר למספר המצוין על גבי המדבקה שעל הכרטיס או להיכנס לאתר הבנק."
            },
            {
                "question": "מה לעשות במקרה של אובדן או גניבת כרטיס?",
                "answer": "יש לדווח מיידית למוקד שירות הלקוחות בטלפון 03-XXXXXXX הזמין 24/7."
            }
        ]
        
        # Filter by query
        if query:
            query = query.lower()
            card_types = [card for card in card_types if query in card["cardType"].lower() or 
                        query in card["cardBrand"].lower() or
                        any(query in feature.lower() for feature in card["features"])]
            
            faq_items = [faq for faq in faq_items if query in faq["question"].lower() or 
                        query in faq["answer"].lower()]
        
        # Filter by categories
        if categories:
            # This is just an example. In a real implementation, cards would have category tags
            filtered_cards = []
            for card in card_types:
                if "travel" in categories and any("טיסה" in feature for feature in card["features"]):
                    filtered_cards.append(card)
                elif "premium" in categories and "VIP" in " ".join(card["features"]):
                    filtered_cards.append(card)
                elif "basic" in categories and "רגיל" in card["cardType"]:
                    filtered_cards.append(card)
            card_types = filtered_cards
        
        return {
            "matching_cards": card_types,
            "matching_faqs": faq_items,
            "matching_services": {}  # Add any other relevant data here
        }

    @staticmethod
    def get_card_recommendations(preferences: Union[str, UserPreferences]) -> List[Dict[str, Any]]:
        """
        Get card recommendations based on user preferences
        
        Args:
            preferences: Either a card type string (e.g., "VISA") or UserPreferences object
            
        Returns:
            List of card recommendations with scores and reasons
        """
        logger.info(f"Getting card recommendations for preferences: {preferences}")
        
        try:
            # Handle string input (card type)
            if isinstance(preferences, str):
                card_type = preferences.upper()
                cards = [
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
                
                # Filter by card type
                filtered_cards = [card for card in cards if card_type in card["cardBrand"].upper()]
                return filtered_cards
                
            # Handle UserPreferences object
            elif isinstance(preferences, UserPreferences):
                cards = [
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
                
                # Score each card based on preferences
                results = []
                
                for card in cards:
                    score = 0
                    reasons = []
                    
                    # Travel frequency
                    if preferences.travel_frequency == "frequent" and any("טיסה" in feature or "נסיעות" in feature for feature in card["features"]):
                        score += 30
                        reasons.append("מתאים לנוסעים תכופים")
                    elif preferences.travel_frequency == "occasional" and "בסיסי" in " ".join(card["features"]):
                        score += 15
                        reasons.append("מציע הטבות נסיעה בסיסיות")
                    
                    # Savings focus
                    if preferences.savings_focus == "high" and "צבירת נקודות" in " ".join(card["benefits"]):
                        score += 20
                        reasons.append("אפשרויות חיסכון טובות")
                    
                    # Premium benefits
                    if preferences.premium_benefits == "important" and ("פלטינום" in card["cardType"] or "VIP" in " ".join(card["features"])):
                        score += 25
                        reasons.append("הטבות פרימיום מורחבות")
                    
                    # Budget control
                    if preferences.budget_control == "strict" and "דביט" in card["cardType"]:
                        score += 30
                        reasons.append("שליטה מלאה בתקציב")
                    
                    # Add to results if score is positive
                    if score > 0:
                        results.append({
                            "card": card,
                            "score": score,
                            "reason": ", ".join(reasons)
                        })
                
                # Sort by score descending
                results.sort(key=lambda x: x["score"], reverse=True)
                
                return results
                
            else:
                logger.error(f"Invalid preferences type: {type(preferences)}")
                return {"error": "Invalid preferences type. Must be either a string or UserPreferences object"}
                
        except Exception as e:
            logger.error(f"Error in get_card_recommendations: {str(e)}")
            return {"error": f"Internal server error: {str(e)}"}

    @staticmethod
    def calculate_rewards(calculation: RewardsCalculation) -> Dict[str, Any]:
        """
        Calculate rewards based on spending amount and card type
        
        Args:
            calculation: Either a spending RewardsCalculation object
            
        Returns:
            Calculated rewards information
        """
        # Calculate rewards points
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
                "cash_value": points / 100,  # Simple conversion: 100 points = $1
                "card_type": calculation.card_type,
                "points_multiplier": points_multiplier
            }
        }

    @staticmethod
    def admin_generate_user(api_key: str) -> Dict[str, Any]:
        """
        Admin tool to generate a new random user
    
        Args:
            api_key: Admin API key for authentication
            
        Returns:
            New user data
        """
        # Check API key (simple example - use proper authentication in production)
        if api_key != "admin_secret_key":
            return {"error": "Unauthorized access"}
        
        # Generate a new user ID
        user_id = f"user{uuid.uuid4().hex[:8]}"
        
        # Generate user data
        user_data = credit_cards_tools.schema_generator.generate_user_data(user_id)
        
        return {
            "user_id": user_id,
            "user_data": user_data
        }

# Create a singleton instance
credit_cards_tools = CreaditCardsTools()

