from __future__ import annotations

import importlib.metadata
from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    NeuRISConnectionError,
    NeuRISForbiddenError,
    NeuRISNotFoundError,
    NeuRISRateLimitError,
    NeuRISServerError,
    NeuRISServiceUnavailableError,
    NeuRISTimeoutError,
    NeuRISTransportError,
    NeuRISValidationError,
)

try:
    _VERSION = importlib.metadata.version("neuris-python")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "dev"

_DEFAULT_TIMEOUT = 30.0
_DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": f"neuris-python/{_VERSION}",
}


def _raise_for_response(response: httpx.Response) -> None:
    """Map HTTP error codes to NeuRIS exceptions."""
    if response.is_success:
        return
    url = str(response.url)
    body = response.text
    code = response.status_code
    if code == 403:
        raise NeuRISForbiddenError(
            f"Forbidden: {url}", status_code=code, url=url, body=body
        )
    if code == 404:
        raise NeuRISNotFoundError(
            f"Not found: {url}", status_code=code, url=url, body=body
        )
    if code == 422:
        raise NeuRISValidationError(
            f"Validation error: {url}", status_code=code, url=url, body=body
        )
    if code == 429:
        retry_after: int | None = None
        raw = response.headers.get("Retry-After")
        if raw is not None:
            try:
                retry_after = int(raw)
            except ValueError:
                pass
        raise NeuRISRateLimitError(
            f"Rate limited: {url}",
            status_code=code,
            url=url,
            body=body,
            retry_after=retry_after,
        )
    if code == 503:
        raise NeuRISServiceUnavailableError(
            f"Service unavailable (may be rate limit — 600 req/min): {url}",
            status_code=code,
            url=url,
            body=body,
        )
    if code >= 500:
        raise NeuRISServerError(
            f"Server error {code}: {url}", status_code=code, url=url, body=body
        )
    from .exceptions import NeuRISAPIError

    raise NeuRISAPIError(
        f"HTTP {code}: {url}", status_code=code, url=url, body=body
    )


class NeuRISTransport(ABC):
    """Synchronous transport interface."""

    @property
    @abstractmethod
    def base_url(self) -> str: ...

    @abstractmethod
    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def get_raw(self, path: str, accept: str, params: dict[str, Any] | None = None) -> bytes: ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> NeuRISTransport:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncNeuRISTransport(ABC):
    """Asynchronous transport interface."""

    @property
    @abstractmethod
    def base_url(self) -> str: ...

    @abstractmethod
    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_raw(
        self, path: str, accept: str, params: dict[str, Any] | None = None
    ) -> bytes: ...

    @abstractmethod
    async def aclose(self) -> None: ...

    async def __aenter__(self) -> AsyncNeuRISTransport:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()


class TestphaseTransport(NeuRISTransport):
    """Sync transport for the NeuRIS testphase API with retry logic."""

    base_url = "https://testphase.rechtsinformationen.bund.de/v1"

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        self._get_with_retry = retry(
            retry=retry_if_exception_type((NeuRISServerError, NeuRISRateLimitError)),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        )(self._raw_get)

    def _raw_get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise NeuRISTimeoutError(f"Request timed out: {path}") from exc
        except httpx.ConnectError as exc:
            raise NeuRISConnectionError(f"Connection failed: {path}") from exc
        _raise_for_response(response)
        return response.json()  # type: ignore[no-any-return]

    def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        result: dict[str, Any] = self._get_with_retry(path, params)
        return result

    def get_raw(
        self, path: str, accept: str, params: dict[str, Any] | None = None
    ) -> bytes:
        try:
            response = self._client.get(path, params=params, headers={"Accept": accept})
        except httpx.TimeoutException as exc:
            raise NeuRISTimeoutError(f"Request timed out: {path}") from exc
        except httpx.ConnectError as exc:
            raise NeuRISConnectionError(f"Connection failed: {path}") from exc
        _raise_for_response(response)
        return response.content

    def close(self) -> None:
        self._client.close()


class ProductionTransport(NeuRISTransport):
    """Stub transport for the production NeuRIS API (not yet live, expected H2 2026)."""

    base_url = "https://rechtsinformationen.bund.de/v1"

    def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        raise NeuRISTransportError(
            "ProductionTransport is not yet live (expected H2 2026). "
            "Use TestphaseTransport instead."
        )

    def get_raw(
        self, path: str, accept: str, params: dict[str, Any] | None = None
    ) -> bytes:
        raise NeuRISTransportError(
            "ProductionTransport is not yet live (expected H2 2026). "
            "Use TestphaseTransport instead."
        )

    def close(self) -> None:
        pass


class AsyncTestphaseTransport(AsyncNeuRISTransport):
    """Async transport for the NeuRIS testphase API with retry logic."""

    base_url = "https://testphase.rechtsinformationen.bund.de/v1"

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        self._get_with_retry = retry(
            retry=retry_if_exception_type((NeuRISServerError, NeuRISRateLimitError)),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        )(self._raw_get)

    async def _raw_get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise NeuRISTimeoutError(f"Request timed out: {path}") from exc
        except httpx.ConnectError as exc:
            raise NeuRISConnectionError(f"Connection failed: {path}") from exc
        _raise_for_response(response)
        return response.json()  # type: ignore[no-any-return]

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        result: dict[str, Any] = await self._get_with_retry(path, params)
        return result

    async def get_raw(
        self, path: str, accept: str, params: dict[str, Any] | None = None
    ) -> bytes:
        try:
            response = await self._client.get(path, params=params, headers={"Accept": accept})
        except httpx.TimeoutException as exc:
            raise NeuRISTimeoutError(f"Request timed out: {path}") from exc
        except httpx.ConnectError as exc:
            raise NeuRISConnectionError(f"Connection failed: {path}") from exc
        _raise_for_response(response)
        return response.content

    async def aclose(self) -> None:
        await self._client.aclose()
