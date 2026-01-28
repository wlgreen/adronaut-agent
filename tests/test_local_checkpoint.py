import os

from src.storage.local_checkpoint import (
    full_state_path,
    load_full_state,
    save_full_state,
)


def test_save_and_load_full_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_CHECKPOINT_DIR", str(tmp_path))

    project_id = "proj_123"
    state = {"project_id": project_id, "foo": {"bar": 1}}

    path = save_full_state(project_id, state)
    assert path.exists()
    assert path == full_state_path(project_id)

    loaded = load_full_state(project_id)
    assert loaded == state


def test_load_full_state_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_CHECKPOINT_DIR", str(tmp_path))
    assert load_full_state("does_not_exist") is None
