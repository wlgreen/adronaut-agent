from __future__ import annotations

from typing import Any, Dict, List, Tuple


def validate_campaign_config(cfg: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Lightweight config quality gate.

    Goal: catch obvious malformed configs before they get deployed or used downstream.
    Keep this deterministic and fast.
    """
    notes: List[str] = []

    if not isinstance(cfg, dict) or not cfg:
        return False, ["Config is empty or not a dict"]

    # Known top-level keys in this repo's generated config
    allowed_sections = {"summary", "meta", "tiktok"}
    if not any(k in cfg for k in allowed_sections):
        notes.append("Config missing expected sections (summary/meta/tiktok)")

    # Validate budgets
    total = None
    if isinstance(cfg.get("summary"), dict):
        td = cfg["summary"].get("total_daily_budget")
        if td is not None:
            try:
                total = float(td)
                if total < 0:
                    notes.append("summary.total_daily_budget is negative")
            except Exception:
                notes.append("summary.total_daily_budget is not numeric")

    def _section_budget(section: str) -> float | None:
        sec = cfg.get(section)
        if not isinstance(sec, dict):
            return None
        b = sec.get("daily_budget")
        if b is None:
            return None
        try:
            return float(b)
        except Exception:
            notes.append(f"{section}.daily_budget is not numeric")
            return None

    meta_b = _section_budget("meta")
    tt_b = _section_budget("tiktok")

    for sec, b in [("meta", meta_b), ("tiktok", tt_b)]:
        if b is not None and b < 0:
            notes.append(f"{sec}.daily_budget is negative")

    if total is not None:
        known = [x for x in [meta_b, tt_b] if x is not None]
        if known:
            s = sum(known)
            # allow small drift
            if abs(s - total) > max(1.0, 0.01 * max(total, 1.0)):
                notes.append(f"Budget mismatch: summary.total_daily_budget={total} vs sections sum={s}")

    ok = len(notes) == 0
    return ok, notes
