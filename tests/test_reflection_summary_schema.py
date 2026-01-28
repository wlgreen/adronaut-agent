from src.agent.actions.reflection_skill import ReflectionSkill
from src.agent.state import create_initial_state


def test_reflection_skill_writes_stable_summary(monkeypatch):
    # Monkeypatch reflection_node to inject a deterministic reflection_analysis
    from src import agent as agent_pkg

    from src.agent import nodes as agent_nodes

    def fake_reflection_node(state):
        state.setdefault("node_outputs", {})
        state["node_outputs"]["reflection_analysis"] = {
            "threshold_met": False,
            "threshold_gap": {"cpa_gap": 5.0},
            "performance_summary": {"overall_cpa": 20.0},
            "winners": {"best_platform": "tiktok"},
            "losers": {"worst_platform": "meta"},
            "variation_analysis": [{"variation_name": "A"}],
            "insights": ["i1"],
            "recommendations": ["r1"],
        }
        state["threshold_status"] = "not_met"
        state["current_phase"] = "optimizing"
        return state

    monkeypatch.setattr(agent_nodes, "reflection_node", fake_reflection_node, raising=True)

    st = create_initial_state(project_id="p_ref", uploaded_files=[], session_num=1)
    st["experiment_results"] = [{"dummy": 1}]

    out = ReflectionSkill().run(st)
    lf = out.get("knowledge_facts", {}).get("latest_reflection", {}).get("value")
    assert isinstance(lf, dict)
    assert "threshold_met" in lf
    assert "winners" in lf
    assert "recommended_next_actions" in lf
