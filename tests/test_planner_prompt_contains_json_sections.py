import json

from src.agent.plan_nodes import _build_planner_prompt
from src.agent.state import create_initial_state
from src.storage.analysis_store import save_insights_cache


def test_planner_prompt_contains_json_sections(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    project_id = "p_prompt"
    storage_path = str(tmp_path / "projects" / project_id / "inputs" / "uploaded" / "hist.csv")

    # seed cached insights
    save_insights_cache(project_id, storage_path, {"strategy": {"insights": {"patterns": ["p1"]}}})

    st = create_initial_state(project_id=project_id, uploaded_files=[], session_num=1)
    st.setdefault("knowledge_facts", {})
    st["knowledge_facts"]["repo_search"] = {"value": {"queries": ["x"], "hit_count": 1}, "confidence": 1.0, "source": "repo_search"}

    prompt = _build_planner_prompt(st)

    assert "CACHED INSIGHTS (JSON" in prompt
    assert "REPO SEARCH SUMMARY (JSON" in prompt

    # ensure cached insights block is JSON parseable
    # Extract the cached insights JSON block by section boundaries
    marker = "CACHED INSIGHTS (JSON"
    start = prompt.find(marker)
    assert start != -1
    start = prompt.find("\n", start) + 1
    end = prompt.find("LATEST REFLECTION (JSON", start)
    assert end != -1
    cached_block = prompt[start:end].strip()
    json.loads(cached_block)
