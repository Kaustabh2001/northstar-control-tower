import asyncio
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def discover_mcp_server(endpoint: str) -> dict[str, Any]:
    try:
        async with asyncio.timeout(5):
            async with streamable_http_client(endpoint) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    initialized = await session.initialize()
                    tools = await session.list_tools()
        return {
            "reachable": True,
            "endpoint": endpoint,
            "protocol_version": initialized.protocolVersion,
            "server": initialized.serverInfo.model_dump(
                mode="json",
                by_alias=True,
            ),
            "capabilities": initialized.capabilities.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            ),
            "tools": [
                tool.model_dump(mode="json", by_alias=True, exclude_none=True)
                for tool in tools.tools
            ],
        }
    except Exception as error:
        return {
            "reachable": False,
            "endpoint": endpoint,
            "error": f"{type(error).__name__}: {error}",
        }


async def invoke_mcp_tool(
    endpoint: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    async with asyncio.timeout(10):
        async with streamable_http_client(endpoint) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
    return result.model_dump(mode="json", by_alias=True, exclude_none=True)
