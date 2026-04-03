#!/usr/bin/env python3
import argparse
import time
import threading
import random
import requests
from datetime import datetime


class LoadTester:
    def __init__(
        self,
        url,
        total_requests,
        concurrency,
        method="GET",
        mode="normal",
        no_ssl_verify=False,
        headers=None,
        data=None,
    ):
        self.url = url
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.method = method
        self.mode = mode
        self.no_ssl_verify = no_ssl_verify
        self.headers = headers or {}
        self.data = data
        self.results = {"success": 0, "failed": 0, "response_times": [], "errors": {}}
        self.lock = threading.Lock()
        self.running = True
        self.request_count = 0

    def make_request(self):
        start = time.time()
        try:
            kwargs = {"timeout": 10, "verify": not self.no_ssl_verify}
            if self.headers:
                kwargs["headers"] = self.headers
            if self.data:
                kwargs["data"] = self.data

            if self.method == "GET":
                response = requests.get(self.url, **kwargs)
            else:
                response = requests.post(self.url, **kwargs)

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

    def worker(self, count):
        for _ in range(count):
            if not self.running:
                break
            self.make_request()
            self.request_count += 1

    def run(self):
        print(f"\n[*] Starting HTTP Flood test: {self.url}")
        print(f"    Total requests: {self.total_requests}")
        print(f"    Concurrency: {self.concurrency}")
        print(f"    Method: {self.method}")
        print(f"    Mode: {self.mode}")

        start_time = time.time()

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
        print("\n" + "=" * 50)
        print("HTTP FLOOD RESULTS")
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
    parser = argparse.ArgumentParser(description="HTTP Flood Load Tester")
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
    parser.add_argument("--mode", default="flood", choices=["flood"], help="Test mode")
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
    )
    tester.run()


if __name__ == "__main__":
    main()
