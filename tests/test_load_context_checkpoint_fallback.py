from src.agent.nodes import load_context_node
from src.agent.state import create_initial_state


def test_load_context_falls_back_to_checkpoint(tmp_path, monkeypatch):
    # Ensure checkpoint dir is temp
    monkeypatch.setenv("ADRONAUT_CHECKPOINT_DIR", str(tmp_path))

    # Mock DB load to return None
    from src.database import persistence as persistence_mod

    monkeypatch.setattr(persistence_mod.ProjectPersistence, "load_project", staticmethod(lambda _pid: None))

    # Create a checkpoint file manually via helper
    from src.storage.local_checkpoint import save_checkpoint

    project_id = "eco-bottle-001"
    checkpoint_state = {
        "project_id": project_id,
        "current_phase": "awaiting_results",
        "iteration": 1,
        "flow_status": "completed",
        "completed_nodes": ["save_state"],
        "last_completed_node": "save_state",
        "current_executing_node": None,
        "historical_data": {},
        "market_data": {},
        "user_inputs": {},
        "current_strategy": {"x": 1},
        "experiment_plan": {},
        "experiment_results": [],
        "current_config": {"y": 2},
        "config_history": [],
        "patch_history": [],
        "metrics_timeline": [],
        "best_performers": {},
        "threshold_status": None,
        "plan": None,
        "plan_step_index": 0,
        "artifacts": {},
        "verification": {},
        "requires_approval": False,
        "approval_status": None,
        "knowledge_facts": {},
    }
    save_checkpoint(project_id, checkpoint_state)

    state = create_initial_state(project_id=project_id, uploaded_files=[], session_num=1)
    out = load_context_node(state)

    assert out.get("project_loaded") is True
    assert out.get("current_phase") == "awaiting_results"
    assert out.get("current_config") == {"y": 2}
    assert any("local checkpoint" in m for m in out.get("messages", []))
