from __future__ import annotations

import os
from pathlib import Path


def adronaut_home() -> Path:
    """Return the ADRONAUT_HOME directory.

    If unset, default to a repo-local hidden folder `.adronaut`.
    """
    home = os.environ.get("ADRONAUT_HOME")
    if home:
        return Path(home)
    return Path(".adronaut")


def global_dir() -> Path:
    return adronaut_home() / "global"


def projects_dir() -> Path:
    return adronaut_home() / "projects"


def project_dir(project_id: str) -> Path:
    return projects_dir() / project_id


def project_state_dir(project_id: str) -> Path:
    return project_dir(project_id) / "state"


def project_logs_dir(project_id: str) -> Path:
    return project_dir(project_id) / "logs"


def project_inputs_dir(project_id: str) -> Path:
    return project_dir(project_id) / "inputs"


def project_analysis_dir(project_id: str) -> Path:
    return project_dir(project_id) / "analysis"


def project_artifacts_dir(project_id: str) -> Path:
    return project_dir(project_id) / "artifacts"


def project_artifact_kind_dir(project_id: str, kind: str) -> Path:
    return project_artifacts_dir(project_id) / kind
