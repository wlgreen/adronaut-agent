from src.agent.graph import _continue_or_execute
from src.agent.state import create_initial_state


def test_continue_or_execute_saves_when_approval_pending():
    st = create_initial_state(project_id="p", uploaded_files=[], session_num=1)
    st["plan"] = {"steps": [{"id": "s1", "action": "campaign_setup"}]}
    st["plan_step_index"] = 0
    st["approval_status"] = "pending"
    assert _continue_or_execute(st) == "save"
