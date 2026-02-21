# Security Policy

## Current Security Limitations

**This is a research prototype, not a production-ready system.**

The current implementation has the following security limitations:

### No Encryption
- All communication is cleartext UDP
- Messages can be intercepted and read by network observers
- No protection against man-in-the-middle attacks

### No Authentication
- Anyone who can reach the collector port can issue commands
- No verification of agent or collector identity
- Vulnerable to unauthorized command injection

### No Authorization
- No access control or user management
- All connected agents have full filesystem access
- No command whitelisting or restrictions

### No Integrity Verification
- No HMAC or message signatures
- Messages can be tampered with in transit
- No way to detect modified commands or responses

### No Rate Limiting
- No protection against command flooding
- Vulnerable to resource exhaustion attacks
- No throttling of file transfers

---

## Production Deployment Requirements

**For production use, the following security measures MUST be implemented:**

### 1. Encryption
- **AES-256-GCM** for payload encryption
- **Perfect Forward Secrecy** using ephemeral key exchange
- **TLS 1.3** if using TCP transport

### 2. Authentication
- **Mutual TLS** with certificate validation
- **Pre-shared keys** for agent-collector authentication
- **HMAC-SHA256** for message signing

### 3. Authorization
- **Command whitelisting** per agent
- **Path restrictions** (sandbox to specific directories)
- **Read-only mode** option for monitoring-only use cases

### 4. Network Security
- **Firewall rules** to restrict collector access
- **VPN or private network** deployment
- **IP whitelisting** for collector endpoint

### 5. Audit and Monitoring
- **Comprehensive logging** of all operations
- **Alerting** for suspicious activity
- **Regular security audits** of deployment

---

## Responsible Disclosure

### Reporting Security Vulnerabilities

If you discover a security vulnerability in this implementation:

1. **Do NOT** create a public issue
2. **DO** send details via private disclosure:
   - Email: [security@example.com]
   - PGP Key: [Link to key]
3. **Include**:
   - Vulnerability description
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 7 days
- **Fix**: As soon as practicable
- **Public Disclosure**: After fix is deployed

---

## Security Best Practices for Deployment

### Network Isolation
```bash
# Deploy on isolated network
# Use VPN for collector access
# Restrict with firewall rules:
sudo ufw allow from 10.0.0.0/8 to any port 5353 proto udp
```

### Filesystem Sandbox
```bash
# Run agent with dedicated user
useradd -r -s /bin/false firmus-agent
# Chroot or containerize
# Set filesystem permissions
chmod -R 750 /var/monitored/data
```

### Monitoring
```bash
# Log all connections
# Monitor for unusual activity
# Set up alerts for file access patterns
```

---

## Threat Model

### Assumed Threats

This prototype does **NOT** protect against:

1. **Network Eavesdropping** - Cleartext communication
2. **Command Injection** - No authentication
3. **Unauthorized Access** - No access control
4. **Data Tampering** - No integrity checks
5. **Replay Attacks** - No sequence number validation

### Out of Scope

The following are explicitly out of scope for this research prototype:

- Protection against compromised collector
- Protection against compromised agent host
- Defense against determined attackers
- Compliance requirements (SOC2, HIPAA, etc.)

---

## Security Research Context

This tool is intended for:

- **Academic research** in distributed systems
- **Legitimate system administration** with proper authorization
- **IoT device monitoring** in trusted environments
- **Educational purposes** to understand network protocols

**NOT intended for**:

- Bypassing security controls without authorization
- Accessing systems without owner consent
- Evading detection in unauthorized scenarios

---

## Disclaimer

This software is provided for research and educational purposes only. Users
are responsible for ensuring compliance with applicable laws and regulations.
The authors accept no liability for misuse or unauthorized use.

**Always obtain proper authorization before deploying monitoring agents.**
