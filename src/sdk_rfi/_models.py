"""Base model configuration for all SDK models."""

from __future__ import annotations

from pydantic import BaseModel as PydanticBaseModel, ConfigDict

__all__ = ["BaseModel"]


class BaseModel(PydanticBaseModel):
    """Base model for all SDK models."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_default=True,
        arbitrary_types_allowed=True,
        extra="ignore",  # Cultivate Labs API may return extra fields
    )
