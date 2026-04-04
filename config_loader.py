#!/usr/bin/env python3
import json
import yaml
import tomllib
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class TargetConfig:
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    data: Optional[str] = None


@dataclass
class LoadTestConfig:
    url: str = ""
    targets: list = field(default_factory=list)
    total_requests: int = 1000
    concurrency: int = 10
    method: str = "GET"
    mode: str = "flood"
    protocol: str = "http1"
    no_ssl_verify: bool = False
    headers: Dict[str, str] = field(default_factory=dict)
    data: Optional[str] = None
    slow_duration: int = 60
    endpoints: list = field(default_factory=list)
    output: Optional[str] = None
    proxy: Optional[str] = None
    proxy_chain: list = field(default_factory=list)
    rps: int = 0
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    tls_version: Optional[str] = None
    ws: bool = False
    pipeline: int = 1
    malformed: int = 0
    real_time: bool = False
    tor_proxy: Optional[str] = None
    auth_type: Optional[str] = None
    auth_token: Optional[str] = None
    session_cookie: Optional[str] = None
    tls_cipher: Optional[str] = None
    udp_flood: bool = False
    raw_socket: bool = False
    http_smuggling: Optional[str] = None
    range_test: bool = False
    slowloris: bool = False
    slow_post: bool = False
    dns_stress: bool = False
    ipv6: bool = False
    http_version: Optional[str] = None
    host_header: Optional[str] = None
    cache_bypass: bool = False
    gzip_bomb: bool = False
    quic: bool = False
    throttle_kbps: int = 0
    follow_redirects: bool = True

    rate_limit: Dict[str, Any] = field(default_factory=dict)
    burst_size: int = 0
    max_concurrent: int = 0

    report_format: str = "all"
    report_output: Optional[str] = None

    distributed_master: Optional[str] = None
    distributed_port: int = 5555
    distributed_workers: list = field(default_factory=list)

    scenario_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoadTestConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class ConfigLoader:
    SUPPORTED_FORMATS = {".json", ".yaml", ".yml", ".toml"}

    @staticmethod
    def detect_format(path: str) -> Optional[str]:
        ext = Path(path).suffix.lower()
        if ext in ConfigLoader.SUPPORTED_FORMATS:
            return ext
        return None

    @staticmethod
    def load(path: str) -> LoadTestConfig:
        format_type = ConfigLoader.detect_format(path)
        if not format_type:
            raise ValueError(f"Unsupported config format: {path}")

        if format_type == ".json":
            return ConfigLoader.load_json(path)
        elif format_type in {".yaml", ".yml"}:
            return ConfigLoader.load_yaml(path)
        elif format_type == ".toml":
            return ConfigLoader.load_toml(path)

    @staticmethod
    def load_json(path: str) -> LoadTestConfig:
        with open(path, "r") as f:
            data = json.load(f)
        return ConfigLoader._parse_config(data)

    @staticmethod
    def load_yaml(path: str) -> LoadTestConfig:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return ConfigLoader._parse_config(data)

    @staticmethod
    def load_toml(path: str) -> LoadTestConfig:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return ConfigLoader._parse_config(data)

    @staticmethod
    def _parse_config(data: Dict[str, Any]) -> LoadTestConfig:
        config = LoadTestConfig()

        simple_fields = {
            "url": "url",
            "total_requests": "total_requests",
            "concurrency": "concurrency",
            "method": "method",
            "mode": "mode",
            "protocol": "protocol",
            "no_ssl_verify": "no_ssl_verify",
            "data": "data",
            "slow_duration": "slow_duration",
            "output": "output",
            "proxy": "proxy",
            "rps": "rps",
            "client_cert": "client_cert",
            "client_key": "client_key",
            "tls_version": "tls_version",
            "ws": "ws",
            "pipeline": "pipeline",
            "malformed": "malformed",
            "real_time": "real_time",
            "tor_proxy": "tor_proxy",
            "auth_type": "auth_type",
            "auth_token": "auth_token",
            "session_cookie": "session_cookie",
            "tls_cipher": "tls_cipher",
            "udp_flood": "udp_flood",
            "raw_socket": "raw_socket",
            "http_smuggling": "http_smuggling",
            "range_test": "range_test",
            "slowloris": "slowloris",
            "slow_post": "slow_post",
            "dns_stress": "dns_stress",
            "ipv6": "ipv6",
            "http_version": "http_version",
            "host_header": "host_header",
            "cache_bypass": "cache_bypass",
            "gzip_bomb": "gzip_bomb",
            "quic": "quic",
            "throttle_kbps": "throttle_kbps",
            "follow_redirects": "follow_redirects",
        }

        for key, attr in simple_fields.items():
            if key in data:
                setattr(config, attr, data[key])

        if "headers" in data and isinstance(data["headers"], dict):
            config.headers = data["headers"]

        if "endpoints" in data and isinstance(data["endpoints"], list):
            config.endpoints = data["endpoints"]

        if "targets" in data and isinstance(data["targets"], list):
            config.targets = data["targets"]

        if "proxy_chain" in data and isinstance(data["proxy_chain"], list):
            config.proxy_chain = data["proxy_chain"]

        if "rate_limit" in data and isinstance(data["rate_limit"], dict):
            config.rate_limit = data["rate_limit"]

        if "burst_size" in data:
            config.burst_size = data["burst_size"]

        if "max_concurrent" in data:
            config.max_concurrent = data["max_concurrent"]

        if "report_format" in data:
            config.report_format = data["report_format"]

        if "report_output" in data:
            config.report_output = data["report_output"]

        if "distributed_master" in data:
            config.distributed_master = data["distributed_master"]

        if "distributed_port" in data:
            config.distributed_port = data["distributed_port"]

        if "distributed_workers" in data:
            config.distributed_workers = data["distributed_workers"]

        if "scenario_file" in data:
            config.scenario_file = data["scenario_file"]

        return config


class ConfigSaver:
    @staticmethod
    def save(config: LoadTestConfig, path: str, format: Optional[str] = None):
        if format is None:
            format = ConfigLoader.detect_format(path) or ".json"

        if format == ".json":
            ConfigSaver.save_json(config, path)
        elif format in {".yaml", ".yml"}:
            ConfigSaver.save_yaml(config, path)
        elif format == ".toml":
            ConfigSaver.save_toml(config, path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def save_json(config: LoadTestConfig, path: str):
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)

    @staticmethod
    def save_yaml(config: LoadTestConfig, path: str):
        with open(path, "w") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False)

    @staticmethod
    def save_toml(config: LoadTestConfig, path: str):
        import tomli_w

        with open(path, "wb") as f:
            tomli_w.dump(config.to_dict(), f)
