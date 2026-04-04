import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock


class TestLoadTesterConfig:
    def test_loadtester_initialization(self):
        from loadtest import LoadTester

        tester = LoadTester(
            url="http://localhost:8080",
            total_requests=100,
            concurrency=10,
        )

        assert tester.url == "http://localhost:8080"
        assert tester.total_requests == 100
        assert tester.concurrency == 10
        assert tester.method == "GET"
        assert tester.mode == "flood"

    def test_loadtester_with_headers(self):
        from loadtest import LoadTester

        tester = LoadTester(
            url="http://localhost:8080",
            total_requests=100,
            concurrency=10,
            headers={"User-Agent": "TestAgent", "X-Custom": "value"},
        )

        assert tester.headers["User-Agent"] == "TestAgent"
        assert tester.headers["X-Custom"] == "value"

    def test_loadtester_with_proxy(self):
        from loadtest import LoadTester

        tester = LoadTester(
            url="http://localhost:8080",
            total_requests=100,
            concurrency=10,
            proxy="http://proxy:8080",
        )

        assert tester.proxy == "http://proxy:8080"

    def test_loadtester_json_config_loading(self, tmp_path):
        from loadtest import LoadTester

        config_file = tmp_path / "config.json"
        config_data = {
            "url": "http://test.example.com",
            "requests": 500,
            "concurrency": 20,
            "method": "POST",
            "mode": "flood",
        }
        config_file.write_text(json.dumps(config_data))

        tester = LoadTester(
            url="http://localhost:8080",
            total_requests=100,
            concurrency=10,
            config=str(config_file),
        )

        assert tester.url == "http://test.example.com"
        assert tester.total_requests == 500
        assert tester.concurrency == 20
        assert tester.method == "POST"

    def test_validate_url_valid(self):
        from loadtest import LoadTester

        tester = LoadTester(
            url="http://localhost:8080",
            total_requests=100,
            concurrency=10,
        )
        tester.validate_url()

    def test_validate_url_invalid(self):
        from loadtest import LoadTester

        tester = LoadTester(
            url="ftp://localhost:8080",
            total_requests=100,
            concurrency=10,
        )

        with pytest.raises(ValueError, match="Invalid URL scheme"):
            tester.validate_url()


class TestReports:
    def test_test_result_dataclass(self):
        from reports import TestResult

        result = TestResult(
            mode="flood",
            url="http://localhost:8080",
            duration=10.5,
            total_requests=1000,
            rps=95.24,
            success=950,
            failed=50,
            avg_response_ms=125.5,
            min_response_ms=10.0,
            max_response_ms=500.0,
            stddev_ms=45.2,
            p50_ms=100.0,
            p90_ms=180.0,
            p95_ms=220.0,
            p99_ms=350.0,
            errors={"Timeout": 30, "Connection Error": 20},
            timestamp="2024-01-01 12:00:00",
        )

        assert result.mode == "flood"
        assert result.total_requests == 1000
        assert result.rps == 95.24
        assert result.success == 950
        assert result.failed == 50

    def test_results_exporter_calculate_statistics(self):
        from reports import ResultsExporter

        response_times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        stats = ResultsExporter.calculate_statistics(response_times)

        assert stats["min"] == 100.0
        assert stats["max"] == 1000.0
        assert stats["p50"] == 500.0
        assert stats["p90"] == 900.0

    def test_results_exporter_calculate_statistics_empty(self):
        from reports import ResultsExporter

        stats = ResultsExporter.calculate_statistics([])

        assert stats["avg"] == 0
        assert stats["min"] == 0
        assert stats["max"] == 0


class TestRateLimit:
    def test_token_bucket_initialization(self):
        from ratelimit import TokenBucket

        bucket = TokenBucket(rate=10.0, capacity=20)
        assert bucket.rate == 10.0
        assert bucket.capacity == 20

    def test_token_bucket_consume(self):
        from ratelimit import TokenBucket

        bucket = TokenBucket(rate=10.0, capacity=20)
        result = bucket.consume(1)
        assert result is True
        assert bucket.tokens < 20

    def test_leaky_bucket_initialization(self):
        from ratelimit import LeakyBucket

        bucket = LeakyBucket(rate=5.0, capacity=10)
        assert bucket.rate == 5.0
        assert bucket.capacity == 10

    def test_sliding_window_counter(self):
        from ratelimit import SlidingWindowCounter

        counter = SlidingWindowCounter(window_size=1.0, max_requests=5)
        for _ in range(5):
            assert counter.allow() is True
        assert counter.allow() is False

    def test_rate_limiter_config(self):
        from ratelimit import RateLimiter, RateLimitConfig

        config = RateLimitConfig(
            requests_per_second=100,
            burst_size=50,
        )
        limiter = RateLimiter(config)
        assert limiter.config.requests_per_second == 100
        assert limiter.config.burst_size == 50


class TestConfigLoader:
    def test_load_json_config(self, tmp_path):
        from config_loader import ConfigLoader

        config_file = tmp_path / "test.json"
        config_data = {
            "url": "http://example.com",
            "total_requests": 1000,
            "concurrency": 10,
            "method": "GET",
        }
        config_file.write_text(json.dumps(config_data))

        config = ConfigLoader.load(str(config_file))
        assert config.url == "http://example.com"
        assert config.total_requests == 1000
        assert config.concurrency == 10

    def test_load_yaml_config(self, tmp_path):
        from config_loader import ConfigLoader

        config_file = tmp_path / "test.yaml"
        config_data = """url: http://example.com
total_requests: 2000
concurrency: 20
method: POST
"""
        config_file.write_text(config_data)

        config = ConfigLoader.load(str(config_file))
        assert config.url == "http://example.com"
        assert config.total_requests == 2000
        assert config.concurrency == 20
        assert config.method == "POST"


