from __future__ import annotations

from typing import Any, Dict, Set


BASE_KEYS: Set[str] = {"id", "action", "rationale", "success", "requires_approval"}

# Per-action allowed extra keys
ALLOWED_EXTRAS: Dict[str, Set[str]] = {
    # Hybrid repo_search supports planner-provided search terms
    "repo_search": {"search", "queries", "query"},
    # Optional structured inputs for adjustment (future use)
    "adjustment": {"patch_overrides"},
    "campaign_setup": {"config_overrides"},
}


def sanitize_step(action: str, step: Dict[str, Any]) -> Dict[str, Any]:
    """Drop unknown keys from a planned step to keep the interface stable."""
    allowed = set(BASE_KEYS)
    allowed |= ALLOWED_EXTRAS.get(action or "", set())

    out: Dict[str, Any] = {}
    for k, v in step.items():
        if k in allowed:
            out[k] = v
    # preserve id/action minimally
    out.setdefault("action", action)
    if "id" in step:
        out.setdefault("id", step.get("id"))
    return out
