"""Types for RFI Prediction Sets (forecasts) API."""

from __future__ import annotations

from datetime import datetime

from .._models import BaseModel

__all__ = [
    "Prediction",
    "PredictionSet",
    "PredictionSetList",
]


class Prediction(BaseModel):
    """A single prediction within a prediction set.

    Each prediction corresponds to one answer of a question and contains
    the forecasted probability.
    """

    id: int
    type: str | None = None
    answer_id: int
    membership_id: int | None = None
    forecasted_probability: float
    starting_probability: float | None = None
    final_probability: float | None = None
    filled_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    made_after_correctness_known: bool | None = None
    confidence_level: int | None = None
    answer_name: str | None = None


class PredictionSet(BaseModel):
    """A set of predictions (forecast) made by a user.

    A prediction set contains one or more predictions for a question's
    answers, along with an optional rationale.
    """

    id: int
    type: str | None = None
    membership_id: int | None = None
    question_id: int | None = None
    discover_question_id: int | None = None
    rationale: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    comment_id: int | None = None
    question_name: str | None = None
    membership_username: str | None = None
    membership_avatar_url: str | None = None
    predictions: list[Prediction] | None = None


class PredictionSetList(BaseModel):
    """A paginated list of prediction sets."""

    prediction_sets: list[PredictionSet]
    page: int = 1
    has_more: bool = False
