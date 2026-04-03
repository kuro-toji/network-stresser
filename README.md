# Network Stresser

A powerful yet simple Python-based load testing tool to evaluate web server performance under high traffic conditions.

## Features

- **HTTP Flood** - High volume requests to test server capacity
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

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` | Target URL | Required |
| `-n, --requests` | Total requests | 1000 |
| `-c, --concurrency` | Concurrent threads | 10 |
| `-m, --method` | HTTP method (GET/POST) | GET |
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