class TestProtocols:
    def test_quic_protocol_initialization(self):
        from protocols import QUICProtocol

        proto = QUICProtocol(host="example.com", port=443)
        assert proto.host == "example.com"
        assert proto.port == 443

    def test_ftp_protocol_initialization(self):
        from protocols import FTProtocol

        proto = FTProtocol(host="ftp.example.com", port=21)
        assert proto.host == "ftp.example.com"
        assert proto.port == 21

    def test_smtp_protocol_initialization(self):
        from protocols import SMTPProtocol

        proto = SMTPProtocol(host="smtp.example.com", port=25)
        assert proto.host == "smtp.example.com"
        assert proto.port == 25

    def test_protocol_fuzzer_list_protocols(self):
        from protocols import ProtocolFuzzer

        protocols = ProtocolFuzzer.list_protocols()
        assert "quic" in protocols
        assert "ftp" in protocols
        assert "smtp" in protocols
        assert "ssh" in protocols

    def test_protocol_fuzzer_get_protocol(self):
        from protocols import ProtocolFuzzer

        proto_class = ProtocolFuzzer.get_protocol("quic")
        assert proto_class is not None


class TestScenario:
    def test_variable_store(self):
        from scenario import VariableStore

        store = VariableStore()
        store.set("test_var", "test_value")
        assert store.get("test_var") == "test_value"
        assert store.get("nonexistent", "default") == "default"

    def test_variable_store_interpolate(self):
        from scenario import VariableStore

        store = VariableStore()
        store.set("name", "Alice")
        result = store.interpolate("Hello {{name}}!")
        assert result == "Hello Alice!"

    def test_variable_store_interpolate_default(self):
        from scenario import VariableStore

        store = VariableStore()
        result = store.interpolate("Hello {{name:World}}!")
        assert result == "Hello World!"

    def test_scenario_loader_validate_valid(self):
        from scenario import ScenarioLoader

        scenario = {
            "name": "Test Scenario",
            "steps": [{"type": "request", "name": "Step 1", "params": {"url": "/test"}}],
        }
        errors = ScenarioLoader.validate(scenario)
        assert len(errors) == 0

    def test_scenario_loader_validate_missing_name(self):
        from scenario import ScenarioLoader

        scenario = {"steps": []}
        errors = ScenarioLoader.validate(scenario)
        assert "Scenario must have a 'name' field" in errors

    def test_scenario_loader_validate_missing_steps(self):
        from scenario import ScenarioLoader

        scenario = {"name": "Test"}
        errors = ScenarioLoader.validate(scenario)
        assert "Scenario must have a 'steps' field" in errors

    def test_scenario_loader_create_example(self):
        from scenario import ScenarioLoader

        example = ScenarioLoader.create_example()
        assert example["name"] == "User Journey Test"
        assert len(example["steps"]) > 0


class TestMetrics:
    def test_latency_stats_initialization(self):
        from metrics import LatencyStats

        stats = LatencyStats()
        assert stats.count == 0
        assert stats.mean == 0

    def test_metrics_collector_record_request(self):
        from metrics import MetricsCollector

        collector = MetricsCollector(interval=1.0)
        collector.start()
        time.sleep(0.1)

        collector.record_request(latency=0.5, success=True, status_code=200)
        collector.record_request(latency=0.3, success=True, status_code=200)
        collector.record_request(latency=-1, success=False, error="Timeout")

        stats = collector.get_latency_stats()
        assert stats.count == 2

        collector.stop()

    def test_metrics_collector_get_latency_percentiles(self):
        from metrics import MetricsCollector

        collector = MetricsCollector()
        for _ in range(100):
            collector.record_request(latency=0.1, success=True)

        percentiles = collector.get_latency_percentiles()
        assert "p50_ms" in percentiles
        assert "p99_ms" in percentiles

    def test_profiler(self):
        from metrics import Profiler

        profiler = Profiler()
        profiler.start("test_operation")
        time.sleep(0.05)
        profiler.end("test_operation")

        stats = profiler.get_stats("test_operation")
        assert stats["count"] == 1
        assert stats["total"] > 0


class TestDistributed:
    def test_worker_node_initialization(self):
        from distributed import WorkerNode

        worker = WorkerNode(host="localhost", port=5555, worker_id="test-001")
        assert worker.host == "localhost"
        assert worker.port == 5555
        assert worker.worker_id == "test-001"
        assert worker.connected is False

    def test_master_node_initialization(self):
        from distributed import MasterNode

        master = MasterNode(host="0.0.0.0", port=5555)
        assert master.host == "0.0.0.0"
        assert master.port == 5555
        assert len(master.workers) == 0

    def test_distributed_coordinator_initialization(self):
        from distributed import DistributedCoordinator

        coord = DistributedCoordinator(master_host="localhost", master_port=5555)
        assert coord.master_host == "localhost"
        assert coord.master_port == 5555


class TestWebUI:
    def test_webui_initialization(self):
        from webui import WebUI

        ui = WebUI(host="0.0.0.0", port=8080)
        assert ui.host == "0.0.0.0"
        assert ui.port == 8080
        assert ui.test_results["status"] == "idle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
