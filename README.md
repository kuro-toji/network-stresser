# Load Tester

A simple Python-based load testing tool to evaluate web server performance under high traffic conditions.

## Installation

```bash
git clone https://github.com/yourusername/loadtester.git
cd loadtester
pip install -r requirements.txt
```

## Usage

```bash
# Basic test
python loadtest.py http://localhost:8080

# Custom load
python loadtest.py http://localhost:8080 -n 10000 -c 50

# POST request
python loadtest.py http://localhost:8080/login -m POST -n 5000 -c 20

# Help
python loadtest.py --help
```

## Options

- `-n, --requests` - Total number of requests (default: 1000)
- `-c, --concurrency` - Number of concurrent threads (default: 10)
- `-m, --method` - HTTP method: GET or POST (default: GET)

## Example Output

```
[*] Starting load test: http://localhost:8080
    Total requests: 1000
    Concurrency: 10
    Method: GET

==================================================
RESULTS
==================================================
Duration:     5.23s
Total reqs:   1000
RPS:          191.20
Success:      1000
Failed:       0

Response times:
  Avg:        45.23ms
  Min:        12.10ms
  Max:        156.80ms
==================================================
```

## Use Cases

- Testing your own web applications
- Evaluating server capacity
- Identifying performance bottlenecks
- Load testing during development

## License

MIT