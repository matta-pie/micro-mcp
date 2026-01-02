# Micro-MCP

A lightweight MCP (Model Context Protocol) Server library for MicroPython, designed for Raspberry Pi Pico W and similar embedded systems.

## Overview

Micro-MCP implements the MCP protocol specification (2025-03-26) with HTTP transport and JSON-RPC 2.0 messaging. It allows you to create MCP servers on MicroPython devices that can expose tools and resources to MCP clients.

## Features

- ✅ Full MCP protocol support (tools, resources, sessions)
- ✅ HTTP transport with JSON-RPC 2.0
- ✅ Decorator-based tool registration
- ✅ Resource support for data exposure
- ✅ Session management
- ✅ Optimized for MicroPython memory constraints

## Compatibility
| Board | Compatibility | MicroPython Support | Chip Family |
|------|---------------|---------------------|-------------|
| Challenger RP2040 WiFi | ✅ | Community | RP2040 + WiFi |
| Raspberry Pi Pico W | ✅ | Official | RP2040 + CYW43439 |
| Raspberry Pi Pico 2 W | ✅ | Official | RP2350 + WiFi |
| ESP32 Dev Module | 🧪 | Official | ESP32 |
| ESP32 WROOM-32 | 🧪 | Official | ESP32 |
| ESP32 DevKitC | 🧪 | Official | ESP32 |
| ESP32-WROVER | 🧪 | Official | ESP32 |
| ESP32 Pico Kit | 🧪 | Official | ESP32 |
| ESP32-S2 Dev Board | 🧪 | Official | ESP32-S2 |
| ESP32-S3 Dev Board | 🧪 | Official | ESP32-S3 |
| ESP32-C3 Dev Board | 🧪 | Official | ESP32-C3 |
| ESP32-C6 Dev Board | 🧪 | Community | ESP32-C6 |
| ESP32-H2 Dev Board | 🧪 | Community | ESP32-H2 |
| NodeMCU ESP32 | 🧪 | Official | ESP32 |
| LOLIN32 / Wemos Lolin32 | 🧪 | Official | ESP32 |
| M5Stack Core (ESP32) | 🧪 | Official | ESP32 |
| M5StickC / M5StickC Plus | 🧪 | Official | ESP32 |
| Adafruit QT Py ESP32 | 🧪 | Official | ESP32-S2 / ESP32-S3 |
| Adafruit Feather ESP32 | 🧪 | Official | ESP32 |
| Adafruit Feather ESP32-S2 | 🧪 | Official | ESP32-S2 |
| Adafruit Feather ESP32-S3 | 🧪 | Official | ESP32-S3 |
| Seeed XIAO ESP32-C3 | 🧪 | Official | ESP32-C3 |
| Seeed XIAO ESP32-S3 | 🧪 | Official | ESP32-S3 |
| ESP8266 ESP-12 / ESP-12F | 🧪 | Official | ESP8266 |
| NodeMCU ESP8266 | 🧪 | Official | ESP8266 |
| Wemos D1 Mini (ESP8266) | 🧪 | Official | ESP8266 |
| ESP8285 Dev Board | 🧪 | Official | ESP8285 |
| Pyboard D-Series (WB55) | 🧪 | Official | STM32WB55 |
| OpenMVG H7 Plus (WiFi variant) | 🧪 | Official | STM32H7 |

Compatible: ✅
Untested: 🧪
Not compatible: ❌

