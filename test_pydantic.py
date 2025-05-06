import asyncio
from pydantic_utils.llms_support import get_gemini_model
from client.pydantic_tools import PydanticMCPAgent

async def main():
    # Create and initialize agent
    agent = PydanticMCPAgent(model=get_gemini_model())
    _, mcp_agent = await agent.initialize()

    
    # Run a query
    query = "Analyze this data: [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]"
    result = await mcp_agent.run(query)
    print(f"Agent response: {result.output}")
    
    # Get user data with explicit user ID
    # user_id = "1234567890"
    # query = f"get_user_data(user_id='{user_id}')"
    query = "my user id is 1234567890. give me my data."
    result = await mcp_agent.run(query)
    print(f"Agent response: {result.output}")
    # Cleanup
    await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())