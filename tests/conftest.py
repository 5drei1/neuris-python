"""Shared fixtures for neuris-python test suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from neuris.transport import AsyncNeuRISTransport, NeuRISTransport

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / name).read_text())


class MockTransport(NeuRISTransport):
    """Sync mock transport that returns pre-configured responses."""

    base_url = "https://testphase.rechtsinformationen.bund.de/v1"

    def __init__(self) -> None:
        self._responses: dict[str, Any] = {}
        self._raw_responses: dict[str, bytes] = {}
        self._calls: list[tuple[str, dict[str, Any] | None]] = []
        self._raw_calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def register(self, path: str, response: dict[str, Any]) -> None:
        self._responses[path] = response

    def register_raw(self, path: str, content: bytes) -> None:
        self._raw_responses[path] = content

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._calls.append((path, params))
        if path in self._responses:
            return self._responses[path]
        raise KeyError(f"MockTransport: no response registered for {path!r}")

    def get_raw(self, path: str, accept: str, params: dict[str, Any] | None = None) -> bytes:
        self._raw_calls.append((path, accept, params))
        if path in self._raw_responses:
            return self._raw_responses[path]
        raise KeyError(f"MockTransport: no raw response registered for {path!r}")

    def close(self) -> None:
        pass


class AsyncMockTransport(AsyncNeuRISTransport):
    """Async mock transport that returns pre-configured responses."""

    base_url = "https://testphase.rechtsinformationen.bund.de/v1"

    def __init__(self) -> None:
        self._responses: dict[str, Any] = {}
        self._raw_responses: dict[str, bytes] = {}
        self._calls: list[tuple[str, dict[str, Any] | None]] = []
        self._raw_calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def register(self, path: str, response: dict[str, Any]) -> None:
        self._responses[path] = response

    def register_raw(self, path: str, content: bytes) -> None:
        self._raw_responses[path] = content

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._calls.append((path, params))
        if path in self._responses:
            return self._responses[path]
        raise KeyError(f"AsyncMockTransport: no response registered for {path!r}")

    async def get_raw(self, path: str, accept: str, params: dict[str, Any] | None = None) -> bytes:
        self._raw_calls.append((path, accept, params))
        if path in self._raw_responses:
            return self._raw_responses[path]
        raise KeyError(f"AsyncMockTransport: no raw response registered for {path!r}")

    async def aclose(self) -> None:
        pass


@pytest.fixture
def mock_transport() -> MockTransport:
    return MockTransport()


@pytest.fixture
def async_mock_transport() -> AsyncMockTransport:
    return AsyncMockTransport()


@pytest.fixture
def legislation_list_fixture() -> dict[str, Any]:
    return load_fixture("legislation_list.json")


@pytest.fixture
def case_law_list_fixture() -> dict[str, Any]:
    return load_fixture("case_law_list.json")


@pytest.fixture
def case_law_detail_fixture() -> dict[str, Any]:
    return load_fixture("case_law_detail.json")


@pytest.fixture
def courts_list_fixture() -> dict[str, Any]:
    return load_fixture("courts_list.json")


@pytest.fixture
def statistics_fixture() -> dict[str, Any]:
    return load_fixture("statistics.json")


@pytest.fixture
def administrative_directive_detail_fixture() -> dict[str, Any]:
    return load_fixture("administrative_directive_detail.json")


@pytest.fixture
def literature_list_fixture() -> dict[str, Any]:
    return load_fixture("literature_list.json")


@pytest.fixture
def literature_detail_fixture() -> dict[str, Any]:
    return load_fixture("literature_detail.json")
