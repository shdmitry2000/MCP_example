from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
import uvicorn
import asyncio
import logging
import os
import json
import sys

# Import tools
from .tools.data_tools import DataTools
from .tools.file_tools import FileTools
from .tools.web_tools import WebTools
from .auth.security import SecurityManager
from .tools.creadit_card.creadit_cards_tools import CreaditCardsTools, RewardsCalculation, UserPreferences, credit_cards_tools
# from .tools.bucket_tools import BucketTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-server")

# Create security manager
security_manager = SecurityManager()

# Add default user
security_manager.add_user("admin", "securepassword")

# Define API models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    username: str
    password: str

class ToolRequest(BaseModel):
    jsonrpc: str
    id: str
    method: str
    params: Dict[str, Any]

class ToolListResponse(BaseModel):
    tools: List[Dict[str, Any]]

# Setup FastAPI for HTTP server
app = FastAPI(
    title="MCP Server",
    description="Secure MCP Server with tools",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Create MCP server
mcp = FastMCP(app)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Token authentication
@app.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Authentication attempt for user: {form_data.username}")
    if not security_manager.authenticate_user(form_data.username, form_data.password):
        logger.error(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = security_manager.generate_token(form_data.username)
    logger.info(f"Authentication successful for user: {form_data.username}")
    return {"access_token": token}

# JSON token authentication
@app.post("/token/json", response_model=TokenResponse)
async def login_json(user: User):
    logger.info(f"JSON authentication attempt for user: {user.username}")
    if not security_manager.authenticate_user(user.username, user.password):
        logger.error(f"JSON authentication failed for user: {user.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = security_manager.generate_token(user.username)
    logger.info(f"JSON authentication successful for user: {user.username}")
    return {"access_token": token}

# User dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = security_manager.validate_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload["sub"]

# Expose MCP tools
@mcp.tool()
async def analyze_data(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze data and provide statistical summary.
    
    Args:
        data: List of dictionaries containing data
        columns: Optional list of columns to analyze (analyzes all if None)
        
    Returns:
        Statistical summary
    """
    return DataTools.analyze_data(data, columns)

@mcp.tool()
async def filter_data(data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter data based on criteria.
    
    Args:
        data: List of dictionaries containing data
        filters: Dictionary of filter criteria (column_name: value)
        
    Returns:
        Filtered data
    """
    return DataTools.filter_data(data, filters)

#add tools for credit cards 
@mcp.tool()
async def get_transactions(user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get transactions for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of transactions
    """
    return credit_cards_tools.get_transactions(user_id)

@mcp.tool()
async def get_filtered_transactions(user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get filtered transactions for a user.
    
    Args:
        user_id: ID of the user
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        List of filtered transactions   
    """
    return credit_cards_tools.get_filtered_transactions(user_id, start_date, end_date)

@mcp.tool()
async def get_user_data(user_id: str) -> Dict[str, Any]:
    """ 
    Get user data for a user.
    
    Args:
        user_id: ID of the user (required)
        
    Returns:
        User data
    """
    if not user_id:
        raise ValueError("user_id is required")
    return credit_cards_tools.get_user_data(user_id)

@mcp.tool()
async def filter_user_fields(user_data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """
    Filter user data based on specific fields.
    
    Args:
        user_data: User data    
        fields: List of fields to filter
        
    Returns:
        Filtered user data
    """
    return credit_cards_tools.filter_user_fields(user_data, fields)  

@mcp.tool()
async def get_frequent_flyer(user_id: str) -> Dict[str, Any]:
    """
    Get frequent flyer information for a user.  
    
    Args:
        user_id: ID of the user
        
    Returns:
        Frequent flyer information
    """
    return credit_cards_tools.get_frequent_flyer(user_id)    

@mcp.tool()
async def search_cards(query: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search for credit cards based on a query and categories.    
    
    Args:
        query: Search query
        categories: Optional list of categories to filter
        
    Returns:
        List of credit cards    
    """
    return credit_cards_tools.search_cards(query, categories)

@mcp.tool()
async def get_card_recommendations(preferences: Union[str, UserPreferences]) -> List[Dict[str, Any]]:   
    """
    Get card recommendations based on user preferences.
    
    Args:
        preferences: User preferences   
        
    Returns:
        List of card recommendations
    """
    return credit_cards_tools.get_card_recommendations(preferences)  

@mcp.tool()
async def get_card_details(card_id: str) -> Dict[str, Any]:
    """
    Get details for a specific credit card. 
    
    Args:
        card_id: ID of the credit card
        
    Returns:
        Credit card details
    """ 
    return credit_cards_tools.get_card_details(card_id)

@mcp.tool()
async def get_card_offers(card_id: str) -> Dict[str, Any]:
    """
    Get offers for a specific credit card.  
    
    Args:
        card_id: ID of the credit card
        
    Returns:
        List of offers  
    """
    return credit_cards_tools.get_card_offers(card_id)

@mcp.tool()
async def get_card_rewards(card_id: str) -> Dict[str, Any]: 
    """
    Get rewards for a specific credit card.
    
    Args:
        card_id: ID of the credit card  
        
    Returns:
        List of rewards
    """
    return credit_cards_tools.get_card_rewards(card_id)  

@mcp.tool()
async def get_card_benefits(card_id: str) -> Dict[str, Any]:
    """
    Get benefits for a specific credit card.    
    
    Args:
        card_id: ID of the credit card
        
    Returns:
        List of benefits
    """ 
    return credit_cards_tools.get_card_benefits(card_id)

@mcp.tool()
async def get_card_fees(card_id: str) -> Dict[str, Any]:
    """
    Get fees for a specific credit card.    
    
    Args:
        card_id: ID of the credit card
        
    Returns:
        List of fees
    """ 
    return credit_cards_tools.get_card_fees(card_id)

@mcp.tool()
async def get_card_terms(card_id: str) -> Dict[str, Any]:
    """
    Get terms for a specific credit card.   
    
    Args:
        card_id: ID of the credit card
        
    Returns:
        List of terms
    """ 
    return credit_cards_tools.get_card_terms(card_id)    

@mcp.tool()
async def get_card_eligibility(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get eligibility for a specific credit card. 
    
    Args:
        user_data: User data
        
    Returns:
        Eligibility information
    """ 
    return credit_cards_tools.get_card_eligibility(user_data)

@mcp.tool()
async def get_card_application_status(user_id: str) -> Dict[str, Any]:
    """
    Get application status for a specific credit card.  
    
    Args:
        user_id: ID of the user
        
    Returns:
        Application status
    """ 
    return credit_cards_tools.get_card_application_status(user_id)   

@mcp.tool()
async def get_card_application_progress(user_id: str) -> Dict[str, Any]:
    """
    Get application progress for a specific credit card.    
    
    Args:
        user_id: ID of the user
        
    Returns:
        Application progress
    """ 
    return credit_cards_tools.get_card_application_progress(user_id)    

@mcp.tool()
async def get_card_application_requirements(user_id: str) -> Dict[str, Any]:
    """
    Get application requirements for a specific credit card.    
    
    Args:
        user_id: ID of the user
        
    Returns:
        Application requirements
    """  
    return credit_cards_tools.get_card_application_requirements(user_id)

@mcp.tool()
async def get_card_application_documents(user_id: str) -> Dict[str, Any]:
    """
    Get application documents for a specific credit card.    
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of application documents   
    """
    return credit_cards_tools.get_card_application_documents(user_id)

@mcp.tool()
async def calculate_rewards(calculation: RewardsCalculation) -> Dict[str, Any]:
    """
    Calculate rewards based on spending amount and card type.
    
    Args:
        calculation: Rewards calculation object
        
    Returns:
        Calculated rewards
    """
    return credit_cards_tools.calculate_rewards(calculation)

@mcp.tool()
async def admin_generate_user(api_key: str) -> Dict[str, Any]:
    """
    Admin tool to generate a new random user.
    
    Args:
        api_key: Admin API key
        
    Returns:
        New user data
    """
    return credit_cards_tools.admin_generate_user(api_key)

# @mcp.tool()
# async def read_file(file_path: str, max_size: int = 1024 * 1024) -> str:
#     """
#     Read content from a file safely.
    
#     Args:
#         file_path: Path to the file
#         max_size: Maximum file size to read (default: 1MB)
        
#     Returns:
#         File content
#     """
#     return FileTools.read_file(file_path, max_size)

# @mcp.tool()
# async def list_directory(directory_path: str, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
#     """
#     List files in a directory.
    
#     Args:
#         directory_path: Path to the directory
#         pattern: Optional glob pattern to filter files
        
#     Returns:
#         List of file information
#     """
#     return FileTools.list_directory(directory_path, pattern)

# @mcp.tool()
# async def fetch_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
#     """
#     Fetch content from a URL.
    
#     Args:
#         url: URL to fetch
#         headers: Optional request headers
#         timeout: Request timeout in seconds
        
#     Returns:
#         Response data
#     """
#     return await WebTools.fetch_url(url, headers, timeout)

# Custom endpoints for the MCP client
# Modify the get_tools function in server.py
@app.get("/tools")
async def get_tools(current_user: str = Depends(get_current_user)):
    """Get all available tools."""
    logger.info(f"Getting tools for user: {current_user}")
    tools = []
    for tool in await mcp.list_tools():
        # Use tool.parameters_json_schema instead of tool.parameters_schema
        tool_dict = {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters_json_schema if hasattr(tool, "parameters_json_schema") else {}
        }
        tools.append(tool_dict)
    logger.info(f"Returning {len(tools)} tools")
    return tools

# Modify the execute_tool function
@app.post("/execute/{tool_name}")
async def execute_tool(
    tool_name: str, 
    request: ToolRequest,
    current_user: str = Depends(get_current_user)
):
    """Execute a specific tool."""
    logger.info(f"Executing tool {tool_name} for user: {current_user}")
    tool = None
    for t in await mcp.list_tools():
        if t.name == tool_name:
            tool = t
            break
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    try:
        arguments = request.params.get("arguments", {})
        # Use call method instead of execute
        result = await mcp.call_tool(tool_name, arguments=arguments)
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
        
# Routes for remote mode
@app.get("/")
async def root():
    return {
        "name": "Secure MCP Server",
        "version": "1.0.0",
        "description": "MCP Server with secure authentication and tools"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Start cleanup task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(token_cleanup_task())

async def token_cleanup_task():
    while True:
        removed = security_manager.cleanup_expired_tokens()
        if removed > 0:
            logger.info(f"Removed {removed} expired tokens")
        await asyncio.sleep(600)  # Run every 10 minutes

# # Add new tool endpoints
# @mcp.tool()
# async def list_bucket_contents(bucket_name: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
#     """
#     List contents of a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         prefix: Optional prefix to filter objects
        
#     Returns:
#         List of objects in the bucket
#     """
#     return BucketTools.list_bucket_contents(bucket_name, prefix)

# @mcp.tool()
# async def read_bucket_file(bucket_name: str, file_key: str) -> str:
#     """
#     Read a file from a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         file_key: Key of the file to read
        
#     Returns:
#         File contents
#     """
#     return BucketTools.read_bucket_file(bucket_name, file_key)

# @mcp.tool()
# async def write_bucket_file(bucket_name: str, file_key: str, content: str) -> Dict[str, Any]:
#     """
#     Write a file to a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         file_key: Key for the file
#         content: Content to write
        
#     Returns:
#         Status information
#     """
#     return BucketTools.write_bucket_file(bucket_name, file_key, content)

def run_server(host: str = "0.0.0.0", port: int = 8000, mode: str = "remote"):
    """
    Run MCP server in either local or remote mode.
    
    Args:
        host: Host to bind to (for remote mode)
        port: Port to bind to (for remote mode)
        mode: "local" for stdio, "remote" for HTTP
    """
    if mode == "local":
        logger.info("Starting MCP server in local mode (stdio)")
        mcp.run()
    else:
        logger.info(f"Starting MCP server in remote mode on {host}:{port}")
        uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Run MCP server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--mode", choices=["local", "remote"], default="remote", help="Server mode")
    
    args = parser.parse_args()
    
    # Run server
    run_server(args.host, args.port, args.mode)