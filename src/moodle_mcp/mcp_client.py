from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession


@asynccontextmanager
async def mcp_client_session(url: str, transport: str) -> AsyncIterator[ClientSession]:
    if transport == "sse":
        from mcp.client.sse import sse_client

        async with sse_client(url) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                yield session
        return
    if transport == "streamable-http":
        try:
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError as exc:
            raise RuntimeError(
                "The installed MCP package does not support streamable HTTP. "
                "Use MCP_CLIENT_TRANSPORT=sse or upgrade the mcp package."
            ) from exc

        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session
        return
    raise ValueError("MCP_CLIENT_TRANSPORT must be either 'sse' or 'streamable-http'.")


def serialize_mcp_result(result: Any) -> Any:
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return result
