"""Exception hierarchy for the SDK."""

from __future__ import annotations


__all__ = [
    "SDKError",
    "APIError",
    "APIStatusError",
    "APIConnectionError",
    "APITimeoutError",
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "InternalServerError",
    "STATUS_CODE_TO_EXCEPTION",
]


class SDKError(Exception):
    """Base exception for all SDK errors."""


class APIError(SDKError):
    """Base class for all API-related errors."""

    message: str
    body: object | None

    def __init__(
        self,
        message: str,
        body: object | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.body = body

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


class APIStatusError(APIError):
    """Raised when the API returns a 4xx or 5xx status code."""

    status_code: int

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: object | None = None,
    ) -> None:
        super().__init__(message, body)
        self.status_code = status_code


class BadRequestError(APIStatusError):
    """HTTP 400."""


class AuthenticationError(APIStatusError):
    """HTTP 401."""


class PermissionDeniedError(APIStatusError):
    """HTTP 403."""


class NotFoundError(APIStatusError):
    """HTTP 404."""


class ConflictError(APIStatusError):
    """HTTP 409."""


class RateLimitError(APIStatusError):
    """HTTP 429."""


class InternalServerError(APIStatusError):
    """HTTP 500+."""


class APIConnectionError(APIError):
    """Raised when a connection to the API cannot be established."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class APITimeoutError(APIError):
    """Raised when an API request times out."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


STATUS_CODE_TO_EXCEPTION: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
}
