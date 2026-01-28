from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .paths import project_artifact_kind_dir


def _latest_file(d: Path, pattern: str) -> Optional[Path]:
    if not d.exists():
        return None
    files = sorted(d.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def project_status_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    pid = state.get("project_id")
    out: Dict[str, Any] = {
        "project_id": pid,
        "phase": state.get("current_phase"),
        "iteration": state.get("iteration"),
        "flow_status": state.get("flow_status"),
        "approval_status": state.get("approval_status"),
        "requires_approval": state.get("requires_approval"),
        "last_completed_node": state.get("last_completed_node"),
    }

    if pid:
        out["latest_config"] = str(_latest_file(project_artifact_kind_dir(pid, "configs"), "campaign_v*.json") or "")
        out["latest_snapshot"] = str(_latest_file(project_artifact_kind_dir(pid, "snapshots"), "*.json") or "")
        out["latest_deployment"] = str(_latest_file(project_artifact_kind_dir(pid, "deployments"), "*_deployment_result.json") or "")

    return out
