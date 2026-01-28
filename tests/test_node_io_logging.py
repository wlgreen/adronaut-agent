from src.agent.nodes import load_context_node
from src.agent.state import create_initial_state


def test_track_node_logs_input_output(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_DISABLE_DB", "1")
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    state = create_initial_state(project_id="p1", uploaded_files=[], session_num=1)
    out = load_context_node(state)

    assert "node_outputs" in out
    assert "load_context" in out["node_outputs"]
    records = out["node_outputs"]["load_context"]
    assert isinstance(records, list)
    assert len(records) >= 1
    rec = records[-1]
    assert "input" in rec and "output" in rec
    assert rec["input"].get("project_id") == "p1"
    assert rec["output"].get("project_id") == "p1"
