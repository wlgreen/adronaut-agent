from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


def _checkpoint_root() -> Path:
    # Default to repo-local ./checkpoints; allow override for tests/deployments.
    root = os.environ.get("ADRNAUT_CHECKPOINT_DIR") or os.environ.get("ADRONAUT_CHECKPOINT_DIR") or "checkpoints"
    return Path(root)


def checkpoint_path(project_id: str) -> Path:
    return _checkpoint_root() / project_id / "state.json"


def save_checkpoint(project_id: str, state: Dict[str, Any]) -> Path:
    """Persist state to a local checkpoint file (atomic write)."""
    path = checkpoint_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(f".tmp.{int(time.time() * 1000)}")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)
    return path


def load_checkpoint(project_id: str) -> Optional[Dict[str, Any]]:
    path = checkpoint_path(project_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
