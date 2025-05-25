
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
