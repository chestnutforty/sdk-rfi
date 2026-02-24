"""RFI SDK Client.

Provides access to the RAND Forecasting Initiative (RFI) API,
powered by the Cultivate Labs forecasting platform.

All requests are routed through the ChestnutForty middleware enclave,
which handles OAuth2 authentication, rate limiting, and observability.

Example usage:
    from sdk_rfi import Client

    client = Client()
    questions = client.questions.list()
    question = client.questions.get(1234)
    forecasts = client.prediction_sets.list(question_id=1234)
"""

from __future__ import annotations

from functools import cached_property
from typing import Any

from ._base_client import BaseClient, AsyncBaseClient, DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from .resources.questions import Questions, AsyncQuestions
from .resources.prediction_sets import PredictionSets, AsyncPredictionSets
from .resources.comments import Comments, AsyncComments

__all__ = ["Client", "AsyncClient"]


class Client:
    """Synchronous client for the RFI API.

    All requests are routed through the ChestnutForty middleware enclave.
    The enclave handles OAuth2 token management, rate limits, and logging.

    Required environment variables:
        ENCLAVE_URL: URL of the middleware enclave
        MIDDLEWARE_AUTH_SECRET: Base64-encoded HMAC secret

    Optional environment variables:
        MIDDLEWARE_CLIENT_ID: Client identifier for logging (defaults to rfi-{tool_name})

    Usage:
        client = Client()

        # List active questions
        questions = client.questions.list()

        # Get a specific question
        question = client.questions.get(1234)

        # Get forecasts for a question
        forecasts = client.prediction_sets.list(question_id=1234)
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._base_client = BaseClient(
            base_url=base_url,
            timeout=timeout,
        )

    @cached_property
    def questions(self) -> Questions:
        """Access the Questions resource."""
        return Questions(self)

    @cached_property
    def prediction_sets(self) -> PredictionSets:
        """Access the Prediction Sets resource."""
        return PredictionSets(self)

    @cached_property
    def comments(self) -> Comments:
        """Access the Comments resource."""
        return Comments(self)

    # Delegate HTTP methods to BaseClient so resource classes can call
    # self._client.get(...) and self._client.post(...) unchanged.

    def get(self, path: str, *, params: Any = None, headers: dict[str, str] | None = None) -> Any:
        """Make a GET request via the middleware enclave."""
        return self._base_client.get(path, params=params, headers=headers)

    def post(self, path: str, *, json: Any = None, params: Any = None, headers: dict[str, str] | None = None) -> Any:
        """Make a POST request via the middleware enclave."""
        return self._base_client.post(path, json=json, params=params, headers=headers)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._base_client.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncClient:
    """Asynchronous client for the RFI API.

    All requests are routed through the ChestnutForty middleware enclave.
    The enclave handles OAuth2 token management, rate limits, and logging.

    Usage:
        async with AsyncClient() as client:
            questions = await client.questions.list()
            question = await client.questions.get(1234)
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._base_client = AsyncBaseClient(
            base_url=base_url,
            timeout=timeout,
        )

    @cached_property
    def questions(self) -> AsyncQuestions:
        """Access the Questions resource."""
        return AsyncQuestions(self)

    @cached_property
    def prediction_sets(self) -> AsyncPredictionSets:
        """Access the Prediction Sets resource."""
        return AsyncPredictionSets(self)

    @cached_property
    def comments(self) -> AsyncComments:
        """Access the Comments resource."""
        return AsyncComments(self)

    # Delegate HTTP methods to AsyncBaseClient

    async def get(self, path: str, *, params: Any = None, headers: dict[str, str] | None = None) -> Any:
        """Make an async GET request via the middleware enclave."""
        return await self._base_client.get(path, params=params, headers=headers)

    async def post(self, path: str, *, json: Any = None, params: Any = None, headers: dict[str, str] | None = None) -> Any:
        """Make an async POST request via the middleware enclave."""
        return await self._base_client.post(path, json=json, params=params, headers=headers)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._base_client.close()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
