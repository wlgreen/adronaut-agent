import os


def test_plan_execute_verify_loop_smoke(monkeypatch):
    # Avoid interactive prompts
    os.environ["INTERACTIVE_MODE"] = "false"
    os.environ.pop("TAVILY_API_KEY", None)

    # --- Patch Gemini so planning doesn't require real API key ---
    class DummyGemini:
        def generate_json(self, prompt=None, system_instruction=None, temperature=None, task_name=None, **kwargs):
            # Combined planner output (includes decision + steps)
            if task_name and "Planning" in task_name:
                return {
                    "decision": "initialize",
                    "reasoning": "New project, starting from scratch",
                    "steps": [
                        {"id": "s_discovery", "action": "discovery", "rationale": "", "success": ""},
                        {"id": "s_collect", "action": "data_collection", "rationale": "", "success": ""},
                        {"id": "s_insight", "action": "insight", "rationale": "", "success": ""},
                        {"id": "s_campaign", "action": "campaign_setup", "rationale": "", "success": ""},
                        {"id": "s_save", "action": "save", "rationale": "", "success": ""},
                    ],
                }
            return {}

    import src.llm.gemini as gem
    monkeypatch.setattr(gem, "get_gemini", lambda: DummyGemini())

    # Import after patching Gemini
    from src.agent.state import create_initial_state
    from src.agent.graph import get_campaign_agent

    # --- Patch persistence to no-op (avoid file I/O during test) ---
    import src.database.persistence as persistence
    monkeypatch.setattr(persistence.ProjectPersistence, "load_project", staticmethod(lambda project_id: None))
    monkeypatch.setattr(persistence.ProjectPersistence, "save_project", staticmethod(lambda project_data: None))
    monkeypatch.setattr(persistence.SessionPersistence, "complete_session", staticmethod(lambda session_id, status: None))

    # --- Patch file analysis to no-op ---
    import src.agent.nodes as nodes
    monkeypatch.setattr(nodes, "analyze_files_node", lambda state: {**state, "file_analyses": [], "cycle_num": state.get("cycle_num", 0) + 1})

    # --- Patch discovery/insight/campaign_setup/save to set minimal fields so verify passes ---
    def fake_discovery(state):
        state.setdefault("knowledge_facts", {})
        state["knowledge_facts"].update({
            "product_description": {"value": "test product", "confidence": 1.0, "source": "test"},
            "target_budget": {"value": 100.0, "confidence": 1.0, "source": "test"},
        })
        state["cycle_num"] = state.get("cycle_num", 0) + 1
        return state

    def fake_data_collection(state):
        state.setdefault("historical_data", {})
        state["historical_data"]["metadata"] = {"file_count": 0, "total_rows": 0}
        state["cycle_num"] = state.get("cycle_num", 0) + 1
        return state

    def fake_insight(state):
        state["current_strategy"] = {"insights": {"patterns": ["p1"]}}
        state["cycle_num"] = state.get("cycle_num", 0) + 1
        return state

    def fake_campaign_setup(state):
        state["current_config"] = {"meta": {"campaign": "x"}}
        state["cycle_num"] = state.get("cycle_num", 0) + 1
        return state

    def fake_save(state):
        state["cycle_num"] = state.get("cycle_num", 0) + 1
        return state

    monkeypatch.setattr(nodes, "discovery_node", fake_discovery)
    monkeypatch.setattr(nodes, "data_collection_node", fake_data_collection)
    monkeypatch.setattr(nodes, "insight_node", fake_insight)
    monkeypatch.setattr(nodes, "campaign_setup_node", fake_campaign_setup)
    monkeypatch.setattr(nodes, "save_state_node", fake_save)

    # --- Run graph ---
    state = create_initial_state(project_id="test-project", uploaded_files=[], session_num=1)
    agent = get_campaign_agent()
    out = agent.invoke(state)

    # Assertions
    assert out.get("plan") is not None
    assert out.get("decision") == "initialize"
    assert out.get("plan_step_index", 0) >= 3  # should have advanced through multiple steps
    assert out.get("current_strategy")
    assert out.get("current_config")
