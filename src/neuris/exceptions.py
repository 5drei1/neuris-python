from __future__ import annotations


class NeuRISError(Exception):
    """Base exception for all NeuRIS client errors."""


class NeuRISAPIError(NeuRISError):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, *, status_code: int, url: str, body: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body = body

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.args[0]!r}, "
            f"status_code={self.status_code}, url={self.url!r})"
        )


class NeuRISNotFoundError(NeuRISAPIError):
    """Raised on HTTP 404."""


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


class NeuRISConnectionError(NeuRISError):
    """Raised when a network connection cannot be established."""


class NeuRISTimeoutError(NeuRISError):
    """Raised when a request times out."""


class NeuRISTransportError(NeuRISError):
    """Raised by transport stubs that are not yet operational (e.g. ProductionTransport)."""
