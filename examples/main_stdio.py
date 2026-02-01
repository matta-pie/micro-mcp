"""
MCP server over stdio (USB serial).

Run this on the Pico when connected via USB. On the laptop, run the
serial bridge and point Cursor (or any MCP client) at the bridge:

  python tools/mcp_serial_bridge.py /dev/ttyACM0 115200

No WiFi required. Copy this file and micro_mcp to the Pico, then run main_stdio.py.
"""

from micro_mcp import MCPServer

mcp = MCPServer(name="pico-stdio-server", version="1.0.0")


@mcp.tool(
    name="echo",
    description="Echo back the given message (for testing stdio transport)",
    input_schema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Message to echo back",
            }
        },
        "required": ["message"],
    },
)
def echo(message):
    return {"echo": message}


@mcp.tool(
    name="ping",
    description="Respond with pong (for testing connectivity)",
    input_schema={"type": "object", "properties": {}, "required": []},
)
def ping():
    return {"status": "pong"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
