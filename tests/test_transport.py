"""Unit tests for NeuRIS transport layer."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest

from neuris.exceptions import (
    NeuRISAPIError,
    NeuRISConnectionError,
    NeuRISNotFoundError,
    NeuRISRateLimitError,
    NeuRISServerError,
    NeuRISTimeoutError,
    NeuRISTransportError,
    NeuRISValidationError,
)
from neuris.transport import (
    AsyncTestphaseTransport,
    ProductionTransport,
    TestphaseTransport,
    _raise_for_response,
)

# ── _raise_for_response ───────────────────────────────────────────────────────

def _mock_response(status_code: int, body: str = "", headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        content=body.encode(),
        headers=headers or {},
        request=httpx.Request("GET", "https://testphase.rechtsinformationen.bund.de/v1/test"),
    )


def test_raise_for_response_200_ok() -> None:
    resp = _mock_response(200, '{"ok": true}')
    _raise_for_response(resp)  # must not raise


def test_raise_for_response_404() -> None:
    resp = _mock_response(404, "not found")
    with pytest.raises(NeuRISNotFoundError) as exc_info:
        _raise_for_response(resp)
    assert exc_info.value.status_code == 404


def test_raise_for_response_422() -> None:
    resp = _mock_response(422, "unprocessable")
    with pytest.raises(NeuRISValidationError) as exc_info:
        _raise_for_response(resp)
    assert exc_info.value.status_code == 422


def test_raise_for_response_429_with_retry_after() -> None:
    resp = _mock_response(429, "rate limited", headers={"Retry-After": "30"})
    with pytest.raises(NeuRISRateLimitError) as exc_info:
        _raise_for_response(resp)
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 30


def test_raise_for_response_429_no_retry_after() -> None:
    resp = _mock_response(429, "rate limited")
    with pytest.raises(NeuRISRateLimitError) as exc_info:
        _raise_for_response(resp)
    assert exc_info.value.retry_after is None


def test_raise_for_response_429_invalid_retry_after() -> None:
    resp = _mock_response(429, "rate limited", headers={"Retry-After": "not-a-number"})
    with pytest.raises(NeuRISRateLimitError) as exc_info:
        _raise_for_response(resp)
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after is None


def test_raise_for_response_500() -> None:
    resp = _mock_response(500, "internal server error")
    with pytest.raises(NeuRISServerError) as exc_info:
        _raise_for_response(resp)
    assert exc_info.value.status_code == 500


def test_raise_for_response_503() -> None:
    resp = _mock_response(503, "service unavailable")
    with pytest.raises(NeuRISServerError):
        _raise_for_response(resp)


# ── ProductionTransport ───────────────────────────────────────────────────────

def test_production_transport_raises_transport_error() -> None:
    t = ProductionTransport()
    with pytest.raises(NeuRISTransportError, match="not yet live"):
        t.get("/statistics")


def test_production_transport_close_noop() -> None:
    t = ProductionTransport()
    t.close()  # must not raise


def test_production_transport_context_manager() -> None:
    with ProductionTransport() as t:
        with pytest.raises(NeuRISTransportError):
            t.get("/anything")


def test_production_transport_base_url() -> None:
    assert "rechtsinformationen.bund.de" in ProductionTransport.base_url
    assert "testphase" not in ProductionTransport.base_url


# ── TestphaseTransport ────────────────────────────────────────────────────────

def test_testphase_transport_base_url() -> None:
    assert "testphase.rechtsinformationen.bund.de" in TestphaseTransport.base_url


def test_testphase_transport_user_agent() -> None:
    t = TestphaseTransport()
    headers = dict(t._client.headers)
    user_agent = headers.get("user-agent", "")
    assert "neuris-python" in user_agent
    t.close()


def test_testphase_transport_accept_header() -> None:
    t = TestphaseTransport()
    headers = dict(t._client.headers)
    assert headers.get("accept") == "application/json"
    t.close()


def test_testphase_transport_context_manager_closes() -> None:
    with TestphaseTransport() as t:
        assert t._client is not None
    assert t._client.is_closed


def test_testphase_transport_timeout_error() -> None:
    t = TestphaseTransport()
    with patch.object(t._client, "get", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(NeuRISTimeoutError):
            t._raw_get("/test")
    t.close()


def test_testphase_transport_connection_error() -> None:
    t = TestphaseTransport()
    with patch.object(t._client, "get", side_effect=httpx.ConnectError("refused")):
        with pytest.raises(NeuRISConnectionError):
            t._raw_get("/test")
    t.close()


def test_testphase_transport_get_success() -> None:
    t = TestphaseTransport()
    mock_resp = _mock_response(200, '{"key": "value"}')
    with patch.object(t._client, "get", return_value=mock_resp):
        result = t.get("/test")
    assert result == {"key": "value"}
    t.close()


# ── AsyncTestphaseTransport ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_testphase_transport_base_url() -> None:
    assert "testphase.rechtsinformationen.bund.de" in AsyncTestphaseTransport.base_url


@pytest.mark.asyncio
async def test_async_testphase_transport_timeout_error() -> None:
    t = AsyncTestphaseTransport()
    with patch.object(t._client, "get", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(NeuRISTimeoutError):
            await t._raw_get("/test")
    await t.aclose()


@pytest.mark.asyncio
async def test_async_testphase_transport_connection_error() -> None:
    t = AsyncTestphaseTransport()
    with patch.object(t._client, "get", side_effect=httpx.ConnectError("refused")):
        with pytest.raises(NeuRISConnectionError):
            await t._raw_get("/test")
    await t.aclose()


@pytest.mark.asyncio
async def test_async_testphase_transport_get_success() -> None:
    t = AsyncTestphaseTransport()
    mock_resp = _mock_response(200, '{"ok": true}')
    # Make it awaitable
    async def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        return mock_resp

    with patch.object(t._client, "get", side_effect=fake_get):
        result = await t._raw_get("/test")
    assert result == {"ok": True}
    await t.aclose()


@pytest.mark.asyncio
async def test_async_testphase_transport_context_manager() -> None:
    async with AsyncTestphaseTransport() as t:
        assert t._client is not None
    assert t._client.is_closed


# ── Exception repr ────────────────────────────────────────────────────────────

def test_api_error_repr() -> None:
    from neuris.exceptions import NeuRISAPIError
    e = NeuRISAPIError("test", status_code=404, url="http://x", body="not found")
    assert "404" in repr(e)
    assert "NeuRISAPIError" in repr(e)
