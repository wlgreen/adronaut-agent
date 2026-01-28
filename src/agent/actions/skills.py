from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from ..state import AgentState


@dataclass
class BaseSkill:
    name: str
    description: str

    def run(self, state: AgentState) -> AgentState:  # pragma: no cover
        raise NotImplementedError

    def verify(self, state: AgentState) -> Tuple[bool, List[str]]:
        return True, []

    def requires_approval(self, state: AgentState) -> bool:
        return False


class NodeWrapperSkill(BaseSkill):
    """Wrap an existing `*_node(state)` function in a skill interface."""

    def __init__(self, name: str, description: str, fn):
        super().__init__(name=name, description=description)
        self._fn = fn

    def run(self, state: AgentState) -> AgentState:
        return self._fn(state)


class CreativeGenerationSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="creative_generation",
            description="Generate creative prompts (MVP demo) and store them in artifacts.",
        )

    def run(self, state: AgentState) -> AgentState:
        # Minimal creative generation: generate prompts for a single test combo.
        from ...modules.creative_generator import generate_creative_prompts
        from ...modules.creative_rater import rate_creative_prompt

        plan = state.get("plan") or {}
        idx = int(state.get("plan_step_index", 0))
        steps = plan.get("steps") or []
        step = steps[idx] if idx < len(steps) else {}
        step_id = state.get("current_step_id") or step.get("id") or f"step_{idx}"

        user_inputs = state.get("user_inputs", {})
        product_desc = user_inputs.get("product_description") or state.get("knowledge_facts", {}).get(
            "product_description", {}
        ).get("value")

        if not product_desc:
            state.setdefault("errors", []).append("creative_generation: missing product_description")
            return state

        combo = {
            "combo_id": "demo_combo_1",
            "platform": "Meta",
            "audience": user_inputs.get("target_audience", "General"),
            "creative_style": "Professional",
        }
        gen = generate_creative_prompts(
            test_combination=combo,
            strategy=state.get("current_strategy", {}),
            user_inputs={"product_description": product_desc},
        )
        rating = rate_creative_prompt(
            original_prompt=gen.get("visual_prompt", ""),
            reviewed_prompt=gen.get("visual_prompt", ""),
            product_description=product_desc,
            required_keywords=None,
            brand_name=None,
            original_requirements={"platform": "Meta"},
        )

        state.setdefault("artifacts", {})
        state["artifacts"][step_id] = {"creative": gen, "rating": rating}
        state.setdefault("messages", []).append("Creative prompts generated")
        return state
