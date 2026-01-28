import json

from src.agent.nodes import analyze_files_node
from src.agent.state import create_initial_state
from src.storage.paths import project_analysis_dir
from src.storage.file_manager import upload_file


def test_analyze_files_persists_file_analyses(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))
    monkeypatch.setenv("ADRONAUT_DISABLE_DB", "1")

    project_id = "p_analysis"

    # create a tiny csv file and upload into local storage
    f = tmp_path / "hist.csv"
    f.write_text("campaign_name,spend,conversions\nA,10,1\n")
    storage_path = upload_file(str(f), project_id)

    state = create_initial_state(
        project_id=project_id,
        uploaded_files=[{"storage_path": storage_path, "original_filename": "hist.csv"}],
        session_num=1,
    )

    out = analyze_files_node(state)
    assert out.get("file_analyses")

    p = project_analysis_dir(project_id) / "file_analyses.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert isinstance(data, list)
    assert data[0].get("file_name") == "hist.csv"
