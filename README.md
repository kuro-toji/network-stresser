# Network Stresser

A professional-grade, feature-rich network load testing and stress testing tool built with Python. Designed for comprehensive web server performance evaluation under various conditions.

## Features

### Attack Modes
- **HTTP Flood** - High volume requests to test server capacity
- **Connection Saturation** - Exhaust connection pools with many concurrent connections
- **Slow Request** - Long-duration requests for legitimate timeout testing
- **Slowloris** - Partial header keep-alive exhaustion attack
- **Slow POST** - Slow body transmission attack
- **UDP Flood** - Direct UDP packet flooding for non-HTTP services
- **Raw TCP Socket** - Direct TCP socket connections

### Protocol Support
- **HTTP/1.1** - Standard HTTP protocol
- **HTTP/2** - Multiplexed connections
- **QUIC/HTTP3** - Next-generation protocol
- **WebSocket** - WebSocket server testing
- **IPv6** - Native IPv6 targeting
- **Custom HTTP Versions** - HTTP/0.9, HTTP/1.0, HTTP/1.1

### Advanced Testing
- **HTTP Pipelining** - Send multiple requests in one connection
- **HTTP Request Smuggling** - TEO+CL, CL+TEO, TE-content variants
- **Range Header Testing** - Partial content requests
- **Malformed Requests** - Invalid HTTP requests for robustness testing
- **GZIP Bomb** - Decompression bomb payload testing
- **DNS Stress Test** - DNS server load testing
- **Host Header Injection** - Virtual host testing
- **Cache Bypass** - Random query params to bypass CDN cache

### Authentication & Security
- **Bearer Token** - OAuth/JWT bearer authentication
- **Basic Auth** - HTTP Basic authentication
- **Session Cookies** - Cookie-based authentication
- **Client Certificates** - SSL/TLS client cert/key support
- **TLS Version Control** - TLSv1, TLSv1.1, TLSv1.2, TLSv1.3
- **TLS Cipher Selection** - Custom cipher suite selection

### Network Features
- **Proxy Support** - Single HTTP proxy
- **Proxy Chain** - Multiple proxies with rotation
- **Tor/Onion Routing** - Anonymous routing via Tor
- **Bandwidth Throttling** - Simulate slow connections (Kbps)
- **Redirect Control** - Toggle 30x redirect following

### Output & Configuration
- **JSON/CSV Export** - Save results to files
- **Real-time Progress** - Live stats during test execution
- **Config Files** - JSON-based attack profiles
- **Multi-target Mode** - Test multiple targets from config

## Installation

```bash
git clone https://github.com/kuro-toji/network-stresser.git
cd network-stresser
pip install -r requirements.txt
```

## Usage Examples

### Basic HTTP Flood

```bash
# Standard flood test
python loadtest.py http://localhost:8080 -n 10000 -c 50

# POST request flood
python loadtest.py http://localhost:8080/login -m POST -n 5000 -c 20

# With custom headers
python loadtest.py http://localhost:8080 -H "Authorization:Bearer token" -c 100
```

### Advanced Attack Modes

```bash
# Connection saturation
python loadtest.py http://localhost:8080 --mode saturation -c 100 -n 1000

# Slowloris attack
python loadtest.py http://localhost:8080 --slowloris -c 50 -n 100

# Slow POST attack
python loadtest.py http://localhost:8080 --slow-post -c 50 -n 100

# UDP flood (non-HTTP)
python loadtest.py 192.168.1.1:53 --udp-flood -c 100 -n 10000
```

### Protocol Testing

```bash
# HTTP/2
python loadtest.py http://localhost:8080 -p h2 -c 50 -n 5000

# QUIC/HTTP3
python loadtest.py http://localhost:8080 --quic -c 50

# WebSocket
python loadtest.py ws://localhost:8080/ws --ws -c 50 -n 1000

# IPv6
python loadtest.py http://localhost:8080 --ipv6 -c 50
```

### HTTP Smuggling & Security Testing

```bash
# HTTP request smuggling (TEO+CL)
python loadtest.py http://localhost:8080 --http-smuggling te-cl -n 100

# HTTP request smuggling (CL+TEO)
python loadtest.py http://localhost:8080 --http-smuggling cl-te -n 100

# Malformed requests
python loadtest.py http://localhost:8080 --malformed 1 -n 100
python loadtest.py http://localhost:8080 --malformed 2 -n 100
python loadtest.py http://localhost:8080 --malformed 3 -n 100

# GZIP bomb
python loadtest.py http://localhost:8080 --gzip-bomb -n 100
```

### Proxy & Anonymity

```bash
# Single proxy
python loadtest.py http://target.com --proxy http://127.0.0.1:8080

# Proxy chain with rotation
python loadtest.py http://target.com --proxy-chain http://proxy1:8080 http://proxy2:3128

# Tor/Onion routing
python loadtest.py http://target.com --tor
python loadtest.py http://target.com --tor --tor-port 9050
```

### Authentication

```bash
# Bearer token
python loadtest.py http://localhost:8080 --auth-type bearer --auth-token "your-token"

# Basic auth
python loadtest.py http://localhost:8080 --auth-type basic --auth-token "user:pass"

# JWT
python loadtest.py http://localhost:8080 --auth-type jwt --auth-token "eyJ..."

# Session cookie
python loadtest.py http://localhost:8080 --session-cookie "session=abc123"
```

