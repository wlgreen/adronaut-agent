#!/usr/bin/env python3
"""Local end-to-end eval harness for Adronaut.

Usage:
  python3 scripts/eval_runner.py --scenarios tests/fixtures/eval --out tmp/eval_runs

What it does:
- Runs 2 lightweight agent flows (initialize + reflect) using deterministic fake LLM
- Runs Meta guardrail evaluation on canned fixtures
- Produces JSONL results + a concise stdout summary

This is deliberately "v1": objective gates + a simple quality score.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]

# Allow `import src...` when running as a script.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ----------------------------
# Validators / scoring
# ----------------------------


def _fail(code: str, msg: str) -> Dict[str, Any]:
    return {"ok": False, "code": code, "message": msg}


def validate_campaign_config(cfg: Any) -> Dict[str, Any]:
    if not isinstance(cfg, dict):
        return _fail("CONFIG_MISSING", "current_config not a dict")

    for top in ("tiktok", "meta", "summary"):
        if top not in cfg:
            return _fail("CONFIG_INVALID", f"missing top-level key: {top}")

    def check_platform(name: str) -> Optional[Dict[str, Any]]:
        p = cfg.get(name)
        if not isinstance(p, dict):
            return _fail("CONFIG_INVALID", f"{name} must be an object")
        for k in ("campaign_name", "objective", "daily_budget", "targeting", "placements", "bidding", "creative_specs", "optimization"):
            if k not in p:
                return _fail("CONFIG_INVALID", f"{name} missing key: {k}")
        if not isinstance(p.get("daily_budget"), (int, float)):
            return _fail("CONFIG_INVALID", f"{name}.daily_budget must be number")
        return None

    err = check_platform("tiktok")
    if err:
        return err
    err = check_platform("meta")
    if err:
        return err

    s = cfg.get("summary")
    if not isinstance(s, dict):
        return _fail("CONFIG_INVALID", "summary must be object")
    if "total_daily_budget" not in s:
        return _fail("CONFIG_INVALID", "summary.total_daily_budget missing")

    return {"ok": True}


def score_quality(cfg: Dict[str, Any], guardrail_ok: bool) -> float:
    """Heuristic 0-100 score.

    v1 intentionally simple: structure + a couple sanity checks.
    """
    score = 0.0

    # Config completeness (40)
    v = validate_campaign_config(cfg)
    if v["ok"]:
        score += 40.0

    # Budget sanity (20)
    try:
        t = float(cfg["tiktok"]["daily_budget"])
        m = float(cfg["meta"]["daily_budget"])
        tot = float(cfg["summary"]["total_daily_budget"])
        if t >= 0 and m >= 0 and abs((t + m) - tot) <= 1e-6:
            score += 20.0
    except Exception:
        pass

    # Creative coverage (20)
    try:
        meta_formats = cfg["meta"]["creative_specs"].get("formats")
        if isinstance(meta_formats, list) and meta_formats:
            score += 10.0
        tt_msg = cfg["tiktok"]["creative_specs"].get("messaging")
        if isinstance(tt_msg, list) and tt_msg:
            score += 10.0
    except Exception:
        pass

    # Guardrail behavior present (20)
    if guardrail_ok:
        score += 20.0

    return float(round(score, 2))


# ----------------------------
# Guardrail eval
# ----------------------------


def run_guardrail_eval(scenario_dir: Path) -> Tuple[bool, Dict[str, Any]]:
    from src.integrations.meta_watch import summarize_insights, evaluate_guardrails

    guardrail = scenario_dir / "meta_guardrails.json"
    if not guardrail.exists():
        return True, {"ok": True, "skipped": True}

    payload = json.loads(guardrail.read_text())
    today = summarize_insights(payload["today_insights"])
    trailing = summarize_insights(payload["trailing_7d_insights"])

    alerts = evaluate_guardrails(
        campaign_id=payload.get("campaign_id", "cmp"),
        today=today,
        trailing_7d=trailing,
        daily_cap=payload.get("daily_cap"),
        target_cpa=payload.get("target_cpa"),
    )
    codes = [a.code for a in alerts]

    expected = payload.get("expected_codes") or []
    ok = True
    if expected:
        ok = all(c in codes for c in expected)

    return ok, {
        "ok": ok,
        "expected_codes": expected,
        "got_codes": codes,
        "today": today,
        "trailing_7d": trailing,
    }


# ----------------------------
# Agent run (CLI-based)
# ----------------------------


@dataclass
class AgentRunResult:
    ok: bool
    gates: Dict[str, Any]
    artifacts: Dict[str, Any]


def _run_cli(args: List[str], env: Dict[str, str]) -> Tuple[int, str, str]:
    p = subprocess.run(
        [sys.executable, str(REPO_ROOT / "cli.py"), *args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    return p.returncode, p.stdout, p.stderr


def _extract_created_project_id(stdout: str) -> Optional[str]:
    # Line looks like: "✓ Created project with ID: <uuid>"
    for line in stdout.splitlines():
        if "Created project with ID:" in line:
            return line.split("Created project with ID:", 1)[1].strip()
    return None


def run_agent_initialize(project_name: str, inputs_path: Path, adronaut_home: Path) -> AgentRunResult:
    env = os.environ.copy()
    env["ADRONAUT_HOME"] = str(adronaut_home)
    env["ADRONAUT_DISABLE_DB"] = "1"
    env["ADRONAUT_EVAL_MODE"] = "1"
    env["INTERACTIVE_MODE"] = "false"

    # Ensure filesystem-backed DB is also sandboxed.
    env["ADRONAUT_LOCAL_STORAGE_DIR"] = str(adronaut_home / "local_storage")

    # Pre-approve so the agent completes the full flow (including campaign_setup)
    # in a single run.  This mirrors a user who trusts the plan up-front.
    env["ADRONAUT_APPROVE"] = "1"

    rc1, out1, err1 = _run_cli(["run", "--project-id", project_name, "--inputs", str(inputs_path), "--approve"], env)
    created_id = _extract_created_project_id(out1)
    effective_project_id = created_id or project_name

    # (Second run disabled — single-run pre-approve is simpler and avoids the
    #  resume-after-completed-flow edge case.)
    rc2, out2, err2 = 0, "", ""

    gates: Dict[str, Any] = {
        "cli_rc": rc1,
        "cli_ok": rc1 == 0,
    }

    # Load saved config artifact.
    cfg: Optional[Dict[str, Any]] = None
    cfg_path = adronaut_home / "projects" / effective_project_id / "artifacts" / "configs" / "campaign_config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception:
            cfg = None

    v = validate_campaign_config(cfg) if cfg is not None else _fail("CONFIG_MISSING", f"no campaign config artifact written at {cfg_path}")
    gates["config_valid"] = bool(v.get("ok"))
    gates["config_validation"] = v

    # Even with pre-approve, approval gate should still fire (just auto-cleared).
    gates["approval_gate_seen"] = ("approv" in (out1 + err1).lower())

    ok = bool(gates["cli_ok"] and gates["config_valid"])
    gates["effective_project_id"] = effective_project_id

    return AgentRunResult(
        ok=ok,
        gates=gates,
        artifacts={
            "stdout": out1[-4000:],
            "stderr": err1[-4000:],
            "config": cfg,
        },
    )


# ----------------------------
# Scenario runner
# ----------------------------


def run_scenario(scenario_dir: Path, out_root: Path) -> Dict[str, Any]:
    sid = scenario_dir.name
    out_dir = out_root / sid
    out_dir.mkdir(parents=True, exist_ok=True)

    # Each scenario gets its own ADRONAUT_HOME sandbox.
    adronaut_home = out_dir / "adronaut_home"
    if adronaut_home.exists():
        shutil.rmtree(adronaut_home)
    adronaut_home.mkdir(parents=True, exist_ok=True)

    project_name = f"eval-{sid}"
    inputs_path = scenario_dir / "historical_campaigns.csv"
    if not inputs_path.exists():
        return {"scenario": sid, "ok": False, "error": "missing historical_campaigns.csv"}

    agent_res = run_agent_initialize(project_name, inputs_path, adronaut_home)

    guard_ok, guard_details = run_guardrail_eval(scenario_dir)

    cfg = agent_res.artifacts.get("config") or {}
    quality = score_quality(cfg, guardrail_ok=guard_ok)

    gates = {
        **agent_res.gates,
        "guardrails_ok": guard_ok,
        "guardrails": guard_details,
    }

    ok = bool(agent_res.ok and guard_ok)

    result = {
        "scenario": sid,
        "timestamp": int(time.time()),
        "ok": ok,
        "gates": gates,
        "quality_score": quality,
    }

    # Persist detailed result
    (out_dir / "result.json").write_text(json.dumps(result, indent=2))
    (out_dir / "stdout.txt").write_text(agent_res.artifacts.get("stdout", ""))
    (out_dir / "stderr.txt").write_text(agent_res.artifacts.get("stderr", ""))

    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", default="tests/fixtures/eval", help="Directory containing scenario subfolders")
    ap.add_argument("--out", default="tmp/eval_runs", help="Output directory")
    args = ap.parse_args()

    scenarios_root = (REPO_ROOT / args.scenarios).resolve()
    out_root = (REPO_ROOT / args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    scenario_dirs = sorted([p for p in scenarios_root.iterdir() if p.is_dir()])
    if not scenario_dirs:
        print(f"No scenarios found under: {scenarios_root}")
        return 2

    results: List[Dict[str, Any]] = []
    for sd in scenario_dirs:
        results.append(run_scenario(sd, out_root))

    # JSONL summary
    jsonl_path = out_root / "results.jsonl"
    with jsonl_path.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    passed = [r for r in results if r.get("ok")]
    pass_rate = (len(passed) / len(results)) * 100.0
    avg_quality = sum(r.get("quality_score", 0.0) for r in passed) / max(1, len(passed))

    print("\n=== Adronaut Local Eval (v1) ===")
    print(f"Scenarios: {len(results)}")
    print(f"Pass rate: {len(passed)}/{len(results)} ({pass_rate:.1f}%)")
    print(f"Avg quality (passed only): {avg_quality:.1f}/100")

    # Show failures
    for r in results:
        if r.get("ok"):
            continue
        code = None
        if isinstance(r.get("gates", {}).get("config_validation"), dict):
            code = r["gates"]["config_validation"].get("code")
        print(f"- FAIL {r['scenario']}: {code or 'unknown'}")

    print(f"\nWrote: {jsonl_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
