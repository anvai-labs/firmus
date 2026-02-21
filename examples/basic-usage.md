# Basic Usage Example

---

## Scenario: Local Testing

Test FIRMUS on a single machine or local network.

```
┌─────────────────────────────────────────┐
│  Terminal 1: Collector (localhost)      │
│  UDP Port: 5353                         │
└─────────────────────────────────────────┘
                  ▲
                  │ Local UDP
                  │
┌─────────────────────────────────────────┐
│  Terminal 2: Agent (localhost)          │
│  Working Dir: /tmp/firmus_test          │
└─────────────────────────────────────────┘
```

---

## Step 1: Prepare Test Directory

```bash
# Create test directory with sample files
mkdir -p /tmp/firmus_test
cd /tmp/firmus_test

# Create sample files
echo "Sample data" > data.txt
echo "More data" > logs.txt
mkdir subdir
echo "Nested file" > subdir/nested.txt
```

---

## Step 2: Start Collector

**Terminal 1:**
```bash
cd /path/to/firmus
python3 remote_filesystem_research.py collector udp --port 5353
```

**Output:**
```
╔═══════════════════════════════════════════════════════════════════╗
║              FIRMUS DATA COLLECTOR (SERVER)                      ║
║              Listening on port  5353                                  ║
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

---

## Step 3: Start Agent

**Terminal 2:**
```bash
cd /path/to/firmus
python3 remote_filesystem_research.py agent udp \\
    --collector 127.0.0.1:5353 \\
    --dir /tmp/firmus_test
```

**Output:**
```
╔═══════════════════════════════════════════════════════════════════╗
║              FIRMUS MONITORING AGENT (CLIENT)                     ║
║              Connecting to collector: 127.0.0.1:5353                ║
║              Working directory: /tmp/firmus_test                    ║
╚═══════════════════════════════════════════════════════════════════╝

[*] Press Ctrl+C to stop
[+] Connected to collector
```

**Collector Terminal 1 shows:**
```
[+] Agent connected from 127.0.0.1:54321
```

---

## Step 4: Interactive Commands

At the collector prompt:

### Test Connectivity
```bash
collector (127.0.0.1)> ping
[+] Response received in 2ms
```

### List Directory (Flat)
```bash
collector (127.0.0.1)> list
  data.txt                                                     12 B
  logs.txt                                                     9 B
  subdir/

collector (127.0.0.1)> list subdir
  nested.txt                                                   12 B
```

### Recursive Tree
```bash
collector (127.0.0.1)> tree
  data.txt                                                     12 B
  logs.txt                                                     9 B
  subdir/
    nested.txt                                                 12 B
```

### Download File
```bash
collector (127.0.0.1)> download data.txt
[*] Downloading data.txt...
  Progress: 12 B / 12 B (100%)
[+] File saved: received/data.txt

# Verify
cat received/data.txt
Sample data
```

---

## Step 5: Cleanup

```bash
# Stop agent (Terminal 2): Ctrl+C
# Stop collector (Terminal 1): type 'exit' or Ctrl+C

# Remove test data
rm -rf /tmp/firmus_test
rm -rf received/
```

---

## Two-Machine Setup

For testing on separate machines:

**Machine A (Collector):**
```bash
# Get IP address
ip addr show | grep inet

# Start collector
python3 remote_filesystem_research.py collector udp --port 5353
```

**Machine B (Agent):**
```bash
# Replace A_IP with Machine A's IP
python3 remote_filesystem_research.py agent udp \\
    --collector A_IP:5353 \\
    --dir /home/user/documents
```

---

<div align="center">

**[← Back to Documentation](../docs/)** • **[IoT Monitoring](iot-monitoring.md)**

</div>
