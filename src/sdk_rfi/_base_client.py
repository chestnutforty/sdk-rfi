"""HTTP client infrastructure for sdk-rfi.

All requests are dispatched through the ChestnutForty middleware enclave,
which handles authentication (OAuth2 token management), rate limiting,
and observability.
"""

from __future__ import annotations

import base64
import json
import os
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import httpx

from chestnutforty_middleware import (
    DispatchErrorCode,
    HttpMethod,
    HttpRequest,
    HttpResponse,
    ServiceRequest,
    ServiceResponse,
)
from chestnutforty_middleware._signing import sign_request

from ._exceptions import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
    SDKError,
    STATUS_CODE_TO_EXCEPTION,
)

if TYPE_CHECKING:
    from ._types import QueryParams

__all__ = ["BaseClient", "AsyncBaseClient"]

DEFAULT_BASE_URL = "https://www.randforecastinginitiative.org"
DEFAULT_TIMEOUT = 60.0
SERVICE_NAME = "rfi"

# Custom headers that the downstream RFI API expects
_SDK_HEADERS: dict[str, str] = {
    "Accept": "application/json",
    "User-Agent": "sdk-rfi/0.1.0",
}


def _read_enclave_config() -> tuple[str, bytes, str]:
    """Read enclave config from environment variables.

    Returns:
        (dispatch_url, auth_secret, default_client_id)
    """
    enclave_url = os.environ.get("ENCLAVE_URL")
    if not enclave_url:
        raise RuntimeError(
            "ENCLAVE_URL environment variable is required. "
            "Set it to the middleware enclave URL."
        )

    secret_b64 = os.environ.get("MIDDLEWARE_AUTH_SECRET", "")
    if not secret_b64:
        raise RuntimeError(
            "MIDDLEWARE_AUTH_SECRET environment variable is required. "
            "Set it to the base64-encoded HMAC secret."
        )

    dispatch_url = enclave_url.rstrip("/") + "/dispatch"
    auth_secret = base64.b64decode(secret_b64)
    default_client_id = os.environ.get("MIDDLEWARE_CLIENT_ID", "")

    return dispatch_url, auth_secret, default_client_id


