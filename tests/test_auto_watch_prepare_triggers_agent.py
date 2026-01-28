import json
from types import SimpleNamespace


def test_auto_watch_prepare_triggers_agent(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))
    monkeypatch.setenv("ADRONAUT_DISABLE_DB", "1")

    # create fake deployment result
    project_id = "p_auto"
    dep_dir = tmp_path / "projects" / project_id / "artifacts" / "deployments"
    dep_dir.mkdir(parents=True, exist_ok=True)
    dep_path = dep_dir / "campaign_p_auto_v0_deployment_result.json"
    dep_path.write_text(json.dumps({"campaign_id": "cmp_123", "guardrails": {"daily_cap": 10.0, "target_cpa": 5.0}}))

    # monkeypatch meta watch deps
    import cli

    class DummyRes:
        def __init__(self):
            self.insights = {"data": []}

    monkeypatch.setattr(cli, "fetch_campaign_metrics", lambda api, campaign_id, a, b: DummyRes(), raising=False)

    # Patch integrations functions used inside auto_watch_command via their modules
    from src.integrations import meta_monitor as mm
    monkeypatch.setattr(mm, "fetch_campaign_metrics", lambda api, campaign_id, a, b: DummyRes(), raising=True)

    from src.integrations import meta_watch as mw

    monkeypatch.setattr(mw, "summarize_insights", lambda insights: {"spend": 100.0, "ctr": 0.0, "cpa": 99.0}, raising=True)

    class A:
        def __init__(self):
            self.code = "CPA_HIGH"
            self.severity = "critical"
            self.message = "bad"
            self.suggested_action = "pause"

    monkeypatch.setattr(mw, "evaluate_guardrails", lambda **kwargs: [A()], raising=True)

    # monkeypatch agent invocation to assert injected results
    from src.agent import graph as graph_mod

    class DummyAgent:
        def invoke(self, state):
            assert state.get("injected_experiment_results"), "expected injected_experiment_results"
            # simulate approval pending
            state["approval_status"] = "pending"
            return state

    monkeypatch.setattr(graph_mod, "get_campaign_agent", lambda: DummyAgent(), raising=True)

    args = SimpleNamespace(project_id=project_id, mode="prepare", deployment_result=None, dry_run=True)
    code = cli.auto_watch_command(args)
    assert code == 0
