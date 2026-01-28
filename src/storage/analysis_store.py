from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

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
