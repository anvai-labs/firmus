# Use Cases

---

## 🏠 IoT Device Monitoring

```
┌─────────────────────────────────────────────────────────────┐
│  HOME NETWORK (behind NAT/firewall)                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Raspberry Pi 4                                     │    │
│  │  - IP: 192.168.1.50 (private)                       │    │
│  │  - Monitors: /var/sensor_data                       │    │
│  │  - Sensors: Temperature, Humidity, Air Quality      │    │
│  │  ┌────────────────────────────────────────────┐   │    │
│  │  │  Monitoring Agent (Client)                 │   │    │
│  │  │  Connects OUT to cloud collector          │   │    │
│  │  └────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Outbound UDP (traverses NAT)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  CLOUD VPS                                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Collector (UDP :5353)                        │    │
│  │  - Public IP: 203.0.113.10                         │    │
│  │  - Stores received data in /data/collected         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Scenario

Smart home sensor data collection without port forwarding.

**Setup:**
```bash
# On cloud VPS
python3 remote_filesystem_research.py collector udp --port 5353

# On Raspberry Pi (home)
python3 remote_filesystem_research.py agent udp \\
    --collector my-vps.com:5353 \\
    --dir /var/sensor_data
```

**Data Collection:**
```bash
# From VPS
collector (192.168.1.50)> list
  sensor_data.json
  logs/
  config.yaml

collector (192.168.1.50)> download sensor_data.json
[+] File saved: received/sensor_data.json
```

**Benefits:**
- ✅ No router configuration
- ✅ Works with dynamic IP
- ✅ No VPN overhead

---

## 🔬 Research Data Collection

```
┌─────────────────────────────────────────────────────────────┐
│  FIELD STATION (remote location, offline-capable)           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Edge Device (Jetson Nano / Industrial PC)          │    │
│  │  - Local storage: /field_data                       │    │
│  │  - Sensors: Camera, Weather, Environmental          │    │
│  │  ┌────────────────────────────────────────────┐   │    │
│  │  │  Monitoring Agent                          │   │    │
│  │  │  - Auto-reconnect on network available      │   │    │
│  │  │  - Buffers data when offline               │   │    │
│  │  └────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
       │                                    │
       │ Cellular (4G/5G)                   │ WiFi (when available)
       ▼                                    ▼
┌─────────────────────────────────────────────────────────────┐
│  UNIVERSITY SERVER                                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Collector + Automated Scripts                │    │
│  │  - Downloads new data hourly                       │    │
│  │  - Processes and archives to /research             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Scenario

Environmental research station data collection.

**Setup:**
```bash
# On university server
python3 remote_filesystem_research.py collector udp --port 5353

# On field station device
python3 remote_filesystem_research.py agent udp \\
    --collector research.edu:5353 \\
    --dir /field_data
```

**Automation (cron):**
```bash
# Hourly data download script
#!/bin/bash
cd /opt/firmus
echo "tree /field_data" | python3 -c "
import sys
sys.path.insert(0, '.')
from remote_filesystem_research import DataCollector, MessageType

c = DataCollector(5353)
c.start()  # Background mode in production
" > /tmp/firmus_commands.txt
```

---

## 🖥️ Home Server Administration

```
┌─────────────────────────────────────────────────────────────┐
│  HOME                                                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Home Server (NAS / Media Server)                   │    │
│  │  - Storage: /mnt/storage (10 TB)                    │    │
│  │  - Services: Plex, Jellyfin, File sharing           │    │
│  │  ┌────────────────────────────────────────────┐   │    │
│  │  │  Monitoring Agent                          │   │    │
│  │  │  - Read-only monitoring mode                │   │    │
│  │  └────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Access from anywhere
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAPTOP / PHONE (remote location)                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  SSH to VPS → Interactive collector session        │    │
│  │  - Check disk space                                │    │
│  │  - Download logs                                   │    │
│  │  - Verify backups                                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Scenario

Remote home server management without exposing SSH.

**Setup:**
```bash
# On VPS (jump host)
python3 remote_filesystem_research.py collector udp --port 5353

# On home server
python3 remote_filesystem_research.py agent udp \\
    --collector my-vps.com:5353 \\
    --dir /mnt/storage
```

**Remote Management:**
```bash
# From laptop (via SSH to VPS)
collector (192.168.1.100)> tree /mnt/storage/backups
  backups/
    2024-01/
    2024-02/
    2024-03/

collector (192.168.1.100)> list /mnt/storage/logs
  plex.log
  system.log
  smartd.log

collector (192.168.1.100)> download /mnt/storage/logs/system.log
```

---

## 🏢 Authorized System Administration

```
┌─────────────────────────────────────────────────────────────┐
│  CORPORATE NETWORK (with proper authorization)              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Managed Workstations                             │    │
│  │  - IT-department approved monitoring               │    │
│  │  - Application: Log collection, Updates            │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Internal network only
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  IT ADMINISTRATION SERVER                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Collector                                   │    │
│  │  - Collects logs from workstations                │    │
│  │  - Pushes update notifications                    │    │
│  │  - Automated monitoring dashboard                 │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Scenario

IT department log collection for authorized monitoring.

**⚠️ Requirements:**
- Written authorization from management
- Employee consent where required
- Network segregation
- Audit logging

---

## 🎓 Educational / Classroom

```
┌─────────────────────────────────────────────────────────────┐
│  COMPUTER LAB                                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Student PC 1│ │ Student PC 2│ │ Student PC 3│  ...      │
│  │ Agent       │ │ Agent       │ │ Agent       │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Lab network (isolated)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  INSTRUCTOR MACHINE                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Collector + Live Demo                        │    │
│  │  - Show filesystem structure                       │    │
│  │  - Demonstrate UDP concepts                        │    │
│  │  - Teaching network protocols                      │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Scenario

Teaching network protocols and filesystem concepts.

**Demo Commands:**
```bash
# Show students live packet structure
collector (student-pc)> list
[Explain binary protocol, JSON payload]

# Demonstrate firewall traversal
# Explain NAT, outbound connections
```

---

<div align="center">

**[← Back to README](../README.md)** • **[Deployment](deployment.md)** • **[Examples](../examples/)**

</div>
