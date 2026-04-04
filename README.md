# Network Stresser

A powerful yet simple Python-based load testing tool to evaluate web server performance under high traffic conditions.

## Features

- **HTTP Flood** - High volume requests to test server capacity
- **Connection Saturation** - Many concurrent connections to exhaust connection pools
- **Slow Request** - Long-duration requests for legitimate timeout testing
- **Random Endpoints** - Test multiple routes with random selection
- **HTTP/2 Support** - HTTP/2 protocol for multiplexed connections
- **Proxy Support** - Route traffic through proxies for evasion
- **JSON/CSV Export** - Save results to file for analysis
- **Rate Limiting** - Custom RPS throttling per thread
- **Client Certificates** - SSL client cert/key support
- **TLS Version Control** - Minimum TLS version selection
- **Multiple HTTP Methods** - GET and POST support
- **Custom Headers** - Add authentication, cookies, etc.
- **SSL Control** - Toggle SSL verification
- **Detailed Results** - Response times, error rates, RPS

## Installation

```bash
git clone https://github.com/kuro-toji/network-stresser.git
cd network-stresser
pip install -r requirements.txt
```

## Usage

### HTTP Flood Mode

```bash
# Basic flood test
python loadtest.py http://localhost:8080 -n 10000 -c 50

# POST request flood
python loadtest.py http://localhost:8080/login -m POST -n 5000 -c 20

# With custom headers
python loadtest.py http://localhost:8080 -H "Authorization:Bearer token" -c 100

# Disable SSL verification
python loadtest.py https://localhost:8080 --no-ssl-verify
```

### Connection Saturation Mode

```bash
# Exhaust connection pools with many concurrent connections
python loadtest.py http://localhost:8080 --mode saturation -c 100 -n 1000
```

### Slow Request Mode

```bash
# Test server timeout handling with long-duration requests
python loadtest.py http://localhost:8080 --mode slow -c 50 -n 10 --slow-duration 120
```

### Random Endpoints Mode

```bash
# Test multiple routes with random selection
python loadtest.py http://localhost:8080 -e /api/users -e /api/login -e /admin -c 50

# Combine with any mode
python loadtest.py http://localhost:8080 --mode saturation -e /api/v1/* -e /admin -c 100
```

### HTTP/2 Mode

```bash
# HTTP/2 with multiplexed connections
python loadtest.py http://localhost:8080 -p h2 -c 50 -n 5000

# HTTP/2 with saturation mode
python loadtest.py http://localhost:8080 --mode saturation -p h2 -c 100
```

### Proxy Support

```bash
# Route traffic through proxy
python loadtest.py http://target.com --proxy http://127.0.0.1:8080 -c 50

# Combine with any mode
python loadtest.py http://target.com --mode saturation --proxy http://proxy:3128 -c 100
```

### Export Results

```bash
# Export to JSON
python loadtest.py http://localhost:8080 -o json -n 10000

# Export to CSV
python loadtest.py http://localhost:8080 -o csv -n 10000
```

### Rate Limiting

```bash
# Limit to 100 RPS
python loadtest.py http://localhost:8080 --rps 100 -n 5000
```

### SSL Options

```bash
# Client certificate authentication
python loadtest.py https://localhost:8080 --client-cert cert.pem --client-key key.pem

# Minimum TLS version
python loadtest.py https://localhost:8080 --tls-version TLSv1.2
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | Target URL | Required |
| `-n, --requests` | Total requests | 1000 |
| `-c, --concurrency` | Concurrent threads | 10 |
| `-m, --method` | HTTP method (GET/POST) | GET |
| `--mode` | Test mode (flood/saturation/slow) | flood |
| `-p, --protocol` | HTTP protocol (http1/h2) | http1 |
| `-e, --endpoint` | Endpoint path for random selection | None |
| `--slow-duration` | Duration for slow mode (seconds) | 60 |
| `-o, --output` | Export format (json/csv) | None |
| `--rps` | Max requests per second | 0 (unlimited) |
| `--client-cert` | Path to client certificate | None |
| `--client-key` | Path to client key | None |
| `--tls-version` | Minimum TLS version | None |
| `--proxy` | Proxy URL | None |
| `-H, --header` | Custom header (key:value) | None |
| `--no-ssl-verify` | Disable SSL verification | False |

## Example Output

```
[*] Starting HTTP Flood test: http://localhost:8080
    Total requests: 10000
    Concurrency: 50
    Method: GET
    Mode: flood

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

- Testing your own web applications
- Evaluating server capacity
- Identifying performance bottlenecks
- Load testing during development

## Disclaimer

This tool is for authorized load testing only. Always ensure you have permission before testing any system.

## License

MIT