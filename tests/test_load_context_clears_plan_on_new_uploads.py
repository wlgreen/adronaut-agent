from src.agent.nodes import load_context_node
from src.agent.state import create_initial_state
from src.storage.local_checkpoint import save_full_state


def test_load_context_clears_plan_on_new_uploads(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))
    monkeypatch.setenv("ADRONAUT_DISABLE_DB", "1")

    project_id = "p_plan"

    # checkpoint with a plan + old uploaded_files
    checkpoint_state = create_initial_state(project_id=project_id, uploaded_files=[], session_num=1)
    checkpoint_state["uploaded_files"] = [{"storage_path": "/old/path.csv", "original_filename": "old.csv"}]
    checkpoint_state["plan"] = {"steps": [{"id": "s1", "action": "insight"}]}
    checkpoint_state["plan_step_index"] = 0
    checkpoint_state["project_loaded"] = True
    save_full_state(project_id, dict(checkpoint_state))

    # incoming uploads differ
    incoming = [{"storage_path": "/new/path.csv", "original_filename": "new.csv"}]
    state = create_initial_state(project_id=project_id, uploaded_files=incoming, session_num=1)
    out = load_context_node(state)

    assert out.get("uploaded_files") == incoming
    assert out.get("plan") is None
    assert out.get("file_analyses") == []
