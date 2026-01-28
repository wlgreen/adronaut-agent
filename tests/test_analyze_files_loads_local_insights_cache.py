from src.agent.nodes import analyze_files_node
from src.agent.state import create_initial_state
from src.storage.analysis_store import save_insights_cache


def test_analyze_files_loads_local_insights_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))
    monkeypatch.setenv("ADRONAUT_DISABLE_DB", "1")

    project_id = "p_cache"
    storage_path = str(tmp_path / "projects" / project_id / "inputs" / "uploaded" / "hist.csv")

    # Create a minimal uploaded file
    p = tmp_path / "projects" / project_id / "inputs" / "uploaded"
    p.mkdir(parents=True, exist_ok=True)
    (p / "hist.csv").write_text("campaign_name,spend,conversions\nA,10,1\n")

    # Write insights cache for it
    cache = {"strategy": {"insights": {"patterns": ["x"]}}}
    save_insights_cache(project_id, storage_path, cache)

    st = create_initial_state(
        project_id=project_id,
        uploaded_files=[{"storage_path": storage_path, "original_filename": "hist.csv"}],
        session_num=1,
    )

    out = analyze_files_node(st)
    assert out["file_analyses"], "expected file_analyses"
    fa = out["file_analyses"][0]
    assert fa.get("cached") is True
    assert fa.get("insights_cache") == cache
