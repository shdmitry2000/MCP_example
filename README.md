# MCP Server & Client Integration Guide

This guide provides a complete overview of setting up and using the secure MCP server with pydantic-ai integration.

## Overview

The Model Context Protocol (MCP) standardizes how applications provide context and tools to large language models (LLMs). This implementation includes:

1. **Secure MCP Server**: A Python server with JWT authentication that exposes three categories of tools
2. **Pydantic-AI Integration**: Client that converts MCP tools to Pydantic Tool instances for use with AI agents
3. **Configuration**: Support for both local (stdio) and remote (HTTP) modes

## Prerequisites

- Python 3.10 or higher
- pip or another package manager
- Basic familiarity with Python and async programming

## Setup Instructions

### 1. Install Dependencies

First, install the required packages:

```bash
pip install mcp>=1.6.0 pydantic-ai fastapi uvicorn httpx pandas python-jose passlib python-multipart pyjwt python-dotenv
```

Or use the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 2. Create Project Structure

Create the following directory structure:

```
mcp-project/
├── server/
│   ├── __init__.py
│   ├── server.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── data_tools.py
│   │   ├── file_tools.py
│   │   └── web_tools.py
│   └── auth/
│       ├── __init__.py
│       └── security.py
├── client/
│   ├── __init__.py
│   ├── mcp_client.py
│   └── pydantic_tools.py
├── config/
│   ├── __init__.py
│   └── mcp_config.json
├── requirements.txt
└── README.md
```

### 3. Copy Implementation Files

Copy the implementation for each file from the provided source code:
- `server/server.py`: Main server implementation
- `server/tools/*.py`: Tool implementations
- `server/auth/security.py`: Security manager
- `client/mcp_client.py`: MCP client
- `client/pydantic_tools.py`: Pydantic-AI integration
- `config/mcp_config.json`: Configuration file

### 4. Configure the Server

Edit `config/mcp_config.json` to set your preferred server configuration:

```json
{
    "mcpServers": {
        "security-mcp-server-local": {
            "command": "python",
            "args": [
                "-m",
                "server.server",
                "--mode",
                "local"
            ],
            "env": {
                "MCP_SERVER_MODE": "local",
                "PYTHONPATH": "."
            }
        },
        "security-mcp-server-remote": {
            "command": "uvicorn",
            "args": [
                "server.server:app",
                "--host",
                "localhost",
                "--port",
                "8000",
                "--url",
                "http://localhost:8000"
            ],
            "env": {
                "MCP_SERVER_MODE": "remote",
                "MCP_SERVER_URL": "http://localhost:8000"
            }
        }
    }
}
```

Modify the host, port, and other settings as needed.

## Running the Server

### Local Mode (stdio)

To run the server in local mode:

```bash
python -m server.server --mode local
```

### Remote Mode (HTTP)

To run the server in remote mode:

```bash
python -m server.server --mode remote --host localhost --port 8000
```

The server will start and listen for incoming connections. You can access the API documentation at:

```
http://localhost:8000/docs
```

This provides an interactive Swagger UI to explore the API endpoints.

## Using the Client

### Basic Usage

```python
import asyncio
from client.mcp_client import MCPClient

async def main():
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
    
    # Cleanup
    await client.cleanup()

# Run the example
asyncio.run(main())
```

### With Pydantic-AI

```python
import asyncio
from pydantic_utils.llms_support import get_gemini_model
from client.pydantic_tools import PydanticMCPAgent

async def main():
    # Create and initialize agent
    agent = PydanticMCPAgent()  #model=get_gemini_model()
    _, mcp_agent = await agent.initialize()

    
    # Run a query
    query = "Analyze this data: [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]"
    result = await mcp_agent.run(query)
    print(f"Agent response: {result.output}")
    
    # query = "give me last news from google.com"
    # result = await mcp_agent.run(query)
    # print(f"Agent response: {result.output}")
    # Cleanup
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Tools

### Data Analysis Tools

1. **analyze_data**: Analyze data and provide statistical summary
   ```python
   await client.execute_tool("analyze_data", data=[...], columns=["name", "age"])
   ```

2. **filter_data**: Filter data based on criteria
   ```python
   await client.execute_tool("filter_data", data=[...], filters={"age": 30})
   ```

### File Tools

1. **read_file**: Read content from a file safely
   ```python
   await client.execute_tool("read_file", file_path="example.txt", max_size=1024*1024)
   ```

2. **list_directory**: List files in a directory
   ```python
   await client.execute_tool("list_directory", directory_path=".", pattern="*.py")
   ```

### Web Tools

1. **fetch_url**: Fetch content from a URL
   ```python
   await client.execute_tool("fetch_url", url="https://example.com", headers={"User-Agent": "Custom"})
   ```

## Security

The server implements JWT-based authentication. By default, it has a single user:
- Username: `admin`
- Password: `securepassword`

To add more users or change the credentials, modify the `server.py` file:

```python
# Add default users
security_manager.add_user("admin", "securepassword")
security_manager.add_user("user1", "password123")
```

## Extending the Server

### Adding New Tools

To add a new tool, follow these steps:

1. Create a new tool module in `server/tools/`
2. Implement the tool functionality
3. Import and register the tool in `server.py` with the `@mcp.tool()` decorator

Example:

```python
# In server/tools/math_tools.py
class MathTools:
    @staticmethod
    def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
        """Calculate statistics for a list of numbers."""
        return {
            "mean": sum(numbers) / len(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "sum": sum(numbers),
            "count": len(numbers)
        }

# In server/server.py
from .tools.math_tools import MathTools

@mcp.tool()
async def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
    """
    Calculate statistics for a list of numbers.
    
    Args:
        numbers: List of numbers
        
    Returns:
        Statistical summary
    """
    return MathTools.calculate_statistics(numbers)
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify username and password
   - Check token expiration
   - Ensure token is included in requests

2. **Connection Errors**:
   - Verify server is running
   - Check server URL and port
   - Ensure network connectivity

3. **Tool Execution Errors**:
   - Verify tool parameters
   - Check error handling
   - Ensure proper permissions

### Debugging

For detailed debugging, increase the logging level:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp-debug.log"),
        logging.StreamHandler()
    ]
)
```

## Best Practices

1. **Security**: Always use HTTPS in production for remote mode
2. **Error Handling**: Implement comprehensive error handling in tools
3. **Input Validation**: Validate all inputs before processing
4. **Documentation**: Document all tools with clear descriptions and examples
5. **Testing**: Write tests for tools and client integration

## Conclusion

This implementation provides a secure, flexible foundation for using MCP with Pydantic-AI. You can extend it with your own tools and integrate it into your AI agent workflows.

For more information about the Model Context Protocol, visit the official documentation:
https://github.com/modelcontextprotocol/modelcontextprotocol




# MCP Project

A secure Model Context Protocol (MCP) server and client with Pydantic-AI integration.

## Structure

See the `server/`, `client/`, and `config/` directories for implementation.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the server:
   ```
   python server/server.py --mode remote
   ```

3. See documentation for more details.
