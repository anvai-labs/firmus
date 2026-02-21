# API Reference

---

## Class Overview

| Class | Role | Methods |
|-------|------|---------|
| `DataCollector` | UDP server, receives connections | `start()`, `send_command()`, `interactive_session()` |
| `MonitoringAgent` | UDP client, connects to collector | `start()`, `_handle_command()` |
| `ProtocolMessage` | Binary protocol serialization | `serialize()`, `deserialize()` |
| `MessageType` | Protocol constants (class) | N/A (constants) |

---

## DataCollector

### Purpose

Central server that listens for agent connections and issues commands.

### Constructor

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `port` | int | ✅ | - | UDP port to listen on |
| `encryption_key` | Optional[str] | ❌ | None | Reserved for future encryption |

```python
collector = DataCollector(port=5353)
```

### Methods

#### `start() → None`

Start the collector server and begin listening for connections.

**Behavior:**
- Binds UDP socket to `0.0.0.0:port`
- Registers connecting agents
- Enters command loop

**Raises:**
- `KeyboardInterrupt` — User stops server

**Example:**
```python
collector = DataCollector(port=5353)
collector.start()
```

---

#### `send_command(addr, msg_type, payload="") → None`

Send a command to a connected agent.

| Parameter | Type | Description |
|-----------|------|-------------|
| `addr` | Tuple[str, int] | Agent (IP, port) |
| `msg_type` | int | `MessageType` constant |
| `payload` | Any | Command data (dict or str) |

**Example:**
```python
collector.send_command(
    ('192.168.1.50', 54321),
    MessageType.DIRECTORY_LIST,
    {'path': '/data'}
)
```

---

#### `await_response(timeout=5.0) → Optional[ProtocolMessage]`

Wait for a response from the agent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | float | 5.0 | Max wait seconds |

**Returns:** `ProtocolMessage` or `None` (timeout)

**Example:**
```python
collector.send_command(addr, MessageType.HEARTBEAT)
response = collector.await_response(timeout=2.0)
if response and response.message_type == MessageType.HEARTBEAT_ACK:
    print("Agent is alive")
```

---

#### `interactive_session() → None`

Run interactive command prompt for connected agent.

**Available Commands:**

| Command | Arguments | Description |
|---------|-----------|-------------|
| `list` | `[path]` | List directory (flat) |
| `tree` | `[path]` | Recursive directory tree |
| `download` | `<filepath>` | Download file from agent |
| `ping` | - | Test connectivity |
| `help` | - | Show commands |
| `exit` | - | Stop collector |

**Example:**
```python
collector = DataCollector(port=5353)
collector.start()  # Runs in main thread
# After agent connects:
collector.interactive_session()
```

---

## MonitoringAgent

### Purpose

Client that connects to collector and services filesystem requests.

### Constructor

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `collector_addr` | str | ✅ | - | `host:port` of collector |
| `working_dir` | str | ✅ | - | Directory to monitor |
| `encryption_key` | Optional[str] | ❌ | None | Reserved for future |

```python
agent = MonitoringAgent(
    collector_addr="192.168.1.10:5353",
    working_dir="/var/sensor_data"
)
```

### Methods

#### `start() → None`

Start agent and connect to collector.

**Behavior:**
- Resolves collector address
- Creates UDP socket
- Enters command loop
- Sends periodic heartbeats

**Raises:**
- `KeyboardInterrupt` — User stops agent
- `ConnectionError` — Collector unreachable

**Example:**
```python
agent = MonitoringAgent("collector.example.com:5353", "/data")
agent.start()
```

---

#### `_handle_command(msg) → ProtocolMessage`

Process incoming command and return response.

| Parameter | Type | Description |
|-----------|------|-------------|
| `msg` | ProtocolMessage | Command from collector |

**Returns:** Response `ProtocolMessage`

**Handled Commands:**

| Type | Action |
|------|--------|
| `DIRECTORY_LIST` | `os.listdir()` + file sizes |
| `DIRECTORY_TREE` | Recursive `os.walk()` |
| `FILE_TRANSFER_REQUEST` | Read file chunk, base64 encode |
| `HEARTBEAT` | Return `HEARTBEAT_ACK` |

---

## ProtocolMessage

### Purpose

Binary protocol serialization/deserialization.

### Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `message_type` | int | `MessageType` constant |
| `sequence` | int | Message sequence number |
| `timestamp` | float | Unix timestamp |
| `payload` | Any | JSON dict or raw bytes |

### Methods

#### `serialize() → bytes`

Convert message to binary for network transmission.

**Format:**
```
[type:1B][seq:4B][ts:4B][len:4B][payload:variable]
```

**Example:**
```python
msg = ProtocolMessage(
    message_type=MessageType.DIRECTORY_LIST,
    sequence=0,
    timestamp=time.time(),
    payload={'path': '/data'}
)
data = msg.serialize()
sock.sendto(data, addr)
```

---

#### `deserialize(data: bytes) → Optional[ProtocolMessage]`

Parse binary data into `ProtocolMessage`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | bytes | Raw packet data |

**Returns:** `ProtocolMessage` or `None` (invalid packet)

**Example:**
```python
data, addr = sock.recvfrom(65535)
msg = ProtocolMessage.deserialize(data)
if msg:
    print(f"Got type {msg.message_type}: {msg.payload}")
```

---

## MessageType

### Purpose

Protocol message type constants (class, not instantiable).

### Constants

| Constant | Value | Direction |
|----------|-------|-----------|
| `DIRECTORY_LIST` | 1 | Collector → Agent |
| `DIRECTORY_TREE` | 2 | Collector → Agent |
| `FILE_TRANSFER_REQUEST` | 3 | Collector → Agent |
| `DATA_RESPONSE` | 100 | Agent → Collector |
| `HEARTBEAT` | 5 | Collector → Agent |
| `HEARTBEAT_ACK` | 102 | Agent → Collector |
| `ERROR_RESPONSE` | 104 | Agent → Collector |

### Usage

```python
from remote_filesystem_research import MessageType

msg = ProtocolMessage(
    message_type=MessageType.HEARTBEAT,
    sequence=0,
    timestamp=time.time(),
    payload=""
)
```

---

## Utility Functions

### `format_bytes(size: int) → str`

Convert byte count to human-readable string.

| Parameter | Type | Description |
|-----------|------|-------------|
| `size` | int | Size in bytes |

**Returns:** Formatted string (`"45.2 KB"`, `"1.2 MB"`, etc.)

**Example:**
```python
format_bytes(45234)   # "44.2 KB"
format_bytes(1024)    # "1.0 KB"
format_bytes(500)     # "500 B"
```

---

## Command-Line Interface

### Collector Mode

```bash
python3 remote_filesystem_research.py collector udp --port 5353
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `collector` | ✅ | - | Run as server |
| `udp` | ✅ | - | Transport protocol |
| `--port` | ❌ | 5353 | Listening port |

---

### Agent Mode

```bash
python3 remote_filesystem_research.py agent udp \\
    --collector HOST:PORT \\
    --dir /path/to/monitor
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `agent` | ✅ | - | Run as client |
| `udp` | ✅ | - | Transport protocol |
| `--collector` | ✅ | - | Collector `host:port` |
| `--dir` | ✅ | - | Directory to monitor |

---

<div align="center">

**[← Back to README](../README.md)** • **[Architecture](architecture.md)** • **[Deployment](deployment.md)**

</div>
