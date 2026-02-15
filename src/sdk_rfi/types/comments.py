"""Types for RFI Comments API."""

from __future__ import annotations

from datetime import datetime

from .._models import BaseModel

__all__ = [
    "Comment",
    "CommentList",
]


class Comment(BaseModel):
    """A comment on a question or other commentable object."""

    id: int
    commentable_id: int | None = None
    commentable_type: str | None = None
    comment_type: str | None = None
    parent_id: int | None = None
    content: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    membership_id: int | None = None
    membership_username: str | None = None
    membership_avatar_url: str | None = None


class CommentList(BaseModel):
    """A paginated list of comments."""

    comments: list[Comment]
    page: int = 1
    has_more: bool = False
