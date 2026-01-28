import json

from src.agent.plan_nodes import _build_planner_prompt
from src.agent.state import create_initial_state


def test_planner_prompt_includes_latest_reflection_json(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    st = create_initial_state(project_id="p_lr", uploaded_files=[], session_num=1)
    st.setdefault("knowledge_facts", {})
    st["knowledge_facts"]["latest_reflection"] = {
        "value": {"threshold_met": False, "winners": {"best_platform": "tiktok"}},
        "confidence": 0.7,
        "source": "reflection",
    }

    prompt = _build_planner_prompt(st)
    assert "LATEST REFLECTION (JSON" in prompt

    # Extract latest reflection block
    marker = "LATEST REFLECTION (JSON"
    start = prompt.find(marker)
    start = prompt.find("\n", start) + 1
    end = prompt.find("REPO SEARCH SUMMARY (JSON", start)
    block = prompt[start:end].strip()
    json.loads(block)
