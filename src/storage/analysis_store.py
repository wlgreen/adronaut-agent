from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import project_analysis_dir, project_inputs_dir


def save_file_analyses(project_id: str, analyses: List[Dict[str, Any]]) -> Path:
    """Persist file analyses for a project in a stable, easy-to-inspect location."""
    d = project_analysis_dir(project_id)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "file_analyses.json"
    p.write_text(json.dumps(analyses, indent=2, sort_keys=True), encoding="utf-8")
    return p


def save_uploaded_files_metadata(project_id: str, uploaded_files: List[Dict[str, Any]]) -> Path:
    d = project_inputs_dir(project_id)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "metadata.json"
    p.write_text(json.dumps({"uploaded_files": uploaded_files}, indent=2, sort_keys=True), encoding="utf-8")
    return p


def _safe_name(storage_path: str) -> str:
    name = Path(storage_path).name
    if not name:
        name = "file"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name


def insights_cache_path(project_id: str, storage_path: str) -> Path:
    base = project_analysis_dir(project_id) / "derived" / "insights_cache"
    return base / f"{_safe_name(storage_path)}.json"


def save_insights_cache(project_id: str, storage_path: str, insights: Dict[str, Any]) -> Path:
    d = project_analysis_dir(project_id) / "derived" / "insights_cache"
    d.mkdir(parents=True, exist_ok=True)
    p = insights_cache_path(project_id, storage_path)
    payload = {"storage_path": storage_path, "insights": insights}
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return p


def load_insights_cache(project_id: str, storage_path: str) -> Optional[Dict[str, Any]]:
    p = insights_cache_path(project_id, storage_path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data.get("insights")
    except Exception:
        return None
    return None
