"""Local filesystem storage + indexing for Adronaut.

Structure:
- local_storage/system.json                     # System-level config/prompts
- local_storage/projects/<project_id>/index.json   # Project-level index
- local_storage/projects/<project_id>/project.json # Full project state
- local_storage/projects/<project_id>/files/       # Uploaded files
- local_storage/projects/<project_id>/files_index.json
- local_storage/projects/<project_id>/sessions/<session_id>.json
- local_storage/projects/<project_id>/cycles/<session_id>/*.json
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


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
    def system_json(self) -> Path:
        """System-level config/prompts."""
        return self.root / "system.json"

    def project_dir(self, project_id: str) -> Path:
        return self.root / "projects" / project_id

    def project_index(self, project_id: str) -> Path:
        """Project-level index (sessions, status summary)."""
        return self.project_dir(project_id) / "index.json"

    def project_json(self, project_id: str) -> Path:
        """Full project state."""
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


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    tmp.replace(path)


def ensure_dirs(project_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
    p = paths()
    p.root.mkdir(parents=True, exist_ok=True)
    (p.root / "projects").mkdir(parents=True, exist_ok=True)

    # Ensure system.json exists
    if not p.system_json.exists():
        _write_json(p.system_json, {
            "version": "1.0",
            "created_at": _utc_now_iso(),
            "system_prompts": {},
            "config": {}
        })

    if project_id:
        p.project_dir(project_id).mkdir(parents=True, exist_ok=True)
        p.project_files_dir(project_id).mkdir(parents=True, exist_ok=True)
        p.sessions_dir(project_id).mkdir(parents=True, exist_ok=True)
        (p.project_dir(project_id) / "cycles").mkdir(parents=True, exist_ok=True)

        # Ensure project index exists
        if not p.project_index(project_id).exists():
            _write_json(p.project_index(project_id), {
                "project_id": project_id,
                "created_at": _utc_now_iso(),
                "updated_at": _utc_now_iso(),
                "status": {},
                "sessions": []
            })

    if project_id and session_id:
        p.cycles_dir(project_id, session_id).mkdir(parents=True, exist_ok=True)


def generate_project_id() -> str:
    return str(uuid.uuid4())


def generate_session_id() -> str:
    return str(uuid.uuid4())


# ============================================================
# System-level operations
# ============================================================

def get_system_config() -> Dict[str, Any]:
    """Read system-level config."""
    ensure_dirs()
    return _read_json(paths().system_json, {})


def update_system_config(updates: Dict[str, Any]) -> None:
    """Update system-level config (shallow merge)."""
    ensure_dirs()
    p = paths()
    current = _read_json(p.system_json, {})
    current.update(updates)
    current["updated_at"] = _utc_now_iso()
    _write_json(p.system_json, current)


def set_system_prompt(key: str, prompt: str) -> None:
    """Store a system-level prompt."""
    ensure_dirs()
    p = paths()
    current = _read_json(p.system_json, {})
    current.setdefault("system_prompts", {})
    current["system_prompts"][key] = prompt
    current["updated_at"] = _utc_now_iso()
    _write_json(p.system_json, current)


def get_system_prompt(key: str) -> Optional[str]:
    """Retrieve a system-level prompt."""
    cfg = get_system_config()
    return cfg.get("system_prompts", {}).get(key)


# ============================================================
# Project-level index operations
# ============================================================

def update_project_index(project_id: str, *, status: Optional[Dict[str, Any]] = None) -> None:
    """Update project-level index with status summary."""
    ensure_dirs(project_id)
    p = paths()
    idx = _read_json(p.project_index(project_id), {
        "project_id": project_id,
        "sessions": []
    })

    idx["updated_at"] = _utc_now_iso()
    if status is not None:
        idx["status"] = status

    _write_json(p.project_index(project_id), idx)


def append_session_to_project_index(
    project_id: str,
    session_id: str,
    session_num: int,
    *,
    uploaded_files: Any = None
) -> None:
    """Append a session entry to project-level index."""
    ensure_dirs(project_id)
    p = paths()
    idx = _read_json(p.project_index(project_id), {
        "project_id": project_id,
        "sessions": []
    })

    idx.setdefault("sessions", [])
    idx["sessions"].append({
        "session_id": session_id,
        "session_num": session_num,
        "uploaded_files": uploaded_files,
        "created_at": _utc_now_iso(),
    })
    idx["updated_at"] = _utc_now_iso()

    _write_json(p.project_index(project_id), idx)


def get_project_index(project_id: str) -> Optional[Dict[str, Any]]:
    """Read project-level index."""
    p = paths()
    idx_path = p.project_index(project_id)
    if not idx_path.exists():
        return None
    return _read_json(idx_path, None)


def list_projects() -> List[str]:
    """List all project IDs (by scanning projects/ directory)."""
    p = paths()
    projects_dir = p.root / "projects"
    if not projects_dir.exists():
        return []
    return [d.name for d in projects_dir.iterdir() if d.is_dir() and (d / "index.json").exists()]
