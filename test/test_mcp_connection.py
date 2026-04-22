import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

@pytest.mark.asyncio
async def test_mcp_greet_tool():
    client = Client(StreamableHttpTransport("http://localhost:8000/mcp"))

    async with client:  
        tools = await client.list_tools()
        assert any(tool.name == "greet" for tool in tools), "Tool 'greet' not found"
        response = await client.call_tool(
            "greet",
            {"name": "Network Engineer"}
        )

        assert response is not None
        # Adjust assertion based on your actual greet tool's expected output format
        assert "Network Engineer" in str(response)
