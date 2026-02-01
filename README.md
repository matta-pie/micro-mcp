# Micro-MCP

A lightweight MCP (Model Context Protocol) Server library for MicroPython, designed for Raspberry Pi Pico W and similar embedded systems.

## Overview

Micro-MCP implements the MCP protocol specification (2025-03-26) with **HTTP** and **stdio** transports and JSON-RPC 2.0 messaging. It allows you to create MCP servers on MicroPython devices that can expose tools and resources to MCP clients.

## Features

- ✅ Full MCP protocol support (tools, resources, sessions)
- ✅ **HTTP transport** with JSON-RPC 2.0 (WiFi)
- ✅ **Stdio transport** over USB serial (no WiFi required)
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

```python
import mip
mip.install("github:matta-pie/micro-mcp")
```

### Connecting to wifi and installing the library
```
import time

import network

# WiFi Configuration - UPDATE THESE WITH YOUR CREDENTIALS
WIFI_SSID = "wifi name"
WIFI_PASSWORD = ""

def connect_wifi():
    """Connect to WiFi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print("Connecting to WiFi:", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
        print()
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("Connected! IP:", ip)
        return ip
    else:
        print("Failed to connect to WiFi")
        return None


connect_wifi()

import mip

mip.install("github:matta-pie/micro-mcp")
```

### Manual Installation

1. Copy the `micro_mcp` directory to your MicroPython device
2. Ensure all files are present:
   - `micro_mcp/__init__.py`
   - `micro_mcp/mcp_server.py`

### Manual Installation (mpremote)

`pipx run mpremote mip install github:matta-pie/micro-mcp`

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

# Start the server (HTTP)
mcp.run(port=8080)
```

## Stdio transport (USB serial)

When the Pico is connected to your laptop via **USB**, you can run the MCP server over **stdio** (newline-delimited JSON-RPC). No WiFi is required.

### On the Pico

1. Copy `micro_mcp` and your main script to the Pico.
2. Run a script that uses stdio transport, e.g. `examples/main_stdio.py`:

```python
from micro_mcp import MCPServer

mcp = MCPServer(name="pico-stdio-server", version="1.0.0")

@mcp.tool("echo", "Echo back a message", {
    "type": "object",
    "properties": {"message": {"type": "string"}},
    "required": ["message"]
})
def echo(message):
    return {"echo": message}

mcp.run(transport="stdio")  # or mcp.run_stdio()
```

### On the laptop: serial bridge

MCP clients (e.g. Cursor) expect to **spawn** a process and talk to it via stdin/stdout. The Pico is already running and connected over USB, so you run a small **bridge** that forwards stdio ↔ serial.

1. **Install pyserial** (pick one):
   - **pipx (recommended on macOS/Homebrew)** — no venv to create; run the bridge with pyserial in one go:
     ```bash
     pipx run --spec pyserial python tools/mcp_serial_bridge.py /dev/ttyACM0 115200
     ```
     For Cursor, set **Command** to `pipx` and **Args** to `run`, `--spec`, `pyserial`, `python`, `path/to/tools/mcp_serial_bridge.py`, `/dev/ttyACM0`, `115200`.
   - **Virtual environment** — if your Python is “externally managed” (e.g. macOS Homebrew):
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate   # Windows: .venv\Scripts\activate
     pip install pyserial
     python tools/mcp_serial_bridge.py /dev/ttyACM0 115200
     ```
     For Cursor, set **Command** to the venv’s Python (e.g. `path/to/pico-mcp/.venv/bin/python`) and **Args** to `tools/mcp_serial_bridge.py`, `/dev/ttyACM0`, `115200`.
   - **System pip** — only if your OS allows it (e.g. some Linux): `pip install pyserial` or `pip install --user pyserial`, then run the bridge with that `python`.
2. **Find the Pico’s serial port** (e.g. `/dev/tty.usbmodem*` or `/dev/ttyACM0` on macOS/Linux, `COM3` on Windows).
3. **Run the bridge** (if not using the pipx one-liner above):

```bash
python tools/mcp_serial_bridge.py /dev/ttyACM0 115200
```

### Cursor configuration

This project includes **`.cursor/mcp.json`** so Cursor can run the serial bridge. You only need to set your Pico’s serial port:

1. Find the port: `ls /dev/tty.usb*` or `ls /dev/cu.usb*` (macOS), or e.g. `COM3` on Windows.
2. Open **`.cursor/mcp.json`** and replace `"/dev/tty.usbmodem101"` in the `args` array with your port (e.g. `"/dev/tty.usbmodem12301"`).
3. Reload Cursor or restart the MCP server so it picks up the change.

