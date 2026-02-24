"""Pytest configuration and fixtures for sdk-rfi tests."""

from __future__ import annotations

import base64
import contextlib
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from chestnutforty_middleware import HttpResponse, ServiceRequest, ServiceResponse
from sdk_rfi import AsyncClient, Client

# Load environment variables: shared .env first, then local .env as override
_shared_env = Path(__file__).resolve().parents[2] / ".env"  # ../../.env (chestnutforty/.env)
_local_env = Path(__file__).resolve().parent.parent / ".env"  # sdk-rfi/.env

if _shared_env.exists():
    from dotenv import load_dotenv

    load_dotenv(_shared_env)
if _local_env.exists():
    from dotenv import load_dotenv

    load_dotenv(_local_env, override=True)

# Expand ~ in file paths (dotenv loads them literally)
for _var in ("GOOGLE_APPLICATION_CREDENTIALS",):
    _val = os.environ.get(_var, "")
    if _val and "~" in _val:
        os.environ[_var] = str(Path(_val).expanduser())

# Ensure middleware env vars have fallback values for unit tests
if not os.environ.get("ENCLAVE_URL"):
    os.environ["ENCLAVE_URL"] = "https://test-enclave.example.com"
if not os.environ.get("MIDDLEWARE_AUTH_SECRET"):
    os.environ["MIDDLEWARE_AUTH_SECRET"] = base64.b64encode(
        b"test-secret-key-32-bytes-long!!"
    ).decode()


# ---------------------------------------------------------------------------
# Mock dispatch helpers
# ---------------------------------------------------------------------------


