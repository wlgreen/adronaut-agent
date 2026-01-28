from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .paths import project_analysis_dir


def save_meta_watch_payload(project_id: str, payload: Dict[str, Any]) -> Path:
    d = project_analysis_dir(project_id) / "derived" / "meta_watch"
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p = d / f"{ts}.json"
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return p
