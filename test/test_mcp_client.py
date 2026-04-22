import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from pprint import pprint

async def main():
    client = Client(StreamableHttpTransport("http://localhost:8000/mcp"))

    async with client:  
        tools = await client.list_tools()
        print("Available tools:")
        pprint(tools)

        response = await client.call_tool(
            "greet",
            {"name": "Network Engineer"}
        )

        pprint(response)

asyncio.run(main())
