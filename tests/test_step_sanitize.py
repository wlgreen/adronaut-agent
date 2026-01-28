from src.agent.step_schema import sanitize_step


def test_sanitize_step_drops_unknown_keys():
    step = {
        "id": "s1",
        "action": "repo_search",
        "rationale": "r",
        "success": "s",
        "requires_approval": False,
        "search": ["x"],
        "unknown": 123,
    }
    out = sanitize_step("repo_search", step)
    assert "unknown" not in out
    assert out["search"] == ["x"]
