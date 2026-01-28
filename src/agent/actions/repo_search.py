from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .skills import BaseSkill
from ..state import AgentState


def _infer_queries_from_state(state: AgentState) -> List[str]:
    """Heuristic (Option 2): infer search queries from file types + decision/phase."""
    plan = state.get("plan") or {}
    decision = plan.get("decision") or state.get("decision") or ""
    phase = state.get("current_phase") or ""

    file_types = [fa.get("type") for fa in (state.get("file_analyses") or []) if isinstance(fa, dict)]
    file_types_set = {ft for ft in file_types if ft}

    queries: List[str] = []

    # By decision
    if decision == "initialize":
        queries += [
            "discovery",
            "knowledge_facts",
            "data_collection",
            "historical_data",
            "generate_insights",
            "current_strategy",
            "campaign_setup",
            "current_config",
            "requires_approval",
        ]
    elif decision == "reflect":
        queries += [
            "experiment_results",
            "reflection",
            "analyze_experiment_results",
            "generate_patch_strategy",
            "patch_history",
            "adjustment",
            "metrics_timeline",
            "watch-meta",
            "guardrails",
        ]
    elif decision == "enrich":
        queries += [
            "market_data",
            "benchmarks",
            "competitor",
            "enrich",
            "tavily",
            "discovery",
        ]
    elif decision == "continue":
        # fall back to phase hints
        queries += ["continue", "current_phase", phase]

    # By current phase
    if phase:
        queries += [phase]
        if phase == "strategy_built":
            queries += ["campaign_setup", "current_config"]
        elif phase == "optimizing":
            queries += ["adjustment", "patch_history"]

    # By uploaded file types
    if "historical" in file_types_set:
        queries += ["historical", "historical_data", "DataLoader", "analyze_file"]
    if "experiment_results" in file_types_set:
        queries += ["experiment_results", "reflection", "analyze_experiment_results", "adjustment"]
    if "enrichment" in file_types_set:
        queries += ["enrichment", "market_data", "competitor", "benchmarks"]

    # De-dupe while preserving order
    seen = set()
    out: List[str] = []
    for q in queries:
        q = (q or "").strip()
        if not q:
            continue
        if q in seen:
            continue
        seen.add(q)
        out.append(q)

    # Keep it bounded
    return out[:12]


def _iter_candidate_files(repo_root: Path) -> List[Path]:
    """Keep search bounded to relevant text files."""
    candidates: List[Path] = []

    # Code
    for pat in ["src/**/*.py", "tests/**/*.py", "cli.py"]:
        candidates += list(repo_root.glob(pat))

    # Docs
    for pat in ["README.md", "ARCHITECTURE.md", "docs/**/*.md", "*.md"]:
        candidates += list(repo_root.glob(pat))

    # De-dupe
    uniq: Dict[str, Path] = {}
    for p in candidates:
        try:
            rp = str(p.resolve())
        except Exception:
            continue
        uniq[rp] = p
    return list(uniq.values())


def _search_file(path: Path, queries: List[str], max_hits_per_file: int = 25) -> List[Dict[str, object]]:
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return []

    lines = text.splitlines()
    hits: List[Dict[str, object]] = []

    for i, line in enumerate(lines, start=1):
        for q in queries:
            if q and q in line:
                # include small context window
                start = max(0, i - 2)
                end = min(len(lines), i + 1)
                snippet = "\n".join(lines[start:end])
                hits.append({"line": i, "query": q, "snippet": snippet})
                if len(hits) >= max_hits_per_file:
                    return hits

    return hits


@dataclass
class RepoSearchSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="repo_search",
            description=(
                "Search the codebase for decision/file-type-specific keywords and summarize results into "
                "knowledge_facts.repo_search (then force a replan)."
            ),
        )

    def run(self, state: AgentState) -> AgentState:
        # Infer queries (Option 2)
        queries = _infer_queries_from_state(state)

        # Repo root = .../src/agent/actions/repo_search.py -> repo
        repo_root = Path(__file__).resolve().parents[3]

        candidates = _iter_candidate_files(repo_root)

        results: List[Dict[str, object]] = []
        for p in candidates:
            rel = str(p.relative_to(repo_root))
            file_hits = _search_file(p, queries)
            if file_hits:
                results.append({"file": rel, "hits": file_hits})

        hit_count = sum(len(r.get("hits", [])) for r in results)
        top_files = [r["file"] for r in results[:10]]

        # Store summary for the planner
        state.setdefault("knowledge_facts", {})
        state["knowledge_facts"]["repo_search"] = {
            "value": {
                "queries": queries,
                "hit_count": hit_count,
                "top_files": top_files,
            },
            "confidence": 1.0,
            "source": "repo_search",
        }

        # Store raw-ish results in artifacts
        step_id = state.get("current_step_id") or "repo_search"
        state.setdefault("artifacts", {})
        state["artifacts"].setdefault(step_id, {})
        # cap payload
        state["artifacts"][step_id]["repo_search_results"] = results[:25]

        state.setdefault("messages", []).append(
            f"Repo search: {hit_count} hits across {len(results)} files (queries={queries})"
        )

        # Force replan so the planner can use repo_search findings
        state["plan"] = None
        state["plan_step_index"] = 0
        state.setdefault("messages", []).append("Repo search complete; forcing replan")

        return state

    def verify(self, state: AgentState) -> Tuple[bool, List[str]]:
        # Search itself is best-effort; even 0 hits can be informative.
        rf = state.get("knowledge_facts", {}).get("repo_search", {}).get("value", {})
        if not isinstance(rf, dict):
            return False, ["repo_search: missing summary"]
        if "queries" not in rf:
            return False, ["repo_search: missing queries"]
        return True, []
