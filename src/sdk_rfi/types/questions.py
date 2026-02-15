"""Types for RFI Questions API."""

from __future__ import annotations

from datetime import datetime

from .._models import BaseModel

__all__ = [
    "Clarification",
    "Answer",
    "Question",
    "QuestionList",
]


class Clarification(BaseModel):
    """A clarification attached to a question."""

    id: int
    question_id: int
    content: str
    created_at: datetime
    updated_at: datetime | None = None


class Answer(BaseModel):
    """An answer option for a question.

    For binary questions, there are typically two answers (Yes/No).
    For multi-choice questions, there can be many.
    """

    id: int
    question_id: int | None = None
    membership_id: int | None = None
    discover_answer_id: int | None = None
    name: str
    description: str | None = None
    active: bool | None = None
    binary: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    resolved_by_id: int | None = None
    correctness_known_at: datetime | None = None
    resolved: bool | None = None
    resolving: bool | None = None
    status: str | None = None
    ended: bool | None = None
    ends_at: datetime | None = None
    probability: float | None = None
    probability_formatted: str | None = None
    display_probability: str | None = None
    normalized_probability: float | None = None
    predictions_count: int | None = None
    positions_count: int | None = None
    type: str | None = None
    sort_order: int | None = None


class Question(BaseModel):
    """A forecasting question on the RFI platform.

    Questions can be binary (yes/no) or multi-choice with multiple answers.
    Each answer has a crowd probability reflecting the aggregated forecast.
    """

    id: int
    name: str
    type: str | None = None
    site_id: int | None = None
    membership_id: int | None = None
    active: bool | None = None
    state: str | None = None  # active, rejected, voided, resolved, pending, pending_resolution
    resolved: bool | None = None
    binary: bool | None = None
    exclusive: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    resolved_at: datetime | None = None
    voided_at: datetime | None = None
    scoring_start_time: datetime | None = None
    scoring_end_time: datetime | None = None
    use_ordinal_scoring: bool | None = None
    brier_score: float | None = None
    description: str | None = None
    resolution_notes: list[str] | None = None
    image: str | None = None
    external_id: str | None = None
    external_source: str | None = None
    featured: bool | None = None
    metadata: dict | None = None
    predictions_count: int | None = None
    comments_count: int | None = None
    answers_count: int | None = None
    prediction_sets_count: int | None = None
    predictors_count: int | None = None
    answers: list[Answer] | None = None
    clarifications: list[Clarification] | None = None


class QuestionList(BaseModel):
    """A paginated list of questions."""

    questions: list[Question]
    page: int = 1
    has_more: bool = False
