#!/usr/bin/env python3
"""
MCP Serial Bridge: forwards stdio <-> serial so Cursor (or any MCP client)
can talk to a Pico running MCP over USB serial.

Usage:
    python mcp_serial_bridge.py <serial_port> [baud_rate]

Examples:
    python mcp_serial_bridge.py /dev/ttyACM0
    python mcp_serial_bridge.py COM3 115200

Cursor config (MCP server): run this script with your Pico's serial port.
The Pico must be running an MCP server with run_stdio() (e.g. examples/main_stdio.py).
"""

import sys
import threading

try:
    import serial
except ImportError:
    print("Install pyserial: pip install pyserial", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: mcp_serial_bridge.py <serial_port> [baud_rate]", file=sys.stderr)
        print("  e.g. mcp_serial_bridge.py /dev/ttyACM0 115200", file=sys.stderr)
        sys.exit(1)
    port = sys.argv[1]
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

    try:
        ser = serial.Serial(port, baud, timeout=0.1)
    except Exception as e:
        print(f"Failed to open {port}: {e}", file=sys.stderr)
        sys.exit(1)

    done = threading.Event()

    def stdin_to_serial():
        try:
            while not done.is_set():
                line = sys.stdin.readline()
                if not line:
                    break
                ser.write(line.encode("utf-8"))
                ser.flush()
        except Exception:
            pass
        finally:
            done.set()

    def serial_to_stdout():
        try:
            buf = b""
            while not done.is_set():
                chunk = ser.read(256)
                if not chunk:
                    continue
                buf += chunk
                while b"\n" in buf:
                    line_bytes, buf = buf.split(b"\n", 1)
                    line = line_bytes.decode("utf-8", errors="replace").strip().rstrip("\r")
                    if line:
                        sys.stdout.write(line + "\n")
                        sys.stdout.flush()
        except Exception:
            pass
        finally:
            done.set()

    t = threading.Thread(target=stdin_to_serial, daemon=True)
    t.start()
    serial_to_stdout()
    done.set()
    ser.close()


if __name__ == "__main__":
    main()
