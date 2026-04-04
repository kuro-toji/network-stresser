#!/usr/bin/env python3
import socket
import ssl
import time
import datetime
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CipherStrength(Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    UNKNOWN = "unknown"


@dataclass
class CertificateInfo:
    subject: Dict[str, str] = field(default_factory=dict)
    issuer: Dict[str, str] = field(default_factory=dict)
    version: int = 0
    serial_number: str = ""
    not_before: Optional[datetime.datetime] = None
    not_after: Optional[datetime.datetime] = None
    is_valid: bool = False
    days_remaining: int = 0
    fingerprint_sha256: str = ""
    fingerprint_sha1: str = ""
    public_key_algo: str = ""
    public_key_bits: int = 0
    signature_algo: str = ""
    subject_alt_names: List[str] = field(default_factory=list)


@dataclass
class TLSInfo:
    version: str = ""
    cipher_suite: str = ""
    cipher_bits: int = 0
    cipher_strength: CipherStrength = CipherStrength.UNKNOWN
    is_secure: bool = False
    vulnerabilities: List[str] = field(default_factory=list)
    certificate: Optional[CertificateInfo] = None


@dataclass
class SSLScanResult:
    host: str
    port: int
    timestamp: float
    tls_info: Optional[TLSInfo] = None
    error: Optional[str] = None
    connection_time: float = 0
    supports_sslv2: bool = False
    supports_sslv3: bool = False
    supports_tlsv10: bool = False
    supports_tlsv11: bool = False
    supports_tlsv12: bool = False
    supports_tlsv13: bool = False


class SSLCertificateAnalyzer:
    KNOWN_CVES = {
        "POODLE": "CVE-2014-3566",
        "BEAST": "CVE-2011-3389",
        "DROWN": "CVE-2016-0800",
        "FREAK": "CVE-2015-0204",
        "LOGJAM": "CVE-2015-4000",
        "SLOTH": "CVE-2015-0204",
        "ROBOT": "CVE-2016-6883",
        "Lucky Thirteen": "CVE-2013-0169",
        "Sweet32": "CVE-2016-2183",
        "DROWN": "CVE-2016-0800",
    }

    WEAK_CIPHERS = [
        "NULL",
        "aNULL",
        "eNULL",
        "EXPORT",
        "RC4",
        "DES",
        "3DES",
        "MD5",
        "SHA",
        "SSLv2",
        "SSLv3",
    ]

    MEDIUM_CIPHERS = [
        "RC4",
        "DES",
        "3DES",
        "MD5",
        "SHA1",
        "TLSv1",
        "TLSv1.1",
    ]

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_certificate(
        self, host: str, port: int, ssl_context: Optional[ssl.SSLContext] = None
    ) -> Optional[CertificateInfo]:
        try:
            if ssl_context is None:
                ssl_context = ssl.create_default_context()

            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with ssl_context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)

                    if not cert:
                        return None

                    return self._parse_certificate(cert, ssock)

        except Exception as e:
            return None

    def _parse_certificate(self, cert_der: bytes, ssock) -> CertificateInfo:
        info = CertificateInfo()

        try:
            import cryptography.x509 as x509

            cert = x509.load_der_x509_certificate(cert_der)

            info.version = cert.version.value
            info.serial_number = format(cert.serial_number, "x")
            info.not_before = cert.not_valid_before_utc
            info.not_after = cert.not_valid_after_utc
            info.is_valid = datetime.datetime.utcnow() < info.not_after

            days_remaining = (info.not_after - datetime.datetime.utcnow()).days
            info.days_remaining = max(0, days_remaining)

            info.fingerprint_sha256 = hashlib.sha256(cert_der).hexdigest()
            info.fingerprint_sha1 = hashlib.sha1(cert_der).hexdigest()

            if hasattr(cert, "signature_hash_algorithm"):
                info.signature_algo = cert.signature_hash_algorithm.name

            public_key = cert.public_key()
            info.public_key_algo = public_key.__class__.__name__

            try:
                if hasattr(public_key, "key_size"):
                    info.public_key_bits = public_key.key_size
            except Exception:
                pass

            try:
                for attr in cert.subject:
                    info.subject[attr.oid._name] = attr.value
            except Exception:
                pass

            try:
                for attr in cert.issuer:
                    info.issuer[attr.oid._name] = attr.value
            except Exception:
                pass

            try:
                san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                info.subject_alt_names = san_ext.value.get_values_for_type(x509.DNSName)
            except Exception:
                pass

        except ImportError:
            import ssl
            import base64

            try:
                pem_cert = ssl.DER_cert_to_PEM_cert(cert_der)
                cert_dict = ssock.getpeercert()

                if cert_dict:
                    if "subject" in cert_dict:
                        for item in cert_dict["subject"]:
                            for key, value in item:
                                info.subject[key] = value

                    if "issuer" in cert_dict:
                        for item in cert_dict["issuer"]:
                            for key, value in item:
                                info.issuer[key] = value

                    if "version" in cert_dict:
                        info.version = cert_dict["version"]

                    info.not_before = cert_dict.get("notBefore")
                    info.not_after = cert_dict.get("notAfter")

            except Exception:
                pass

        return info

    def check_vulnerabilities(self, cipher_suite: str, tls_version: str) -> List[str]:
        vulnerabilities = []

        cipher_upper = cipher_suite.upper()
        version_upper = tls_version.upper()

        for weak in self.WEAK_CIPHERS:
            if weak in cipher_upper:
                vulnerabilities.append(f"Uses weak cipher: {weak}")

        if "SSLv2" in version_upper or "SSLv2" in cipher_upper:
            vulnerabilities.append("POODLE (SSLv2)")

        if "SSLv3" in version_upper or "SSLv3" in cipher_upper:
            vulnerabilities.append("POODLE (SSLv3)")

        if "RC4" in cipher_upper:
            vulnerabilities.append("BEAST (RC4)")

        if "3DES" in cipher_upper:
            vulnerabilities.append("Sweet32 (3DES)")

        if "MD5" in cipher_upper:
            vulnerabilities.append("Weak hash algorithm (MD5)")

        if "SHA1" in cipher_upper:
            vulnerabilities.append("Weak hash algorithm (SHA1)")

        if tls_version in ("TLSv1.0", "TLSv1.1"):
            vulnerabilities.append("Deprecated TLS version")

        return vulnerabilities

    def get_cipher_strength(self, cipher_suite: str, tls_version: str) -> CipherStrength:
        cipher_upper = cipher_suite.upper()
        version_upper = tls_version.upper()

        for weak in self.WEAK_CIPHERS:
            if weak in cipher_upper:
                return CipherStrength.WEAK

        for medium in self.MEDIUM_CIPHERS:
            if medium in cipher_upper:
                return CipherStrength.MEDIUM

        if "TLSv1.3" in version_upper and "AES" in cipher_upper:
            return CipherStrength.STRONG

        if "TLSv1.2" in version_upper and any(x in cipher_upper for x in ["AES", "CHACHA"]):
            return CipherStrength.STRONG

        if "TLSv1.2" in version_upper and "GCM" in cipher_upper:
            return CipherStrength.STRONG

        return CipherStrength.MEDIUM


