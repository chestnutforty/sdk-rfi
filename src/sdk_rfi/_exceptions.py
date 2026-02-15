"""Exception hierarchy for the SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

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
]


class SDKError(Exception):
    """Base exception for all SDK errors."""

    pass


class APIError(SDKError):
    """Base class for all API-related errors."""

    message: str
    request: httpx.Request
    body: object | None

    def __init__(
        self,
        message: str,
        request: httpx.Request,
        *,
        body: object | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.request = request
        self.body = body


class APIStatusError(APIError):
    """Raised when the API returns a 4xx or 5xx status code."""

    response: httpx.Response
    status_code: int

    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response,
        body: object | None = None,
    ) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class APIConnectionError(APIError):
    """Raised when a connection to the API cannot be established."""

    def __init__(
        self,
        *,
        message: str = "Connection error.",
        request: httpx.Request,
    ) -> None:
        super().__init__(message, request, body=None)


class APITimeoutError(APIConnectionError):
    """Raised when an API request times out."""

    def __init__(self, request: httpx.Request) -> None:
        super().__init__(message="Request timed out.", request=request)


class BadRequestError(APIStatusError):
    """HTTP 400."""

    status_code: int = 400


class AuthenticationError(APIStatusError):
    """HTTP 401."""

    status_code: int = 401


class PermissionDeniedError(APIStatusError):
    """HTTP 403."""

    status_code: int = 403


class NotFoundError(APIStatusError):
    """HTTP 404."""

    status_code: int = 404


class ConflictError(APIStatusError):
    """HTTP 409."""

    status_code: int = 409


class RateLimitError(APIStatusError):
    """HTTP 429."""

    status_code: int = 429


class InternalServerError(APIStatusError):
    """HTTP 500+."""

    status_code: int = 500