## Tested LLM Libraries
| Library | Class | Language |
|---------|-------|----------|
| [PydanticAI](https://ai.pydantic.dev/) | MCPServerStreamableHTTP | Python |

## Installation

### Using MIP (MicroPython Package Installer)

**From GitHub (current):**
```python
import mip
mip.install("github:matta-pie/micro-mcp")
```

**From micropython-lib (once submitted):**
```python
import mip
mip.install("micro-mcp")  # Available from default index
```

> **Note**: To make this package available in the official `mip` index, see [MICROPYTHON_LIB_SUBMISSION.md](MICROPYTHON_LIB_SUBMISSION.md) for submission instructions.


### Manual Installation

1. Copy the `micro_mcp` directory to your MicroPython device
2. Ensure all files are present:
   - `micro_mcp/__init__.py`
   - `micro_mcp/mcp_server.py`

## Quick Start

```python
from micro_mcp import MCPServer
import network
import time

# Connect to WiFi (required for network access)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("YOUR_SSID", "YOUR_PASSWORD")

# Wait for connection
while not wlan.isconnected():
    time.sleep(1)

# Create MCP server
mcp = MCPServer(name="my-server", version="1.0.0")

# Register a tool using decorator
@mcp.tool(
    name="echo",
    description="Echo back a message",
    input_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Message to echo"}
        },
        "required": ["message"]
    }
)
def echo(message):
    return {"echoed": message}

# Start the server
mcp.run(port=8080)
```

## Usage

### Tool Registration

#### Using Decorators

```python
@mcp.tool(
    name="tool_name",
    description="Tool description",
    input_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "number"}
        },
        "required": ["param1"]
    }
)
def my_tool(param1, param2=10):
    return {"result": f"{param1}: {param2}"}
```

#### Programmatic Registration

```python
def my_handler(param1, param2=10):
    return {"result": f"{param1}: {param2}"}

mcp.register_tool(
    name="tool_name",
    description="Tool description",
    input_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "number"}
        },
        "required": ["param1"]
    },
    handler=my_handler
)
```

### Resource Registration

```python
@mcp.resource(
    uri="device://status",
    name="Device Status",
    description="Current device status",
    mime_type="application/json"
)
def device_status():
    import json
    import gc
    return json.dumps({
        "memory_free": gc.mem_free(),
        "uptime": time.ticks_ms()
    })
```

### GPIO Example

```python
from machine import Pin

led = Pin("LED", Pin.OUT)

@mcp.tool(
    name="led_control",
    description="Control the onboard LED",
    input_schema={
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "enum": ["on", "off", "toggle"]
            }
        },
        "required": ["state"]
    }
)
def led_control(state):
    if state == "on":
        led.on()
    elif state == "off":
        led.off()
    elif state == "toggle":
        led.toggle()
    return {"status": "success", "led": state}
```

## API Reference

### MCPServer

#### `MCPServer(name="mcp-server", version="1.0.0", protocol_version="2025-03-26")`

Initialize an MCP server instance.

**Parameters:**
- `name` (str): Server name
- `version` (str): Server version
- `protocol_version` (str): MCP protocol version

#### `tool(name, description, input_schema)`

Decorator to register a tool.

**Parameters:**
- `name` (str): Tool name
- `description` (str): Tool description
- `input_schema` (dict): JSON Schema for tool input

#### `register_tool(name, description, input_schema, handler)`

Programmatically register a tool.

**Parameters:**
- `name` (str): Tool name
- `description` (str): Tool description
- `input_schema` (dict): JSON Schema for tool input
- `handler` (callable): Function to execute (takes **kwargs)

#### `resource(uri, name, description, mime_type="text/plain")`

Decorator to register a resource.

**Parameters:**
- `uri` (str): Resource URI
- `name` (str): Resource name
- `description` (str): Resource description
- `mime_type` (str): MIME type of resource content

#### `run(host='0.0.0.0', port=8080)`

Start the MCP server.

**Parameters:**
- `host` (str): Host to bind to (default: '0.0.0.0')
- `port` (int): Port to listen on (default: 8080)

## Examples

See the `examples/` directory for complete working examples including:
- GPIO control (LED, digital I/O)
- PWM control
- System information
- Resource exposure

## Protocol Support

### Supported Methods

- `initialize` - Initialize MCP session
- `initialized` - Confirm initialization
- `tools/list` - List available tools
- `tools/call` - Execute a tool
- `resources/list` - List available resources
- `resources/read` - Read a resource
- `ping` - Health check

### Limitations

- SSE (Server-Sent Events) streaming is not implemented
- Single-threaded request handling
- No request timeout handling (planned for future versions)

## Requirements

- MicroPython with network support
- WiFi connectivity (for network access)
- Compatible with Raspberry Pi Pico W and similar devices

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- MCP Protocol: [Model Context Protocol Specification](https://modelcontextprotocol.io)
- MicroPython: [MicroPython Project](https://micropython.org)

