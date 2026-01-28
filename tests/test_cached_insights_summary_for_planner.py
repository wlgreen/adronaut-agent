from src.storage.analysis_store import save_insights_cache, summarize_cached_insights_for_planner


def test_summarize_cached_insights_for_planner(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    project_id = "p_sum"
    storage_path = str(tmp_path / "projects" / project_id / "inputs" / "uploaded" / "hist.csv")

    insights = {
        "strategy": {
            "insights": {
                "patterns": ["p1", "p2"],
                "strengths": ["s1"],
                "weaknesses": ["w1"],
            }
        },
        "execution_timeline": {"days": 7},
    }
    save_insights_cache(project_id, storage_path, insights)

    s = summarize_cached_insights_for_planner(project_id)
    assert "patterns" in s
    assert "hist.csv" in s
