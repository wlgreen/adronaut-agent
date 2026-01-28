import json

from src.agent.nodes import load_context_node
from src.agent.state import create_initial_state


def test_node_io_written_under_project_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_DISABLE_DB", "1")
    monkeypatch.setenv("ADRONAUT_CHECKPOINT_DIR", str(tmp_path))

    project_id = "p_file_log"
    state = create_initial_state(project_id=project_id, uploaded_files=[], session_num=1)
    load_context_node(state)

    log_path = tmp_path / project_id / "node_io.jsonl"
    assert log_path.exists()

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    obj = json.loads(lines[-1])
    assert obj["node"] == "load_context"
    assert obj["input"]["project_id"] == project_id
    assert obj["output"]["project_id"] == project_id
