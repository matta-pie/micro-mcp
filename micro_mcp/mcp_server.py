"""
MCP (Model Context Protocol) Library for MicroPython
Implements Streamable HTTP transport (MCP specification 2025-03-26)

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

import binascii
import json
import socket
import time

from machine import Pin, unique_id


class MCPServer:
    def __init__(self, name="mcp-server", version="1.0.0", protocol_version="2025-03-26"):
        """
        Initialize MCP Server
        
        Args:
            name: Server name
            version: Server version
            protocol_version: MCP protocol version
        """
        self.server_info = {
            "name": name,
            "version": version
        }
        self.protocol_version = protocol_version
        self.capabilities = {
            "tools": {}
        }
        
        # Tool registry: {tool_name: {"schema": {...}, "handler": func}}
        self._tools = {}
        
        # Resource registry (for future expansion)
        self._resources = {}
        
        # Session management
        self._session_id = None
        
        # Pin cache for GPIO operations
        self._pin_cache = {}
    
    def tool(self, name, description, input_schema):
        """
        Decorator to register a tool
        
        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON Schema for tool input
        
        Example:
            @mcp.tool("add", "Add two numbers", {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            })
            def add(a, b):
                return {"sum": a + b}
        """
        def decorator(func):
            self._tools[name] = {
                "schema": {
                    "name": name,
                    "description": description,
                    "inputSchema": input_schema
                },
                "handler": func
            }
            return func
        return decorator
    
    def register_tool(self, name, description, input_schema, handler):
        """
        Programmatically register a tool without decorator
        
        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON Schema for tool input
            handler: Function to execute (takes **kwargs)
        """
        self._tools[name] = {
            "schema": {
                "name": name,
                "description": description,
                "inputSchema": input_schema
            },
            "handler": handler
        }
    
    def resource(self, uri, name, description, mime_type="text/plain"):
        """
        Decorator to register a resource
        
        Args:
            uri: Resource URI
            name: Resource name
            description: Resource description
            mime_type: MIME type of resource content
        """
        def decorator(func):
            self._resources[uri] = {
                "schema": {
                    "uri": uri,
                    "name": name,
                    "description": description,
                    "mimeType": mime_type
                },
                "handler": func
            }
            return func
        return decorator
    
    def _get_pin(self, pin_num, mode=Pin.IN):
        """Get or create a Pin object (helper for GPIO operations)"""
        key = (pin_num, mode)
        if key not in self._pin_cache:
            self._pin_cache[key] = Pin(pin_num, mode)
        return self._pin_cache[key]
    
    def _execute_tool(self, tool_name, arguments):
        """Execute a registered tool"""
        if tool_name not in self._tools:
            return {"error": f"Tool not found: {tool_name}"}
        
        try:
            handler = self._tools[tool_name]["handler"]
            # Call handler with arguments as kwargs
            result = handler(**arguments)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _execute_resource(self, uri):
        """Get a resource"""
        if uri not in self._resources:
            return {"error": f"Resource not found: {uri}"}
        
        try:
            handler = self._resources[uri]["handler"]
            content = handler()
            mime_type = self._resources[uri]["schema"]["mimeType"]
            return {"content": content, "mimeType": mime_type}
        except Exception as e:
            return {"error": f"Resource fetch failed: {str(e)}"}
    
    def _handle_jsonrpc(self, request):
        """Handle a JSON-RPC 2.0 request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")
            
            print(f"JSONRPC METHOD: {method}")
            print(f"JSONRPC PARAMS: {params}")
            print(f"JSONRPC ID: {req_id}")
            
            if method == "initialize":
                # Generate session ID
                self._session_id = binascii.hexlify(unique_id()).decode() + "-" + str(time.ticks_ms())
                print(f"GENERATED SESSION ID: {self._session_id}")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": self.protocol_version,
                        "capabilities": self.capabilities,
                        "serverInfo": self.server_info,
                        "_meta": {
                            "sessionId": self._session_id
                        }
                    }
                }
                print(f"INITIALIZE RESPONSE: {response}")
            
            elif method == "initialized":
                # Client confirms initialization
                print("CLIENT CONFIRMED INITIALIZATION")
                response = None  # No response needed for notification
            
            elif method == "tools/list":
                tools_list = [tool["schema"] for tool in self._tools.values()]
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": tools_list
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = self._execute_tool(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result)
                            }
                        ]
                    }
                }
            
            elif method == "resources/list":
                resources_list = [res["schema"] for res in self._resources.values()]
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "resources": resources_list
                    }
                }
            
            elif method == "resources/read":
                uri = params.get("uri")
                result = self._execute_resource(uri)
                
                if "error" in result:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32602,
                            "message": result["error"]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": result["mimeType"],
                                    "text": result["content"]
                                }
                            ]
                        }
                    }
            
            elif method == "ping":
                # Simple ping/pong
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return response
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def _send_http_response(self, client, status, content_type, body, extra_headers=None):
        """Send an HTTP response"""
        response = "HTTP/1.1 " + status + "\r\n"
        response += "Content-Type: " + content_type + "\r\n"
        response += "Access-Control-Allow-Origin: *\r\n"
        response += "Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE\r\n"
        response += "Access-Control-Allow-Headers: Content-Type, Mcp-Session-Id\r\n"
        
        # Add session ID header if we have one
        if self._session_id and extra_headers is None:
            response += "Mcp-Session-Id: " + self._session_id + "\r\n"
        
        # Add any extra headers
        if extra_headers:
            for key, value in extra_headers.items():
                response += key + ": " + value + "\r\n"
        
        response += "Content-Length: " + str(len(body)) + "\r\n"
        response += "\r\n"
        
        client.send(response.encode())
        client.send(body.encode() if isinstance(body, str) else body)
    
    def _handle_request(self, client):
        """Handle an incoming HTTP request"""
        try:
            # Read the request - may need multiple recv calls
            request = b""
            content_length = 0
            headers_complete = False
            
            # First, read headers
            while not headers_complete:
                chunk = client.recv(1024)
                if not chunk:
                    break
                request += chunk
                
                # Check if we have complete headers
                if b'\r\n\r\n' in request:
                    headers_complete = True
                    # Parse content-length from headers
                    try:
                        headers_part = request.split(b'\r\n\r\n')[0].decode()
                        for line in headers_part.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                content_length = int(line.split(':')[1].strip())
                                print(f"CONTENT-LENGTH HEADER: {content_length}")
                                break
                    except:
                        pass
            
            # Now read the body if there's a content-length
            if content_length > 0:
                headers_end = request.find(b'\r\n\r\n') + 4
                body_received = len(request) - headers_end
                print(f"BODY RECEIVED SO FAR: {body_received}/{content_length}")
                
                # Read remaining body
                while body_received < content_length:
                    chunk = client.recv(min(1024, content_length - body_received))
                    if not chunk:
                        break
                    request += chunk
                    body_received = len(request) - headers_end
                    print(f"BODY RECEIVED: {body_received}/{content_length}")
            
            # Convert to string for processing
            request = request.decode()
            
            print("\n" + "="*50)
            print("RAW REQUEST (first 500 chars):")
            print(request[:500])
            print("="*50)
            
            # Parse HTTP request
            lines = request.split('\r\n')
            if not lines:
                print("ERROR: No lines in request")
                return
            
            request_line = lines[0].split()
            if len(request_line) < 2:
                print("ERROR: Invalid request line:", lines[0])
                return
            
            method = request_line[0]
            path = request_line[1]
            
            print(f"METHOD: {method}")
            print(f"PATH: {path}")
            
            # Parse headers
            headers = {}
            for line in lines[1:]:
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    headers[key.lower()] = value
            
            print(f"HEADERS: {headers}")
            
            # Handle CORS preflight
            if method == "OPTIONS":
                self._send_http_response(client, "204 No Content", "text/plain", "")
                return
            
            # Handle DELETE - session termination
            if method == "DELETE" and path == "/mcp":
                session_id = headers.get('mcp-session-id')
                if session_id == self._session_id:
                    self._session_id = None
                    self._send_http_response(client, "200 OK", "application/json", "{}")
                else:
                    self._send_http_response(client, "404 Not Found", "application/json", 
                                           '{"error":"Session not found"}')
                return
            
            # Handle POST to /mcp endpoint - main MCP messages
            if method == "POST" and path == "/mcp":
                body_start = request.find('\r\n\r\n')
                if body_start != -1:
                    body = request[body_start + 4:]
                    print(f"BODY LENGTH: {len(body)}")
                    print(f"BODY: {body[:200]}")  # First 200 chars
                    
                    try:
                        # Check if request wants streaming
                        accept = headers.get('accept', '')
                        print(f"ACCEPT HEADER: {accept}")
                        
                        # Parse JSON-RPC request
                        json_request = json.loads(body)
                        print(f"PARSED JSON: {json_request}")
                        
                        # Handle batch or single request
                        if isinstance(json_request, list):
                            # Batch request
                            print("HANDLING BATCH REQUEST")
                            responses = []
                            for req in json_request:
                                print(f"Processing request: {req}")
                                resp = self._handle_jsonrpc(req)
                                print(f"Response: {resp}")
                                if resp:  # None for notifications
                                    responses.append(resp)
                            response_body = json.dumps(responses)
                        else:
                            # Single request
                            print("HANDLING SINGLE REQUEST")
                            json_response = self._handle_jsonrpc(json_request)
                            print(f"JSON RESPONSE: {json_response}")
                            
                            if json_response is None:
                                # Notification - no response
                                print("SENDING 204 NO CONTENT")
                                self._send_http_response(client, "204 No Content", "application/json", "")
                                return
                            response_body = json.dumps(json_response)
                        
                        print(f"RESPONSE BODY: {response_body[:200]}")
                        
                        # For now, always respond with JSON (not SSE streaming)
                        # SSE would require maintaining long-lived connections
                        extra_headers = {}
                        if self._session_id:
                            extra_headers["Mcp-Session-Id"] = self._session_id
                            print(f"ADDING SESSION HEADER: {self._session_id}")
                        
                        print("SENDING 200 OK RESPONSE")
                        self._send_http_response(client, "200 OK", "application/json", 
                                               response_body, extra_headers)
                        
                    except Exception as e:
                        print(f"ERROR PROCESSING REQUEST: {e}")
                        import sys
                        sys.print_exception(e)
                        error_body = json.dumps({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32700,
                                "message": "Parse error: " + str(e)
                            }
                        })
                        print("SENDING 400 BAD REQUEST")
                        self._send_http_response(client, "400 Bad Request", "application/json", error_body)
                else:
                    print("ERROR: No body found in POST request")
            
            # Handle GET to /mcp - SSE stream (not implemented for simplicity)
            elif method == "GET" and path == "/mcp":
                # For now, return error - SSE streaming not implemented
                error_body = json.dumps({"error": "GET/SSE streaming not implemented on Pico"})
                self._send_http_response(client, "501 Not Implemented", "application/json", error_body)
            
            # Handle GET to root - info page
            elif method == "GET" and path == "/":
                tools_html = ""
                for name in self._tools.keys():
                    desc = self._tools[name]["schema"]["description"]
                    tools_html += "<li><strong>" + name + "</strong>: " + desc + "</li>"
                
                resources_html = ""
                for uri in self._resources.keys():
                    desc = self._resources[uri]["schema"]["description"]
                    resources_html += "<li><strong>" + uri + "</strong>: " + desc + "</li>"
                
                html = "<!DOCTYPE html>"
                html += "<html>"
                html += "<head><title>" + self.server_info["name"] + "</title></head>"
                html += "<body>"
                html += "<h1>MCP Server: " + self.server_info["name"] + "</h1>"
                html += "<p>Version: " + self.server_info["version"] + "</p>"
                html += "<p>Protocol: " + self.protocol_version + "</p>"
                html += "<p>MCP Endpoint: <code>POST /mcp</code></p>"
                if self._session_id:
                    html += "<p>Session ID: <code>" + self._session_id + "</code></p>"
                html += "<h2>Tools (" + str(len(self._tools)) + ")</h2>"
                if tools_html:
                    html += "<ul>" + tools_html + "</ul>"
                else:
                    html += "<p><em>No tools registered</em></p>"
                html += "<h2>Resources (" + str(len(self._resources)) + ")</h2>"
                if resources_html:
                    html += "<ul>" + resources_html + "</ul>"
                else:
                    html += "<p><em>No resources registered</em></p>"
                html += "</body>"
                html += "</html>"
                self._send_http_response(client, "200 OK", "text/html", html)
            
            else:
                self._send_http_response(client, "404 Not Found", "text/plain", "Not Found")
                
        except Exception as e:
            print("ERROR HANDLING REQUEST:", e)
            import sys
            sys.print_exception(e)
            try:
                error_body = json.dumps({"error": str(e)})
                self._send_http_response(client, "500 Internal Server Error", "application/json", error_body)
            except:
                pass
        finally:
            client.close()
            print("CONNECTION CLOSED")
            print("="*50 + "\n")
    
    def run(self, host='0.0.0.0', port=8080):
        """
        Start the MCP server
        
        Args:
            host: Host to bind to (default: '0.0.0.0')
            port: Port to listen on (default: 8080)
        """
        # Get actual IP address
        import network
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            ip_address = wlan.ifconfig()[0]
        else:
            ip_address = host
        
        # Create socket server
        addr = socket.getaddrinfo(host, port)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        
        print("=" * 50)
        print("MCP Server:", self.server_info["name"])
        print("Version:", self.server_info["version"])
        print("Protocol:", self.protocol_version)
        print("Listening on: http://" + ip_address + ":" + str(port))
        print("MCP Endpoint: http://" + ip_address + ":" + str(port) + "/mcp")
        print("Registered tools:", len(self._tools))
        print("Registered resources:", len(self._resources))
        print("=" * 50)
        
        # Main server loop
        while True:
            try:
                client, addr = s.accept()
                print("Connection from", addr)
                self._handle_request(client)
            except Exception as e:
                print("Error:", e)

