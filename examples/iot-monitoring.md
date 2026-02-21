# IoT Monitoring Example

---

## Scenario: Smart Home Sensor Collection

Collect sensor data from a Raspberry Pi without port forwarding.

```
┌─────────────────────────────────────────────────────────────┐
│  HOME NETWORK (192.168.1.0/24)                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Raspberry Pi 4                                     │    │
│  │  IP: 192.168.1.50 (DHCP - may change)              │    │
│  │                                                     │    │
│  │  Sensors Connected:                                 │    │
│  │  • DHT22 - Temperature/Humidity                     │    │
│  │  • MQ-135 - Air Quality                             │    │
│  │  • BMP280 - Barometric Pressure                     │    │
│  │                                                     │    │
│  │  Data Storage: /var/sensor_data                     │    │
│  │  ├── readings.json (updated every 5 min)           │    │
│  │  ├── logs/                                          │    │
│  │  └── config.yaml                                    │    │
│  │                                                     │    │
│  │  ┌────────────────────────────────────────────┐   │    │
│  │  │  Monitoring Agent (autostart on boot)      │   │    │
│  │  │  - Connects to cloud collector             │   │    │
│  │  │  - Survives DHCP IP changes                │   │    │
│  │  └────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Outbound UDP :5353
                          │ (no port forwarding needed)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  CLOUD VPS                                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Collector                                    │    │
│  │  IP: 203.0.113.10 (static public IP)               │    │
│  │                                                     │    │
│  │  Stores received data in:                          │    │
│  │  ~/firmus_collected/                               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Hardware

| Component | Specification |
|-----------|---------------|
| **Board** | Raspberry Pi 4 (2GB RAM minimum) |
| **Storage** | 16GB+ microSD (or SSD via USB) |
| **Network** | Ethernet or WiFi |
| **Sensors** | DHT22, MQ-135, BMP280 (I2C/GPIO) |
| **Power** | 5V 3A USB-C supply |

---

## Software Setup

### 1. Install Raspberry Pi OS

```bash
# Flash Raspberry Pi OS Lite (64-bit)
# Enable SSH during setup
# Connect to network
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python3 and sensors libraries
sudo apt install -y python3 python3-pip
pip3 install adafruit-circuitpython-dht
pip3 install smbus2  # for I2C sensors

# Enable I2C (if using I2C sensors)
sudo raspi-config
# Interface Options → I2C → Enable
```

### 3. Create Sensor Script

```bash
# Create sensor reading script
sudo nano /usr/local/bin/read_sensors.py
```

```python
#!/usr/bin/env python3
import json
import time
from datetime import datetime

# Sensor imports (actual implementation varies)
# import board
# import adafruit_dht

def read_sensors():
    """Read all sensors and return data dict."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "temperature": 22.5,  # Replace with actual sensor reading
        "humidity": 45.2,
        "pressure": 1013.25,
        "air_quality": 150
    }

    # Example: DHT22
    # dht = adafruit_dht.DHT22(board.D4)
    # data["temperature"] = dht.temperature
    # data["humidity"] = dht.humidity

    return data

def main():
    while True:
        reading = read_sensors()

        # Save to file
        with open("/var/sensor_data/readings.json", "w") as f:
            json.dump(reading, f, indent=2)

        print(f"[{reading['timestamp']}] T={reading['temperature']}°C "
              f"H={reading['humidity']}%")

        time.sleep(300)  # Every 5 minutes

if __name__ == "__main__":
    main()
```

```bash
# Make executable
chmod +x /usr/local/bin/read_sensors.py
```

### 4. Create Data Directory

```bash
sudo mkdir -p /var/sensor_data/logs
sudo chown pi:pi /var/sensor_data
```

### 5. Install FIRMUS

```bash
# On Raspberry Pi
cd ~
git clone https://github.com/yourusername/firmus.git
cd firmus

# Test agent manually first
python3 remote_filesystem_research.py agent udp \\
    --collector YOUR_VPS_IP:5353 \\
    --dir /var/sensor_data
```

---

## Cloud VPS Setup

### 1. Create VPS

**Provider:** Any VPS provider (DigitalOcean, Linode, AWS Lightsail, etc.)

**Specs:**
- 1 vCPU, 512MB RAM minimum
- Ubuntu 22.04 LTS or similar
- Public IP required

### 2. Configure Firewall

```bash
# On VPS
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5353/udp  # FIRMUS
sudo ufw enable
```

### 3. Start Collector

```bash
# On VPS
cd ~/firmus
python3 remote_filesystem_research.py collector udp --port 5353
```

---

## Auto-Start on Boot

### Raspberry Pi (Agent)

Create systemd service: `sudo nano /etc/systemd/system/firmus-agent.service`

```ini
[Unit]
Description=FIRMUS Monitoring Agent
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/firmus
ExecStart=/usr/bin/python3 /home/pi/firmus/remote_filesystem_research.py agent udp \\
    --collector YOUR_VPS_IP:5353 \\
    --dir /var/sensor_data
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable firmus-agent
sudo systemctl start firmus-agent
sudo systemctl status firmus-agent
```

### Sensor Reading Service

`sudo nano /etc/systemd/system/sensor-reader.service`

```ini
[Unit]
Description=Sensor Data Reader
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /usr/local/bin/read_sensors.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable sensor-reader
sudo systemctl start sensor-reader
```

---

## Usage

### Interactive Collection

From your VPS (SSH into it):

```bash
# Start collector (or use systemd service)
python3 remote_filesystem_research.py collector udp --port 5353

# When agent connects
collector (192.168.1.50)> tree
  readings.json                                               245 B
  config.yaml                                                 156 B
  logs/
    2024-02-19.log                                            1.2 KB
    2024-02-20.log                                            2.1 KB

collector (192.168.1.50)> download readings.json
[+] File saved: received/readings.json

collector (192.168.1.50)> download logs/2024-02-20.log
[+] File saved: received/2024-02-20.log
```

---

## Automation

### Cron Job (Hourly Collection)

On VPS: `crontab -e`

```cron
# Hourly sensor data collection
0 * * * * cd ~/firmus && /usr/bin/python3 -c "
from remote_filesystem_research import DataCollector, MessageType
import time

c = DataCollector(5353)
# Wait for agent connection
time.sleep(2)

# Download latest readings
addr = ('192.168.1.50', 54321)  # Agent's ephemeral port
c.send_command(addr, MessageType.FILE_TRANSFER_REQUEST, {
    'file': '/var/sensor_data/readings.json',
    'offset': 0,
    'size': 8192
})
" >> ~/firmus/collector.log 2>&1
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent won't connect | Check VPS firewall, verify `--collector` IP |
| Can't read sensors | Check GPIO/I2C permissions, run as pi user |
| Data not updating | Check `sensor-reader` service status |
| Connection drops | Check network stability, agent auto-reconnects |

---

<div align="center">

**[← Back to Documentation](../docs/)** • **[Data Collection](data-collection.md)**

</div>
