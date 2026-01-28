import json

from src.storage.analysis_store import load_insights_cache, save_insights_cache, insights_cache_path


def test_save_and_load_insights_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    project_id = "p_insights"
    storage_path = str(tmp_path / "projects" / project_id / "inputs" / "uploaded" / "hist.csv")

    payload = {"strategy": {"insights": {"patterns": ["x"]}}, "execution_timeline": {"days": 7}}
    p = save_insights_cache(project_id, storage_path, payload)

    assert p == insights_cache_path(project_id, storage_path)
    assert p.exists()

    raw = json.loads(p.read_text())
    assert raw["storage_path"] == storage_path

    loaded = load_insights_cache(project_id, storage_path)
    assert loaded == payload
