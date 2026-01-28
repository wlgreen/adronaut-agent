from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import project_analysis_dir, project_inputs_dir
from .inputs_hash import compute_inputs_hash


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
    payload = {"uploaded_files": uploaded_files, "inputs_hash": compute_inputs_hash(uploaded_files)}
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return p


def inputs_hash_path(project_id: str) -> Path:
    return project_analysis_dir(project_id) / "derived" / "inputs_hash.json"


def save_inputs_hash(project_id: str, uploaded_files: List[Dict[str, Any]]) -> Path:
    d = project_analysis_dir(project_id) / "derived"
    d.mkdir(parents=True, exist_ok=True)
    p = inputs_hash_path(project_id)
    payload = {"inputs_hash": compute_inputs_hash(uploaded_files)}
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return p


def load_inputs_hash(project_id: str) -> Optional[str]:
    p = inputs_hash_path(project_id)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            v = data.get("inputs_hash")
            return v if isinstance(v, str) else None
    except Exception:
        return None
    return None


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


def list_insights_cache_files(project_id: str) -> List[Path]:
    d = project_analysis_dir(project_id) / "derived" / "insights_cache"
    if not d.exists():
        return []
    return sorted(d.glob("*.json"))


def summarize_cached_insights_for_planner(project_id: str, max_files: int = 3) -> str:
    """Return a short JSON summary of cached insights to include in planner prompt."""
    files = list_insights_cache_files(project_id)[:max_files]
    out: List[Dict[str, Any]] = []

    for p in files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        insights = (data or {}).get("insights") or {}
        strategy = insights.get("strategy") or {}
        ins = (strategy.get("insights") or {}) if isinstance(strategy, dict) else {}

        out.append(
            {
                "file": p.name,
                "patterns": (ins.get("patterns") or [])[:3],
                "strengths": (ins.get("strengths") or [])[:3],
                "weaknesses": (ins.get("weaknesses") or [])[:3],
            }
        )

    return json.dumps(out, indent=2) if out else "[]"
