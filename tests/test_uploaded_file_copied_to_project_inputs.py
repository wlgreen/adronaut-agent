from pathlib import Path

from src.storage.file_manager import upload_file
from src.storage.paths import project_inputs_dir


def test_upload_file_copies_into_project_inputs(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))

    src = tmp_path / "src.txt"
    src.write_text("hello")

    project_id = "p_inputs"
    storage_path = upload_file(str(src), project_id)

    stored = Path(storage_path)
    assert stored.exists()
    assert stored.parent == project_inputs_dir(project_id) / "uploaded"
    assert stored.read_text() == "hello"
