#!/usr/bin/env python3
"""
MCP Serial Bridge: forwards stdio <-> serial so Cursor (or any MCP client)
can talk to a Pico running MCP over USB serial.

Install pyserial (if your Python is "externally managed", e.g. macOS Homebrew):
  pipx run --spec pyserial python mcp_serial_bridge.py <port> [baud]
  # or: python3 -m venv .venv && source .venv/bin/activate && pip install pyserial

Usage:
    python mcp_serial_bridge.py <serial_port> [baud_rate] [--debug]

Options:
    --debug    Log each line sent/received to stderr (for debugging; does not affect stdout).

Examples:
    python mcp_serial_bridge.py /dev/ttyACM0
    python mcp_serial_bridge.py COM3 115200
    python mcp_serial_bridge.py /dev/cu.usbmodem21401 115200 --debug

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
    args = [a for a in sys.argv[1:] if a != "--debug"]
    debug = "--debug" in sys.argv
    if len(args) < 1:
        print("Usage: mcp_serial_bridge.py <serial_port> [baud_rate] [--debug]", file=sys.stderr)
        print("  e.g. mcp_serial_bridge.py /dev/ttyACM0 115200", file=sys.stderr)
        sys.exit(1)
    port = args[0]
    baud = int(args[1]) if len(args) > 1 else 115200

    try:
        ser = serial.Serial(port, baud, timeout=0.1)
    except Exception as e:
        print(f"Failed to open {port}: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"MCP serial bridge: connected to {port} at {baud} baud. "
        "If Cursor times out, ensure the Pico is running MCP with run(transport='stdio').",
        file=sys.stderr,
    )
    if debug:
        print("Debug: logging each line to stderr (> stdin→serial, < serial→stdout)", file=sys.stderr)
    sys.stderr.flush()

    done = threading.Event()

    def log_debug(prefix, line):
        if debug and line:
            preview = line[:80] + "..." if len(line) > 80 else line
            print(f"{prefix} {preview}", file=sys.stderr)
            sys.stderr.flush()

    def stdin_to_serial():
        try:
            while not done.is_set():
                line = sys.stdin.readline()
                if not line:
                    break
                log_debug(">", line.rstrip("\n\r"))
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
                        log_debug("<", line)
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
