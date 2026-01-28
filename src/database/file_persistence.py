"""Local persistence for uploaded files + cached insights.

Replaces the Supabase-backed uploaded_files table with a JSON file per project:
- local_storage/projects/<project_id>/files_index.json

This keeps the previous interface so nodes can keep using FilePersistence.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..local_storage import ensure_dirs, paths


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _read_index(project_id: str) -> List[Dict[str, Any]]:
    ensure_dirs(project_id)
    p = paths().project_files_index(project_id)
    if not p.exists():
        return []
    import json

    return json.loads(p.read_text())


def _write_index(project_id: str, rows: List[Dict[str, Any]]) -> None:
    ensure_dirs(project_id)
    p = paths().project_files_index(project_id)
    import json

    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    tmp.replace(p)


def _find(rows: List[Dict[str, Any]], project_id: str, storage_path: str) -> Optional[Dict[str, Any]]:
    for r in rows:
        if r.get("project_id") == project_id and r.get("storage_path") == storage_path:
            return r
    return None


class FilePersistence:
    """Filesystem-backed file record cache."""

    @staticmethod
    def save_file_record(
        project_id: str,
        storage_path: str,
        original_filename: str,
        file_type: Optional[str] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        rows = _read_index(project_id)
        rec = _find(rows, project_id, storage_path)
        if rec is None:
            rec = {
                "file_id": f"local_{len(rows) + 1}",
                "project_id": project_id,
                "storage_path": storage_path,
                "original_filename": original_filename,
                "uploaded_at": _utc_now_iso(),
            }
            rows.append(rec)

        rec["file_type"] = file_type
        rec["file_metadata"] = file_metadata or {}
        rec["last_analyzed_at"] = _utc_now_iso()

        _write_index(project_id, rows)
        return rec["file_id"]

    @staticmethod
    def get_file_record(project_id: str, storage_path: str) -> Optional[Dict[str, Any]]:
        rows = _read_index(project_id)
        return _find(rows, project_id, storage_path)

    @staticmethod
    def update_file_analysis(project_id: str, storage_path: str, file_metadata: Dict[str, Any], file_type: str) -> None:
        rows = _read_index(project_id)
        rec = _find(rows, project_id, storage_path)
        if rec is None:
            # Create on the fly
            FilePersistence.save_file_record(
                project_id=project_id,
                storage_path=storage_path,
                original_filename=Path(storage_path).name,
                file_type=file_type,
                file_metadata=file_metadata,
            )
            return

        rec["file_metadata"] = file_metadata
        rec["file_type"] = file_type
        rec["last_analyzed_at"] = _utc_now_iso()
        _write_index(project_id, rows)

    @staticmethod
    def cache_file_insights(project_id: str, storage_path: str, insights: Dict[str, Any]) -> None:
        rows = _read_index(project_id)
        rec = _find(rows, project_id, storage_path)
        if rec is None:
            FilePersistence.save_file_record(
                project_id=project_id,
                storage_path=storage_path,
                original_filename=Path(storage_path).name,
                file_metadata={},
            )
            rows = _read_index(project_id)
            rec = _find(rows, project_id, storage_path)

        assert rec is not None
        rec["insights_cache"] = insights
        rec["last_analyzed_at"] = _utc_now_iso()
        _write_index(project_id, rows)

    @staticmethod
    def get_project_files(project_id: str) -> List[Dict[str, Any]]:
        rows = _read_index(project_id)
        # mimic DB ordering: newest first
        return list(reversed(rows))

    @staticmethod
    def delete_file_record(project_id: str, storage_path: str) -> None:
        rows = _read_index(project_id)
        rows = [r for r in rows if not (r.get("project_id") == project_id and r.get("storage_path") == storage_path)]
        _write_index(project_id, rows)

    @staticmethod
    def upsert_file_record(
        project_id: str,
        storage_path: str,
        original_filename: str,
        file_type: Optional[str] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
        insights_cache: Optional[Dict[str, Any]] = None,
    ) -> str:
        rows = _read_index(project_id)
        rec = _find(rows, project_id, storage_path)
        if rec is None:
            rec = {
                "file_id": f"local_{len(rows) + 1}",
                "project_id": project_id,
                "storage_path": storage_path,
                "original_filename": original_filename,
                "uploaded_at": _utc_now_iso(),
            }
            rows.append(rec)

        if file_type is not None:
            rec["file_type"] = file_type
        if file_metadata is not None:
            rec["file_metadata"] = file_metadata
        if insights_cache is not None:
            rec["insights_cache"] = insights_cache
            rec["last_analyzed_at"] = _utc_now_iso()

        _write_index(project_id, rows)
        return rec["file_id"]
