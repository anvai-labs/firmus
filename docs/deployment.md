# Deployment Guide

---

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8 | 3.10+ |
| Network | UDP connectivity | Low-latency link |
| RAM | 64 MB | 128 MB |
| Disk | 10 MB | 100 MB+ (for received files) |
| Permissions | User space | No root required |

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/firmus.git
cd firmus
```

### Step 2: Verify Python

```bash
python3 --version  # Should be 3.8+
```

### Step 3: No Dependencies Required

✅ Uses Python standard library only

---

## Configuration

### Collector Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--port` | 5353 | UDP listening port |
| Bind address | `0.0.0.0` | All interfaces |

**Example:**
```bash
python3 remote_filesystem_research.py collector udp --port 5353
```

---

### Agent Configuration

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--collector` | ✅ | `host:port` of collector |
| `--dir` | ✅ | Directory to monitor |

**Example:**
```bash
python3 remote_filesystem_research.py agent udp \\
    --collector collector.example.com:5353 \\
    --dir /var/sensor_data
```

---

## Network Setup

### Firewall Rules (Collector)

```bash
# Linux (ufw)
sudo ufw allow from 10.0.0.0/8 to any port 5353 proto udp

# Linux (firewalld)
sudo firewall-cmd --permanent --add-port=5353/udp
sudo firewall-cmd --reload

# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3

# Windows (netsh)
netsh advfirewall firewall add rule name="FIRMUS" dir=in action=allow protocol=UDP localport=5353
```

---

### Port Forwarding (if applicable)

```
Router: Forward UDP 5353 → Collector IP
```

**Note:** Typically NOT needed since agent connects out.

---

## Service Setup

### systemd (Linux)

**Collector Service** (`/etc/systemd/system/firmus-collector.service`):

```ini
[Unit]
Description=FIRMUS Data Collector
After=network.target

[Service]
Type=simple
User=firmus
WorkingDirectory=/opt/firmus
ExecStart=/usr/bin/python3 /opt/firmus/remote_filesystem_research.py collector udp --port 5353
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Agent Service** (`/etc/systemd/system/firmus-agent.service`):

```ini
[Unit]
Description=FIRMUS Monitoring Agent
After=network.target

[Service]
Type=simple
User=firmus-agent
WorkingDirectory=/opt/firmus
ExecStart=/usr/bin/python3 /opt/firmus/remote_filesystem_research.py agent udp \\
    --collector collector.example.com:5353 \\
    --dir /var/sensor_data
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable firmus-collector  # or firmus-agent
sudo systemctl start firmus-collector
sudo systemctl status firmus-collector
```

---

### launchd (macOS)

**Collector plist** (`~/Library/LaunchAgents/com.firmus.collector.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.firmus.collector</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/opt/firmus/remote_filesystem_research.py</string>
        <string>collector</string>
        <string>udp</string>
        <string>--port</string>
        <string>5353</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Load:**
```bash
launchctl load ~/Library/LaunchAgents/com.firmus.collector.plist
launchctl start com.firmus.collector
```

---

## Docker Deployment

### Dockerfile (Agent)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY remote_filesystem_research.py .

RUN useradd -r -s /bin/false firmus
USER firmus

CMD ["python3", "remote_filesystem_research.py", "agent", "udp", \\
     "--collector", "host.docker.internal:5353", \\
     "--dir", "/data"]
```

**Build and run:**
```bash
docker build -t firmus-agent .
docker run -v /var/sensor_data:/data firmus-agent
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Start collector** | `python3 remote_filesystem_research.py collector udp --port 5353` |
| **Start agent** | `python3 remote_filesystem_research.py agent udp --collector HOST:5353 --dir /path` |
| **Test connectivity** | At collector: `ping` |
| **List directory** | At collector: `list /path` |
| **Download file** | At collector: `download /path/file` |
| **Stop** | `Ctrl+C` or `exit` |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent won't connect | Wrong address/firewall | Check `--collector`, firewall rules |
| "No response" | Agent offline/crashed | Check agent logs, restart agent |
| Permission denied | Insufficient rights | Run agent with appropriate user |
| Port in use | Conflicting service | Change `--port` |

---

<div align="center">

**[← Back to README](../README.md)** • **[API Reference](api.md)** • **[Use Cases](use-cases.md)**

</div>
