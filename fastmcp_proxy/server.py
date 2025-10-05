"""
FastMCP Proxy Server for AI Infra

This server acts as a gateway for MCP (Model Context Protocol) servers,
providing HTTP/SSE transport and integration with the LiteLLM stack.
"""

import asyncio
from fastmcp import FastMCP, Context
from fastmcp.server.proxy import ProxyClient


# Create the main FastMCP proxy server
mcp = FastMCP("AI Infra MCP Proxy")


@mcp.tool
async def health_check() -> str:
    """Health check endpoint for the proxy server"""
    return "FastMCP Proxy is running"


@mcp.tool
async def echo(message: str, ctx: Context) -> str:
    """Echo a message back (demo tool)"""
    await ctx.info(f"Echoing message: {message}")
    return f"Echo: {message}"


# Example: Add a proxied backend server (uncomment when you have a backend)
# You can add more backend servers using configuration
# backend_server = ProxyClient("http://localhost:8001/mcp/sse")
# backend_proxy = FastMCP.as_proxy(backend_server, name="BackendProxy")
# mcp.mount(backend_proxy, prefix="backend")


def main():
    """Run the FastMCP proxy server"""
    # Run with HTTP transport for production deployment
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/mcp"
    )


if __name__ == "__main__":
    main()
