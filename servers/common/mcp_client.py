from typing import Any
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(self, server_params: StdioServerParameters):
        self.server_params = server_params

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> types.CallToolRequest:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    name=name,
                    arguments=arguments,
                )
                return result