class DispatchRecorder:
    """Captures dispatch calls and returns a canned ServiceResponse.

    Usage:
        recorder = DispatchRecorder(body=mock_data)
        client._base_client._dispatch = recorder

        client.questions.list()

        req = recorder.last_request
        assert "created_before" in req.request.endpoint
    """

    def __init__(
        self,
        body: Any = None,
        *,
        status: int = 200,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        if error_code is not None:
            from chestnutforty_middleware import DispatchErrorCode

            self._response = ServiceResponse.fail(
                DispatchErrorCode(error_code), error_message or "error"
            )
        else:
            self._response = ServiceResponse.ok(
                HttpResponse(status=status, body=body)
            )
        self.calls: list[tuple[ServiceRequest, str]] = []

    def __call__(self, request: ServiceRequest, client_id: str) -> ServiceResponse:
        self.calls.append((request, client_id))
        return self._response

    @property
    def called(self) -> bool:
        return len(self.calls) > 0

    @property
    def last_request(self) -> ServiceRequest:
        return self.calls[-1][0]

    @property
    def last_endpoint(self) -> str:
        return self.last_request.request.endpoint

    @property
    def last_client_id(self) -> str:
        return self.calls[-1][1]


class AsyncDispatchRecorder(DispatchRecorder):
    """Async version of DispatchRecorder."""

    async def __call__(  # type: ignore[override]
        self, request: ServiceRequest, client_id: str
    ) -> ServiceResponse:
        self.calls.append((request, client_id))
        return self._response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> Iterator[Client]:
    """Create a synchronous client with mocked dispatch."""
    with Client() as c:
        yield c


@pytest.fixture
async def async_client() -> Iterator[AsyncClient]:
    """Create an asynchronous client with mocked dispatch."""
    async with AsyncClient() as c:
        yield c


# ---------------------------------------------------------------------------
# Mock data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_questions_data() -> list[dict[str, Any]]:
    """Mock questions list response (list format)."""
    return [
        {
            "id": 1001,
            "name": "Will X happen by 2026?",
            "description": "Detailed description of the question.",
            "type": "Forecast::Question::Binary",
            "ends_at": "2026-12-31T23:59:59.000Z",
            "published_at": "2025-01-15T12:00:00.000Z",
            "created_at": "2025-01-10T08:00:00.000Z",
            "updated_at": "2025-02-01T10:00:00.000Z",
            "resolved_at": None,
            "voided_at": None,
            "active": True,
            "scoring_start_time": "2025-01-15T12:00:00.000Z",
            "scoring_end_time": "2026-12-31T23:59:59.000Z",
            "use_ordinal_scoring": False,
            "answers": [
                {
                    "id": 2001,
                    "name": "Yes",
                    "probability": 0.65,
                    "sort_order": 0,
                    "created_at": "2025-01-10T08:00:00.000Z",
                    "updated_at": "2025-02-01T10:00:00.000Z",
                    "resolved_at": None,
                },
                {
                    "id": 2002,
                    "name": "No",
                    "probability": 0.35,
                    "sort_order": 1,
                    "created_at": "2025-01-10T08:00:00.000Z",
                    "updated_at": "2025-02-01T10:00:00.000Z",
                    "resolved_at": None,
                },
            ],
            "clarifications": [],
        },
    ]


@pytest.fixture
def mock_question_data() -> dict[str, Any]:
    """Mock single question response."""
    return {
        "id": 1001,
        "name": "Will X happen by 2026?",
        "description": "Detailed description of the question.",
        "type": "Forecast::Question::Binary",
        "ends_at": "2026-12-31T23:59:59.000Z",
        "published_at": "2025-01-15T12:00:00.000Z",
        "created_at": "2025-01-10T08:00:00.000Z",
        "updated_at": "2025-02-01T10:00:00.000Z",
        "resolved_at": None,
        "voided_at": None,
        "active": True,
        "scoring_start_time": "2025-01-15T12:00:00.000Z",
        "scoring_end_time": "2026-12-31T23:59:59.000Z",
        "use_ordinal_scoring": False,
        "answers": [
            {
                "id": 2001,
                "name": "Yes",
                "probability": 0.65,
                "sort_order": 0,
                "created_at": "2025-01-10T08:00:00.000Z",
                "updated_at": "2025-02-01T10:00:00.000Z",
                "resolved_at": None,
            },
            {
                "id": 2002,
                "name": "No",
                "probability": 0.35,
                "sort_order": 1,
                "created_at": "2025-01-10T08:00:00.000Z",
                "updated_at": "2025-02-01T10:00:00.000Z",
                "resolved_at": None,
            },
        ],
        "clarifications": [],
    }


@pytest.fixture
def mock_prediction_sets_data() -> list[dict[str, Any]]:
    """Mock prediction sets list response (list format)."""
    return [
        {
            "id": 5001,
            "membership_id": 100,
            "membership_username": "forecaster1",
            "question_id": 1001,
            "created_at": "2025-02-01T14:30:00.000Z",
            "updated_at": "2025-02-01T14:30:00.000Z",
            "comment": "I think this is likely.",
            "predictions": [
                {
                    "id": 6001,
                    "answer_id": 2001,
                    "membership_id": 100,
                    "filled_at": "2025-02-01T14:30:00.000Z",
                    "created_at": "2025-02-01T14:30:00.000Z",
                    "updated_at": "2025-02-01T14:30:00.000Z",
                    "forecasted_probability": 0.72,
                    "starting_probability": 0.65,
                    "final_probability": 0.72,
                },
            ],
        },
    ]


@pytest.fixture
def mock_comments_data() -> list[dict[str, Any]]:
    """Mock comments list response (list format)."""
    return [
        {
            "id": 8001,
            "content": "This is an interesting question.",
            "commentable_id": 1001,
            "commentable_type": "Forecast::Question",
            "membership_id": 100,
            "membership_username": "forecaster1",
            "created_at": "2025-02-05T09:00:00.000Z",
            "updated_at": "2025-02-05T09:00:00.000Z",
        },
    ]


@contextlib.contextmanager
def env_override(**env_vars: str | None) -> Iterator[None]:
    """Temporarily override environment variables."""
    original = {}
    for key, value in env_vars.items():
        original[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
