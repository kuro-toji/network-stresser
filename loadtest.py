#!/usr/bin/env python3
import argparse
import time
import threading
import random
import socket
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class LoadTester:
    def __init__(
        self,
        url,
        total_requests,
        concurrency,
        method="GET",
        mode="flood",
        no_ssl_verify=False,
        headers=None,
        data=None,
        slow_duration=60,
        endpoints=None,
    ):
        self.url = url
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.method = method
        self.mode = mode
        self.no_ssl_verify = no_ssl_verify
        self.headers = headers or {}
        self.data = data
        self.slow_duration = slow_duration
        self.endpoints = endpoints or []
        self.results = {"success": 0, "failed": 0, "response_times": [], "errors": {}}
        self.lock = threading.Lock()
        self.running = True
        self.request_count = 0
        self.connections = []

    def make_request(self):
        start = time.time()
        try:
            target_url = self.get_target_url()
            kwargs = {"timeout": 10, "verify": not self.no_ssl_verify}
            if self.headers:
                kwargs["headers"] = self.headers
            if self.data:
                kwargs["data"] = self.data

            if self.method == "GET":
                response = requests.get(target_url, **kwargs)
            else:
                response = requests.post(target_url, **kwargs)

            elapsed = time.time() - start
            status = response.status_code

            with self.lock:
                if 200 <= status < 300:
                    self.results["success"] += 1
                else:
                    self.results["failed"] += 1
                    err = f"HTTP {status}"
                    self.results["errors"][err] = self.results["errors"].get(err, 0) + 1
                self.results["response_times"].append(elapsed)

        except requests.exceptions.Timeout:
            with self.lock:
                self.results["failed"] += 1
                self.results["errors"]["Timeout"] = (
                    self.results["errors"].get("Timeout", 0) + 1
                )
        except requests.exceptions.ConnectionError:
            with self.lock:
                self.results["failed"] += 1
                self.results["errors"]["Connection Error"] = (
                    self.results["errors"].get("Connection Error", 0) + 1
                )
        except Exception as e:
            with self.lock:
                self.results["failed"] += 1
                self.results["errors"][str(type(e).__name__)] = (
                    self.results["errors"].get(str(type(e).__name__), 0) + 1
                )

    def saturation_worker(self):
        session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=self.concurrency,
            pool_maxsize=self.concurrency,
            max_retries=Retry(total=0),
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        while self.running:
            try:
                target_url = self.get_target_url()
                start = time.time()
                kwargs = {"timeout": 30, "verify": not self.no_ssl_verify}
                if self.headers:
                    kwargs["headers"] = self.headers
                if self.data:
                    kwargs["data"] = self.data

                if self.method == "GET":
                    response = session.get(target_url, **kwargs)
                else:
                    response = session.post(target_url, **kwargs)

                elapsed = time.time() - start

                with self.lock:
                    if 200 <= response.status_code < 300:
                        self.results["success"] += 1
                    else:
                        self.results["failed"] += 1
                        self.results["errors"][f"HTTP {response.status_code}"] = (
                            self.results["errors"].get(
                                f"HTTP {response.status_code}", 0
                            )
                            + 1
                        )
                    self.results["response_times"].append(elapsed)

            except requests.exceptions.Timeout:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"]["Timeout"] = (
                        self.results["errors"].get("Timeout", 0) + 1
                    )
            except requests.exceptions.ConnectionError:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"]["Connection Error"] = (
                        self.results["errors"].get("Connection Error", 0) + 1
                    )
            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"][str(type(e).__name__)] = (
                        self.results["errors"].get(str(type(e).__name__), 0) + 1
                    )

    def slow_worker(self):
        session = requests.Session()
        while self.running:
            try:
                target_url = self.get_target_url()
                start = time.time()
                kwargs = {
                    "timeout": self.slow_duration + 10,
                    "verify": not self.no_ssl_verify,
                }
                if self.headers:
                    kwargs["headers"] = self.headers
                if self.data:
                    kwargs["data"] = self.data

                if self.method == "GET":
                    response = session.get(target_url, **kwargs)
                else:
                    response = session.post(target_url, **kwargs)

                elapsed = time.time() - start

                with self.lock:
                    if 200 <= response.status_code < 300:
                        self.results["success"] += 1
                    else:
                        self.results["failed"] += 1
                        self.results["errors"][f"HTTP {response.status_code}"] = (
                            self.results["errors"].get(
                                f"HTTP {response.status_code}", 0
                            )
                            + 1
                        )
                    self.results["response_times"].append(elapsed)

            except requests.exceptions.Timeout:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"]["Timeout"] = (
                        self.results["errors"].get("Timeout", 0) + 1
                    )
            except requests.exceptions.ConnectionError:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"]["Connection Error"] = (
                        self.results["errors"].get("Connection Error", 0) + 1
                    )
            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"][str(type(e).__name__)] = (
                        self.results["errors"].get(str(type(e).__name__), 0) + 1
                    )

    def get_target_url(self):
        if self.endpoints:
            path = random.choice(self.endpoints)
            if path.startswith("/"):
                base = self.url.rstrip("/")
                return base + path
            return path
        return self.url

    def worker(self, count):
        for _ in range(count):
            if not self.running:
                break
            self.make_request()
            self.request_count += 1

    def run(self):
        print(f"\n[*] Starting {self.mode.upper()} test: {self.url}")
        print(f"    Total requests: {self.total_requests}")
        print(f"    Concurrency: {self.concurrency}")
        print(f"    Method: {self.method}")
        print(f"    Mode: {self.mode}")
        if self.endpoints:
            print(f"    Endpoints: {self.endpoints}")
        if self.mode == "slow":
            print(f"    Slow duration: {self.slow_duration}s")

        start_time = time.time()

        if self.mode == "saturation":
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.saturation_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

            self.running = False
            for t in threads:
                t.join()
        elif self.mode == "slow":
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.slow_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests * self.slow_duration / self.concurrency)

            self.running = False
            for t in threads:
                t.join()
        else:
            threads = []
            requests_per_thread = self.total_requests // self.concurrency

            for _ in range(self.concurrency):
                t = threading.Thread(target=self.worker, args=(requests_per_thread,))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

            self.running = False

        duration = time.time() - start_time

        self.print_results(duration)

    def print_results(self, duration):
        mode_name = self.mode.upper()
        print("\n" + "=" * 50)
        print(f"{mode_name} RESULTS")
        print("=" * 50)

        total = self.results["success"] + self.results["failed"]
        rps = total / duration

        print(f"Duration:     {duration:.2f}s")
        print(f"Total reqs:   {total}")
        print(f"RPS:          {rps:.2f}")
        print(f"Success:      {self.results['success']}")
        print(f"Failed:       {self.results['failed']}")

        if self.results["response_times"]:
            times = self.results["response_times"]
            avg = sum(times) / len(times)
            min_t = min(times)
            max_t = max(times)

            print(f"\nResponse times:")
            print(f"  Avg:        {avg * 1000:.2f}ms")
            print(f"  Min:        {min_t * 1000:.2f}ms")
            print(f"  Max:        {max_t * 1000:.2f}ms")

        if self.results["failed"] > 0:
            error_rate = (self.results["failed"] / total) * 100
            print(f"\nError rate:   {error_rate:.2f}%")

        if self.results["errors"]:
            print(f"\nErrors:")
            for err, count in self.results["errors"].items():
                print(f"  {err}:       {count}")

        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Network Stresser - Load Testing Tool")
    parser.add_argument("url", help="Target URL (e.g., http://localhost:8080)")
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=1000,
        help="Total requests (default: 1000)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=10,
        help="Concurrent threads (default: 10)",
    )
    parser.add_argument(
        "-m", "--method", default="GET", choices=["GET", "POST"], help="HTTP method"
    )
    parser.add_argument(
        "--mode",
        default="flood",
        choices=["flood", "saturation", "slow"],
        help="Test mode: flood (high requests), saturation (connection pool exhaustion), slow (long-duration requests)",
    )
    parser.add_argument(
        "--no-ssl-verify", action="store_true", help="Disable SSL verification"
    )
    parser.add_argument(
        "-H",
        "--header",
        action="append",
        dest="headers",
        help="Add custom header (key:value)",
    )
    parser.add_argument(
        "-e",
        "--endpoint",
        action="append",
        dest="endpoints",
        help="Add endpoint path (e.g., /api/users). Use multiple for random selection",
    )
    parser.add_argument(
        "--slow-duration",
        type=int,
        default=60,
        help="Duration for slow request mode in seconds (default: 60)",
    )

    args = parser.parse_args()

    headers = {}
    if args.headers:
        for h in args.headers:
            if ":" in h:
                key, val = h.split(":", 1)
                headers[key.strip()] = val.strip()

    tester = LoadTester(
        args.url,
        args.requests,
        args.concurrency,
        args.method,
        mode=args.mode,
        no_ssl_verify=args.no_ssl_verify,
        headers=headers if headers else None,
        endpoints=args.endpoints,
        slow_duration=args.slow_duration,
    )
    tester.run()


if __name__ == "__main__":
    main()
