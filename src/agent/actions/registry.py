from __future__ import annotations

from typing import Dict, List, Tuple

from .skills import CreativeGenerationSkill, NodeWrapperSkill


def _verify_discovery(state) -> Tuple[bool, List[str]]:
    kf = state.get("knowledge_facts", {})
    ok = bool(kf.get("product_description") and kf.get("target_budget"))
    notes: List[str] = []
    if not ok:
        notes.append("Missing product_description/target_budget")
    return ok, notes


def _verify_insight(state) -> Tuple[bool, List[str]]:
    ok = bool(state.get("current_strategy"))
    notes: List[str] = []
    if not ok:
        notes.append("Strategy missing")
    return ok, notes


def _verify_campaign_setup(state) -> Tuple[bool, List[str]]:
    ok = bool(state.get("current_config"))
    notes: List[str] = []
    if not ok:
        notes.append("Config missing")
    return ok, notes


def _approval_campaign_or_adjustment(_state) -> bool:
    return True


def build_action_registry() -> Dict[str, object]:
    """Create the action registry mapping action name -> skill implementation.

    We wrap existing node functions to avoid rewriting business logic.
    """
    from .. import nodes as agent_nodes

    return {
        "discovery": NodeWrapperSkill(
            name="discovery",
            description=(
                "Infer project context and populate knowledge_facts (e.g., product_description, "
                "target_budget, audience hints)."
            ),
            fn=agent_nodes.discovery_node,
            verify_fn=_verify_discovery,
        ),
        "data_collection": NodeWrapperSkill(
            name="data_collection",
            description=(
                "Parse uploaded files/inputs into state: historical_data, market_data, user_inputs, "
                "and experiment_results (if present)."
            ),
            fn=agent_nodes.data_collection_node,
        ),
        "insight": NodeWrapperSkill(
            name="insight",
            description=(
                "Generate current_strategy + experiment_plan from collected data and update key insights "
                "(may also enrich knowledge_facts)."
            ),
            fn=agent_nodes.insight_node,
            verify_fn=_verify_insight,
        ),
        "creative_generation": CreativeGenerationSkill(),
        "campaign_setup": NodeWrapperSkill(
            name="campaign_setup",
            description=(
                "Produce current_config (platform configs, budgets, targeting, creatives) and append to config_history; "
                "may require approval if it will be deployed externally."
            ),
            fn=agent_nodes.campaign_setup_node,
            verify_fn=_verify_campaign_setup,
            requires_approval_fn=_approval_campaign_or_adjustment,
        ),
        "reflection": NodeWrapperSkill(
            name="reflection",
            description=(
                "Analyze experiment_results to summarize performance deltas and populate patch/metrics context "
                "for the next iteration."
            ),
            fn=agent_nodes.reflection_node,
        ),
        "adjustment": NodeWrapperSkill(
            name="adjustment",
            description=(
                "Generate patch strategy and update current_config; append patch_history and/or new config version "
                "for optimization iterations."
            ),
            fn=agent_nodes.adjustment_node,
            requires_approval_fn=_approval_campaign_or_adjustment,
        ),
        "save": NodeWrapperSkill(
            name="save",
            description=(
                "Persist project/session state for resumption (plan/artifacts/flow tracking + configs/strategy)."
            ),
            fn=agent_nodes.save_state_node,
        ),
    }


def list_available_actions(registry: Dict[str, object]) -> List[str]:
    lines = []
    for name, skill in registry.items():
        desc = getattr(skill, "description", "")
        lines.append(f"- {name}: {desc}")
    return lines
