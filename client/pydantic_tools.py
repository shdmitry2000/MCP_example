from pydantic_ai import Agent
from pydantic_ai import RunContext, Tool as PydanticTool
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import logging

# Import client
from .mcp_client import MCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PydanticMCPAgent:
    """Integration of MCP client with Pydantic-AI."""
    
    def __init__(self, model=None, token=None):
        """
        Initialize the MCP client and agent.
        
        Args:
            model: LLM model to use with pydantic-ai
            token: Optional authentication token
        """
        self.client = None
        self.agent = None
        self.token = token
        self.model = model
            
    async def initialize(self, config_file="config/mcp_config.json") -> Tuple[MCPClient, Agent]:
        """
        Initialize the MCP client and agent.
        
        Args:
            config_file: Path to MCP configuration file
        
        Returns:
            Tuple of (client, agent)
        """
        # Initialize MCP client
        self.client = MCPClient()
        self.client.load_servers(config_file)
        
        # Set token if provided
        if self.token:
            self.client.token = self.token
            
        # Start the client and get tools
        tools = await self.client.start()
        
        # Initialize agent
        if self.model:
            self.agent = Agent(
                model=self.model, 
                tools=tools,
                instrument=True
            )
        else:
            # Use default model if none provided
            self.agent = Agent(
                tools=tools,
                instrument=True
            )
        
        return self.client, self.agent
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.cleanup()
            
    async def run(self, query: str) -> Any:
        """
        Run a query through the agent.
        
        Args:
            query: User query to process
            
        Returns:
            Agent response
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        return await self.agent.run(query)

async def get_pydantic_mcp_agent(model=None, config_file="config/mcp_config.json") -> Tuple[MCPClient, Agent]:
    """
    Helper function to create and initialize a PydanticMCPAgent.
    
    Args:
        model: LLM model to use
        config_file: Path to configuration file
        
    Returns:
        Tuple of (client, agent)
    """
    agent = PydanticMCPAgent(model=model)
    client, agent_instance = await agent.initialize(config_file)
    return client, agent_instance

async def main():
    """Example usage of PydanticMCPAgent."""
    # Create and initialize agent
    agent = PydanticMCPAgent()
    client, mcp_agent = await agent.initialize()
    
    try:
        # Run a simple query
        query = "Analyze this data: [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]"
        result = await agent.run(query)
        print(f"Result: {result.output}")
    finally:
        # Cleanup
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())