"""Local filesystem storage + indexing for Adronaut.

Goal: support a fully-local demo mode (no Supabase required) where:
- Projects/sessions/cycles are persisted as JSON files under a local storage dir
- An `index.json` file provides a quick listing of projects + sessions

This module is intentionally small and dependency-free.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def get_storage_root() -> Path:
    """Return the root directory for all local storage."""
    root = os.getenv("ADRONAUT_LOCAL_STORAGE_DIR")
    if root:
        return Path(root).expanduser().resolve()
    # Default inside repo
    return (Path(__file__).resolve().parent.parent / "local_storage").resolve()


@dataclass
class StoragePaths:
    root: Path

    @property
    def index_path(self) -> Path:
        return self.root / "index.json"

    def project_dir(self, project_id: str) -> Path:
        return self.root / "projects" / project_id

    def project_json(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "project.json"

    def project_files_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "files"

    def project_files_index(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "files_index.json"

    def sessions_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "sessions"

    def session_json(self, project_id: str, session_id: str) -> Path:
        return self.sessions_dir(project_id) / f"{session_id}.json"

    def cycles_dir(self, project_id: str, session_id: str) -> Path:
        return self.project_dir(project_id) / "cycles" / session_id


def paths() -> StoragePaths:
    return StoragePaths(root=get_storage_root())


def ensure_dirs(project_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
    p = paths()
    p.root.mkdir(parents=True, exist_ok=True)
    (p.root / "projects").mkdir(parents=True, exist_ok=True)

    # Ensure index exists
    if not p.index_path.exists():
        p.index_path.write_text(json.dumps({"projects": {}}, indent=2))

    if project_id:
        p.project_dir(project_id).mkdir(parents=True, exist_ok=True)
        p.project_files_dir(project_id).mkdir(parents=True, exist_ok=True)
        p.sessions_dir(project_id).mkdir(parents=True, exist_ok=True)
        (p.project_dir(project_id) / "cycles").mkdir(parents=True, exist_ok=True)

    if project_id and session_id:
        p.cycles_dir(project_id, session_id).mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    tmp.replace(path)


def generate_project_id() -> str:
    return str(uuid.uuid4())


def generate_session_id() -> str:
    return str(uuid.uuid4())


def update_index_project(project_id: str, project_name: str, *, status: Optional[Dict[str, Any]] = None) -> None:
    ensure_dirs()
    p = paths()
    idx = _read_json(p.index_path, {"projects": {}})
    idx.setdefault("projects", {})

    entry = idx["projects"].get(project_id, {})
    entry.update({
        "project_id": project_id,
        "project_name": project_name,
        "updated_at": _utc_now_iso(),
    })
    if status is not None:
        entry["status"] = status

    idx["projects"][project_id] = entry
    _write_json(p.index_path, idx)


def append_index_session(project_id: str, session_id: str, session_num: int, *, uploaded_files: Any) -> None:
    ensure_dirs()
    p = paths()
    idx = _read_json(p.index_path, {"projects": {}})
    idx.setdefault("projects", {})
    idx["projects"].setdefault(project_id, {"project_id": project_id})

    proj = idx["projects"][project_id]
    proj.setdefault("sessions", [])
    proj["sessions"].append({
        "session_id": session_id,
        "session_num": session_num,
        "uploaded_files": uploaded_files,
        "created_at": _utc_now_iso(),
    })
    proj["updated_at"] = _utc_now_iso()

    _write_json(p.index_path, idx)
