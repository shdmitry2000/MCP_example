from typing import Any, List, Dict, Optional
import asyncio
import logging
import json
import os
import httpx
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    """Client for connecting to MCP servers."""
    
    def __init__(self) -> None:
        self.servers: Dict[str, Any] = {}
        self.token: Optional[str] = None
        self.server_mode = os.getenv("MCP_SERVER_MODE", "remote")
        self.session_id = str(uuid.uuid4())
        self.server_url = None
    
    def load_servers(self, config_file: str) -> None:
        """Load server configurations from a JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.servers = config.get('mcpServers', {})
                logger.info(f"Loaded {len(self.servers)} server configurations")
        except Exception as e:
            logger.error(f"Error loading server configurations: {e}")
            raise
    
    async def authenticate(self, username: str, password: str) -> str:
        """
        Authenticate with the MCP server and get a token.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authentication token
        """
        if not self.server_url:
            raise ValueError("Server URL not set. Call start() first.")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.server_url}/token",
                    data={"username": username, "password": password}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Authentication failed: {response.text}")
                
                data = response.json()
                self.token = data["access_token"]
                return self.token
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                raise
    
    async def start(self) -> List[Any]:
        """Start the MCP client and return available tools."""
        try:
            # Get server config based on mode
            server_config = None
            for name, config in self.servers.items():
                if config.get("env", {}).get("MCP_SERVER_MODE") == self.server_mode:
                    server_config = config
                    break

            if not server_config:
                raise ValueError(f"No server configuration found for mode: {self.server_mode}")

            if self.server_mode == "local":
                # For local mode, use stdio
                from mcp import ClientSession, StdioServerParameters
                from mcp.client.stdio import stdio_client
                from contextlib import AsyncExitStack
                
                command = server_config["command"]
                args = server_config["args"]
                env = server_config.get("env", {})

                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=env
                )
                
                self.exit_stack = AsyncExitStack()
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read, write = stdio_transport
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await self.session.initialize()
                
                # Get tools from the session
                tools_response = await self.session.list_tools()
                return [self.create_tool_instance(tool) for tool in tools_response.tools]
            else:
                # For remote mode, use HTTP
                server_url = next((arg for arg in server_config["args"] if arg.startswith("http")), None)
                if not server_url:
                    raise ValueError("No URL found in remote server configuration")

                # Remove trailing /mcp if present
                self.server_url = server_url.rstrip("/")

                # Authenticate if no token yet
                if not self.token:
                    await self.authenticate("admin", "securepassword")

                # Get tools
                async with httpx.AsyncClient() as client:
                    headers = {"Authorization": f"Bearer {self.token}"}
                    response = await client.get(
                        f"{self.server_url}/tools",
                        headers=headers
                    )
                    
                    if response.status_code != 200:
                        raise ValueError(f"Failed to get tools: {response.status_code}")
                    
                    tools = response.json()
                    logger.info(f"Retrieved {len(tools)} tools from MCP server")
                    return [self.create_remote_tool_instance(tool) for tool in tools]
        except Exception as e:
            logger.error(f"Error starting MCP client: {e}")
            return []
    
    def create_tool_instance(self, tool) -> Any:
        """Create a Tool instance from an MCP Tool."""
        # Import here to avoid circular imports
        from pydantic_ai import RunContext, Tool as PydanticTool
        from pydantic_ai.tools import ToolDefinition
        
        async def execute_tool(**kwargs: Any) -> Any:
            if not hasattr(self, 'session') or not self.session:
                raise RuntimeError("Session not initialized")
            return await self.session.call_tool(tool.name, arguments=kwargs)

        async def prepare_tool(ctx: RunContext, tool_def: ToolDefinition) -> ToolDefinition | None:
            tool_def.parameters_json_schema = tool.inputSchema
            return tool_def
        
        return PydanticTool(
            execute_tool,
            name=tool.name,
            description=tool.description or "",
            takes_ctx=False,
            prepare=prepare_tool
        )
    
    def create_remote_tool_instance(self, tool_dict: Dict[str, Any]) -> Any:
        """Create a Tool instance for remote execution."""
        # Import here to avoid circular imports
        from pydantic_ai import RunContext, Tool as PydanticTool
        from pydantic_ai.tools import ToolDefinition
        
        async def execute_tool(**kwargs: Any) -> Any:
            if not self.server_url:
                raise ValueError("Server URL not set")
            
            if not self.token:
                raise ValueError("Not authenticated")
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                
                # Create a JSON-RPC request
                request = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "call_tool",
                    "params": {
                        "name": tool_dict["name"],
                        "arguments": kwargs
                    }
                }
                
                response = await client.post(
                    f"{self.server_url}/execute/{tool_dict['name']}",
                    json=request,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result:
                        return result["result"]
                    else:
                        raise RuntimeError(f"Error: {result.get('error', 'Unknown error')}")
                else:
                    raise RuntimeError(f"Failed to execute tool: {response.status_code}")

        async def prepare_tool(ctx: RunContext, tool_def: ToolDefinition) -> ToolDefinition | None:
            tool_def.parameters_json_schema = tool_dict.get("parameters", {})
            return tool_def

        return PydanticTool(
            execute_tool,
            name=tool_dict["name"],
            description=tool_dict.get("description", ""),
            takes_ctx=False,
            prepare=prepare_tool
        )
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'exit_stack') and self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        """Execute a tool on the MCP server."""
        try:
            if self.server_mode == "local":
                if not hasattr(self, 'session') or not self.session:
                    raise RuntimeError("Session not initialized")
                return await self.session.call_tool(tool_name, arguments=kwargs)
            else:
                if not self.server_url:
                    raise ValueError("Server URL not set")
                
                if not self.token:
                    raise ValueError("Not authenticated")
                
                async with httpx.AsyncClient() as client:
                    headers = {
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                    
                    # Create a JSON-RPC request
                    request = {
                        "jsonrpc": "2.0",
                        "id": str(uuid.uuid4()),
                        "method": "call_tool",
                        "params": {
                            "name": tool_name,
                            "arguments": kwargs
                        }
                    }
                    
                    response = await client.post(
                        f"{self.server_url}/execute/{tool_name}",
                        json=request,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.error(f"Failed to execute tool {tool_name}: {response.status_code}")
                        return {"error": f"Failed to execute tool: {response.status_code}"}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}