class TLSFuzzer:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.analyzer = SSLCertificateAnalyzer(timeout)

    def scan(self, host: str, port: int = 443, include_raw: bool = False) -> SSLScanResult:
        result = SSLScanResult(host=host, port=port, timestamp=time.time())

        start = time.time()

        try:
            for version, version_name, enabled in self._test_tls_versions(host, port):
                setattr(result, f"supports_{version_name}", enabled)

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                start_conn = time.time()
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    result.connection_time = time.time() - start_conn

                    cipher = ssock.cipher()
                    if cipher:
                        result.tls_info = TLSInfo(
                            version=cipher[2] if len(cipher) > 2 else "Unknown",
                            cipher_suite=cipher[0] if cipher else "None",
                            cipher_bits=cipher[2] if len(cipher) > 2 else 0,
                            cipher_strength=self.analyzer.get_cipher_strength(
                                cipher[0] if cipher else "", cipher[2] if cipher else ""
                            ),
                        )

                        if cipher[0]:
                            vulns = self.analyzer.check_vulnerabilities(cipher[0], cipher[2] if len(cipher) > 2 else "")
                            result.tls_info.vulnerabilities = vulns
                            result.tls_info.is_secure = len(vulns) == 0 and "TLSv1" not in cipher[2]

                    result.tls_info.certificate = self.analyzer.get_certificate(host, port, context)

        except Exception as e:
            result.error = str(e)

        result.connection_time = time.time() - start

        return result

    def _test_tls_versions(self, host: str, port: int) -> List[Tuple[str, str, bool]]:
        results = []
        versions = [
            (ssl.TLSVersion.SSLv3, "ssl_v3"),
            (ssl.TLSVersion.TLSv1, "tls_v10"),
            (ssl.TLSVersion.TLSv1_1, "tls_v11"),
            (ssl.TLSVersion.TLSv1_2, "tls_v12"),
            (ssl.TLSVersion.TLSv1_3, "tls_v13"),
        ]

        for version_enum, version_name in versions:
            enabled = False
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
                context.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED

                try:
                    context.maximum_version = version_enum
                    context.minimum_version = version_enum
                except AttributeError:
                    pass

                with socket.create_connection((host, port), timeout=self.timeout) as sock:
                    try:
                        with context.wrap_socket(sock, server_hostname=host) as ssock:
                            enabled = True
                    except ssl.SSLError:
                        pass
                    except Exception:
                        pass

            except Exception:
                pass

            results.append((version_enum, version_name, enabled))

        return results

    def test_cipher_suites(self, host: str, port: int = 443) -> List[str]:
        supported_ciphers = []

        cipher_suites = [
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "AES256-GCM-SHA384",
            "AES128-GCM-SHA256",
            "DES-CBC3-SHA",
            "RC4-SHA",
            "RC4-MD5",
            "NULL-SHA",
        ]

        for cipher in cipher_suites:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.set_ciphers(cipher)

                with socket.create_connection((host, port), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        supported_ciphers.append(cipher)
            except Exception:
                pass

        return supported_ciphers


class SSLAnalyzer:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.fuzzer = TLSFuzzer(timeout)
        self.analyzer = SSLCertificateAnalyzer(timeout)

    def full_scan(self, host: str, port: int = 443) -> Dict[str, Any]:
        result = self.fuzzer.scan(host, port)

        output = {
            "host": result.host,
            "port": result.port,
            "timestamp": datetime.datetime.fromtimestamp(result.timestamp).isoformat(),
            "connection_time_ms": round(result.connection_time * 1000, 2),
            "supports_sslv2": result.supports_sslv2,
            "supports_sslv3": result.supports_sslv3,
            "supports_tlsv10": result.supports_tlsv10,
            "supports_tlsv11": result.supports_tlsv11,
            "supports_tlsv12": result.supports_tlsv12,
            "supports_tlsv13": result.supports_tlsv13,
        }

        if result.tls_info:
            output["tls"] = {
                "version": result.tls_info.version,
                "cipher_suite": result.tls_info.cipher_suite,
                "cipher_bits": result.tls_info.cipher_bits,
                "cipher_strength": result.tls_info.cipher_strength.value,
                "is_secure": result.tls_info.is_secure,
                "vulnerabilities": result.tls_info.vulnerabilities,
            }

            if result.tls_info.certificate:
                cert = result.tls_info.certificate
                output["certificate"] = {
                    "subject": cert.subject,
                    "issuer": cert.issuer,
                    "version": cert.version,
                    "serial_number": cert.serial_number,
                    "not_before": cert.not_before.isoformat() if cert.not_before else None,
                    "not_after": cert.not_after.isoformat() if cert.not_after else None,
                    "is_valid": cert.is_valid,
                    "days_remaining": cert.days_remaining,
                    "fingerprint_sha256": cert.fingerprint_sha256,
                    "fingerprint_sha1": cert.fingerprint_sha1,
                    "public_key_algorithm": cert.public_key_algo,
                    "public_key_bits": cert.public_key_bits,
                    "signature_algorithm": cert.signature_algo,
                    "subject_alt_names": cert.subject_alt_names,
                }

        if result.error:
            output["error"] = result.error

        return output

    def check_certificate_chain(self, host: str, port: int = 443) -> Dict[str, Any]:
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    cipher = ssock.cipher()

                    return {
                        "host": host,
                        "port": port,
                        "has_valid_chain": True,
                        "cipher_suite": cipher[0] if cipher else None,
                        "tls_version": cipher[2] if cipher else None,
                        "certificate_provided": cert is not None,
                    }

        except Exception as e:
            return {"host": host, "port": port, "error": str(e)}
