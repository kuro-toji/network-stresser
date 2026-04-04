# Network Stresser

A professional-grade, feature-rich network load testing and stress testing tool built with Python. Designed for comprehensive web server performance evaluation under various conditions.

## Features

### Core Attack Modes
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
- **FTP** - FTP server load testing
- **SMTP** - SMTP server stress testing
- **SSH** - SSH service testing
- **MySQL** - Database server testing
- **Telnet** - Telnet service testing
- **Memcache** - Memcached protocol testing

### Advanced Testing
- **HTTP Pipelining** - Send multiple requests in one connection
- **HTTP Request Smuggling** - TEO+CL, CL+TEO, TE-content variants
- **Range Header Testing** - Partial content requests
- **Malformed Requests** - Invalid HTTP requests for robustness testing
- **GZIP Bomb** - Decompression bomb payload testing
- **DNS Stress Test** - DNS server load testing
- **Host Header Injection** - Virtual host testing
- **Cache Bypass** - Random query params to bypass CDN cache
- **Scenario Testing** - JSON-defined request sequences and workflows

### Authentication & Security
- **Bearer Token** - OAuth/JWT bearer authentication
- **Basic Auth** - HTTP Basic authentication
- **Session Cookies** - Cookie-based authentication
- **Client Certificates** - SSL/TLS client cert/key support
- **TLS Version Control** - TLSv1, TLSv1.1, TLSv1.2, TLSv1.3
- **TLS Cipher Selection** - Custom cipher suite selection
- **SSL/TLS Analysis** - Certificate validation, cipher strength testing, vulnerability scanning

### Network Features
- **Proxy Support** - Single HTTP proxy
- **Proxy Chain** - Multiple proxies with rotation
- **Proxy Fetcher** - Built-in proxy list fetching from public sources
- **Proxy Rotator** - Round-robin, random, least-used, fastest, healthy strategies
- **Tor/Onion Routing** - Anonymous routing via Tor
- **Bandwidth Throttling** - Simulate slow connections (Kbps)
- **Redirect Control** - Toggle 30x redirect following

### Rate Limiting
- **Token Bucket** - Classic token bucket algorithm
- **Leaky Bucket** - Traffic shaping with uniform outflow
- **Sliding Window Counter** - Fixed window with sliding count
- **Sliding Window Log** - Precise sliding window logging
- **Adaptive Rate Limiter** - Automatic rate adjustment based on success rate
- **Per-worker RPS Limits** - Precise requests per second controls

### Distributed Testing
- **Master Node** - Central coordinator for distributed tests
- **Worker Node** - Remote workers that execute tests
- **Real-time Stats Aggregation** - Combined statistics from all workers
- **Scalable Load Generation** - Horizontally scale across multiple machines

### Reporting & Metrics
- **HTML Reports** - Interactive charts with Chart.js
- **JSON Export** - Machine-readable detailed output
- **CSV Export** - Spreadsheet-compatible format
- **Response Time Histograms** - Latency distribution visualization
- **Percentile Analysis** - p50, p90, p95, p99, p99.9
- **System Metrics** - CPU, memory, thread counts
- **Interval Metrics** - Time-series performance data

### Configuration
- **JSON Config** - Traditional JSON configuration files
- **YAML Config** - Human-readable YAML format
- **TOML Config** - TOML configuration support
- **Environment Variables** - Runtime configuration
- **Config Merging** - CLI args override config file values

### Web UI
- **Browser-based Interface** - Configure tests visually
- **Real-time Statistics** - Live RPS, success/failure counters
- **Interactive Charts** - Visual performance graphs
- **Live Log View** - Streaming test output
- **Start/Stop Controls** - Control tests from browser

### CI/CD Integration
- **Pytest Test Suite** - Comprehensive unit tests
- **GitHub Actions** - Automated CI pipeline
- **Code Coverage** - Coverage reporting with codecov
- **Lint Checking** - ruff code quality checks

## Installation

### Standard Installation

```bash
git clone https://github.com/kuro-toji/network-stresser.git
cd network-stresser
pip install -r requirements.txt
```

### Pip Installation

```bash
pip install -e .
# or
pip install -e ".[dev]"  # with development dependencies
```

### Using pyproject.toml

```bash
pip install -e .
network-stresser --help
```

### Install Dependencies for Optional Features

```bash
pip install network-stresser[reports]  # For HTML reports with charts
pip install network-stresser[dev]      # For development/testing
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

# Load from YAML config
python loadtest.py --config profile.yaml

# Load from TOML config
python loadtest.py --config profile.toml
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

Example `profile.yaml`:
```yaml
url: http://target.com
requests: 10000
concurrency: 50
mode: flood
proxy: http://proxy:8080
auth_type: bearer
auth_token: your-token
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

## Advanced Features

### Distributed Mode

Start a master node:
```bash
python distributed.py --mode master --bind 0.0.0.0 --port 5555
```

Start a worker node:
```bash
python distributed.py --mode worker --master-host localhost --master-port 5555 --config-file test_config.json
```

### Web UI

Start the web-based user interface:
```bash
python webui.py --host 0.0.0.0 --port 8080
```

Then open http://localhost:8080 in your browser to:
- Configure tests visually
- View real-time statistics
- Monitor live charts
- Start/stop tests

### Scenario Testing

