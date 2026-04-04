#!/usr/bin/env python3
import json
import csv
import time
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TestResult:
    mode: str
    url: str
    duration: float
    total_requests: int
    rps: float
    success: int
    failed: int
    avg_response_ms: float
    min_response_ms: float
    max_response_ms: float
    stddev_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    errors: Dict[str, int]
    timestamp: str
    bytes_sent: int = 0
    bytes_received: int = 0
    worker_count: int = 1


class ReportGenerator:
    def __init__(self, results: TestResult):
        self.results = results
        self.template_dir = os.path.dirname(os.path.abspath(__file__))

    def _calculate_percentiles(
        self, response_times: List[float], percentiles: List[int] = [50, 90, 95, 99]
    ) -> Dict[str, float]:
        if not response_times:
            return {f"p{p}": 0.0 for p in percentiles}

        sorted_times = sorted(response_times)
        return {f"p{p}": sorted_times[int(len(sorted_times) * p / 100)] * 1000 for p in percentiles}

    def generate_html(self, output_path: str, response_times: Optional[List[float]] = None):
        percentiles = self._calculate_percentiles(response_times or []) if response_times else {}

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Load Test Report - {self.results.url}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--bg-secondary);
            border-radius: 12px;
        }}
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: var(--accent);
        }}
        .header .timestamp {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--bg-card);
        }}
        .card h3 {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--bg-card);
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric .label {{ color: var(--text-secondary); }}
        .metric .value {{
            font-weight: 600;
            font-size: 1.1rem;
        }}
        .metric .value.success {{ color: var(--success); }}
        .metric .value.danger {{ color: var(--danger); }}
        .metric .value.accent {{ color: var(--accent); }}
        .chart-container {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .chart-title {{
            font-size: 1rem;
            margin-bottom: 1rem;
            color: var(--text-secondary);
        }}
        .errors-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        .errors-table th, .errors-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--bg-card);
        }}
        .errors-table th {{
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge.success {{ background: rgba(34, 197, 94, 0.2); color: var(--success); }}
        .badge.danger {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .summary-row {{
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
        }}
        canvas {{ max-height: 300px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Load Test Report</h1>
            <p class="timestamp">Generated: {self.results.timestamp}</p>
            <p style="margin-top: 0.5rem; color: var(--accent);">{self.results.url}</p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Overview</h3>
                <div class="metric">
                    <span class="label">Test Mode</span>
                    <span class="badge">{self.results.mode.upper()}</span>
                </div>
                <div class="metric">
                    <span class="label">Duration</span>
                    <span class="value">{self.results.duration:.2f}s</span>
                </div>
                <div class="metric">
                    <span class="label">Total Requests</span>
                    <span class="value accent">{self.results.total_requests:,}</span>
                </div>
                <div class="metric">
                    <span class="label">Requests/sec</span>
                    <span class="value accent">{self.results.rps:.2f}</span>
                </div>
            </div>

            <div class="card">
                <h3>Results</h3>
                <div class="metric">
                    <span class="label">Success</span>
                    <span class="value success">{self.results.success:,}</span>
                </div>
                <div class="metric">
                    <span class="label">Failed</span>
                    <span class="value danger">{self.results.failed:,}</span>
                </div>
                <div class="metric">
                    <span class="label">Success Rate</span>
                    <span class="value {
            "success"
            if self.results.total_requests > 0 and (self.results.success / self.results.total_requests) > 0.95
            else "danger"
        }">
                        {100 * self.results.success / self.results.total_requests:.1f}%
                    </span>
                </div>
                <div class="metric">
                    <span class="label">Workers</span>
                    <span class="value">{self.results.worker_count}</span>
                </div>
            </div>

            <div class="card">
                <h3>Latency (ms)</h3>
                <div class="metric">
                    <span class="label">Average</span>
                    <span class="value">{self.results.avg_response_ms:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">Minimum</span>
                    <span class="value">{self.results.min_response_ms:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">Maximum</span>
                    <span class="value">{self.results.max_response_ms:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">Std Dev</span>
                    <span class="value">{self.results.stddev_ms:.2f}</span>
                </div>
            </div>

            <div class="card">
                <h3>Percentiles (ms)</h3>
                <div class="metric">
                    <span class="label">p50</span>
                    <span class="value">{percentiles.get("p50", 0):.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">p90</span>
                    <span class="value">{percentiles.get("p90", 0):.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">p95</span>
                    <span class="value">{percentiles.get("p95", 0):.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">p99</span>
                    <span class="value">{percentiles.get("p99", 0):.2f}</span>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h3 class="chart-title">Response Time Distribution</h3>
            <canvas id="latencyChart"></canvas>
        </div>

        <div class="chart-container">
            <h3 class="chart-title">Requests Over Time</h3>
            <canvas id="requestsChart"></canvas>
        </div>

        <div class="card">
            <h3>Errors</h3>
            {"<p>No errors recorded</p>" if not self.results.errors else ""}
            <table class="errors-table">
                <thead>
                    <tr>
                        <th>Error Type</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {
            "".join(
                f'''
                    <tr>
                        <td>{error}</td>
                        <td>{count:,}</td>
                        <td>{100 * count / self.results.total_requests:.2f}%</td>
                    </tr>'''
                for error, count in self.results.errors.items()
            )
        }
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('latencyChart').getContext('2d');
        const responseTimes = {json.dumps([rt * 1000 for rt in (response_times or [])])};
        
        const buckets = {{}};
        const bucketSize = 10;
        responseTimes.forEach(rt => {{
            const bucket = Math.floor(rt / bucketSize) * bucketSize;
            buckets[bucket] = (buckets[bucket] || 0) + 1;
        }});
        
        const labels = Object.keys(buckets).map(Number).sort((a, b) => a - b);
        const data = labels.map(l => buckets[l]);
        
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels.map(l => l + '-' + (l + bucketSize) + 'ms'),
                datasets: [{{
                    label: 'Requests',
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
        }});

        const reqCtx = document.getElementById('requestsChart').getContext('2d');
        const totalRequests = {self.results.total_requests};
        const duration = {self.results.duration};
        const interval = Math.max(1, Math.floor(duration / 50));
        
        const reqLabels = [];
        const reqData = [];
        for (let i = 0; i < duration; i += interval) {{
            reqLabels.push(i + 's');
            reqData.push(Math.floor(totalRequests * (i + interval) / duration));
        }}
        
        new Chart(reqCtx, {{
            type: 'line',
            data: {{
                labels: reqLabels,
                datasets: [{{
                    label: 'Cumulative Requests',
                    data: reqData,
                    borderColor: 'rgba(34, 197, 94, 1)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        with open(output_path, "w") as f:
            f.write(html_content)

    def export_json(self, output_path: str, response_times: Optional[List[float]] = None):
        data = asdict(self.results)
        if response_times:
            data["response_times_raw"] = [rt * 1000 for rt in response_times]

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def export_csv(self, output_path: str):
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Mode", self.results.mode])
            writer.writerow(["URL", self.results.url])
            writer.writerow(["Duration (s)", self.results.duration])
            writer.writerow(["Total Requests", self.results.total_requests])
            writer.writerow(["RPS", self.results.rps])
            writer.writerow(["Success", self.results.success])
            writer.writerow(["Failed", self.results.failed])
            writer.writerow(["Avg Response (ms)", self.results.avg_response_ms])
            writer.writerow(["Min Response (ms)", self.results.min_response_ms])
            writer.writerow(["Max Response (ms)", self.results.max_response_ms])
            writer.writerow(["Std Dev (ms)", self.results.stddev_ms])
            writer.writerow(["p50 (ms)", self.results.p50_ms])
            writer.writerow(["p90 (ms)", self.results.p90_ms])
            writer.writerow(["p95 (ms)", self.results.p95_ms])
            writer.writerow(["p99 (ms)", self.results.p99_ms])
            writer.writerow(["Timestamp", self.results.timestamp])

            if self.results.errors:
                writer.writerow([])
                writer.writerow(["Errors"])
                for error, count in self.results.errors.items():
                    writer.writerow([error, count])


class ResultsExporter:
    @staticmethod
    def calculate_statistics(response_times: List[float]) -> Dict[str, float]:
        if not response_times:
            return {
                "avg": 0,
                "min": 0,
                "max": 0,
                "stddev": 0,
                "p50": 0,
                "p90": 0,
                "p95": 0,
                "p99": 0,
            }

        sorted_times = sorted(response_times)
        n = len(sorted_times)

        avg = sum(sorted_times) / n
        variance = sum((t - avg) ** 2 for t in sorted_times) / n
        stddev = variance**0.5

        return {
            "avg": avg * 1000,
            "min": sorted_times[0] * 1000,
            "max": sorted_times[-1] * 1000,
            "stddev": stddev * 1000,
            "p50": sorted_times[int(n * 0.50)] * 1000,
            "p90": sorted_times[int(n * 0.90)] * 1000,
            "p95": sorted_times[int(n * 0.95)] * 1000,
            "p99": sorted_times[int(n * 0.99)] * 1000,
        }

    @staticmethod
    def export(
        results: Dict[str, Any],
        output_format: str,
        output_path: Optional[str] = None,
        response_times: Optional[List[float]] = None,
    ):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = results.get("success", 0) + results.get("failed", 0)
        duration = results.get("duration", 1)
        stats = ResultsExporter.calculate_statistics(response_times or [])

        result = TestResult(
            mode=results.get("mode", "unknown"),
            url=results.get("url", ""),
            duration=duration,
            total_requests=total,
            rps=total / duration if duration > 0 else 0,
            success=results.get("success", 0),
            failed=results.get("failed", 0),
            avg_response_ms=stats["avg"],
            min_response_ms=stats["min"],
            max_response_ms=stats["max"],
            stddev_ms=stats["stddev"],
            p50_ms=stats["p50"],
            p90_ms=stats["p90"],
            p95_ms=stats["p95"],
            p99_ms=stats["p99"],
            errors=results.get("errors", {}),
            timestamp=timestamp,
            bytes_sent=results.get("bytes_sent", 0),
            bytes_received=results.get("bytes_received", 0),
            worker_count=results.get("worker_count", 1),
        )

        generator = ReportGenerator(result)

        if not output_path:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"loadtest_report_{timestamp_str}"

        if output_format == "html":
            generator.generate_html(f"{output_path}.html", response_times)
        elif output_format == "json":
            generator.export_json(f"{output_path}.json", response_times)
        elif output_format == "csv":
            generator.export_csv(f"{output_path}.csv")
        elif output_format == "all":
            generator.generate_html(f"{output_path}.html", response_times)
            generator.export_json(f"{output_path}.json", response_times)
            generator.export_csv(f"{output_path}.csv")

        return output_path
