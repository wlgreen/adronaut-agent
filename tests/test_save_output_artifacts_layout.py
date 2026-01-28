import json

from pathlib import Path

from cli import save_output_artifacts


def test_save_output_artifacts_writes_subdirs(tmp_path):
    final_state = {
        "project_id": "p1",
        "session_num": 1,
        "current_phase": "initialized",
        "iteration": 0,
        "flow_status": "completed",
        "completed_nodes": [],
        "knowledge_facts": {},
        "current_strategy": {},
        "experiment_plan": {},
        "artifacts": {"s1": {"creative": {"x": 1}, "rating": {"y": 2}}},
        "current_config": {"meta": {"daily_budget": 10}},
    }

    saved = save_output_artifacts(final_state, Path(tmp_path))
    # ensure files are created in expected subfolders
    assert (tmp_path / "configs" / "campaign_config.json").exists()
    assert (tmp_path / "creatives" / "creative_prompts.json").exists()
    assert (tmp_path / "reports" / "report.md").exists()

    # sanity check json contents
    cfg = json.loads((tmp_path / "configs" / "campaign_config.json").read_text())
    assert cfg["meta"]["daily_budget"] == 10

    assert any("configs/campaign_config.json" in s for s in saved)
