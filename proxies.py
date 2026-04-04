#!/usr/bin/env python3
import json
import time
import threading
import random
import socket
import ssl
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import urllib.request
import urllib.error


class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


@dataclass
class Proxy:
    host: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    latency: float = 0
    uptime: float = 100.0
    last_check: float = 0
    is_working: bool = True
    country: Optional[str] = None
    anonymity: str = "unknown"

    def to_url(self) -> str:
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.protocol.value}://{auth}{self.host}:{self.port}"

    def __str__(self) -> str:
        return f"{self.host}:{self.port} ({self.protocol.value})"


@dataclass
class ProxyPool:
    proxies: List[Proxy] = field(default_factory=list)
    current_index: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add(self, proxy: Proxy):
        with self.lock:
            self.proxies.append(proxy)

    def add_from_url(self, url: str):
        parts = url.split("://")
        protocol_str = parts[0] if len(parts) > 1 else "http"
        host_port = parts[1] if len(parts) > 1 else parts[0]

        auth = None
        if "@" in host_port:
            auth, host_port = host_port.split("@")

        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)

        protocol = ProxyProtocol(protocol_str)

        username = None
        password = None
        if auth:
            if ":" in auth:
                username, password = auth.split(":", 1)

        proxy = Proxy(
            host=host,
            port=port,
            protocol=protocol,
            username=username,
            password=password,
        )
        self.add(proxy)

    def get_next(self) -> Optional[Proxy]:
        with self.lock:
            if not self.proxies:
                return None

            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy

    def get_random(self) -> Optional[Proxy]:
        with self.lock:
            if not self.proxies:
                return None
            return random.choice(self.proxies)

    def get_working(self) -> List[Proxy]:
        with self.lock:
            return [p for p in self.proxies if p.is_working]

    def remove_failed(self, proxy: Proxy):
        with self.lock:
            if proxy in self.proxies:
                proxy.is_working = False

    def rotate(self) -> Optional[Proxy]:
        return self.get_next()


