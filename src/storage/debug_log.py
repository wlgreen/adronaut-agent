from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


from .paths import project_logs_dir


def node_io_log_path(project_id: str) -> Path:
    return project_logs_dir(project_id) / "node_io.jsonl"


def append_node_io_record(project_id: str, node_name: str, record: Dict[str, Any]) -> Optional[Path]:
    """Append a single node input/output record as JSONL under the project folder."""
    if not project_id:
        return None

    path = node_io_log_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "ts_ms": int(time.time() * 1000),
        "node": node_name,
        **record,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
    return path
