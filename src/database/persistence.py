"""Local persistence layer (filesystem-based).

This repo originally used Supabase for persistence. For the demo flow we support
"local-only" mode: all project/session/cycle state is stored on disk.

Storage layout (default root: ./local_storage):
- local_storage/index.json
- local_storage/projects/<project_id>/project.json
- local_storage/projects/<project_id>/sessions/<session_id>.json
- local_storage/projects/<project_id>/cycles/<session_id>/<cycle_num>_<node>.json

The public interface of ProjectPersistence/SessionPersistence/CyclePersistence
matches the previous Supabase-backed version.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..local_storage import (
    append_index_session,
    ensure_dirs,
    generate_project_id,
    generate_session_id,
    paths,
    update_index_project,
)


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    import json

    return json.loads(path.read_text())


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    tmp.replace(path)


class ProjectPersistence:
    """Handle all persistence operations for projects (local filesystem)."""

    @staticmethod
    def load_project(project_id: str) -> Optional[Dict[str, Any]]:
        ensure_dirs(project_id)
        p = paths()
        return _read_json(p.project_json(project_id))

    @staticmethod
    def create_project(user_id: str, project_name: str, product_description: str, target_budget: float) -> str:
        project_id = generate_project_id()
        ensure_dirs(project_id)
        p = paths()

        project_data: Dict[str, Any] = {
            "project_id": project_id,
            "user_id": user_id,
            "project_name": project_name,
            "product_description": product_description,
            "target_budget": target_budget,
            "current_phase": "initialized",
            "iteration": 0,
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            # Flow fields (kept for compatibility)
            "flow_status": "not_started",
            "last_completed_node": None,
            "completed_nodes": [],
            "current_executing_node": None,
        }

        _write_json(p.project_json(project_id), project_data)
        update_index_project(project_id, project_name, status={"flow_status": "not_started"})
        return project_id

    @staticmethod
    def save_project(project_data: Dict[str, Any]) -> None:
        project_id = project_data["project_id"]
        ensure_dirs(project_id)
        p = paths()

        project_data = {**project_data}
        project_data["updated_at"] = _utc_now_iso()
        _write_json(p.project_json(project_id), project_data)

        update_index_project(
            project_id,
            project_data.get("project_name", project_id),
            status={
                "flow_status": project_data.get("flow_status"),
                "current_phase": project_data.get("current_phase"),
                "iteration": project_data.get("iteration"),
                "last_completed_node": project_data.get("last_completed_node"),
            },
        )

    @staticmethod
    def update_project_field(project_id: str, field: str, value: Any) -> None:
        proj = ProjectPersistence.load_project(project_id)
        if not proj:
            raise ValueError(f"Project {project_id} not found")
        proj[field] = value
        ProjectPersistence.save_project(proj)

    @staticmethod
    def append_to_array_field(project_id: str, field: str, item: Any) -> None:
        proj = ProjectPersistence.load_project(project_id)
        if not proj:
            raise ValueError(f"Project {project_id} not found")
        current = proj.get(field) or []
        if not isinstance(current, list):
            current = []
        current.append(item)
        proj[field] = current
        ProjectPersistence.save_project(proj)


class SessionPersistence:
    """Handle all persistence operations for sessions (local filesystem)."""

    @staticmethod
    def create_session(project_id: str, session_num: int, uploaded_files: List[Dict[str, Any]]) -> str:
        session_id = generate_session_id()
        ensure_dirs(project_id, session_id)
        p = paths()

        data = {
            "session_id": session_id,
            "project_id": project_id,
            "session_num": session_num,
            "uploaded_files": uploaded_files,
            "execution_status": "running",
            "created_at": _utc_now_iso(),
            "completed_at": None,
        }

        _write_json(p.session_json(project_id, session_id), data)
        append_index_session(project_id, session_id, session_num, uploaded_files=uploaded_files)
        return session_id

    @staticmethod
    def update_session(session_id: str, updates: Dict[str, Any]) -> None:
        # We don't have a global session index by id; scan projects quickly via index.
        from ..local_storage import _read_json as _idx_read  # type: ignore

        idx = _idx_read(paths().index_path, {"projects": {}})
        for project_id in (idx.get("projects") or {}).keys():
            p = paths().session_json(project_id, session_id)
            if p.exists():
                sess = _read_json(p) or {}
                sess.update(updates)
                sess["updated_at"] = _utc_now_iso()
                _write_json(p, sess)
                return
        raise ValueError(f"Session {session_id} not found")

    @staticmethod
    def complete_session(session_id: str, status: str = "completed") -> None:
        SessionPersistence.update_session(
            session_id,
            {
                "execution_status": status,
                "completed_at": _utc_now_iso(),
            },
        )


class CyclePersistence:
    """Log per-node cycles for debugging/traceability (local filesystem)."""

    @staticmethod
    def log_cycle(
        session_id: str,
        project_id: str,
        cycle_num: int,
        node_name: str,
        thought: Optional[str] = None,
        action: Optional[Dict[str, Any]] = None,
        observation: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        llm_tokens_used: Optional[int] = None,
    ) -> None:
        ensure_dirs(project_id, session_id)
        p = paths()

        payload = {
            "session_id": session_id,
            "project_id": project_id,
            "cycle_num": cycle_num,
            "node_name": node_name,
            "thought": thought,
            "action": action,
            "observation": observation,
            "execution_time_ms": execution_time_ms,
            "llm_tokens_used": llm_tokens_used,
            "created_at": _utc_now_iso(),
        }

        fname = f"{cycle_num:04d}_{node_name}.json"
        out = p.cycles_dir(project_id, session_id) / fname
        _write_json(out, payload)

    @staticmethod
    def get_session_cycles(session_id: str) -> List[Dict[str, Any]]:
        # Best-effort: scan all project cycle dirs.
        from ..local_storage import _read_json as _idx_read  # type: ignore

        idx = _idx_read(paths().index_path, {"projects": {}})
        cycles: List[Dict[str, Any]] = []
        for project_id in (idx.get("projects") or {}).keys():
            cdir = paths().project_dir(project_id) / "cycles" / session_id
            if cdir.exists():
                for f in sorted(cdir.glob("*.json")):
                    obj = _read_json(f)
                    if obj:
                        cycles.append(obj)
        return cycles
