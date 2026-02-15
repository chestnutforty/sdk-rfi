"""Comments resource for the RFI SDK."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ..types.comments import Comment, CommentList

if TYPE_CHECKING:
    from .._base_client import BaseClient, AsyncBaseClient

__all__ = ["Comments", "AsyncComments"]


def _filter_comments_by_cutoff(comments: list[Comment], cutoff_date: str) -> list[Comment]:
    """Filter comments to only those created before cutoff_date."""
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    filtered = []
    for c in comments:
        if c.created_at is not None:
            created_dt = c.created_at if isinstance(c.created_at, datetime) else datetime.fromisoformat(str(c.created_at))
            if created_dt.replace(tzinfo=None) <= cutoff_dt:
                filtered.append(c)
        else:
            filtered.append(c)
    return filtered


class Comments:
    """Comments resource for sync client.

    Example:
        client = Client()
        comments = client.comments.list(commentable_id=1234, commentable_type="Forecast::Question")
    """

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    def list(
        self,
        *,
        commentable_id: int | None = None,
        commentable_type: str | None = None,
        page: int | None = None,
        created_before: str | None = None,
        created_after: str | None = None,
        cutoff_date: str = datetime.now().strftime("%Y-%m-%d"),
    ) -> CommentList:
        """List comments.

        BACKTESTING: Supported via created_before API param + client-side filtering.

        Args:
            commentable_id: Filter by the ID of the commented object (e.g., question ID).
            commentable_type: Filter by type (e.g., 'Forecast::Question').
            page: Page number for pagination.
            created_before: ISO8601 date.
            created_after: ISO8601 date.
            cutoff_date: Filter to comments made before this date (YYYY-MM-DD).
        """
        params: dict = {}
        if commentable_id is not None:
            params["commentable_id"] = commentable_id
        if commentable_type is not None:
            params["commentable_type"] = commentable_type
        if page is not None:
            params["page"] = page

        if created_before is not None:
            params["created_before"] = created_before
        else:
            params["created_before"] = f"{cutoff_date}T23:59:59"

        if created_after is not None:
            params["created_after"] = created_after

        data = self._client.get("/api/v1/comments", params=params)

        if isinstance(data, list):
            comments = [Comment.model_validate(c) for c in data]
            has_more = len(comments) >= 20
        elif isinstance(data, dict):
            items = data.get("comments", data.get("results", data.get("data", [])))
            if isinstance(items, list):
                comments = [Comment.model_validate(c) for c in items]
            else:
                comments = []
            has_more = bool(data.get("next") or data.get("has_more"))
        else:
            comments = []
            has_more = False

        comments = _filter_comments_by_cutoff(comments, cutoff_date)

        return CommentList(
            comments=comments,
            page=page or 1,
            has_more=has_more,
        )


class AsyncComments:
    """Comments resource for async client."""

    def __init__(self, client: "AsyncBaseClient") -> None:
        self._client = client

    async def list(
        self,
        *,
        commentable_id: int | None = None,
        commentable_type: str | None = None,
        page: int | None = None,
        created_before: str | None = None,
        created_after: str | None = None,
        cutoff_date: str = datetime.now().strftime("%Y-%m-%d"),
    ) -> CommentList:
        """List comments.

        BACKTESTING: Supported via created_before API param + client-side filtering.
        """
        params: dict = {}
        if commentable_id is not None:
            params["commentable_id"] = commentable_id
        if commentable_type is not None:
            params["commentable_type"] = commentable_type
        if page is not None:
            params["page"] = page

        if created_before is not None:
            params["created_before"] = created_before
        else:
            params["created_before"] = f"{cutoff_date}T23:59:59"

        if created_after is not None:
            params["created_after"] = created_after

        data = await self._client.get("/api/v1/comments", params=params)

        if isinstance(data, list):
            comments = [Comment.model_validate(c) for c in data]
            has_more = len(comments) >= 20
        elif isinstance(data, dict):
            items = data.get("comments", data.get("results", data.get("data", [])))
            if isinstance(items, list):
                comments = [Comment.model_validate(c) for c in items]
            else:
                comments = []
            has_more = bool(data.get("next") or data.get("has_more"))
        else:
            comments = []
            has_more = False

        comments = _filter_comments_by_cutoff(comments, cutoff_date)

        return CommentList(
            comments=comments,
            page=page or 1,
            has_more=has_more,
        )
