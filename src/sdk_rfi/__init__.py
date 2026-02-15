"""RFI SDK - Python SDK for the RAND Forecasting Initiative API.

Usage:
    from sdk_rfi import Client

    client = Client()  # Uses RFI_EMAIL and RFI_PASSWORD env vars
    questions = client.questions.list()
    question = client.questions.get(1234)
"""

from . import types
from ._client import Client, AsyncClient
from ._version import __title__, __version__
from ._exceptions import (
    SDKError,
    APIError,
    APIStatusError,
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    InternalServerError,
)
from .types import (
    Answer,
    Clarification,
    Question,
    QuestionList,
    Prediction,
    PredictionSet,
    PredictionSetList,
    Comment,
    CommentList,
)

__all__ = [
    "Client",
    "AsyncClient",
    "types",
    "Answer",
    "Clarification",
    "Question",
    "QuestionList",
    "Prediction",
    "PredictionSet",
    "PredictionSetList",
    "Comment",
    "CommentList",
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
    "__version__",
    "__title__",
]
