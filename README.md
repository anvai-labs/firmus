# FIRMUS

<div align="center">

**Firewall-traversing Independent Remote Monitoring and Uninterrupted Filesystem Access System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A research implementation for remote filesystem monitoring of IoT and edge devices behind NAT/firewalls.

[⚠️ Security Notice](#security-notice) • [📖 Documentation](#documentation) • [🚀 Quick Start](#quick-start) • [📝 Blog Post](MEDIUM_BLOG_POST.md)

</div>

---

## ⚠️ Security Notice

**This is a research prototype, NOT production-ready software.**

- ❌ No encryption (cleartext communication)
- ❌ No authentication (anyone can connect)
- ❌ No authorization (no access control)

**DO NOT deploy on production systems without additional security measures.**

See [SECURITY.md](SECURITY.md) for details and [DISCLAIMER.md](DISCLAIMER.md) for legal and ethical use guidelines.

---

## Overview

FIRMUS enables remote filesystem monitoring through firewalls and NAT without requiring:

- ✅ No root privileges
- ✅ No port forwarding
- ✅ No static IP addresses
- ✅ No VPN infrastructure
- ✅ No complex configuration

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR MACHINE                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │         DATA COLLECTOR (SERVER)                     │    │
│  │  Listens on UDP port 5353                          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ Outbound connection (firewall-friendly)
                            │
┌─────────────────────────────────────────────────────────────┐
│                    TARGET DEVICE                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │         MONITORING AGENT (CLIENT)                   │    │
│  │  Connects OUT to collector                          │    │
│  │  Uses ephemeral port                                │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

The key insight: **Most firewalls allow outbound connections.** By having the agent initiate the connection, we achieve reliable NAT/firewall traversal.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔓 **Firewall Traversal** | Agent connects out through NAT/firewall |
| 👤 **No Root Required** | Runs in user space with standard sockets |
| 📁 **Directory Listing** | Flat and recursive directory tree traversal |
| 📥 **File Download** | Chunked file transfer with progress tracking |
| 💓 **Connectivity Check** | Ping/pong for connection verification |
| 🪶 **Lightweight** | ~500 lines, standard library only |
| 🐍 **Cross-Platform** | Works on Linux, macOS, Windows |

---

## Use Cases

### IoT Device Monitoring
Monitor home automation, sensors, or edge devices:

```bash
# On IoT device (Raspberry Pi, etc.)
agent --collector cloud.researchlab.edu:5353 --dir /var/sensor_data
```

### Remote Data Collection
Collect research data from field deployments:

```bash
# Field station agent
agent --collector data-collector.example.com:5353 --dir /field_data
```

### Home Server Administration
Access home servers from anywhere:

```bash
# Home server agent
agent --collector my-vps.com:5353 --dir /mnt/storage
```

### Authorized System Analysis
Retrieve system logs and diagnostic data during authorized security assessments with proper documentation and approval.

---

## Quick Start

### Requirements

- Python 3.8 or higher
- Network connectivity between collector and agents
- Write access to working directory (for agent)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/firmus.git
cd firmus

# No dependencies required - uses Python standard library only
```

### Starting the Collector (Server)

**Terminal 1 - On your machine:**

```bash
python3 remote_filesystem_research.py collector udp --port 5353
```

Output:
```
╔═══════════════════════════════════════════════════════════════════╗
║              FIRMUS DATA COLLECTOR (SERVER)                      ║
║              Listening on port  5353                                 ║
║              Waiting for agents to connect...                     ║
╚═══════════════════════════════════════════════════════════════════╝

[*] Available commands (when agent connects):
    list              List directory contents
    tree <path>       Recursive directory tree
    download <file>   Download file from agent
    ping              Test connectivity
    help              Show help
    exit              Stop collector
```

### Starting the Agent (Client)

**Terminal 2 - On target device:**

```bash
python3 remote_filesystem_research.py agent udp \\
    --collector YOUR_IP:5353 \\
    --dir /path/to/monitor
```

Output:
```
╔═══════════════════════════════════════════════════════════════════╗
║              FIRMUS MONITORING AGENT (CLIENT)                     ║
║              Connecting to collector: YOUR_IP:5353                ║
║              Working directory: /path/to/monitor                  ║
╚═══════════════════════════════════════════════════════════════════╝

[*] Press Ctrl+C to stop
[+] Connected to collector
```

### Interactive Commands

Once connected, use these commands at the collector:

```bash
# Test connectivity
collector (192.168.1.50)> ping
[+] Response received in 12ms

# List directory (flat)
collector (192.168.1.50)> list /data
  logs/
  sensor_data.json
  config.yaml

# Recursive directory tree
collector (192.168.1.50)> tree /data
  logs/
    app.log
    error.log
  sensor_data.json
  config.yaml

# Download file
collector (192.168.1.50)> download /data/sensor_data.json
[*] Downloading /data/sensor_data.json...
  Progress: 45.2 KB / 45.2 KB (100%)
[+] File saved: received/sensor_data.json

# Show help
collector (192.168.1.50)> help

# Exit
collector (192.168.1.50)> exit
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [MEDIUM_BLOG_POST.md](MEDIUM_BLOG_POST.md) | Detailed blog post explaining architecture and use cases |
| [SECURITY.md](SECURITY.md) | Security limitations and production requirements |
| [DISCLAIMER.md](DISCLAIMER.md) | Legal and ethical use guidelines |
| [LICENSE](LICENSE) | MIT License |

---

## Architecture

### Protocol Design

FIRMUS uses a simple binary protocol over UDP:

```
[Header: 13 bytes]
├─ Message Type: 1 byte  (LIST, TREE, PULL, DATA, PING, PONG, ERROR)
├─ Sequence:     4 bytes (Message sequencing)
├─ Timestamp:    4 bytes (Unix timestamp)
└─ Payload Len:  4 bytes (Length of payload)

[Payload: Variable]
└─ JSON-encoded data
```

### Message Types

| Type | Value | Purpose |
|------|-------|---------|
| DIRECTORY_LIST | 1 | List directory contents (flat) |
| DIRECTORY_TREE | 2 | Recursive directory listing |
| FILE_TRANSFER_REQUEST | 3 | Request file chunk |
| DATA_RESPONSE | 100 | Return requested data |
| HEARTBEAT | 5 | Connectivity check |
| HEARTBEAT_ACK | 102 | Connectivity acknowledgment |
| ERROR_RESPONSE | 104 | Error information |

### File Transfer

Files are transferred in 8KB chunks with base64 encoding:

1. Collector requests chunk with offset and size
2. Agent responds with base64-encoded data
3. Collector decodes and writes to file
4. Process repeats until file complete

This enables:
- Resume capability (offset-based)
- Progress tracking
- Memory efficiency
- Network-friendly packets

---

## Performance

Tested on standard residential network (100 Mbps):

| Operation | Time | Notes |
|-----------|------|-------|
| Agent connection | < 100ms | One-way UDP |
| Directory listing (100 files) | ~50ms | Single packet |
| File download (1 MB) | ~200ms | 8KB chunks |
| Recursive scan (1000 files) | ~500ms | Depends on filesystem |

---

## Limitations

### Current Limitations

1. **UDP transport only** - No reliability guarantees
2. **No encryption** - Cleartext communication
3. **No authentication** - Anyone who can connect can issue commands
4. **Single-threaded** - One agent at a time
5. **No compression** - Files transferred as-is
6. **IPv4 only** - IPv6 not implemented

### Future Enhancements

- [ ] TCP transport option
- [ ] End-to-end encryption (AES-256-GCM)
- [ ] Mutual authentication (mTLS)
- [ ] Multi-agent support
- [ ] Web-based UI
- [ ] Agent auto-update
- [ ] Compression (zlib)
- [ ] IPv6 support

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

For security issues, please see [SECURITY.md](SECURITY.md#responsible-disclosure).

---

## Citation

If you use FIRMUS in research, please cite:

```bibtex
@software{firmus2024,
  title = {FIRMUS: Firewall-traversing Independent Remote Monitoring System},
  author = {FIRMUS Contributors},
  year = {2024},
  url = {https://github.com/yourusername/firmus},
  note = {Research prototype for remote filesystem monitoring}
}
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Disclaimer

**FIRMUS is a research prototype provided for educational and authorized administrative purposes only.**

Users are responsible for:
- Obtaining proper authorization before deployment
- Ensuring compliance with applicable laws
- Implementing appropriate security measures

See [DISCLAIMER.md](DISCLAIMER.md) for legal and ethical use guidelines.

**The authors accept no liability for misuse or unauthorized use.**

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/firmus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/firmus/discussions)
- **Security**: See [SECURITY.md](SECURITY.md#responsible-disclosure)

---

<div align="center">

**[⬆ Back to Top](#firmus)**

Made with ❤️ for the research community

</div>
