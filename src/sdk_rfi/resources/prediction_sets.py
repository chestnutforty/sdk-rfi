"""Prediction Sets resource for the RFI SDK."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .._utils import _resolve_cutoff_date
from ..types.prediction_sets import PredictionSet, PredictionSetList

if TYPE_CHECKING:
    from .._base_client import BaseClient, AsyncBaseClient

__all__ = ["PredictionSets", "AsyncPredictionSets"]


def _filter_prediction_sets_by_cutoff(prediction_sets: list[PredictionSet], cutoff_date: str) -> list[PredictionSet]:
    """Filter prediction sets to only those created before cutoff_date."""
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    filtered = []
    for ps in prediction_sets:
        if ps.created_at is not None:
            created_dt = ps.created_at if isinstance(ps.created_at, datetime) else datetime.fromisoformat(str(ps.created_at))
            if created_dt.replace(tzinfo=None) <= cutoff_dt:
                filtered.append(ps)
        else:
            filtered.append(ps)
    return filtered


class PredictionSets:
    """Prediction Sets (forecasts) resource for sync client.

    Example:
        client = Client()
        forecasts = client.prediction_sets.list(question_id=1234)
    """

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    def list(
        self,
        *,
        question_id: int | None = None,
        membership_id: int | None = None,
        filter: str | None = None,
        page: int | None = None,
        created_before: str | None = None,
        created_after: str | None = None,
        updated_before: str | None = None,
        updated_after: str | None = None,
        cutoff_date: str | None = None,
    ) -> PredictionSetList:
        """List prediction sets (forecasts).

        BACKTESTING: Supported via created_before API param + client-side filtering.
        Only returns forecasts made before cutoff_date. Set cutoff_date or
        CUTOFF_DATE env var.

        Args:
            question_id: Filter by question ID.
            membership_id: Filter by membership (user) ID.
            filter: 'comments_with_links' or 'comments_following'.
            page: Page number for pagination.
            created_before: ISO8601 date.
            created_after: ISO8601 date.
            updated_before: ISO8601 date.
            updated_after: ISO8601 date.
            cutoff_date: Filter to forecasts made before this date (YYYY-MM-DD).
                         Overridden by CUTOFF_DATE environment variable if set.
        """
        cutoff_date = _resolve_cutoff_date(cutoff_date)

        params: dict = {}
        if question_id is not None:
            params["question_id"] = question_id
        if membership_id is not None:
            params["membership_id"] = membership_id
        if filter is not None:
            params["filter"] = filter
        if page is not None:
            params["page"] = page

        # Use cutoff_date as created_before if not explicitly set
        if created_before is not None:
            params["created_before"] = created_before
        elif cutoff_date:
            params["created_before"] = f"{cutoff_date}T23:59:59"

        if created_after is not None:
            params["created_after"] = created_after
        if updated_before is not None:
            params["updated_before"] = updated_before
        if updated_after is not None:
            params["updated_after"] = updated_after

        data = self._client.get("/api/v1/prediction_sets", params=params)

        if isinstance(data, list):
            prediction_sets = [PredictionSet.model_validate(ps) for ps in data]
            has_more = len(prediction_sets) >= 20
        elif isinstance(data, dict):
            items = data.get("prediction_sets", data.get("results", data.get("data", [])))
            if isinstance(items, list):
                prediction_sets = [PredictionSet.model_validate(ps) for ps in items]
            else:
                prediction_sets = []
            has_more = bool(data.get("next") or data.get("has_more"))
        else:
            prediction_sets = []
            has_more = False

        # Client-side filtering
        if cutoff_date:
            prediction_sets = _filter_prediction_sets_by_cutoff(prediction_sets, cutoff_date)

        return PredictionSetList(
            prediction_sets=prediction_sets,
            page=page or 1,
            has_more=has_more,
        )


class AsyncPredictionSets:
    """Prediction Sets resource for async client."""

    def __init__(self, client: "AsyncBaseClient") -> None:
        self._client = client

    async def list(
        self,
        *,
        question_id: int | None = None,
        membership_id: int | None = None,
        filter: str | None = None,
        page: int | None = None,
        created_before: str | None = None,
        created_after: str | None = None,
        updated_before: str | None = None,
        updated_after: str | None = None,
        cutoff_date: str | None = None,
    ) -> PredictionSetList:
        """List prediction sets (forecasts).

        BACKTESTING: Supported via created_before API param + client-side filtering.
        Set cutoff_date or CUTOFF_DATE env var.

        Args:
            cutoff_date: Filter to forecasts made before this date (YYYY-MM-DD).
                         Overridden by CUTOFF_DATE environment variable if set.
        """
        cutoff_date = _resolve_cutoff_date(cutoff_date)

        params: dict = {}
        if question_id is not None:
            params["question_id"] = question_id
        if membership_id is not None:
            params["membership_id"] = membership_id
        if filter is not None:
            params["filter"] = filter
        if page is not None:
            params["page"] = page

        if created_before is not None:
            params["created_before"] = created_before
        elif cutoff_date:
            params["created_before"] = f"{cutoff_date}T23:59:59"

        if created_after is not None:
            params["created_after"] = created_after
        if updated_before is not None:
            params["updated_before"] = updated_before
        if updated_after is not None:
            params["updated_after"] = updated_after

        data = await self._client.get("/api/v1/prediction_sets", params=params)

        if isinstance(data, list):
            prediction_sets = [PredictionSet.model_validate(ps) for ps in data]
            has_more = len(prediction_sets) >= 20
        elif isinstance(data, dict):
            items = data.get("prediction_sets", data.get("results", data.get("data", [])))
            if isinstance(items, list):
                prediction_sets = [PredictionSet.model_validate(ps) for ps in items]
            else:
                prediction_sets = []
            has_more = bool(data.get("next") or data.get("has_more"))
        else:
            prediction_sets = []
            has_more = False

        if cutoff_date:
            prediction_sets = _filter_prediction_sets_by_cutoff(prediction_sets, cutoff_date)

        return PredictionSetList(
            prediction_sets=prediction_sets,
            page=page or 1,
            has_more=has_more,
        )
