#!/usr/bin/env python3
import json
import time
import threading
import random
import re
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class StepType(Enum):
    REQUEST = "request"
    THINK = "think"
    LOOP = "loop"
    CONDITION = "condition"
    VARIABLE_SET = "variable_set"
    VARIABLE_GET = "variable_get"
    ASSERT = "assert"
    GROUP = "group"


@dataclass
class ScenarioStep:
    type: str
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    iterations: int = 1
    condition: Optional[str] = None
    steps: List["ScenarioStep"] = field(default_factory=list)


@dataclass
class RequestTemplate:
    method: str = "GET"
    url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    follow_redirects: bool = True
    timeout: int = 30


@dataclass
class ScenarioResult:
    step_name: str
    success: bool
    latency: float = 0
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = 0


class VariableStore:
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.lock = threading.Lock()

    def set(self, key: str, value: Any):
        with self.lock:
            self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self.lock:
            return self.variables.get(key, default)

    def interpolate(self, text: str) -> str:
        pattern = r"\{\{(\w+)(?::([^}]+))?\}\}"

        def replacer(match):
            var_name = match.group(1)
            default_val = match.group(2)
            value = self.get(var_name, default_val or "")
            return str(value)

        return re.sub(pattern, replacer, text)


class ScenarioRunner:
    def __init__(
        self,
        scenario: Dict[str, Any],
        base_url: str = "",
        variables: Optional[VariableStore] = None,
        request_func: Optional[Callable] = None,
    ):
        self.scenario = scenario
        self.base_url = base_url
        self.variables = variables or VariableStore()
        self.request_func = request_func
        self.results: List[ScenarioResult] = []
        self.lock = threading.Lock()
        self.running = False

    def run(self, iterations: int = 1) -> List[ScenarioResult]:
        self.running = True
        steps = self._parse_steps(self.scenario.get("steps", []))

        for i in range(iterations):
            if not self.running:
                break
            self._execute_steps(steps)

        return self.results

    def stop(self):
        self.running = False

    def _parse_steps(self, step_data: List[Dict[str, Any]]) -> List[ScenarioStep]:
        steps = []
        for step_dict in step_data:
            step = ScenarioStep(
                type=step_dict.get("type", "request"),
                name=step_dict.get("name", "Unnamed Step"),
                params=step_dict.get("params", {}),
                iterations=step_dict.get("iterations", 1),
                condition=step_dict.get("condition"),
                steps=[self._parse_steps([s])[0] for s in step_dict.get("steps", [])],
            )
            steps.append(step)
        return steps

    def _execute_steps(self, steps: List[ScenarioStep]):
        for step in steps:
            if not self.running:
                break

            if not self._evaluate_condition(step.condition):
                continue

            if step.type == "request":
                self._execute_request(step)
            elif step.type == "think":
                self._execute_think(step)
            elif step.type == "loop":
                self._execute_loop(step)
            elif step.type == "condition":
                self._execute_condition(step)
            elif step.type == "variable_set":
                self._execute_variable_set(step)
            elif step.type == "assert":
                self._execute_assert(step)
            elif step.type == "group":
                self._execute_steps(step.steps)

    def _evaluate_condition(self, condition: Optional[str]) -> bool:
        if not condition:
            return True

        condition = self.variables.interpolate(condition)

        operators = ["!=", "==", ">=", "<=", ">", "<", "contains"]
        for op in operators:
            if op in condition:
                parts = condition.split(op)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    left_val = self.variables.get(left, left)
                    right_val = self.variables.get(right, right)

                    try:
                        left_val = int(left_val)
                        right_val = int(right_val)
                    except (ValueError, TypeError):
                        pass

                    if op == "==" and left_val == right_val:
                        return True
                    elif op == "!=" and left_val != right_val:
                        return True
                    elif op == ">=" and left_val >= right_val:
                        return True
                    elif op == "<=" and left_val <= right_val:
                        return True
                    elif op == ">" and left_val > right_val:
                        return True
                    elif op == "<" and left_val < right_val:
                        return True
                    elif op == "contains" and str(right_val) in str(left_val):
                        return True

                    return False

        return True

    def _execute_request(self, step: ScenarioStep):
        params = step.params.copy()

        url = self.variables.interpolate(params.get("url", ""))
        if url and not url.startswith(("http://", "https://")):
            url = self.base_url.rstrip("/") + "/" + url.lstrip("/")

        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        headers = {k: self.variables.interpolate(v) for k, v in headers.items()}
        body = params.get("body")
        if body:
            body = self.variables.interpolate(body)

        timeout = params.get("timeout", 30)
        follow_redirects = params.get("follow_redirects", True)

        start = time.time()
        try:
            if self.request_func:
                response = self.request_func(
                    method=method,
                    url=url,
                    headers=headers,
                    body=body,
                    timeout=timeout,
                    follow_redirects=follow_redirects,
                )
                status_code = getattr(response, "status_code", 0)
                response_body = getattr(response, "text", "") or ""
            else:
                import requests

                resp = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=body,
                    timeout=timeout,
                    allow_redirects=follow_redirects,
                )
                status_code = resp.status_code
                response_body = resp.text

            latency = time.time() - start

            extract = params.get("extract", {})
            for var_name, json_path in extract.items():
                try:
                    if json_path.startswith("$."):
                        import json

                        data = json.loads(response_body)
                        value = self._extract_json_path(data, json_path)
                        self.variables.set(var_name, value)
                    else:
                        match = re.search(json_path, response_body)
                        if match:
                            self.variables.set(var_name, match.group(1))
                except Exception:
                    pass

            with self.lock:
                self.results.append(
                    ScenarioResult(
                        step_name=step.name,
                        success=200 <= status_code < 300,
                        latency=latency,
                        status_code=status_code,
                        response_body=response_body[:1000],
                        timestamp=time.time(),
                    )
                )

        except Exception as e:
            latency = time.time() - start
            with self.lock:
                self.results.append(
                    ScenarioResult(
                        step_name=step.name,
                        success=False,
                        latency=latency,
                        error=str(e),
                        timestamp=time.time(),
                    )
                )

    def _extract_json_path(self, data: Any, path: str) -> Any:
        parts = path[2:].split(".")
        for part in parts:
            if isinstance(data, dict):
                data = data.get(part, {})
            elif isinstance(data, list):
                try:
                    data = data[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return data

    def _execute_think(self, step: ScenarioStep):
        delay = step.params.get("duration", 1)
        time.sleep(delay)

        with self.lock:
            self.results.append(
                ScenarioResult(
                    step_name=step.name,
                    success=True,
                    latency=delay,
                    timestamp=time.time(),
                )
            )

    def _execute_loop(self, step: ScenarioStep):
        iterations = step.params.get("iterations", 1)
        for _ in range(iterations):
            if not self.running:
                break
            self._execute_steps(step.steps)

    def _execute_condition(self, step: ScenarioStep):
        self._execute_steps(step.steps)

    def _execute_variable_set(self, step: ScenarioStep):
        var_name = step.params.get("name")
        var_value = step.params.get("value", "")

        if step.params.get("random"):
            min_val = step.params.get("min", 0)
            max_val = step.params.get("max", 100)
            var_value = random.randint(min_val, max_val)
        elif step.params.get("timestamp"):
            var_value = int(time.time() * 1000)
        elif step.params.get("uuid"):
            import uuid

            var_value = str(uuid.uuid4())
        elif isinstance(var_value, str):
            var_value = self.variables.interpolate(var_value)

        if var_name:
            self.variables.set(var_name, var_value)

    def _execute_assert(self, step: ScenarioStep):
        assertion = step.params.get("expression", "")
        expected = step.params.get("expected")
       negate = step.params.get("negate", False)

        actual = self.variables.interpolate(assertion) if assertion else None

        success = str(actual) == str(expected) if expected is not None else bool(actual)
        if negate:
            success = not success

        with self.lock:
            self.results.append(
                ScenarioResult(
                    step_name=step.name,
                    success=success,
                    error=f"Assertion failed: expected {expected}, got {actual}" if not success else None,
                    timestamp=time.time(),
                )
            )


class ScenarioLoader:
    @staticmethod
    def load(path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            return json.load(f)

    @staticmethod
    def validate(scenario: Dict[str, Any]) -> List[str]:
        errors = []

        if "name" not in scenario:
            errors.append("Scenario must have a 'name' field")

        if "steps" not in scenario:
            errors.append("Scenario must have a 'steps' field")
        elif not isinstance(scenario["steps"], list):
            errors.append("'steps' must be an array")

        return errors

    @staticmethod
    def create_example() -> Dict[str, Any]:
        return {
            "name": "User Journey Test",
            "description": "Test user registration and login flow",
            "steps": [
                {
                    "type": "variable_set",
                    "name": "Generate User",
                    "params": {
                        "uuid": True,
                    },
                },
                {
                    "type": "request",
                    "name": "Register User",
                    "params": {
                        "method": "POST",
                        "url": "/api/users/register",
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(
                            {
                                "username": "{{uuid}}",
                                "email": "{{uuid}}@example.com",
                                "password": "test123",
                            }
                        ),
                        "extract": {"user_id": "$.id", "token": "$.auth_token"},
                    },
                },
                {
                    "type": "think",
                    "name": "Wait before login",
                    "params": {"duration": 1},
                },
                {
                    "type": "request",
                    "name": "Login",
                    "params": {
                        "method": "POST",
                        "url": "/api/auth/login",
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(
                            {
                                "username": "{{uuid}}@example.com",
                                "password": "test123",
                            }
                        ),
                        "extract": {"session_token": "$.session_token"},
                    },
                },
                {
                    "type": "request",
                    "name": "Get Profile",
                    "params": {
                        "method": "GET",
                        "url": "/api/users/me",
                        "headers": {"Authorization": "Bearer {{session_token}}"},
                    },
                },
            ],
        }
