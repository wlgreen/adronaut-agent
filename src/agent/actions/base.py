from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Protocol

from ..state import AgentState


class ActionSkill(Protocol):
    """A single executable action available to the planning/execution loop."""

    name: str
    description: str

    def run(self, state: AgentState) -> AgentState: ...

    def verify(self, state: AgentState) -> Tuple[bool, List[str]]:
        """Return (ok, notes). Default: (True, [])."""
        ...

    def requires_approval(self, state: AgentState) -> bool:
        """Whether this step should be gated behind human approval."""
        ...
