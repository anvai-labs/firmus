#!/usr/bin/env python3
"""
FIRMUS - Firewall-traversing Independent Remote Monitoring and Filesystem Access System

Research Implementation for Academic Paper

Architecture:
    Collector (SERVER)  → Listens on port, receives connections from monitored nodes
    Agent (CLIENT)      → Connects OUT to collector (firewall-traversable)

Use Case:
    Remote filesystem monitoring of IoT/home devices behind NAT/firewalls
    without requiring port forwarding or root privileges.

Author: Research Project
License: MIT (See LICENSE file)
"""

import socket
import struct
import json
import base64
import os
import sys
import time
import argparse
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass


# ── Protocol Constants ──────────────────────────────────────────────
MAX_PACKET_SIZE = 65535
DEFAULT_PORT = 5353

# Message Type Enumeration
class MessageType:
    """Protocol message type constants."""
    DIRECTORY_LIST = 1          # List directory contents (non-recursive)
    DIRECTORY_TREE = 2          # List directory contents (recursive)
    FILE_TRANSFER_REQUEST = 3   # Request file chunk
    DATA_RESPONSE = 100         # Data response
    HEARTBEAT = 5               # Connectivity check
    HEARTBEAT_ACK = 102         # Connectivity acknowledgment
    ERROR_RESPONSE = 104        # Error response


# ── Protocol Implementation ────────────────────────────────────────────
@dataclass
class ProtocolMessage:
    """Structured protocol message."""
    message_type: int
    sequence: int
    timestamp: float
    payload: Any

    def serialize(self) -> bytes:
        """Serialize message to bytes for network transmission."""
        payload_bytes = json.dumps(self.payload).encode() if isinstance(self.payload, dict) else self.payload
        header = struct.pack("!BII", self.message_type, self.sequence, int(self.timestamp))
        length_field = struct.pack("!I", len(payload_bytes))
        return header + length_field + payload_bytes

    @classmethod
    def deserialize(cls, data: bytes) -> Optional['ProtocolMessage']:
        """Deserialize bytes into ProtocolMessage."""
        if len(data) < 13:
            return None

        msg_type, seq, ts, length = struct.unpack("!BIII", data[:13])

        if len(data) < 13 + length:
            return None

        payload = data[13:13+length]

        try:
            payload = json.loads(payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass  # Keep as bytes

        return cls(msg_type, seq, ts, payload)


def format_bytes(size: int) -> str:
    """Format byte count to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024.0
    return f"{size:.1f} TB"


# ── COLLECTOR (SERVER) ───────────────────────────────────────────────
class DataCollector:
    """
    Data Collector - Central server for receiving monitoring data.

    The Collector runs on the researcher's machine and listens for connections
    from monitored Agents. This architecture enables firewall traversal since
    Agents initiate outbound connections.
    """

    def __init__(self, port: int, encryption_key: Optional[str] = None):
        """
        Initialize Data Collector.

        Args:
            port: UDP port to listen on
            encryption_key: Optional encryption key for future implementation
        """
        self.port = port
        self.encryption_key = encryption_key
        self.running = False
        self.connected_agents: Dict[str, int] = {}  # IP -> port mapping
        self.last_response: Optional[Dict] = None
        self.socket: Optional[socket.socket] = None

    def start(self) -> None:
        """Start the collector server."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", self.port))
        sock.settimeout(1)

        self.running = True
        self.socket = sock

        print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║              FIRMUS DATA COLLECTOR (SERVER)                      ║
