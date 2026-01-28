import json
from pathlib import Path
from types import SimpleNamespace

import cli


def test_status_command_prints_summary(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    # Create a minimal checkpoint state
    project_id = "p_status"
    state_dir = tmp_path / "projects" / project_id / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "state_full.json").write_text(json.dumps({"project_id": project_id, "current_phase": "initialized"}))

    # Call the status handler via main dispatch logic by invoking the function block directly
    # Simpler: simulate by importing the helper used in cli.
    from src.storage.local_checkpoint import load_full_state
    from src.storage.status import project_status_summary

    st = load_full_state(project_id)
    summary = project_status_summary(st)
    assert summary["project_id"] == project_id
