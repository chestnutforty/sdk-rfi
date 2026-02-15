"""Common type definitions used throughout the SDK."""

from __future__ import annotations

from typing import Any, Mapping, TypeAlias

import httpx

__all__ = [
    "Headers",
    "QueryParams",
    "RequestData",
    "Timeout",
]

Headers: TypeAlias = Mapping[str, str]
QueryParams: TypeAlias = Mapping[str, str | int | bool | None]
RequestData: TypeAlias = Mapping[str, Any]
Timeout: TypeAlias = float | httpx.Timeout | None
