"""RFI SDK Client.

Provides access to the RAND Forecasting Initiative (RFI) API,
powered by the Cultivate Labs forecasting platform.

Example usage:
    from sdk_rfi import Client

    client = Client()  # Uses RFI_EMAIL and RFI_PASSWORD env vars
    questions = client.questions.list()
    question = client.questions.get(1234)
    forecasts = client.prediction_sets.list(question_id=1234)
"""

from __future__ import annotations

from functools import cached_property

from ._base_client import BaseClient, AsyncBaseClient, DEFAULT_TIMEOUT
from ._types import Headers, Timeout
from .resources.questions import Questions, AsyncQuestions
from .resources.prediction_sets import PredictionSets, AsyncPredictionSets
from .resources.comments import Comments, AsyncComments

__all__ = ["Client", "AsyncClient"]

DEFAULT_BASE_URL = "https://www.randforecastinginitiative.org"


class Client(BaseClient):
    """Synchronous client for the RFI API.

    Usage:
        # Using env vars (RFI_EMAIL, RFI_PASSWORD):
        client = Client()

        # Explicit credentials:
        client = Client(email="user@example.com", password="secret")

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
        base_url: str | None = None,
        email: str | None = None,
        password: str | None = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        headers: Headers | None = None,
        proxy: str | None = None,
    ) -> None:
        if base_url is None:
            base_url = DEFAULT_BASE_URL

        super().__init__(
            base_url=base_url,
            email=email,
            password=password,
            timeout=timeout,
            headers=headers,
            proxy=proxy,
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


class AsyncClient(AsyncBaseClient):
    """Asynchronous client for the RFI API.

    Usage:
        async with AsyncClient() as client:
            questions = await client.questions.list()
            question = await client.questions.get(1234)
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        email: str | None = None,
        password: str | None = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        headers: Headers | None = None,
        proxy: str | None = None,
    ) -> None:
        if base_url is None:
            base_url = DEFAULT_BASE_URL

        super().__init__(
            base_url=base_url,
            email=email,
            password=password,
            timeout=timeout,
            headers=headers,
            proxy=proxy,
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
