import os

from src.storage.local_checkpoint import checkpoint_path, load_checkpoint, save_checkpoint


def test_save_and_load_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_CHECKPOINT_DIR", str(tmp_path))

    project_id = "proj_123"
    state = {"project_id": project_id, "foo": {"bar": 1}}

    path = save_checkpoint(project_id, state)
    assert path.exists()
    assert path == checkpoint_path(project_id)

    loaded = load_checkpoint(project_id)
    assert loaded == state


def test_load_checkpoint_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_CHECKPOINT_DIR", str(tmp_path))
    assert load_checkpoint("does_not_exist") is None