class BaseClient:
    """Synchronous HTTP client for the RFI API.

    Routes all requests through the ChestnutForty middleware enclave.
    The enclave handles OAuth2 authentication, rate limiting, and logging.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._dispatch_url, self._auth_secret, self._default_client_id = (
            _read_enclave_config()
        )
        self._http = httpx.Client(timeout=timeout)

    def _build_params(self, params: QueryParams | None) -> dict[str, Any]:
        """Build query parameters. No credentials -- enclave injects them."""
        base_params: dict[str, Any] = {}
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            base_params.update(filtered)
        return base_params

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Make a request through the middleware enclave."""
        url = f"{self.base_url}{path}"
        full_params = self._build_params(params)

        # Build full endpoint URL with query string
        if full_params:
            endpoint = f"{url}?{urlencode(full_params)}"
        else:
            endpoint = url

        tool_name = path.strip("/").replace("/", "-")
        client_id = self._default_client_id or f"rfi-{tool_name}"

        # Merge SDK default headers with any per-request overrides
        request_headers = dict(_SDK_HEADERS)
        if headers:
            request_headers.update(headers)

        http_request = HttpRequest(
            method=HttpMethod(method),
            endpoint=endpoint,
            headers=request_headers,
            timeout_ms=int(self.timeout * 1000),
        )
        if json_body is not None:
            http_request.body = json_body

        service_req = ServiceRequest(
            service=SERVICE_NAME,
            request=http_request,
            app_name="rfi-sdk",
            tool_name=tool_name,
        )

        service_resp = self._dispatch(service_req, client_id)
        return self._handle_response(service_resp)

    def _dispatch(self, request: ServiceRequest, client_id: str) -> ServiceResponse:
        """Send a signed request to the enclave."""
        body_bytes = json.dumps(
            request.model_dump(mode="json"), separators=(",", ":")
        ).encode()

        headers = {"Content-Type": "application/json"}
        headers.update(sign_request(body_bytes, self._auth_secret, client_id))

        try:
            resp = self._http.post(
                self._dispatch_url, content=body_bytes, headers=headers
            )
        except httpx.TimeoutException:
            raise APITimeoutError("Enclave request timed out")
        except httpx.ConnectError:
            raise APIConnectionError("Cannot reach enclave")

        return self._parse_enclave_response(resp)

    @staticmethod
    def _parse_enclave_response(resp: httpx.Response) -> ServiceResponse:
        """Parse the raw HTTP response from the enclave into a ServiceResponse."""
        if resp.status_code == 401:
            raise AuthenticationError(
                "Enclave authentication failed", status_code=401
            )
        if resp.status_code >= 500:
            raise InternalServerError(
                f"Enclave returned {resp.status_code}", status_code=resp.status_code
            )

        try:
            return ServiceResponse.model_validate(resp.json())
        except Exception as exc:
            raise SDKError(f"Failed to parse enclave response: {exc}") from exc

    def _handle_response(self, sr: ServiceResponse) -> Any:
        """Convert a ServiceResponse into a return value or raise an exception."""
        if not sr.success:
            assert sr.error is not None
            _raise_dispatch_error(sr.error.code, sr.error.message)

        assert sr.response is not None
        if sr.response.status >= 400:
            _raise_http_error(sr.response.status, sr.response.body)

        return sr.response.body

    def get(self, path: str, *, params: QueryParams | None = None, headers: dict[str, str] | None = None) -> Any:
        """Make a GET request."""
        return self._request("GET", path, params=params, headers=headers)

    def post(self, path: str, *, json: Any | None = None, params: QueryParams | None = None, headers: dict[str, str] | None = None) -> Any:
        """Make a POST request."""
        return self._request("POST", path, json_body=json, params=params, headers=headers)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> BaseClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncBaseClient:
    """Asynchronous HTTP client for the RFI API.

    Routes all requests through the ChestnutForty middleware enclave.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._dispatch_url, self._auth_secret, self._default_client_id = (
            _read_enclave_config()
        )
        self._http = httpx.AsyncClient(timeout=timeout)

    def _build_params(self, params: QueryParams | None) -> dict[str, Any]:
        """Build query parameters. No credentials -- enclave injects them."""
        base_params: dict[str, Any] = {}
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            base_params.update(filtered)
        return base_params

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Make an async request through the middleware enclave."""
        url = f"{self.base_url}{path}"
        full_params = self._build_params(params)

        if full_params:
            endpoint = f"{url}?{urlencode(full_params)}"
        else:
            endpoint = url

        tool_name = path.strip("/").replace("/", "-")
        client_id = self._default_client_id or f"rfi-{tool_name}"

        # Merge SDK default headers with any per-request overrides
        request_headers = dict(_SDK_HEADERS)
        if headers:
            request_headers.update(headers)

        http_request = HttpRequest(
            method=HttpMethod(method),
            endpoint=endpoint,
            headers=request_headers,
            timeout_ms=int(self.timeout * 1000),
        )
        if json_body is not None:
            http_request.body = json_body

        service_req = ServiceRequest(
            service=SERVICE_NAME,
            request=http_request,
            app_name="rfi-sdk",
            tool_name=tool_name,
        )

        service_resp = await self._dispatch(service_req, client_id)
        return self._handle_response(service_resp)

    async def _dispatch(
        self, request: ServiceRequest, client_id: str
    ) -> ServiceResponse:
        """Send a signed request to the enclave (async)."""
        body_bytes = json.dumps(
            request.model_dump(mode="json"), separators=(",", ":")
        ).encode()

        headers = {"Content-Type": "application/json"}
        headers.update(sign_request(body_bytes, self._auth_secret, client_id))

        try:
            resp = await self._http.post(
                self._dispatch_url, content=body_bytes, headers=headers
            )
        except httpx.TimeoutException:
            raise APITimeoutError("Enclave request timed out")
        except httpx.ConnectError:
            raise APIConnectionError("Cannot reach enclave")

        return BaseClient._parse_enclave_response(resp)

    def _handle_response(self, sr: ServiceResponse) -> Any:
        """Convert a ServiceResponse into a return value or raise an exception."""
        if not sr.success:
            assert sr.error is not None
            _raise_dispatch_error(sr.error.code, sr.error.message)

        assert sr.response is not None
        if sr.response.status >= 400:
            _raise_http_error(sr.response.status, sr.response.body)

        return sr.response.body

    async def get(self, path: str, *, params: QueryParams | None = None, headers: dict[str, str] | None = None) -> Any:
        """Make an async GET request."""
        return await self._request("GET", path, params=params, headers=headers)

    async def post(self, path: str, *, json: Any | None = None, params: QueryParams | None = None, headers: dict[str, str] | None = None) -> Any:
        """Make an async POST request."""
        return await self._request("POST", path, json_body=json, params=params, headers=headers)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncBaseClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


# ---------------------------------------------------------------------------
# Shared error helpers
# ---------------------------------------------------------------------------


def _raise_dispatch_error(code: DispatchErrorCode, message: str) -> None:
    """Map a middleware DispatchErrorCode to an SDK exception."""
    if code == DispatchErrorCode.RATE_LIMITED:
        raise RateLimitError(message, status_code=429)
    if code == DispatchErrorCode.DOWNSTREAM_TIMEOUT:
        raise APITimeoutError(message)
    if code in (
        DispatchErrorCode.DOWNSTREAM_UNREACHABLE,
        DispatchErrorCode.ENCLAVE_UNAVAILABLE,
    ):
        raise APIConnectionError(message)
    if code == DispatchErrorCode.AUTH_FAILED:
        raise AuthenticationError(message, status_code=401)
    if code == DispatchErrorCode.SERVICE_NOT_FOUND:
        raise SDKError(f"Service not found: {message}")
    raise SDKError(message)


def _raise_http_error(status_code: int, body: Any) -> None:
    """Map an HTTP status code to an SDK exception."""
    message = f"HTTP {status_code}"
    if isinstance(body, dict) and "error" in body:
        message = body["error"]
    elif isinstance(body, dict) and "error_message" in body:
        message = body["error_message"]

    exc_class = STATUS_CODE_TO_EXCEPTION.get(status_code, InternalServerError)
    raise exc_class(message, status_code=status_code, body=body)