The default config uses **pipx** (no venv). If you use a **venv** instead, change the entry to:

```json
"pico-serial": {
  "command": "${workspaceFolder}/.venv/bin/python",
  "args": [
    "${workspaceFolder}/tools/mcp_serial_bridge.py",
    "/dev/tty.usbmodem101",
    "115200"
  ]
}
```

Ensure the Pico is running an MCP server with `run(transport="stdio")` before connecting.

### If Cursor shows "Request timed out" (MCP error -32001)

1. **Pico must be running the MCP server**  
   On the Pico, run `examples/main_stdio.py` (or your script that calls `mcp.run(transport="stdio")`). Start it from Thonny, mpremote, or your IDE, then **disconnect** the IDE so the serial port is free for the bridge.

2. **Use the correct serial port**  
   In `.cursor/mcp.json`, the port in `args` must match your Pico. On macOS, try **`/dev/cu.usbmodem21401`** (or your number) if **`/dev/tty.usbmodem21401`** fails; `cu` is often better for programmatic access.

3. **Only one program can use the port**  
   Close Thonny, mpremote, or any other app that has the Pico’s serial port open before starting the bridge (or connecting in Cursor).

4. **Check the bridge started**  
   In Cursor’s MCP / output logs you should see: `MCP serial bridge: connected to ...`. If you see `Failed to open ...`, the port is wrong or in use.

### Debugging

1. **Run the bridge in a terminal**  
   So you see stderr (errors and the “connected to…” message):
   ```bash
   pipx run --spec pyserial python tools/mcp_serial_bridge.py /dev/cu.usbmodem21401 115200
   ```
   If the port fails to open, you’ll see the error there.

2. **Use `--debug` to log every line**  
   The bridge can log each message sent/received to stderr (stdout stays clean for MCP):
   ```bash
   pipx run --spec pyserial python tools/mcp_serial_bridge.py /dev/cu.usbmodem21401 115200 --debug
   ```
   In Cursor, add `--debug` to the bridge `args` in `.cursor/mcp.json`; then check Cursor’s MCP/output logs for `> ` (Cursor → Pico) and `< ` (Pico → Cursor). If you see `> ` but never `< `, the Pico isn’t replying.

3. **Test the Pico with a one-line request**  
   With the Pico running `main_stdio.py` and nothing else using the port, send one JSON-RPC line and see if you get a response:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | pipx run --spec pyserial python tools/mcp_serial_bridge.py /dev/cu.usbmodem21401 115200 --debug
   ```
   You should see `> ...` and then `< ...` (the Pico’s initialize result). If you only see `> `, the Pico isn’t reading or replying.

4. **Check Cursor’s MCP logs**  
   In Cursor: **Help → Toggle Developer Tools → Console**, or open the **Output** panel and choose the MCP channel. Look for “MCP serial bridge: connected to…”, “Failed to open…”, or `--debug` lines.

5. **Pico side**  
   Ensure the script is actually running (e.g. you ran `main_stdio.py` from Thonny and see no errors). In stdio mode the Pico does not log to the serial port (only MCP JSON is sent), so you won’t see debug lines from the Pico when using the bridge.

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

#### `run(host='0.0.0.0', port=8080, transport='http', stream_in=None, stream_out=None)`

Start the MCP server.

**Parameters:**
- `host` (str): Host to bind to (default: '0.0.0.0') — HTTP only
- `port` (int): Port to listen on (default: 8080) — HTTP only
- `transport` (str): `'http'` or `'stdio'`
- `stream_in`: Input stream for stdio (default: `sys.stdin`)
- `stream_out`: Output stream for stdio (default: `sys.stdout`)

#### `run_stdio(stream_in=None, stream_out=None)`

Run the MCP server over stdio (newline-delimited JSON-RPC). Use when the Pico is connected via USB; the laptop runs the serial bridge. Equivalent to `run(transport='stdio', ...)`.

**Parameters:**
- `stream_in`: Input stream (default: `sys.stdin`)
- `stream_out`: Output stream (default: `sys.stdout`)

## Examples

See the `examples/` directory for complete working examples including:
- **main.py** — HTTP transport with WiFi (e.g. printer tool)
- **main_stdio.py** — Stdio transport over USB (no WiFi; echo, ping tools)
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

- MicroPython (with network support for HTTP transport)
- **HTTP:** WiFi connectivity
- **Stdio:** USB connection only; no WiFi required
- Compatible with Raspberry Pi Pico W and similar devices

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- MCP Protocol: [Model Context Protocol Specification](https://modelcontextprotocol.io)
- MicroPython: [MicroPython Project](https://micropython.org)

