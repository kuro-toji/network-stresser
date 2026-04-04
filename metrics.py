#!/usr/bin/env python3
import time
import threading
import statistics
import math
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class LatencyStats:
    count: int = 0
    total: float = 0
    min_val: float = float("inf")
    max_val: float = 0
    mean: float = 0
    median: float = 0
    stddev: float = 0
    p50: float = 0
    p75: float = 0
    p90: float = 0
    p95: float = 0
    p99: float = 0
    p999: float = 0


@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float = 0
    memory_mb: float = 0
    threads: int = 0
    open_files: int = 0
    network_sent_bytes: int = 0
    network_recv_bytes: int = 0


@dataclass
class IntervalMetrics:
    interval_start: float
    interval_end: float
    requests: int = 0
    successes: int = 0
    failures: int = 0
    rps: float = 0
    avg_latency: float = 0
    max_latency: float = 0
    min_latency: float = 0


class MetricsCollector:
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.latencies: List[float] = []
        self.interval_metrics: List[IntervalMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        self.errors: Dict[str, int] = defaultdict(int)
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.lock = threading.Lock()
        self.running = False
        self._start_time = 0
        self._interval_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []

    def start(self):
        self.running = True
        self._start_time = time.time()
        self._interval_thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._interval_thread.start()

    def stop(self):
        self.running = False
        if self._interval_thread:
            self._interval_thread.join(timeout=5)

    def _collect_loop(self):
        while self.running:
            start = time.time()
            self._collect_interval_metrics()
            self._collect_system_metrics()
            elapsed = time.time() - start
            sleep_time = max(0, self.interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def record_request(
        self, latency: float, success: bool, status_code: Optional[int] = None, error: Optional[str] = None
    ):
        with self.lock:
            self.latencies.append(latency)
            if status_code:
                self.status_codes[status_code] += 1
            if error:
                self.errors[error] += 1

    def _collect_interval_metrics(self):
        now = time.time()
        elapsed = now - self._start_time

        with self.lock:
            total = len(self.latencies)
            successes = sum(1 for lat in self.latencies if lat >= 0)
            failures = total - successes

            interval_data = IntervalMetrics(
                interval_start=max(0, elapsed - self.interval),
                interval_end=elapsed,
                requests=total,
                successes=successes,
                failures=failures,
                rps=total / elapsed if elapsed > 0 else 0,
            )

            if self.latencies:
                interval_data.avg_latency = statistics.mean(self.latencies)
                interval_data.max_latency = max(self.latencies)
                interval_data.min_latency = min(self.latencies)

            self.interval_metrics.append(interval_data)

            if len(self.interval_metrics) > 3600:
                self.interval_metrics = self.interval_metrics[-3600:]

    def _collect_system_metrics(self):
        try:
            import psutil

            process = psutil.Process()

            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=process.cpu_percent(),
                memory_mb=process.memory_info().rss / (1024 * 1024),
                threads=process.num_threads(),
                open_files=len(process.open_files()),
            )

            with self.lock:
                self.system_metrics.append(metrics)

                if len(self.system_metrics) > 3600:
                    self.system_metrics = self.system_metrics[-3600:]
        except ImportError:
            pass

    def get_latency_stats(self) -> LatencyStats:
        with self.lock:
            if not self.latencies:
                return LatencyStats()

            sorted_latencies = sorted(self.latencies)
            n = len(sorted_latencies)

            return LatencyStats(
                count=n,
                total=sum(sorted_latencies),
                min_val=sorted_latencies[0],
                max_val=sorted_latencies[-1],
                mean=statistics.mean(sorted_latencies),
                median=statistics.median(sorted_latencies),
                stddev=statistics.stdev(sorted_latencies) if n > 1 else 0,
                p50=sorted_latencies[int(n * 0.50)],
                p75=sorted_latencies[int(n * 0.75)],
                p90=sorted_latencies[int(n * 0.90)],
                p95=sorted_latencies[int(n * 0.95)],
                p99=sorted_latencies[int(n * 0.99)],
                p999=sorted_latencies[int(n * 0.999)] if n > 100 else sorted_latencies[-1],
            )

    def get_latency_histogram(self, bucket_count: int = 50) -> Dict[str, Any]:
        with self.lock:
            if not self.latencies:
                return {"buckets": [], "counts": []}

            min_val = min(self.latencies)
            max_val = max(self.latencies)
            bucket_size = (max_val - min_val) / bucket_count if max_val > min_val else 1

            buckets = []
            counts = []

            for i in range(bucket_count):
                bucket_start = min_val + i * bucket_size
                bucket_end = bucket_start + bucket_size
                buckets.append(f"{bucket_start:.2f}-{bucket_end:.2f}")

                count = sum(1 for lat in self.latencies if bucket_start <= lat < bucket_end)
                counts.append(count)

            return {"buckets": buckets, "counts": counts}

    def get_latency_percentiles(self) -> Dict[str, float]:
        stats = self.get_latency_stats()
        return {
            "p50_ms": stats.p50 * 1000,
            "p75_ms": stats.p75 * 1000,
            "p90_ms": stats.p90 * 1000,
            "p95_ms": stats.p95 * 1000,
            "p99_ms": stats.p99 * 1000,
            "p999_ms": stats.p999 * 1000,
        }

    def get_summary(self) -> Dict[str, Any]:
        with self.lock:
            total = len(self.latencies)
            elapsed = time.time() - self._start_time if self._start_time > 0 else 1

            return {
                "total_requests": total,
                "duration_seconds": elapsed,
                "requests_per_second": total / elapsed if elapsed > 0 else 0,
                "success_count": sum(1 for lat in self.latencies if lat >= 0),
                "failure_count": sum(1 for lat in self.latencies if lat < 0),
                "error_distribution": dict(self.errors),
                "status_code_distribution": {str(k): v for k, v in self.status_codes.items()},
            }

    def export_json(self, path: str):
        data = {
            "summary": self.get_summary(),
            "latency_stats": {
                "min_ms": self.get_latency_stats().min_val * 1000,
                "max_ms": self.get_latency_stats().max_val * 1000,
                "mean_ms": self.get_latency_stats().mean * 1000,
                "median_ms": self.get_latency_stats().median * 1000,
                "stddev_ms": self.get_latency_stats().stddev * 1000,
                **self.get_latency_percentiles(),
            },
            "latency_histogram": self.get_latency_histogram(),
            "interval_metrics": [asdict(m) for m in self.interval_metrics],
            "system_metrics": [asdict(m) for m in self.system_metrics],
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)


from dataclasses import asdict


class Profiler:
    def __init__(self):
        self.start_times: Dict[str, float] = {}
        self.durations: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def start(self, label: str):
        with self.lock:
            self.start_times[label] = time.time()

    def end(self, label: str):
        with self.lock:
            if label in self.start_times:
                duration = time.time() - self.start_times[label]
                self.durations[label].append(duration)
                del self.start_times[label]

    def get_stats(self, label: str) -> Dict[str, float]:
        with self.lock:
            durations = self.durations.get(label, [])
            if not durations:
                return {}

            return {
                "count": len(durations),
                "total": sum(durations),
                "mean": statistics.mean(durations),
                "min": min(durations),
                "max": max(durations),
                "stddev": statistics.stdev(durations) if len(durations) > 1 else 0,
            }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        with self.lock:
            return {label: self.get_stats(label) for label in self.durations.keys()}

    def reset(self):
        with self.lock:
            self.start_times.clear()
            self.durations.clear()
