import asyncio
from client.mcp_client import MCPClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Create and initialize client
        client = MCPClient()
        client.load_servers("config/mcp_config.json")
        
        # Start client
        tools = await client.start()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Execute a tool
        result = await client.execute_tool(
            "analyze_data", 
            data=[{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
        )
        print(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Cleanup
        await client.cleanup()

# Run the example
if __name__ == "__main__":
    asyncio.run(main())