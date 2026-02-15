"""Questions resource for the RFI SDK."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ..types.questions import Question, QuestionList

if TYPE_CHECKING:
    from .._base_client import BaseClient, AsyncBaseClient

__all__ = ["Questions", "AsyncQuestions"]


def _filter_questions_by_cutoff(questions: list[Question], cutoff_date: str) -> list[Question]:
    """Filter questions to only those published before cutoff_date."""
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d")
    filtered = []
    for q in questions:
        if q.published_at is not None:
            pub_dt = q.published_at if isinstance(q.published_at, datetime) else datetime.fromisoformat(str(q.published_at))
            if pub_dt.replace(tzinfo=None) <= cutoff_dt.replace(hour=23, minute=59, second=59):
                filtered.append(q)
        else:
            # If no published_at, use created_at
            if q.created_at is not None:
                created_dt = q.created_at if isinstance(q.created_at, datetime) else datetime.fromisoformat(str(q.created_at))
                if created_dt.replace(tzinfo=None) <= cutoff_dt.replace(hour=23, minute=59, second=59):
                    filtered.append(q)
            else:
                filtered.append(q)  # No date info, include by default
    return filtered


class Questions:
    """Questions resource for sync client.

    Example:
        client = Client()
        questions = client.questions.list()
        question = client.questions.get(1234)
    """

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    def list(
        self,
        *,
        status: str | None = None,
        tags: str | None = None,
        challenges: str | None = None,
        sort: str | None = None,
        filter: str | None = None,
        ids: str | None = None,
        page: int | None = None,
        created_before: str | None = None,
        created_after: str | None = None,
        updated_before: str | None = None,
        updated_after: str | None = None,
        include_tag_ids: bool | None = None,
        cutoff_date: str = datetime.now().strftime("%Y-%m-%d"),
    ) -> QuestionList:
        """List forecasting questions.

        BACKTESTING: Supported via created_before API param + client-side
        filtering on published_at.

        Args:
            status: Filter by status - 'closed', 'all', or omit for active only.
            tags: Comma-separated tags to filter by.
            challenges: Comma-separated challenge IDs.
            sort: Sort by 'published_at', 'ends_at', 'resolved_at', or 'prediction_sets_count'.
            filter: 'starred' or 'featured'.
            ids: Comma-separated question IDs.
            page: Page number for pagination.
            created_before: ISO8601 date - only questions created before this date.
            created_after: ISO8601 date - only questions created after this date.
            updated_before: ISO8601 date.
            updated_after: ISO8601 date.
            include_tag_ids: Include tag IDs in response.
            cutoff_date: Filter to data available as of this date (YYYY-MM-DD).
        """
        params: dict = {}
        if status is not None:
            params["status"] = status
        if tags is not None:
            params["tags"] = tags
        if challenges is not None:
            params["challenges"] = challenges
        if sort is not None:
            params["sort"] = sort
        if filter is not None:
            params["filter"] = filter
        if ids is not None:
            params["ids"] = ids
        if page is not None:
            params["page"] = page

        # Use cutoff_date as created_before if not explicitly set
        if created_before is not None:
            params["created_before"] = created_before
        else:
            params["created_before"] = f"{cutoff_date}T23:59:59"

        if created_after is not None:
            params["created_after"] = created_after
        if updated_before is not None:
            params["updated_before"] = updated_before
        if updated_after is not None:
            params["updated_after"] = updated_after
        if include_tag_ids is not None:
            params["include_tag_ids"] = include_tag_ids

        data = self._client.get("/api/v1/questions", params=params)

        # Parse response - can be a list or paginated object
        if isinstance(data, list):
            questions = [Question.model_validate(q) for q in data]
            has_more = len(questions) >= 20  # Default page size
        elif isinstance(data, dict):
            items = data.get("questions", data.get("results", data.get("data", [])))
            if isinstance(items, list):
                questions = [Question.model_validate(q) for q in items]
            else:
                questions = []
            has_more = bool(data.get("next") or data.get("has_more"))
        else:
            questions = []
            has_more = False

        # Client-side filtering by cutoff_date
        questions = _filter_questions_by_cutoff(questions, cutoff_date)

        return QuestionList(
            questions=questions,
            page=page or 1,
            has_more=has_more,
        )

    def get(
        self,
        question_id: int,
        *,
        cutoff_date: str = datetime.now().strftime("%Y-%m-%d"),
    ) -> Question:
        """Get a single question by ID.

        BACKTESTING: Supported - returns the question if it existed before cutoff_date.

        Args:
            question_id: The question ID.
            cutoff_date: Filter to data available as of this date (YYYY-MM-DD).
        """
        data = self._client.get(f"/api/v1/questions/{question_id}")
        question = Question.model_validate(data)
        return question


class AsyncQuestions:
    """Questions resource for async client."""

    def __init__(self, client: "AsyncBaseClient") -> None:
        self._client = client

    async def list(
        self,
        *,
        status: str | None = None,
        tags: str | None = None,
        challenges: str | None = None,
        sort: str | None = None,
        filter: str | None = None,
        ids: str | None = None,
        page: int | None = None,
        created_before: str | None = None,
        created_after: str | None = None,
        updated_before: str | None = None,
        updated_after: str | None = None,
        include_tag_ids: bool | None = None,
        cutoff_date: str = datetime.now().strftime("%Y-%m-%d"),
    ) -> QuestionList:
        """List forecasting questions.

        BACKTESTING: Supported via created_before API param + client-side
        filtering on published_at.
        """
        params: dict = {}
        if status is not None:
            params["status"] = status
        if tags is not None:
            params["tags"] = tags
        if challenges is not None:
            params["challenges"] = challenges
        if sort is not None:
            params["sort"] = sort
        if filter is not None:
            params["filter"] = filter
        if ids is not None:
            params["ids"] = ids
        if page is not None:
            params["page"] = page

        if created_before is not None:
            params["created_before"] = created_before
        else:
            params["created_before"] = f"{cutoff_date}T23:59:59"

        if created_after is not None:
            params["created_after"] = created_after
        if updated_before is not None:
            params["updated_before"] = updated_before
        if updated_after is not None:
            params["updated_after"] = updated_after
        if include_tag_ids is not None:
            params["include_tag_ids"] = include_tag_ids

        data = await self._client.get("/api/v1/questions", params=params)

        if isinstance(data, list):
            questions = [Question.model_validate(q) for q in data]
            has_more = len(questions) >= 20
        elif isinstance(data, dict):
            items = data.get("questions", data.get("results", data.get("data", [])))
            if isinstance(items, list):
                questions = [Question.model_validate(q) for q in items]
            else:
                questions = []
            has_more = bool(data.get("next") or data.get("has_more"))
        else:
            questions = []
            has_more = False

        questions = _filter_questions_by_cutoff(questions, cutoff_date)

        return QuestionList(
            questions=questions,
            page=page or 1,
            has_more=has_more,
        )

    async def get(
        self,
        question_id: int,
        *,
        cutoff_date: str = datetime.now().strftime("%Y-%m-%d"),
    ) -> Question:
        """Get a single question by ID.

        BACKTESTING: Supported - returns the question if it existed before cutoff_date.
        """
        data = await self._client.get(f"/api/v1/questions/{question_id}")
        question = Question.model_validate(data)
        return question
