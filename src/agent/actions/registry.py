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
            description="Discover product/context and populate knowledge_facts.",
            fn=agent_nodes.discovery_node,
            verify_fn=_verify_discovery,
        ),
        "data_collection": NodeWrapperSkill(
            name="data_collection",
            description="Collect/parse input data into state (historical/market/user inputs).",
            fn=agent_nodes.data_collection_node,
        ),
        "insight": NodeWrapperSkill(
            name="insight",
            description="Generate insights/strategy from data.",
            fn=agent_nodes.insight_node,
            verify_fn=_verify_insight,
        ),
        "campaign_setup": NodeWrapperSkill(
            name="campaign_setup",
            description="Generate campaign configuration(s) based on strategy.",
            fn=agent_nodes.campaign_setup_node,
            verify_fn=_verify_campaign_setup,
            requires_approval_fn=_approval_campaign_or_adjustment,
        ),
        "reflection": NodeWrapperSkill(
            name="reflection",
            description="Analyze experiment results and summarize performance.",
            fn=agent_nodes.reflection_node,
        ),
        "adjustment": NodeWrapperSkill(
            name="adjustment",
            description="Generate patch/adjustment strategy and update configuration.",
            fn=agent_nodes.adjustment_node,
            requires_approval_fn=_approval_campaign_or_adjustment,
        ),
        "save": NodeWrapperSkill(
            name="save",
            description="Persist state/artifacts for resumption.",
            fn=agent_nodes.save_state_node,
        ),
        "creative_generation": CreativeGenerationSkill(),
    }


def list_available_actions(registry: Dict[str, object]) -> List[str]:
    lines = []
    for name, skill in registry.items():
        desc = getattr(skill, "description", "")
        lines.append(f"- {name}: {desc}")
    return lines
