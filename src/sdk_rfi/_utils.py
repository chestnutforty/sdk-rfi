"""Shared utilities for the RFI SDK."""

import os


def _resolve_cutoff_date(cutoff_date: str | None = None) -> str | None:
    """Resolve effective cutoff date.

    Priority: CUTOFF_DATE env var > cutoff_date parameter > None.

    The CUTOFF_DATE env var is set by the backtesting evaluation harness.
    When set, it ALWAYS overrides the parameter to prevent look-ahead bias.
    Returns None when nothing is set -- forward testing MUST be a no-op.
    """
    env_cutoff = os.environ.get("CUTOFF_DATE")
    if env_cutoff:
        return env_cutoff
    if cutoff_date:
        return cutoff_date
    return None  # MUST return None, not today -- forward testing is a no-op
