from src.storage.paths import (
    adronaut_home,
    global_dir,
    project_artifact_kind_dir,
    project_logs_dir,
    project_state_dir,
)


def test_paths_use_adronaut_home(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    assert adronaut_home() == tmp_path
    assert global_dir() == tmp_path / "global"

    pid = "p123"
    assert project_state_dir(pid) == tmp_path / "projects" / pid / "state"
    assert project_logs_dir(pid) == tmp_path / "projects" / pid / "logs"
    assert project_artifact_kind_dir(pid, "configs") == tmp_path / "projects" / pid / "artifacts" / "configs"
