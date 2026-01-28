import json

from src.storage.analysis_store import load_inputs_hash, save_inputs_hash


def test_save_and_load_inputs_hash(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    project_id = "p_hash"
    uploaded_files = [{"storage_path": "/a", "original_filename": "a.csv"}]
    p = save_inputs_hash(project_id, uploaded_files)
    assert p.exists()

    v = load_inputs_hash(project_id)
    assert isinstance(v, str) and len(v) == 64

    payload = json.loads(p.read_text())
    assert payload["inputs_hash"] == v
