"""Tests for the RFI SDK client initialization and middleware integration."""

from __future__ import annotations

import pytest

from sdk_rfi import Client, AsyncClient, SDKError, NotFoundError, RateLimitError, AuthenticationError
from tests.conftest import DispatchRecorder, AsyncDispatchRecorder, env_override


class TestClientInit:
    """Test client initialization."""

    def test_init_default(self) -> None:
        """Client initializes with default settings."""
        client = Client()
        assert client._base_client.base_url == "https://www.randforecastinginitiative.org"
        assert client._base_client.timeout == 60.0
        client.close()

    def test_init_custom_base_url(self) -> None:
        """Client accepts custom base URL."""
        client = Client(base_url="https://custom.example.com")
        assert client._base_client.base_url == "https://custom.example.com"
        client.close()

    def test_init_custom_timeout(self) -> None:
        """Client accepts custom timeout."""
        client = Client(timeout=120.0)
        assert client._base_client.timeout == 120.0
        client.close()

    def test_init_missing_enclave_url(self) -> None:
        """Client raises if ENCLAVE_URL is not set."""
        with env_override(ENCLAVE_URL=None):
            with pytest.raises(RuntimeError, match="ENCLAVE_URL"):
                Client()

    def test_init_missing_auth_secret(self) -> None:
        """Client raises if MIDDLEWARE_AUTH_SECRET is not set."""
        with env_override(MIDDLEWARE_AUTH_SECRET=None):
            with pytest.raises(RuntimeError, match="MIDDLEWARE_AUTH_SECRET"):
                Client()

    def test_context_manager(self) -> None:
        """Client works as a context manager."""
        with Client() as client:
            assert client._base_client is not None


class TestAsyncClientInit:
    """Test async client initialization."""

    def test_init_default(self) -> None:
        """AsyncClient initializes with default settings."""
        client = AsyncClient()
        assert client._base_client.base_url == "https://www.randforecastinginitiative.org"
        assert client._base_client.timeout == 60.0

    def test_init_missing_enclave_url(self) -> None:
        """AsyncClient raises if ENCLAVE_URL is not set."""
        with env_override(ENCLAVE_URL=None):
            with pytest.raises(RuntimeError, match="ENCLAVE_URL"):
                AsyncClient()


class TestServiceRequestMetadata:
    """Test that service requests have correct metadata."""

    def test_service_request_metadata(self, client: Client, mock_questions_data: list) -> None:
        """Service request includes correct service name and app name."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        client.questions.list()

        req = recorder.last_request
        assert req.service == "rfi"
        assert req.app_name == "rfi-sdk"
        assert req.request.method.value == "GET"

    def test_client_id_defaults_to_service_tool(self, client: Client, mock_questions_data: list) -> None:
        """Client ID defaults to rfi-{tool_name} when MIDDLEWARE_CLIENT_ID is unset."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._default_client_id = ""
        client._base_client._dispatch = recorder

        client.questions.list()

        assert recorder.last_client_id == "rfi-api-v1-questions"

    def test_custom_headers_forwarded(self, client: Client, mock_questions_data: list) -> None:
        """SDK headers (Accept, User-Agent) are forwarded via HttpRequest.headers."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        client.questions.list()

        req = recorder.last_request
        assert req.request.headers is not None
        assert req.request.headers.get("Accept") == "application/json"
        assert req.request.headers.get("User-Agent") == "sdk-rfi/0.1.0"

    def test_endpoint_includes_params(self, client: Client, mock_questions_data: list) -> None:
        """Query parameters are encoded into the endpoint URL."""
        recorder = DispatchRecorder(body=mock_questions_data)
        client._base_client._dispatch = recorder

        client.questions.list(status="closed", page=2)

        endpoint = recorder.last_endpoint
        assert "status=closed" in endpoint
        assert "page=2" in endpoint


class TestDispatchErrors:
    """Test middleware dispatch error handling."""

    def test_rate_limit_error(self, client: Client) -> None:
        """RATE_LIMITED dispatch error maps to RateLimitError."""
        recorder = DispatchRecorder(
            error_code="RATE_LIMITED",
            error_message="rate limit exceeded for service rfi",
        )
        client._base_client._dispatch = recorder

        with pytest.raises(RateLimitError):
            client.questions.list()

    def test_auth_failed_error(self, client: Client) -> None:
        """AUTH_FAILED dispatch error maps to AuthenticationError."""
        recorder = DispatchRecorder(
            error_code="AUTH_FAILED",
            error_message="authentication failed",
        )
        client._base_client._dispatch = recorder

        with pytest.raises(AuthenticationError):
            client.questions.list()

    def test_service_not_found_error(self, client: Client) -> None:
        """SERVICE_NOT_FOUND dispatch error maps to SDKError."""
        recorder = DispatchRecorder(
            error_code="SERVICE_NOT_FOUND",
            error_message="rfi not registered",
        )
        client._base_client._dispatch = recorder

        with pytest.raises(SDKError, match="Service not found"):
            client.questions.list()


class TestHTTPErrors:
    """Test HTTP status code error handling."""

    def test_not_found_error(self, client: Client) -> None:
        """HTTP 404 raises NotFoundError."""
        recorder = DispatchRecorder(
            body={"error": "Question not found"},
            status=404,
        )
        client._base_client._dispatch = recorder

        with pytest.raises(NotFoundError) as exc_info:
            client.questions.get(99999)

        assert exc_info.value.status_code == 404

    def test_bad_request_error(self, client: Client) -> None:
        """HTTP 400 raises BadRequestError."""
        from sdk_rfi import BadRequestError

        recorder = DispatchRecorder(
            body={"error": "Invalid parameters"},
            status=400,
        )
        client._base_client._dispatch = recorder

        with pytest.raises(BadRequestError) as exc_info:
            client.questions.list()

        assert exc_info.value.status_code == 400

    def test_internal_server_error(self, client: Client) -> None:
        """HTTP 500 raises InternalServerError."""
        from sdk_rfi import InternalServerError

        recorder = DispatchRecorder(
            body={"error": "Internal server error"},
            status=500,
        )
        client._base_client._dispatch = recorder

        with pytest.raises(InternalServerError) as exc_info:
            client.questions.list()

        assert exc_info.value.status_code == 500
