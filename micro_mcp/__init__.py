"""
Micro-MCP: MCP (Model Context Protocol) Server Library for MicroPython

A lightweight implementation of the MCP server protocol for MicroPython devices,
specifically designed for Raspberry Pi Pico W and similar embedded systems.

Usage:
    from micro_mcp import MCPServer
    
    mcp = MCPServer(name="my-server", version="1.0.0")
    
    @mcp.tool("my_tool", "Does something cool", {
        "type": "object",
        "properties": {"param": {"type": "string"}},
        "required": ["param"]
    })
    def my_tool(param):
        return {"result": param}
    
    mcp.run(port=8080)
"""

from .mcp_server import MCPServer

__version__ = "1.0.0"
__all__ = ["MCPServer"]

