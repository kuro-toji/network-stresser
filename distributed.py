#!/usr/bin/env python3
import socket
import struct
import json
import time
import threading
import argparse
import base64
import hashlib
import sys
from typing import Optional, Dict, Any


class WorkerNode:
    def __init__(self, host: str, port: int, worker_id: str):
        self.host = host
        self.port = port
        self.worker_id = worker_id
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.stats = {"requests": 0, "success": 0, "failed": 0, "bytes_sent": 0}
        self.running = False

    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            self.socket.connect((self.host, self.port))
            self._send_handshake()
            self.connected = True
            return True
        except Exception as e:
            print(f"[!] Worker {self.worker_id} connection failed: {e}")
            return False

    def _send_handshake(self):
        handshake = {
            "type": "handshake",
            "worker_id": self.worker_id,
            "version": "1.0.0",
            "capabilities": ["http", "udp", "tcp", "dns"],
        }
        self._send(handshake)

    def _send(self, data: Dict[str, Any]):
        try:
            msg = json.dumps(data).encode()
            header = struct.pack("!I", len(msg))
            self.socket.sendall(header + msg)
        except Exception as e:
            print(f"[!] Send error: {e}")
            self.connected = False

    def _recv(self) -> Optional[Dict[str, Any]]:
        try:
            header = self.socket.recv(4)
            if len(header) < 4:
                return None
            length = struct.unpack("!I", header)[0]
            data = b""
            while len(data) < length:
                chunk = self.socket.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            return json.loads(data.decode())
        except Exception:
            return None

    def start(self, config: Dict[str, Any]):
        if not self.connect():
            return

        self.running = True
        self._send({"type": "start", "config": config})

        while self.running and self.connected:
            try:
                result = self._recv()
                if result is None:
                    break

                if result["type"] == "stats":
                    self.stats["requests"] = result["requests"]
                    self.stats["success"] = result["success"]
                    self.stats["failed"] = result["failed"]
                    self.stats["bytes_sent"] = result["bytes_sent"]
                elif result["type"] == "stop":
                    self.running = False
                elif result["type"] == "ping":
                    self._send({"type": "pong"})
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[!] Worker {self.worker_id} error: {e}")
                break

        self.disconnect()

    def stop(self):
        self.running = False
        self._send({"type": "stop"})
        time.sleep(0.5)
        self.disconnect()

    def disconnect(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None


class MasterNode:
    def __init__(self, host: str = "0.0.0.0", port: int = 5555):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.workers: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.lock = threading.Lock()
        self.stats = {"total_requests": 0, "total_success": 0, "total_failed": 0}
        self.config: Dict[str, Any] = {}

    def start_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(50)
        self.socket.settimeout(1)
        self.running = True

        print(f"[*] Master listening on {self.host}:{self.port}")

        while self.running:
            try:
                client_socket, address = self.socket.accept()
                thread = threading.Thread(target=self._handle_worker, args=(client_socket, address))
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[!] Accept error: {e}")

    def _handle_worker(self, sock: socket.socket, address: tuple):
        worker_id = f"{address[0]}:{address[1]}"
        print(f"[*] Worker connected: {worker_id}")

        try:
            sock.settimeout(30)
            header = sock.recv(4)
            if len(header) < 4:
                sock.close()
                return

            length = struct.unpack("!I", header)[0]
            data = b""
            while len(data) < length:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    sock.close()
                    return
                data += chunk

            handshake = json.loads(data.decode())

            if handshake.get("type") != "handshake":
                sock.close()
                return

            worker_info = {
                "id": worker_id,
                "socket": sock,
                "addr": address,
                "capabilities": handshake.get("capabilities", []),
                "stats": {"requests": 0, "success": 0, "failed": 0, "bytes_sent": 0},
                "last_seen": time.time(),
            }

            with self.lock:
                self.workers[worker_id] = worker_info

            self._send(sock, {"type": "ack", "master_version": "1.0.0"})

            while self.running:
                try:
                    header = sock.recv(4)
                    if len(header) < 4:
                        break

                    length = struct.unpack("!I", header)[0]
                    data = b""
                    while len(data) < length:
                        chunk = sock.recv(length - len(data))
                        if not chunk:
                            break
                        data += chunk

                    msg = json.loads(data.decode())

                    if msg["type"] == "stats":
                        with self.lock:
                            if worker_id in self.workers:
                                self.workers[worker_id]["stats"] = msg
                                self.workers[worker_id]["last_seen"] = time.time()
                                self._update_total_stats()
                    elif msg["type"] == "pong":
                        with self.lock:
                            if worker_id in self.workers:
                                self.workers[worker_id]["last_seen"] = time.time()

                except socket.timeout:
                    self._check_worker_health(worker_id)
                    continue
                except Exception as e:
                    break

        except Exception as e:
            print(f"[!] Worker {worker_id} handler error: {e}")
        finally:
            with self.lock:
                if worker_id in self.workers:
                    del self.workers[worker_id]
            sock.close()
            print(f"[*] Worker disconnected: {worker_id}")

    def _check_worker_health(self, worker_id: str):
        with self.lock:
            if worker_id in self.workers:
                last_seen = self.workers[worker_id]["last_seen"]
                if time.time() - last_seen > 60:
                    print(f"[!] Worker {worker_id} health check failed")
                    del self.workers[worker_id]

    def _update_total_stats(self):
        self.stats["total_requests"] = 0
        self.stats["total_success"] = 0
        self.stats["total_failed"] = 0

        for worker in self.workers.values():
            self.stats["total_requests"] += worker["stats"].get("requests", 0)
            self.stats["total_success"] += worker["stats"].get("success", 0)
            self.stats["total_failed"] += worker["stats"].get("failed", 0)

    def _send(self, sock: socket.socket, data: Dict[str, Any]):
        try:
            msg = json.dumps(data).encode()
            header = struct.pack("!I", len(msg))
            sock.sendall(header + msg)
        except Exception:
            pass

    def broadcast(self, message: Dict[str, Any]):
        with self.lock:
            for worker_id, worker in self.workers.items():
                self._send(worker["socket"], message)

    def distribute_config(self, config: Dict[str, Any]):
        self.config = config
        self.broadcast({"type": "start", "config": config})

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            workers_list = []
            for wid, w in self.workers.items():
                workers_list.append(
                    {
                        "id": wid,
                        "stats": w["stats"],
                        "capabilities": w["capabilities"],
                        "last_seen": w["last_seen"],
                    }
                )
            return {
                "master_stats": self.stats.copy(),
                "worker_count": len(self.workers),
                "workers": workers_list,
            }

    def stop(self):
        self.running = False
        self.broadcast({"type": "stop"})
        time.sleep(1)
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class DistributedCoordinator:
    def __init__(self, master_host: str = "localhost", master_port: int = 5555):
        self.master_host = master_host
        self.master_port = master_port
        self.worker_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.worker: Optional[WorkerNode] = None
        self.results = {"success": 0, "failed": 0, "errors": {}}

    def start_worker(self, config: Dict[str, Any]):
        self.worker = WorkerNode(self.master_host, self.master_port, self.worker_id)
        print(f"[*] Starting distributed worker {self.worker_id}")
        self.worker.start(config)

    def start_master_mode(self, bind_host: str = "0.0.0.0", bind_port: int = 5555):
        master = MasterNode(bind_host, bind_port)
        return master


def start_distributed_worker(master_host: str, master_port: int, config: Dict[str, Any]):
    coordinator = DistributedCoordinator(master_host, master_port)
    coordinator.start_worker(config)


def start_distributed_master(bind_host: str = "0.0.0.0", bind_port: int = 5555):
    coordinator = DistributedCoordinator()
    master = coordinator.start_master_mode(bind_host, bind_port)
    return master


def main():
    parser = argparse.ArgumentParser(description="Network Stresser - Distributed Mode")
    parser.add_argument(
        "--mode",
        choices=["master", "worker"],
        required=True,
        help="Run as master or worker node",
    )
    parser.add_argument(
        "--bind",
        default="0.0.0.0",
        help="Bind address for master (default: 0.0.0.0)",
    )
    parser.add_argument("--port", type=int, default=5555, help="Port for master/worker (default: 5555)")
    parser.add_argument("--master-host", default="localhost", help="Master host for worker mode")
    parser.add_argument("--config-file", help="Load test configuration from JSON file")

    args = parser.parse_args()

    config = {}
    if args.config_file:
        with open(args.config_file, "r") as f:
            config = json.load(f)

    if args.mode == "master":
        master = start_distributed_master(args.bind, args.port)
        try:
            master.start_server()
        except KeyboardInterrupt:
            print("\n[*] Shutting down master...")
            master.stop()
    else:
        start_distributed_worker(args.master_host, args.port, config)


if __name__ == "__main__":
    main()
