"""Deprecated Supabase client.

The demo flow now supports fully-local persistence (no Supabase required).
This module remains only for backwards compatibility with older imports.

If you still want Supabase, reintroduce the original implementation.
"""

from __future__ import annotations

from typing import Any


def get_db() -> Any:  # pragma: no cover
    raise RuntimeError(
        "Supabase client is disabled in local-only demo mode. "
        "Use local persistence (default) or restore Supabase client implementation."
    )
