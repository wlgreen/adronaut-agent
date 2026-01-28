from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


from .paths import project_state_dir


def checkpoint_path(project_id: str) -> Path:
    """Legacy project_dict checkpoint path (kept for backward compat)."""
    return project_state_dir(project_id) / "state.json"


def full_state_path(project_id: str) -> Path:
    """Full AgentState checkpoint path."""
    return project_state_dir(project_id) / "state_full.json"


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp.{int(time.time() * 1000)}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)
    return path


def save_checkpoint(project_id: str, state: Dict[str, Any]) -> Path:
    """Persist a project-shaped dict to local checkpoint (atomic write)."""
    return _atomic_write_json(checkpoint_path(project_id), state)


def save_full_state(project_id: str, state: Dict[str, Any]) -> Path:
    """Persist the full AgentState dict to local checkpoint (atomic write)."""
    return _atomic_write_json(full_state_path(project_id), state)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def load_checkpoint(project_id: str) -> Optional[Dict[str, Any]]:
    return _load_json(checkpoint_path(project_id))


def load_full_state(project_id: str) -> Optional[Dict[str, Any]]:
    return _load_json(full_state_path(project_id))
