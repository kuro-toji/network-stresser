#!/usr/bin/env python3
import time
import threading
import math
from typing import Optional
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    requests_per_second: float = 0
    requests_per_minute: float = 0
    requests_per_hour: float = 0
    burst_size: int = 0
    bandwidth_kbps: float = 0
    max_concurrent: int = 0


class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_for_token(self, tokens: int = 1):
        while not self.consume(tokens):
            time.sleep(0.001)


class LeakyBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.level = 0
        self.last_update = time.time()
        self.lock = threading.Lock()

    def add(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.level = max(0, self.level - elapsed * self.rate)
            self.last_update = now

            if self.level + tokens <= self.capacity:
                self.level += tokens
                return True
            return False

    def drain(self) -> float:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.level = max(0, self.level - elapsed * self.rate)
            self.last_update = now
            return self.level


class SlidingWindowCounter:
    def __init__(self, window_size: float, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = []
        self.lock = threading.Lock()

    def allow(self) -> bool:
        with self.lock:
            now = time.time()
            cutoff = now - self.window_size
            self.requests = [t for t in self.requests if t > cutoff]

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False

    def wait_for_slot(self):
        while not self.allow():
            time.sleep(0.001)


class SlidingWindowLog:
    def __init__(self, window_size: float, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.timestamps = []
        self.lock = threading.Lock()

    def allow(self) -> bool:
        with self.lock:
            now = time.time()
            cutoff = now - self.window_size
            self.timestamps = [t for t in self.timestamps if t > cutoff]

            if len(self.timestamps) < self.max_requests:
                self.timestamps.append(now)
                return True
            return False


class RateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.token_bucket: Optional[TokenBucket] = None
        self.leaky_bucket: Optional[LeakyBucket] = None
        self.sliding_window: Optional[SlidingWindowCounter] = None
        self.sliding_log: Optional[SlidingWindowLog] = None
        self.semaphore: Optional[threading.Semaphore] = None

        self._setup_limiters()

    def _setup_limiters(self):
        if self.config.requests_per_second > 0:
            rate = self.config.requests_per_second
            capacity = self.config.burst_size if self.config.burst_size > 0 else int(rate)
            self.token_bucket = TokenBucket(rate, capacity)

        if self.config.requests_per_minute > 0:
            rate = self.config.requests_per_minute / 60.0
            capacity = self.config.burst_size if self.config.burst_size > 0 else int(rate * 2)
            self.leaky_bucket = LeakyBucket(rate, capacity)

        if self.config.requests_per_hour > 0:
            rate = self.config.requests_per_hour / 3600.0
            capacity = self.config.burst_size if self.config.burst_size > 0 else int(rate * 2)
            self.sliding_window = SlidingWindowCounter(3600, int(self.config.requests_per_hour))

        if self.config.max_concurrent > 0:
            self.semaphore = threading.Semaphore(self.config.max_concurrent)

    def acquire(self, blocking: bool = True) -> bool:
        if self.semaphore:
            if blocking:
                return self.semaphore.acquire(blocking=True)
            else:
                return self.semaphore.acquire(blocking=False)

        if self.token_bucket:
            if blocking:
                self.token_bucket.wait_for_token()
                return True
            else:
                return self.token_bucket.consume()

        if self.leaky_bucket:
            while not self.leaky_bucket.add():
                time.sleep(0.001)

        if self.sliding_window:
            if blocking:
                self.sliding_window.wait_for_slot()
                return True
            else:
                return self.sliding_window.allow()

        return True

    def release(self):
        if self.semaphore:
            self.semaphore.release()

    def get_wait_time(self) -> float:
        if self.token_bucket:
            tokens_needed = 1 - self.token_bucket.tokens
            if tokens_needed > 0:
                return tokens_needed / self.token_bucket.rate
        return 0.0


class AdaptiveRateLimiter:
    def __init__(
        self,
        initial_rate: float,
        min_rate: float = 1,
        max_rate: float = 10000,
        increase_factor: float = 1.1,
        decrease_factor: float = 0.9,
        adjustment_interval: float = 5.0,
    ):
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor
        self.adjustment_interval = adjustment_interval
        self.last_adjustment = time.time()
        self.success_count = 0
        self.failure_count = 0
        self.lock = threading.Lock()
        self.token_bucket: Optional[TokenBucket] = None
        self._update_bucket()

    def _update_bucket(self):
        if self.token_bucket:
            self.token_bucket.rate = self.current_rate
        else:
            self.token_bucket = TokenBucket(self.current_rate, int(self.current_rate * 2))

    def _adjust_rate(self):
        now = time.time()
        if now - self.last_adjustment < self.adjustment_interval:
            return

        with self.lock:
            success_rate = self.success_count / (self.success_count + self.failure_count + 1)

            if success_rate > 0.99:
                self.current_rate = min(self.max_rate, self.current_rate * self.increase_factor)
            elif success_rate < 0.50:
                self.current_rate = max(self.min_rate, self.current_rate * self.decrease_factor)

            self._update_bucket()
            self.last_adjustment = now
            self.success_count = 0
            self.failure_count = 0

    def record_success(self):
        with self.lock:
            self.success_count += 1
        self._adjust_rate()

    def record_failure(self):
        with self.lock:
            self.failure_count += 1
        self._adjust_rate()

    def acquire(self, blocking: bool = True) -> bool:
        if not self.token_bucket:
            return True

        if blocking:
            self.token_bucket.wait_for_token()
            return True
        else:
            return self.token_bucket.consume()


class BandwidthThrottler:
    def __init__(self, kbps: float):
        self.kbps = kbps
        self.bytes_per_second = kbps * 1000 / 8
        self.bytes_sent = 0
        self.last_reset = time.time()
        self.lock = threading.Lock()

    def throttle(self, bytes_to_send: int):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_reset

            if elapsed >= 1.0:
                self.bytes_sent = 0
                self.last_reset = now

            if self.bytes_sent >= self.bytes_per_second:
                sleep_time = 1.0 - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.bytes_sent = 0
                self.last_reset = time.time()

            self.bytes_sent += bytes_to_send

    def wait_for_bandwidth(self, bytes_to_send: int):
        self.throttle(bytes_to_send)
