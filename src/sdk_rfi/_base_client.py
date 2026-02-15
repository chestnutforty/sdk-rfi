"""Base HTTP client with OAuth2 authentication for Cultivate Labs API."""

from __future__ import annotations

import os
import threading
import time

import httpx
from typing import Any

from ._types import Headers, QueryParams, Timeout
from ._exceptions import (
    APIStatusError,
    APITimeoutError,
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    InternalServerError,
    SDKError,
)

__all__ = ["BaseClient", "AsyncBaseClient"]

DEFAULT_TIMEOUT = 60.0

STATUS_CODE_TO_EXCEPTION: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
}

# Token refresh buffer: refresh 5 minutes before expiry
TOKEN_REFRESH_BUFFER_SECONDS = 300


class _TokenManager:
    """Thread-safe OAuth2 token manager.

    Handles token acquisition and auto-refresh for the Cultivate Labs API.
    """

    def __init__(self, base_url: str, email: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._password = password
        self._access_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        with self._lock:
            if self._access_token and time.time() < self._expires_at:
                return self._access_token
            return self._refresh_token()

    def _refresh_token(self) -> str:
        """Acquire a new OAuth token."""
        response = httpx.post(
            f"{self._base_url}/oauth/token",
            data={
                "grant_type": "password",
                "email": self._email,
                "password": self._password,
            },
            timeout=30.0,
        )
        if not response.is_success:
            raise SDKError(
                f"Failed to authenticate with RFI: {response.status_code} - {response.text[:200]}"
            )

        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 7200)
        self._expires_at = time.time() + expires_in - TOKEN_REFRESH_BUFFER_SECONDS
        return self._access_token


class BaseClient:
    """Synchronous base client with OAuth2 authentication."""

    def __init__(
        self,
        *,
        base_url: str,
        email: str | None = None,
        password: str | None = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        headers: Headers | None = None,
        proxy: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._custom_headers = headers or {}

        # Resolve credentials
        resolved_email = email or os.environ.get("RFI_EMAIL", "")
        resolved_password = password or os.environ.get("RFI_PASSWORD", "")
        if not resolved_email or not resolved_password:
            raise SDKError(
                "RFI credentials required. Set RFI_EMAIL and RFI_PASSWORD environment variables "
                "or pass email/password to Client()."
            )

        self._token_manager = _TokenManager(self.base_url, resolved_email, resolved_password)

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._build_default_headers(),
            proxy=proxy,
        )

    def _build_default_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "sdk-rfi/0.1.0",
        }
        headers.update(self._custom_headers)
        return headers

    def _get_auth_headers(self) -> dict[str, str]:
        token = self._token_manager.get_token()
        return {"Authorization": f"Bearer {token}"}

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            return response.text

        try:
            body = response.json()
            message = body.get("error", response.text) if isinstance(body, dict) else response.text
        except Exception:
            body = None
            message = response.text

        status_code = response.status_code
        exception_class = STATUS_CODE_TO_EXCEPTION.get(status_code)

        if exception_class:
            raise exception_class(message, response=response, body=body)
        elif status_code >= 500:
            raise InternalServerError(message, response=response, body=body)
        else:
            raise APIStatusError(message, response=response, body=body)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        json: Any | None = None,
        headers: Headers | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        # Merge auth headers
        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=request_headers,
            )
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise APITimeoutError(e.request) from e
        except httpx.ConnectError as e:
            raise APIConnectionError(request=e.request) from e

    def get(self, path: str, *, params: QueryParams | None = None, headers: Headers | None = None) -> Any:
        return self._request("GET", path, params=params, headers=headers)

    def post(self, path: str, *, json: Any | None = None, params: QueryParams | None = None, headers: Headers | None = None) -> Any:
        return self._request("POST", path, json=json, params=params, headers=headers)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BaseClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncBaseClient:
    """Asynchronous base client with OAuth2 authentication."""

    def __init__(
        self,
        *,
        base_url: str,
        email: str | None = None,
        password: str | None = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        headers: Headers | None = None,
        proxy: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._custom_headers = headers or {}

        resolved_email = email or os.environ.get("RFI_EMAIL", "")
        resolved_password = password or os.environ.get("RFI_PASSWORD", "")
        if not resolved_email or not resolved_password:
            raise SDKError(
                "RFI credentials required. Set RFI_EMAIL and RFI_PASSWORD environment variables "
                "or pass email/password to AsyncClient()."
            )

        # Reuse sync token manager (thread-safe, works in async context)
        self._token_manager = _TokenManager(self.base_url, resolved_email, resolved_password)

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._build_default_headers(),
            proxy=proxy,
        )

    def _build_default_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "sdk-rfi/0.1.0",
        }
        headers.update(self._custom_headers)
        return headers

    def _get_auth_headers(self) -> dict[str, str]:
        token = self._token_manager.get_token()
        return {"Authorization": f"Bearer {token}"}

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            return response.text

        try:
            body = response.json()
            message = body.get("error", response.text) if isinstance(body, dict) else response.text
        except Exception:
            body = None
            message = response.text

        status_code = response.status_code
        exception_class = STATUS_CODE_TO_EXCEPTION.get(status_code)

        if exception_class:
            raise exception_class(message, response=response, body=body)
        elif status_code >= 500:
            raise InternalServerError(message, response=response, body=body)
        else:
            raise APIStatusError(message, response=response, body=body)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        json: Any | None = None,
        headers: Headers | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)

        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=request_headers,
            )
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise APITimeoutError(e.request) from e
        except httpx.ConnectError as e:
            raise APIConnectionError(request=e.request) from e

    async def get(self, path: str, *, params: QueryParams | None = None, headers: Headers | None = None) -> Any:
        return await self._request("GET", path, params=params, headers=headers)

    async def post(self, path: str, *, json: Any | None = None, params: QueryParams | None = None, headers: Headers | None = None) -> Any:
        return await self._request("POST", path, json=json, params=params, headers=headers)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncBaseClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