║              Listening on port {self.port:5d}                                  ║
║              Waiting for agents to connect...                     ║
╚═══════════════════════════════════════════════════════════════════╝
        """)

        self._print_available_commands()

        try:
            while self.running:
                try:
                    data, addr = sock.recvfrom(MAX_PACKET_SIZE)
                    self._register_agent(addr)
                    msg = ProtocolMessage.deserialize(data)
                    if msg:
                        self._handle_message(msg, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[-] Error: {e}")

        except KeyboardInterrupt:
            print("\n[*] Shutting down collector...")
        finally:
            sock.close()

    def _register_agent(self, addr: Tuple[str, int]) -> None:
        """Register a connected agent."""
        if addr[0] not in self.connected_agents:
            print(f"[+] Agent connected from {addr[0]}:{addr[1]}")
            self.connected_agents[addr[0]] = addr[1]

    def _print_available_commands(self) -> None:
        """Print available interactive commands."""
        print("[*] Available commands (when agent connects):")
        print("    list              List directory contents")
        print("    tree <path>       Recursive directory tree")
        print("    download <file>   Download file from agent")
        print("    ping              Test connectivity")
        print("    help              Show help")
        print("    exit              Stop collector")
        print()

    def _handle_message(self, msg: ProtocolMessage, addr: Tuple[str, int]) -> None:
        """Handle incoming message from agent."""
        self.last_response = {
            'message': msg,
            'address': addr,
            'timestamp': time.time()
        }

        # Heartbeat acknowledgments handled silently
        if msg.message_type == MessageType.HEARTBEAT_ACK:
            pass

    def send_command(self, addr: Tuple[str, int], msg_type: int, payload: Any = "") -> None:
        """Send command to agent."""
        msg = ProtocolMessage(msg_type, 0, time.time(), payload)
        self.socket.sendto(msg.serialize(), addr)

    def await_response(self, timeout: float = 5.0) -> Optional[ProtocolMessage]:
        """Wait for response from agent."""
        start = time.time()
        while time.time() - start < timeout:
            if self.last_response:
                resp = self.last_response
                self.last_response = None
                return resp['message']
            time.sleep(0.1)
        return None

    def interactive_session(self) -> None:
        """Run interactive command session."""
        if not self.connected_agents:
            print("[*] No agents connected. Waiting...")
            return

        agent_ip = list(self.connected_agents.keys())[0]
        agent_addr = (agent_ip, self.connected_agents[agent_ip])

        print(f"\n[*] Connected to agent: {agent_ip}:{self.connected_agents[agent_ip]}")

        while True:
            try:
                cmd = input(f"collector ({agent_ip})> ").strip()

                if not cmd:
                    continue

                parts = cmd.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                if command in ['exit', 'quit', 'q']:
                    break

                elif command == 'list':
                    path = args[0] if args else "."
                    self.send_command(agent_addr, MessageType.DIRECTORY_LIST, {'path': path})
                    response = self.await_response()
                    if response:
                        self._display_directory_listing(response)

                elif command == 'tree':
                    path = args[0] if args else "."
                    self.send_command(agent_addr, MessageType.DIRECTORY_TREE, {'path': path})
                    response = self.await_response()
                    if response:
                        self._display_directory_listing(response)

                elif command == 'download':
                    if not args:
                        print("Usage: download <filepath>")
                        continue
                    self._download_file(agent_addr, args[0])

                elif command == 'ping':
                    start = time.time()
                    self.send_command(agent_addr, MessageType.HEARTBEAT)
                    response = self.await_response()
                    if response and response.message_type == MessageType.HEARTBEAT_ACK:
                        elapsed = (time.time() - start) * 1000
                        print(f"[+] Response received in {elapsed:.0f}ms")
                    else:
                        print("[-] No response")

                elif command == 'help':
                    self._print_available_commands()

                else:
                    print(f"Unknown command: {command}")

            except KeyboardInterrupt:
                print("\n[*] Exiting session...")
                break

    def _display_directory_listing(self, response: ProtocolMessage) -> None:
        """Display directory listing from agent."""
        if response.message_type == MessageType.DATA_RESPONSE:
            payload = response.payload if isinstance(response.payload, dict) else {}

            for directory in payload.get('dirs', []):
                print(f"  {directory}/")

            for file_info in payload.get('files', []):
                name = file_info.get('name', '?')
                size = file_info.get('size', 0)
                print(f"  {name:50s} {format_bytes(size)}")

    def _download_file(self, addr: Tuple[str, int], filepath: str) -> None:
        """Download file from agent."""
        print(f"[*] Downloading {filepath}...")

        os.makedirs("received", exist_ok=True)
        output_path = os.path.join("received", os.path.basename(filepath))

        offset = 0
        chunk_size = 8192

        try:
            with open(output_path, 'wb') as f:
                while True:
                    self.send_command(addr, MessageType.FILE_TRANSFER_REQUEST, {
                        'file': filepath,
                        'offset': offset,
                        'size': chunk_size
                    })

                    response = self.await_response()

                    if not response:
                        print("[-] No response from agent")
                        return

                    if response.message_type == MessageType.ERROR_RESPONSE:
                        error_msg = response.payload.get('error', 'Unknown error') if isinstance(response.payload, dict) else 'Unknown error'
                        print(f"[-] Error: {error_msg}")
                        return

                    if response.message_type == MessageType.DATA_RESPONSE:
                        result = response.payload if isinstance(response.payload, dict) else {}
                        encoded = result.get('data', '')

                        if not encoded:
                            break

                        data = base64.b64decode(encoded)
                        f.write(data)
                        offset += len(data)

                        total = result.get('total', 0)
                        if total > 0:
                            pct = int(offset * 100 / total)
                            print(f"\r  Progress: {format_bytes(offset)} / {format_bytes(total)} ({pct}%)",
                                  end='', flush=True)

                        if len(data) < chunk_size:
                            print()
                            break

            print(f"\n[+] File saved: {output_path}")

        except Exception as e:
            print(f"[-] Download failed: {e}")


# ── AGENT (CLIENT) ───────────────────────────────────────────────────
class MonitoringAgent:
    """
    Monitoring Agent - Client that connects to Data Collector.

    The Agent runs on monitored devices and initiates outbound connections
    to the Collector. This design enables NAT/firewall traversal without
    requiring port forwarding or root privileges.
    """

    def __init__(self, collector_address: str, work_directory: str = ".", encryption_key: Optional[str] = None):
        """
        Initialize Monitoring Agent.

        Args:
            collector_address: Collector address as "host:port" or "host"
            work_directory: Directory to monitor/share
            encryption_key: Optional encryption key
        """
        # Parse collector address
        if ':' in collector_address:
            self.collector_host, self.collector_port = collector_address.split(':')
            self.collector_port = int(self.collector_port)
        else:
            self.collector_host = collector_address
            self.collector_port = DEFAULT_PORT

        self.work_directory = os.path.abspath(work_directory)
        self.encryption_key = encryption_key
        self.running = False
        self.socket: Optional[socket.socket] = None
        self.sequence = 0
        self.collector_address: Tuple[str, int] = (self.collector_host, self.collector_port)

    def start(self) -> None:
        """Start agent and connect to collector."""
        # Create UDP socket with ephemeral port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 0))  # OS assigns available port
        sock.settimeout(5)

        self.running = True
        self.socket = sock

        print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║              FIRMUS MONITORING AGENT (CLIENT)                     ║
║              Connecting to collector: {self.collector_host:15s}:{self.collector_port:5d}              ║
║              Working directory: {self.work_directory}                     ║
╚═══════════════════════════════════════════════════════════════════╝
        """)

        print("[*] Press Ctrl+C to stop")
        print()

        # Send initial heartbeat
        try:
            self._send_message(MessageType.HEARTBEAT)
            print("[+] Connected to collector")
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            return

        # Main event loop - listen for commands
        try:
            while self.running:
                try:
                    data, addr = sock.recvfrom(MAX_PACKET_SIZE)

                    # Only accept messages from registered collector
                    if addr != self.collector_address:
                        continue

                    msg = ProtocolMessage.deserialize(data)
                    if msg:
                        response = self._handle_command(msg)
                        if response:
                            resp_msg = ProtocolMessage(
                                response['type'],
                                self.sequence,
                                time.time(),
                                response.get('payload', b"")
                            )
                            sock.sendto(resp_msg.serialize(), self.collector_address)
                            self.sequence += 1

                except socket.timeout:
                    # Optional: send periodic heartbeat
                    continue

        except KeyboardInterrupt:
            print("\n[*] Shutting down agent...")
        finally:
            sock.close()

    def _send_message(self, msg_type: int, payload: Any = "") -> None:
        """Send message to collector."""
        msg = ProtocolMessage(msg_type, self.sequence, time.time(), payload)
        self.socket.sendto(msg.serialize(), self.collector_address)
        self.sequence += 1

    def _handle_command(self, msg: ProtocolMessage) -> Optional[Dict]:
        """Handle command from collector."""
        payload = msg.payload if isinstance(msg.payload, dict) else {}

        if msg.message_type == MessageType.DIRECTORY_LIST:
            path = payload.get('path', '.')
            files, dirs = self._scan_directory(path, recursive=False)
            return {'type': MessageType.DATA_RESPONSE, 'payload': {'files': files, 'dirs': dirs}}

        elif msg.message_type == MessageType.DIRECTORY_TREE:
            path = payload.get('path', '.')
            files, dirs = self._scan_directory(path, recursive=True)
            return {'type': MessageType.DATA_RESPONSE, 'payload': {'files': files, 'dirs': dirs}}

        elif msg.message_type == MessageType.FILE_TRANSFER_REQUEST:
            filepath = payload.get('file', '')
            offset = payload.get('offset', 0)
            size = payload.get('size', 8192)

            result = self._read_file_chunk(filepath, offset, size)
            if 'error' in result:
                return {'type': MessageType.ERROR_RESPONSE, 'payload': result}
            return {'type': MessageType.DATA_RESPONSE, 'payload': result}

        elif msg.message_type == MessageType.HEARTBEAT:
            return {'type': MessageType.HEARTBEAT_ACK}

        else:
            return {'type': MessageType.ERROR_RESPONSE, 'payload': {'error': 'Unknown command'}}

    def _scan_directory(self, path: str, recursive: bool) -> Tuple[List[Dict], List[str]]:
        """Scan directory and return files and subdirectories."""
        try:
            full_path = os.path.join(self.work_directory, path)

            if not os.path.exists(full_path):
                return [], []

            if os.path.isfile(full_path):
                stat = os.stat(full_path)
                return [{'name': os.path.basename(full_path), 'size': stat.st_size}], []

            files = []
            dirs = []

            if recursive:
                for root, dirnames, filenames in os.walk(full_path):
                    rel_root = os.path.relpath(root, self.work_directory)
                    if rel_root != '.':
                        dirs.append(rel_root.replace('\\', '/'))

                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        stat = os.stat(filepath)
                        rel_path = os.path.relpath(filepath, self.work_directory)
                        files.append({
                            'name': rel_path.replace('\\', '/'),
                            'size': stat.st_size
                        })
            else:
                for name in os.listdir(full_path):
                    entry_path = os.path.join(full_path, name)

                    if os.path.isfile(entry_path):
                        stat = os.stat(entry_path)
                        files.append({'name': name, 'size': stat.st_size})
                    elif os.path.isdir(entry_path):
                        dirs.append(name)

            return files, dirs

        except Exception as e:
            print(f"[-] Directory scan error: {e}")
            return [], []

    def _read_file_chunk(self, filepath: str, offset: int, size: int) -> Dict:
        """Read a chunk of file data."""
        try:
            full_path = os.path.join(self.work_directory, filepath)

            if not os.path.isfile(full_path):
                return {'error': 'File not found'}

            filesize = os.path.getsize(full_path)

            with open(full_path, 'rb') as f:
                f.seek(offset)
                data = f.read(size)

            return {
                'file': filepath,
                'offset': offset,
                'size': len(data),
                'total': filesize,
                'data': base64.b64encode(data).decode('ascii')
            }

        except Exception as e:
            return {'error': str(e)}