### SSL/TLS Options

```bash
# Client certificate
python loadtest.py https://localhost:8080 --client-cert cert.pem --client-key key.pem

# TLS version
python loadtest.py https://localhost:8080 --tls-version TLSv1.2

# Custom cipher
python loadtest.py https://localhost:8080 --tls-cipher "ECDHE-RSA-AES256-GCM-SHA384"

# Disable SSL verification
python loadtest.py https://localhost:8080 --no-ssl-verify
```

### Configuration Files

```bash
# Load from JSON config
python loadtest.py --config profile.json
```

Example `profile.json`:
```json
{
  "url": "http://target.com",
  "requests": 10000,
  "concurrency": 50,
  "mode": "flood",
  "proxy": "http://proxy:8080",
  "auth_type": "bearer",
  "auth_token": "your-token"
}
```

### Output & Monitoring

```bash
# JSON export
python loadtest.py http://localhost:8080 -o json -n 10000

# CSV export
python loadtest.py http://localhost:8080 -o csv -n 10000

# Real-time progress
python loadtest.py http://localhost:8080 -n 10000 --real-time

# Rate limiting (100 RPS)
python loadtest.py http://localhost:8080 --rps 100 -n 5000
```

### Multi-target Testing

```bash
# Load multiple targets
python loadtest.py --targets-file targets.json
```

Example `targets.json`:
```json
{
  "targets": [
    "http://server1.com",
    "http://server2.com",
    "http://server3.com"
  ]
}
```

## Command Options

| Category | Option | Description | Default |
|----------|--------|-------------|---------|
| **Basic** | `url` | Target URL | Required |
| | `-n, --requests` | Total requests | 1000 |
| | `-c, --concurrency` | Concurrent threads | 10 |
| | `-m, --method` | HTTP method (GET/POST) | GET |
| **Mode** | `--mode` | Test mode (flood/saturation/slow) | flood |
| | `--slow-duration` | Slow mode duration (seconds) | 60 |
| **Protocol** | `-p, --protocol` | Protocol (http1/h2) | http1 |
| | `--quic` | QUIC/HTTP3 support | False |
| | `--ws` | WebSocket mode | False |
| | `--ipv6` | IPv6 connections | False |
| | `--http-version` | HTTP version (0.9/1.0/1.1) | None |
| **Attack** | `--udp-flood` | UDP flood mode | False |
| | `--raw-socket` | Raw TCP socket | False |
| | `--slowloris` | Slowloris attack | False |
| | `--slow-post` | Slow POST attack | False |
| | `--http-smuggling` | Smuggling type (te-cl/cl-te/te-content) | None |
| | `--malformed` | Malformed request (1-4) | 0 |
| | `--gzip-bomb` | GZIP bomb payload | False |
| | `--dns-stress` | DNS stress test | False |
| | `--range-test` | Range header test | False |
| **Network** | `--proxy` | HTTP proxy | None |
| | `--proxy-chain` | Multiple proxies | None |
| | `--tor` | Use Tor proxy | False |
| | `--tor-port` | Tor proxy port | 9050 |
| | `--throttle` | Bandwidth throttle (Kbps) | 0 |
| **Auth** | `--auth-type` | Auth type (bearer/basic/jwt) | None |
| | `--auth-token` | Auth token | None |
| | `--session-cookie` | Session cookie | None |
| **SSL** | `--client-cert` | Client certificate | None |
| | `--client-key` | Client key | None |
| | `--tls-version` | TLS version | None |
| | `--tls-cipher` | TLS cipher | None |
| | `--no-ssl-verify` | Disable SSL verify | False |
| **Advanced** | `--pipeline` | HTTP pipelining count | 1 |
| | `--rps` | Max requests per second | 0 |
| | `--host-header` | Custom Host header | None |
| | `--cache-bypass` | Random query params | False |
| | `--no-follow-redirects` | Don't follow redirects | False |
| **Output** | `-o, --output` | Export format (json/csv) | None |
| | `--real-time` | Show live progress | False |
| | `--config` | Load JSON config | None |
| | `--targets-file` | Load multiple targets | None |

## Example Output

```
[*] Starting HTTP FLOOD test: http://localhost:8080
    Total requests: 10000
    Concurrency: 50
    Method: GET
    Mode: flood
    Protocol: HTTP1

==================================================
HTTP FLOOD RESULTS
==================================================
Duration:     12.34s
Total reqs:   10000
RPS:          810.50
Success:      9850
Failed:       150

Response times:
  Avg:        45.23ms
  Min:        12.10ms
  Max:        892.30ms

Error rate:   1.50%

Errors:
  HTTP 503:       120
  Timeout:        30
==================================================
```

## Use Cases

- Performance testing and capacity planning
- Identifying server bottlenecks
- Load testing during development
- DDoS mitigation testing
- SSL/TLS configuration validation
- Proxy and network infrastructure testing

## Disclaimer

This tool is intended for authorized security testing and load testing only. Always ensure you have explicit permission before testing any system. Unauthorized testing may be illegal.

## License

MIT License