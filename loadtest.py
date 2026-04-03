#!/usr/bin/env python3
import argparse
import time
import threading
import requests
from datetime import datetime


class LoadTester:
    def __init__(self, url, total_requests, concurrency, method="GET"):
        self.url = url
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.method = method
        self.results = {"success": 0, "failed": 0, "response_times": []}
        self.lock = threading.Lock()

    def make_request(self):
        start = time.time()
        try:
            if self.method == "GET":
                response = requests.get(self.url, timeout=10)
            else:
                response = requests.post(self.url, timeout=10)

            elapsed = time.time() - start

            with self.lock:
                if response.status_code == 200:
                    self.results["success"] += 1
                else:
                    self.results["failed"] += 1
                self.results["response_times"].append(elapsed)

        except Exception as e:
            with self.lock:
                self.results["failed"] += 1

    def worker(self, count):
        for _ in range(count):
            self.make_request()

    def run(self):
        print(f"\n[*] Starting load test: {self.url}")
        print(f"    Total requests: {self.total_requests}")
        print(f"    Concurrency: {self.concurrency}")
        print(f"    Method: {self.method}")

        start_time = time.time()

        threads = []
        requests_per_thread = self.total_requests // self.concurrency

        for _ in range(self.concurrency):
            t = threading.Thread(target=self.worker, args=(requests_per_thread,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        duration = time.time() - start_time

        self.print_results(duration)

    def print_results(self, duration):
        print("\n" + "=" * 50)
        print("RESULTS")
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

        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Simple load testing tool")
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

    args = parser.parse_args()

    tester = LoadTester(args.url, args.requests, args.concurrency, args.method)
    tester.run()


if __name__ == "__main__":
    main()
