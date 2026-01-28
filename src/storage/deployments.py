from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .paths import project_artifact_kind_dir


def latest_deployment_result_path(project_id: str) -> Optional[Path]:
    d = project_artifact_kind_dir(project_id, "deployments")
    if not d.exists():
        return None
    files = sorted(d.glob("*_deployment_result.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_deployment_result(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
