#!/usr/bin/env python3
import json
import time
import threading
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any, Optional
from dataclasses import asdict
import io


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Stresser - Web UI</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding: 1rem 1.5rem;
            background: var(--bg-secondary);
            border-radius: 12px;
        }
        .header h1 { color: var(--accent); font-size: 1.5rem; }
        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-badge.idle { background: rgba(148, 163, 184, 0.2); color: var(--text-secondary); }
        .status-badge.running { background: rgba(59, 130, 246, 0.2); color: var(--accent); }
        .status-badge.completed { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        .card {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
        }
        .card h2 {
            font-size: 1rem;
            margin-bottom: 1rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .form-group { margin-bottom: 1rem; }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--bg-card);
            border-radius: 8px;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 0.9rem;
        }
        .form-group textarea { min-height: 80px; resize: vertical; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary { background: var(--accent); color: white; }
        .btn-primary:hover { background: #2563eb; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-danger:hover { background: #dc2626; }
        .btn-secondary { background: var(--bg-card); color: var(--text-primary); }
        .btn-secondary:hover { background: #475569; }
        .btn-group { display: flex; gap: 1rem; margin-top: 1rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
        .stat-box {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        .stat-box .value { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
        .stat-box .label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
        .log-container {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1rem;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
        }
        .log-entry { padding: 0.25rem 0; border-bottom: 1px solid var(--bg-card); }
        .log-entry.success { color: var(--success); }
        .log-entry.error { color: var(--danger); }
        .log-entry.info { color: var(--accent); }
        .chart-container { height: 200px; margin-top: 1rem; }
        @media (max-width: 1024px) {
            .grid { grid-template-columns: 1fr; }
            .form-row { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Network Stresser</h1>
            <div class="status-badge idle" id="statusBadge">Idle</div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>Test Configuration</h2>
                <form id="configForm">
                    <div class="form-group">
                        <label>Target URL</label>
                        <input type="text" name="url" value="http://localhost:8080" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Total Requests</label>
                            <input type="number" name="total_requests" value="1000">
                        </div>
                        <div class="form-group">
                            <label>Concurrency</label>
                            <input type="number" name="concurrency" value="10">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Method</label>
                            <select name="method">
                                <option value="GET">GET</option>
                                <option value="POST">POST</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Mode</label>
                            <select name="mode">
                                <option value="flood">Flood</option>
                                <option value="saturation">Saturation</option>
                                <option value="slow">Slow</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Protocol</label>
                            <select name="protocol">
                                <option value="http1">HTTP/1.1</option>
                                <option value="h2">HTTP/2</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>RPS Limit</label>
                            <input type="number" name="rps" value="0" placeholder="0 = unlimited">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Headers (JSON)</label>
                        <textarea name="headers">{}</textarea>
                    </div>
                    <div class="form-group">
                        <label>Custom Data</label>
                        <input type="text" name="data">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Proxy (optional)</label>
                            <input type="text" name="proxy" placeholder="http://proxy:8080">
                        </div>
                        <div class="form-group">
                            <label>Output Format</label>
                            <select name="output">
                                <option value="">None</option>
                                <option value="json">JSON</option>
                                <option value="csv">CSV</option>
                                <option value="html">HTML</option>
                            </select>
                        </div>
                    </div>
                    <div class="btn-group">
                        <button type="submit" class="btn btn-primary" id="startBtn">Start Test</button>
                        <button type="button" class="btn btn-danger" id="stopBtn" disabled>Stop Test</button>
                        <button type="button" class="btn btn-secondary" id="resetBtn">Reset</button>
                    </div>
                </form>
            </div>

            <div class="card">
                <h2>Real-time Stats</h2>
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="value" id="statRequests">0</div>
                        <div class="label">Total</div>
                    </div>
                    <div class="stat-box">
                        <div class="value" id="statSuccess">0</div>
                        <div class="label">Success</div>
                    </div>
                    <div class="stat-box">
                        <div class="value" id="statFailed">0</div>
                        <div class="label">Failed</div>
                    </div>
                    <div class="stat-box">
                        <div class="value" id="statRps">0</div>
                        <div class="label">RPS</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="requestsChart"></canvas>
                </div>
            </div>
        </div>

        <div class="card" style="margin-top: 1.5rem;">
            <h2>Live Log</h2>
            <div class="log-container" id="logContainer">
                <div class="log-entry info">Ready to start test...</div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        let isRunning = false;
        let statsInterval = null;
        let chart = null;
        let chartData = [];

        const statusBadge = document.getElementById('statusBadge');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const logContainer = document.getElementById('logContainer');

        function addLog(message, type = 'info') {
            const entry = document.createElement('div');
            entry.className = 'log-entry ' + type;
            entry.textContent = new Date().toLocaleTimeString() + ' - ' + message;
            logContainer.insertBefore(entry, logContainer.firstChild);
            if (logContainer.children.length > 100) {
                logContainer.removeChild(logContainer.lastChild);
            }
        }

        function updateStats() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('statRequests').textContent = data.total || 0;
                    document.getElementById('statSuccess').textContent = data.success || 0;
                    document.getElementById('statFailed').textContent = data.failed || 0;
                    document.getElementById('statRps').textContent = data.rps || 0;
                });
        }

        function initChart() {
            const ctx = document.getElementById('requestsChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Requests/sec',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (isRunning) return;

            const formData = new FormData(e.target);
            const config = {};
            formData.forEach((value, key) => {
                if (value === '' || value === '0') return;
                if (key === 'headers') {
                    try { config[key] = JSON.parse(value); } catch {}
                } else if (['total_requests', 'concurrency', 'rps', 'pipeline'].includes(key)) {
                    config[key] = parseInt(value);
                } else {
                    config[key] = value;
                }
            });

            addLog('Starting test...', 'info');
            
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                isRunning = true;
                statusBadge.textContent = 'Running';
                statusBadge.className = 'status-badge running';
                startBtn.disabled = true;
                stopBtn.disabled = false;
                addLog('Test started', 'success');
                
                statsInterval = setInterval(updateStats, 1000);
            }
        });

        stopBtn.addEventListener('click', async () => {
            await fetch('/api/stop', { method: 'POST' });
            isRunning = false;
            statusBadge.textContent = 'Stopping...';
            statusBadge.className = 'status-badge';
            clearInterval(statsInterval);
            addLog('Stopping test...', 'warning');
        });

        resetBtn.addEventListener('click', () => {
            document.getElementById('configForm').reset();
        });

        setInterval(async () => {
            if (!isRunning) return;
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();
                if (data.status === 'completed') {
                    isRunning = false;
                    statusBadge.textContent = 'Completed';
                    statusBadge.className = 'status-badge completed';
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    clearInterval(statsInterval);
                    addLog('Test completed!', 'success');
                }
            } catch {}
        }, 2000);

        initChart();
    </script>
</body>
</html>
"""


class WebUI:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.test_results: Dict[str, Any] = {
            "status": "idle",
            "total": 0,
            "success": 0,
            "failed": 0,
            "rps": 0,
            "errors": {},
            "start_time": 0,
            "duration": 0,
        }
        self.lock = threading.Lock()
        self.test_config: Dict[str, Any] = {}

    def start(self):
        handler = self._create_handler()
        self.server = HTTPServer((self.host, self.port), handler)
        print(f"[*] Web UI running at http://{self.host}:{self.port}")
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()

    def _create_handler(self):
        ui = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(HTML_TEMPLATE.encode())
                elif self.path == "/api/stats":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    with ui.lock:
                        stats = ui.test_results.copy()
                    self.wfile.write(json.dumps(stats).encode())
                elif self.path == "/api/status":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    with ui.lock:
                        status = {"status": ui.test_results["status"]}
                    self.wfile.write(json.dumps(status).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path == "/api/start":
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length).decode()
                    config = json.loads(body)

                    with ui.lock:
                        ui.test_config = config
                        ui.test_results = {
                            "status": "running",
                            "total": 0,
                            "success": 0,
                            "failed": 0,
                            "rps": 0,
                            "errors": {},
                            "start_time": time.time(),
                            "duration": 0,
                        }

                    threading.Thread(target=ui._run_test, daemon=True).start()

                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "started"}).encode())

                elif self.path == "/api/stop":
                    with ui.lock:
                        ui.test_results["status"] = "stopping"

                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "stopped"}).encode())

                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass

        return Handler

    def _run_test(self):
        from loadtest import LoadTester

        with self.lock:
            config = self.test_config.copy()
            status = self.test_results["status"]

        if status != "running":
            return

        try:
            tester = LoadTester(
                url=config.get("url", "http://localhost:8080"),
                total_requests=config.get("total_requests", 1000),
                concurrency=config.get("concurrency", 10),
                method=config.get("method", "GET"),
                mode=config.get("mode", "flood"),
                protocol=config.get("protocol", "http1"),
                headers=config.get("headers"),
                data=config.get("data"),
                rps=config.get("rps", 0),
                proxy=config.get("proxy"),
                output=config.get("output"),
            )

            threading.Thread(target=self._update_stats, args=(tester,), daemon=True).start()

            tester.run()

            with self.lock:
                self.test_results["status"] = "completed"
                self.test_results["duration"] = time.time() - self.test_results["start_time"]

        except Exception as e:
            with self.lock:
                self.test_results["status"] = "error"
                self.test_results["errors"]["Exception"] = str(e)

    def _update_stats(self, tester: LoadTester):
        while self.test_results["status"] == "running":
            with self.lock:
                self.test_results["total"] = tester.results["success"] + tester.results["failed"]
                self.test_results["success"] = tester.results["success"]
                self.test_results["failed"] = tester.results["failed"]
                self.test_results["errors"] = tester.results["errors"].copy()

                elapsed = time.time() - self.test_results["start_time"]
                if elapsed > 0:
                    self.test_results["rps"] = self.test_results["total"] / elapsed

            time.sleep(0.5)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Network Stresser Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    args = parser.parse_args()

    ui = WebUI(args.host, args.port)
    try:
        ui.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        ui.stop()


if __name__ == "__main__":
    main()