class ProxyFetcher:
    FREE_PROXY_LIST_URL = "https://free-proxy-list.net/"
    GITHUB_RAW_URL = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.cache: List[Proxy] = []
        self.cache_time: float = 0
        self.cache_duration: float = 300

    def fetch_from_free_proxy_list(self) -> List[Proxy]:
        proxies = []

        try:
            req = urllib.request.Request(
                self.FREE_PROXY_LIST_URL,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                html = response.read().decode("utf-8", errors="ignore")

            import re

            rows = re.findall(
                r"<tr><td>([\d.]+)</td><td>(\d+)</td><td>[^<]*</td><td[^>]*>([^<]*)</td><td[^>]*>([^<]*)</td>",
                html,
            )

            for row in rows[:50]:
                host, port, country, anonymity = row
                proxy = Proxy(
                    host=host,
                    port=int(port),
                    country=country if country else None,
                    anonymity=anonymity if anonymity else "unknown",
                )
                proxies.append(proxy)

        except Exception as e:
            print(f"[!] Failed to fetch from free proxy list: {e}")

        return proxies

    def fetch_from_github(self) -> List[Proxy]:
        proxies = []

        try:
            req = urllib.request.Request(self.GITHUB_RAW_URL)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read().decode("utf-8", errors="ignore")

            for line in data.strip().split("\n")[:100]:
                line = line.strip()
                if ":" not in line:
                    continue

                try:
                    host, port_str = line.rsplit(":", 1)
                    port = int(port_str)
                    proxy = Proxy(host=host, port=port)
                    proxies.append(proxy)
                except ValueError:
                    continue

        except Exception as e:
            print(f"[!] Failed to fetch from GitHub: {e}")

        return proxies

    def fetch_all(self) -> List[Proxy]:
        all_proxies = []

        all_proxies.extend(self.fetch_from_free_proxy_list())
        all_proxies.extend(self.fetch_from_github())

        with self.lock:
            self.cache = all_proxies
            self.cache_time = time.time()

        return all_proxies

    def get_proxies(self, force_refresh: bool = False) -> List[Proxy]:
        if not force_refresh and self.cache and time.time() - self.cache_time < self.cache_duration:
            return self.cache

        return self.fetch_all()

    lock = threading.Lock()


class ProxyChecker:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def check_proxy(self, proxy: Proxy) -> bool:
        try:
            if proxy.protocol in (ProxyProtocol.HTTP, ProxyProtocol.HTTPS):
                return self._check_http_proxy(proxy)
            elif proxy.protocol == ProxyProtocol.SOCKS4:
                return self._check_socks4_proxy(proxy)
            elif proxy.protocol == ProxyProtocol.SOCKS5:
                return self._check_socks5_proxy(proxy)
        except Exception:
            return False
        return False

    def _check_http_proxy(self, proxy: Proxy) -> bool:
        try:
            start = time.time()

            proxy_handler = urllib.request.ProxyHandler({proxy.protocol.value: proxy.to_url()})
            opener = urllib.request.build_opener(proxy_handler)

            test_url = "http://www.google.com/generate_204"

            try:
                opener.open(test_url, timeout=self.timeout)
                proxy.latency = (time.time() - start) * 1000
                proxy.last_check = time.time()
                proxy.is_working = True
                return True
            except urllib.error.HTTPError:
                proxy.latency = (time.time() - start) * 1000
                proxy.last_check = time.time()
                proxy.is_working = True
                return True
            except Exception:
                return False

        except Exception:
            return False

    def _check_socks4_proxy(self, proxy: Proxy) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            sock.connect((proxy.host, proxy.port))

            request = bytearray()
            request.append(0x04)
            request.append(0x01)
            request.extend(struct.pack("!H", 80))
            request.extend(socket.gethostbyname("google.com").split("."))
            request.append(0x00)

            sock.send(bytes(request))

            response = sock.recv(8)
            sock.close()

            if len(response) >= 2 and response[1] == 0x5A:
                proxy.is_working = True
                return True

        except Exception:
            pass

        return False

    def _check_socks5_proxy(self, proxy: Proxy) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            sock.connect((proxy.host, proxy.port))

            greeting = bytearray([0x05, 0x01, 0x00])
            sock.send(bytes(greeting))

            response = sock.recv(2)
            if len(response) != 2 or response[0] != 0x05:
                sock.close()
                return False

            request = bytearray()
            request.append(0x05)
            request.append(0x01)
            request.append(0x00)
            request.append(0x03)
            request.append(len("google.com"))
            request.extend("google.com".encode())
            request.extend(struct.pack("!H", 80))

            sock.send(bytes(request))
            sock.close()

            proxy.is_working = True
            return True

        except Exception:
            pass

        return False

    def check_proxies(
        self, proxies: List[Proxy], max_threads: int = 10, callback: Optional[Callable] = None
    ) -> List[Proxy]:
        working = []
        lock = threading.Lock()

        def check(p: Proxy):
            if self.check_proxy(p):
                with lock:
                    working.append(p)
            if callback:
                callback(p)

        threads = []
        for proxy in proxies:
            t = threading.Thread(target=check, args=(proxy,))
            t.start()
            threads.append(t)

            if len(threads) >= max_threads:
                for t in threads:
                    t.join()
                threads = []

        for t in threads:
            t.join()

        return working


import struct


class ProxyRotator:
    def __init__(self, pool: ProxyPool):
        self.pool = pool
        self.usage_count: Dict[str, int] = {}
        self.lock = threading.Lock()

    def get_proxy(self, strategy: str = "round_robin") -> Optional[Proxy]:
        with self.lock:
            if strategy == "round_robin":
                return self.pool.get_next()
            elif strategy == "random":
                return self.pool.get_random()
            elif strategy == "least_used":
                return self._get_least_used()
            elif strategy == "fastest":
                return self._get_fastest()
            elif strategy == "healthy":
                return self._get_healthy()
            else:
                return self.pool.get_next()

    def _get_least_used(self) -> Optional[Proxy]:
        working = self.pool.get_working()
        if not working:
            return None

        min_usage = min(self.usage_count.get(str(p), 0) for p in working)
        least_used = [p for p in working if self.usage_count.get(str(p), 0) == min_usage]
        selected = random.choice(least_used)

        self.usage_count[str(selected)] = self.usage_count.get(str(selected), 0) + 1
        return selected

    def _get_fastest(self) -> Optional[Proxy]:
        working = self.pool.get_working()
        if not working:
            return None

        working_with_latency = [p for p in working if p.latency > 0]
        if working_with_latency:
            return min(working_with_latency, key=lambda p: p.latency)
        return random.choice(working)

    def _get_healthy(self) -> Optional[Proxy]:
        working = self.pool.get_working()
        if not working:
            return None

        high_uptime = [p for p in working if p.uptime > 95]
        if high_uptime:
            return random.choice(high_uptime)
        return random.choice(working)

    def record_usage(self, proxy: Proxy):
        with self.lock:
            self.usage_count[str(proxy)] = self.usage_count.get(str(proxy), 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total = len(self.pool.proxies)
            working = len(self.pool.get_working())
            return {
                "total_proxies": total,
                "working_proxies": working,
                "usage_counts": dict(self.usage_count),
            }