# ── Main Entry Point ─────────────────────────────────────────────────
def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="FIRMUS - Firewall-traversing Independent Remote Monitoring System",
        epilog="""
Research Implementation for Remote Filesystem Monitoring

Examples:
  # Start Collector (server) - Researcher's machine
  python3 remote_filesystem_research.py collector udp --port 5353

  # Start Agent (client) - Monitored device
  python3 remote_filesystem_research.py agent udp --collector 192.168.1.100:5353 --dir /data
        """
    )

    subparsers = parser.add_subparsers(dest='mode', help='Operating mode')

    # Collector mode (SERVER)
    collector_parser = subparsers.add_parser('collector', help='Run data collector (server)')
    collector_parser.add_argument('transport', choices=['udp'], help='Network transport')
    collector_parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Listening port')
    collector_parser.add_argument('--key', help='Encryption key (future)')

    # Agent mode (CLIENT)
    agent_parser = subparsers.add_parser('agent', help='Run monitoring agent (client)')
    agent_parser.add_argument('transport', choices=['udp'], help='Network transport')
    agent_parser.add_argument('--collector', required=True, help='Collector address (host:port)')
    agent_parser.add_argument('--dir', default='.', help='Directory to monitor')
    agent_parser.add_argument('--key', help='Encryption key (future)')

    args = parser.parse_args()

    if args.mode == 'collector':
        collector = DataCollector(args.port, args.key)

        # Start server in background thread
        import threading
        server_thread = threading.Thread(target=collector.start, daemon=True)
        server_thread.start()

        time.sleep(1)

        # Run interactive mode
        try:
            while True:
                if collector.connected_agents:
                    collector.interactive_session()
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Stopping collector...")
            collector.running = False
            server_thread.join(timeout=2)

    elif args.mode == 'agent':
        agent = MonitoringAgent(args.collector, args.dir, args.key)
        agent.start()


if __name__ == "__main__":
    main()
