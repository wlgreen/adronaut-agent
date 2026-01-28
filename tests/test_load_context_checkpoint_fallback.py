from src.agent.nodes import load_context_node
from src.agent.state import create_initial_state


def test_load_context_falls_back_to_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_CHECKPOINT_DIR", str(tmp_path))
    monkeypatch.setenv("ADRONAUT_DISABLE_DB", "1")

    from src.storage.local_checkpoint import save_full_state

    project_id = "eco-bottle-001"

    # Minimal full AgentState payload that load_context can consume.
    checkpoint_state = create_initial_state(project_id=project_id, uploaded_files=[], session_num=1)
    checkpoint_state.update(
        {
            "project_loaded": True,
            "current_phase": "awaiting_results",
            "iteration": 1,
            "flow_status": "completed",
            "completed_nodes": ["save_state"],
            "last_completed_node": "save_state",
            "current_executing_node": None,
            "current_strategy": {"x": 1},
            "current_config": {"y": 2},
        }
    )

    save_full_state(project_id, dict(checkpoint_state))

    state = create_initial_state(project_id=project_id, uploaded_files=[], session_num=1)
    out = load_context_node(state)

    assert out.get("project_loaded") is True
    assert out.get("current_phase") == "awaiting_results"
    assert out.get("current_config") == {"y": 2}
    assert any("local checkpoint" in m for m in out.get("messages", []))
