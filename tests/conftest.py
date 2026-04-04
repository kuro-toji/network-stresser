import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_config():
    return {
        "url": "http://localhost:8080",
        "total_requests": 100,
        "concurrency": 10,
        "method": "GET",
        "mode": "flood",
        "protocol": "http1",
    }


@pytest.fixture
def sample_response_times():
    import random

    return [random.uniform(0.01, 0.5) for _ in range(100)]