Create a scenario file (`scenario.json`):
```json
{
  "name": "User Journey Test",
  "description": "Test user registration and login flow",
  "steps": [
    {
      "type": "variable_set",
      "name": "Generate User",
      "params": { "uuid": true }
    },
    {
      "type": "request",
      "name": "Register User",
      "params": {
        "method": "POST",
        "url": "/api/users/register",
        "headers": { "Content-Type": "application/json" },
        "body": "{\"username\": \"{{uuid}}\", \"email\": \"{{uuid}}@example.com\", \"password\": \"test123\"}",
        "extract": { "user_id": "$.id", "token": "$.auth_token" }
      }
    },
    {
      "type": "think",
      "name": "Wait before login",
      "params": { "duration": 1 }
    },
    {
      "type": "request",
      "name": "Login",
      "params": {
        "method": "POST",
        "url": "/api/auth/login",
        "headers": { "Content-Type": "application/json" },
        "body": "{\"username\": \"{{uuid}}@example.com\", \"password\": \"test123\"}",
        "extract": { "session_token": "$.session_token" }
      }
    },
    {
      "type": "request",
      "name": "Get Profile",
      "params": {
        "method": "GET",
        "url": "/api/users/me",
        "headers": { "Authorization": "Bearer {{session_token}}" }
      }
    }
  ]
}
```

Run the scenario:
```python
from scenario import ScenarioLoader, ScenarioRunner

scenario = ScenarioLoader.load("scenario.json")
runner = ScenarioRunner(scenario, base_url="http://localhost:8080")
results = runner.run(iterations=10)
```

### SSL/TLS Analysis

Analyze SSL/TLS configuration of a server:
```python
from ssl_analyzer import SSLAnalyzer

analyzer = SSLAnalyzer(timeout=10)
results = analyzer.full_scan("example.com", 443)

print(f"Supports TLSv1.2: {results['supports_tlsv12']}")
print(f"Supports TLSv1.3: {results['supports_tlsv13']}")
print(f"Cipher strength: {results['tls']['cipher_strength']}")
print(f"Vulnerabilities: {results['tls']['vulnerabilities']}")
print(f"Certificate valid: {results['certificate']['is_valid']}")
print(f"Days remaining: {results['certificate']['days_remaining']}")
```

### Proxy Fetcher & Rotator

Fetch and use proxies:
```python
from proxies import ProxyFetcher, ProxyChecker, ProxyPool, ProxyRotator

# Fetch proxies
fetcher = ProxyFetcher()
proxies = fetcher.get_proxies(force_refresh=True)

# Check which ones work
checker = ProxyChecker()
working = checker.check_proxies(proxies, max_threads=10)

# Create a pool
pool = ProxyPool()
for proxy in working:
    pool.add(proxy)

# Use rotator with strategy
rotator = ProxyRotator(pool)
proxy = rotator.get_proxy(strategy="fastest")  # or "round_robin", "random", "least_used"
```

### Rate Limiting Controls

Use advanced rate limiting:
```python
from ratelimit import RateLimiter, RateLimitConfig, TokenBucket, AdaptiveRateLimiter

# Token bucket with burst
config = RateLimitConfig(requests_per_second=100, burst_size=50)
limiter = RateLimiter(config)

# Adaptive rate limiting
adaptive = AdaptiveRateLimiter(initial_rate=100, min_rate=10, max_rate=1000)

for _ in range(1000):
    limiter.acquire()
    # ... make request ...
    if success:
        adaptive.record_success()
    else:
        adaptive.record_failure()
```

### Metrics Collection

Collect detailed metrics:
```python
from metrics import MetricsCollector

collector = MetricsCollector(interval=1.0)
collector.start()

# ... run load test ...

collector.stop()

# Get statistics
stats = collector.get_latency_stats()
percentiles = collector.get_latency_percentiles()
histogram = collector.get_latency_histogram(bucket_count=50)
summary = collector.get_summary()

# Export to JSON
collector.export_json("metrics_report.json")
```

### HTML Reports

Generate beautiful HTML reports:
```python
from reports import ResultsExporter, ReportGenerator, TestResult

# Export results to all formats
ResultsExporter.export(
    results={"success": 950, "failed": 50, "errors": {}, "mode": "flood", "url": "http://test.com"},
    output_format="all",
    output_path="loadtest_report",
    response_times=[0.1, 0.2, 0.3, ...]
)
```

This creates:
- `loadtest_report.html` - Interactive HTML report with charts
- `loadtest_report.json` - Detailed JSON data
- `loadtest_report.csv` - CSV spreadsheet

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

## Module Structure

| Module | Description |
|--------|-------------|
| `loadtest.py` | Main entry point with LoadTester class |
| `distributed.py` | Master/worker architecture for distributed testing |
| `reports.py` | HTML, JSON, CSV report generation |
| `protocols.py` | QUIC, FTP, SMTP, SSH, MySQL, Telnet, Memcache protocols |
| `ratelimit.py` | TokenBucket, LeakyBucket, SlidingWindow algorithms |
| `config_loader.py` | JSON, YAML, TOML configuration loading |
| `webui.py` | Browser-based web interface |
| `metrics.py` | Metrics collection and analysis |
| `scenario.py` | JSON-based scenario/workflow testing |
| `proxies.py` | Proxy fetching, checking, and rotation |
| `ssl_analyzer.py` | SSL/TLS certificate and cipher analysis |

## Use Cases

- Performance testing and capacity planning
- Identifying server bottlenecks
- Load testing during development
- DDoS mitigation testing
- SSL/TLS configuration validation
- Proxy and network infrastructure testing
- CI/CD pipeline integration
- Multi-protocol service testing
- Distributed load generation across multiple machines

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_loadtest.py -v
```

## Disclaimer

This tool is intended for authorized security testing and load testing only. Always ensure you have explicit permission before testing any system. Unauthorized testing may be illegal.

## License

MIT License
