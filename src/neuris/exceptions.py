from __future__ import annotations

import json


class NeuRISError(Exception):
    """Base exception for all NeuRIS client errors."""


class NeuRISAPIError(NeuRISError):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, *, status_code: int, url: str, body: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body = body
        self.error_code: str | None = None
        self.error_message: str | None = None
        self.parameter: str | None = None
        try:
            data = json.loads(body)
            errors = data.get("errors")
            if errors and isinstance(errors, list):
                first = errors[0]
                self.error_code = first.get("code")
                self.error_message = first.get("message")
                self.parameter = first.get("parameter")
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.args[0]!r}, "
            f"status_code={self.status_code}, url={self.url!r})"
        )


class NeuRISNotFoundError(NeuRISAPIError):
    """Raised on HTTP 404."""


class NeuRISForbiddenError(NeuRISAPIError):
    """Raised on HTTP 403."""


class NeuRISValidationError(NeuRISAPIError):
    """Raised on HTTP 422."""


class NeuRISRateLimitError(NeuRISAPIError):
    """Raised on HTTP 429. Includes Retry-After header value when available."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        url: str,
        body: str,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, url=url, body=body)
        self.retry_after = retry_after


class NeuRISServerError(NeuRISAPIError):
    """Raised on HTTP 5xx."""


class NeuRISServiceUnavailableError(NeuRISServerError):
    """Raised on HTTP 503 Service Unavailable.

    The NeuRIS API uses 503 (not 429) when the rate limit of
    600 requests per minute is exceeded.  This error may therefore
    indicate either a genuine outage or a rate-limit breach.
    Inspect ``likely_rate_limited`` or the ``body`` attribute to
    distinguish the two cases.
    """

    _RATE_LIMIT_HINTS: frozenset[str] = frozenset(
        {"rate", "limit", "throttl", "too many", "quota"}
    )

    @property
    def likely_rate_limited(self) -> bool:
        """True when the response body contains rate-limit language."""
        body_lower = self.body.lower()
        return any(hint in body_lower for hint in self._RATE_LIMIT_HINTS)


class NeuRISConnectionError(NeuRISError):
    """Raised when a network connection cannot be established."""


class NeuRISTimeoutError(NeuRISError):
    """Raised when a request times out."""


class NeuRISTransportError(NeuRISError):
    """Raised by transport stubs that are not yet operational (e.g. ProductionTransport)."""
