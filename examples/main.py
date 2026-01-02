"""
Example usage of Micro-MCP library for Raspberry Pi Pico 2 W

This file demonstrates how to use the Micro-MCP library to create
a custom MCP server with your own tools and resources.

Installation:
    import mip
    mip.install("github:yourusername/micro-mcp")
    
    Then copy this example to your device and customize it.
"""

import json
import time

import network
from machine import Pin

from micro_mcp import MCPServer

# WiFi Configuration - UPDATE THESE WITH YOUR CREDENTIALS
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

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

# Initialize MCP Server
mcp = MCPServer(name="pico2w-iot-server", version="1.0.0")

# Example 1: Register LED control tool using decorator
led = Pin("LED", Pin.OUT)

@mcp.tool(
    name="led_control",
    description="Control the onboard LED on the Pico 2 W",
    input_schema={
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "enum": ["on", "off", "toggle"],
                "description": "LED state to set"
            }
        },
        "required": ["state"]
    }
)
def led_control(state):
    """Control the LED"""
    if state == "on":
        led.on()
        return {"status": "success", "led_state": "on"}
    elif state == "off":
        led.off()
        return {"status": "success", "led_state": "off"}
    elif state == "toggle":
        led.toggle()
        return {"status": "success", "led_state": "toggled"}

# Example 2: Register GPIO read tool
@mcp.tool(
    name="read_gpio",
    description="Read the digital state of a GPIO pin",
    input_schema={
        "type": "object",
        "properties": {
            "pin": {
                "type": "integer",
                "description": "GPIO pin number (0-28)",
                "minimum": 0,
                "maximum": 28
            }
        },
        "required": ["pin"]
    }
)
def read_gpio(pin):
    """Read a GPIO pin"""
    try:
        gpio = Pin(pin, Pin.IN)
        value = gpio.value()
        return {
            "pin": pin,
            "value": value,
            "state": "HIGH" if value else "LOW"
        }
    except Exception as e:
        return {"error": str(e)}

# Example 3: Register GPIO write tool
@mcp.tool(
    name="write_gpio",
    description="Set a GPIO pin to HIGH or LOW",
    input_schema={
        "type": "object",
        "properties": {
            "pin": {
                "type": "integer",
                "description": "GPIO pin number (0-28)",
                "minimum": 0,
                "maximum": 28
            },
            "state": {
                "type": "string",
                "enum": ["HIGH", "LOW"],
                "description": "Pin state to set"
            }
        },
        "required": ["pin", "state"]
    }
)
def write_gpio(pin, state):
    """Write to a GPIO pin"""
    try:
        gpio = Pin(pin, Pin.OUT)
        value = 1 if state == "HIGH" else 0
        gpio.value(value)
        return {
            "pin": pin,
            "state": state,
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}

# Example 4: Register PWM control tool
@mcp.tool(
    name="set_pwm",
    description="Set PWM duty cycle on a pin (for LED brightness, motor speed, etc.)",
    input_schema={
        "type": "object",
        "properties": {
            "pin": {
                "type": "integer",
                "description": "GPIO pin number",
                "minimum": 0,
                "maximum": 28
            },
            "duty": {
                "type": "integer",
                "description": "PWM duty cycle (0-65535)",
                "minimum": 0,
                "maximum": 65535
            },
            "frequency": {
                "type": "integer",
                "description": "PWM frequency in Hz (default: 1000)",
                "default": 1000
            }
        },
        "required": ["pin", "duty"]
    }
)
def set_pwm(pin, duty, frequency=1000):
    """Set PWM on a pin"""
    try:
        from machine import PWM
        pwm = PWM(Pin(pin))
        pwm.freq(frequency)
        pwm.duty_u16(duty)
        return {
            "pin": pin,
            "duty": duty,
            "frequency": frequency,
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}

# Example 5: Register a tool programmatically (without decorator)
def get_system_info():
    """Get system information"""
    import binascii
    import gc

    from machine import unique_id
    
    return {
        "device": "Raspberry Pi Pico 2 W",
        "device_id": binascii.hexlify(unique_id()).decode(),
        "free_memory": gc.mem_free(),
        "allocated_memory": gc.mem_alloc(),
        "uptime_ms": time.ticks_ms()
    }

mcp.register_tool(
    name="system_info",
    description="Get Pico 2 W system information and status",
    input_schema={"type": "object", "properties": {}},
    handler=get_system_info
)

# Example 6: Register a resource (for data that can be read)
@mcp.resource(
    uri="device://pico2w/status",
    name="Device Status",
    description="Current device status information",
    mime_type="application/json"
)
def device_status_resource():
    """Provide device status as a resource"""
    import gc
    return json.dumps({
        "led_state": "on" if led.value() else "off",
        "memory_free": gc.mem_free(),
        "uptime_ms": time.ticks_ms()
    })

# Example 7: Temperature sensor (if you have one connected)
# Uncomment and modify if you have a sensor like DHT22 or DS18B20
"""
@mcp.tool(
    name="read_temperature",
    description="Read temperature from DHT22 sensor",
    input_schema={
        "type": "object",
        "properties": {
            "pin": {
                "type": "integer",
                "description": "GPIO pin where DHT22 is connected"
            }
        },
        "required": ["pin"]
    }
)
def read_temperature(pin):
    from dht import DHT22
    sensor = DHT22(Pin(pin))
    sensor.measure()
    return {
        "temperature_c": sensor.temperature(),
        "humidity": sensor.humidity()
    }
"""

# Main execution
if __name__ == "__main__":
    # Connect to WiFi
    ip = connect_wifi()
    if not ip:
        print("Cannot start without WiFi")
    else:
        # Start the MCP server
        mcp.run(port=8080)

