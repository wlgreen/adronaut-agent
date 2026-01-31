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

# Load .env if present so GEMINI_API_KEY / OPENAI_API_KEY work in local runs.
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


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


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    import csv

    rows: List[Dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()})
    return rows


def _to_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, str) and x.strip() == "":
            return None
        return float(x)
    except Exception:
        return None


def compute_experiment_cpa(experiment_results_csv: Path) -> Optional[float]:
    """Compute blended CPA from experiment_results.csv if possible."""
    try:
        rows = _read_csv_rows(experiment_results_csv)
    except Exception:
        return None

    spend = 0.0
    conv = 0.0

    for r in rows:
        # Accept common column variants
        s = _to_float(r.get("spend") or r.get("Spend") or r.get("SPEND"))
        c = _to_float(r.get("conversions") or r.get("Conversions") or r.get("conv") or r.get("CONVERSIONS"))
        if s is not None:
            spend += s
        if c is not None:
            conv += c

    if conv <= 0:
        return None
    return spend / conv


def diff_gate_reflect_adjust(
    *,
    scenario_dir: Path,
    init_cfg: Optional[Dict[str, Any]],
    reflect_cfg: Optional[Dict[str, Any]],
    guardrails_payload: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """High-ROI gate: ensure reflect/adjust causes the *right kind* of config change.

    v1 policy:
    - If blended experiment CPA > 1.2 * target_cpa => require target_cpa to change in config.
    - If CPA <= target_cpa => require target_cpa to stay the same (avoid needless churn).

    We intentionally start narrow (target_cpa) because it's measurable and central.
    """
    exp_path = scenario_dir / "experiment_results.csv"
    if not exp_path.exists() or reflect_cfg is None or init_cfg is None:
        return True, {"ok": True, "skipped": True}

    target_cpa = guardrails_payload.get("target_cpa") if isinstance(guardrails_payload, dict) else None
    if target_cpa is None:
        target_cpa = 25.0

    exp_cpa = compute_experiment_cpa(exp_path)
    if exp_cpa is None:
        # Not enough info; don't gate yet.
        return True, {"ok": True, "skipped": True, "reason": "could not compute experiment CPA"}

    def get_target(cfg: Dict[str, Any], platform: str) -> Optional[float]:
        try:
            return _to_float(((cfg.get(platform) or {}).get("bidding") or {}).get("target_cpa"))
        except Exception:
            return None

    init_meta = get_target(init_cfg, "meta")
    init_tt = get_target(init_cfg, "tiktok")
    ref_meta = get_target(reflect_cfg, "meta")
    ref_tt = get_target(reflect_cfg, "tiktok")

    # Also ensure objective doesn't flip unexpectedly.
    init_obj = ((init_cfg.get("meta") or {}).get("objective"))
    ref_obj = ((reflect_cfg.get("meta") or {}).get("objective"))
    objective_ok = (init_obj == ref_obj)

    # Change detection.
    changed = (init_meta != ref_meta) or (init_tt != ref_tt)

    needs_change = exp_cpa > 1.2 * float(target_cpa)

    ok = True
    notes: List[str] = []

    if not objective_ok:
        ok = False
        notes.append(f"Objective changed unexpectedly: {init_obj} -> {ref_obj}")

    if needs_change and not changed:
        ok = False
        notes.append(f"High CPA (${exp_cpa:.2f} > 1.2*${float(target_cpa):.2f}) but target_cpa did not change")

    if not needs_change and changed:
        ok = False
        notes.append(f"CPA ok (${exp_cpa:.2f} <= ${float(target_cpa):.2f}) but target_cpa changed (unnecessary churn)")

    return ok, {
        "ok": ok,
        "exp_cpa": exp_cpa,
        "target_cpa": float(target_cpa),
        "needs_change": needs_change,
        "init": {"meta_target_cpa": init_meta, "tiktok_target_cpa": init_tt, "meta_objective": init_obj},
        "reflect": {"meta_target_cpa": ref_meta, "tiktok_target_cpa": ref_tt, "meta_objective": ref_obj},
        "notes": notes,
    }


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


def _base_env(adronaut_home: Path, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = os.environ.copy()
    env["ADRONAUT_HOME"] = str(adronaut_home.resolve())
    env["ADRONAUT_DISABLE_DB"] = "1"
    env["ADRONAUT_EVAL_MODE"] = "1"
    env["INTERACTIVE_MODE"] = "false"
    # Ensure filesystem-backed DB is sandboxed too.
    env["ADRONAUT_LOCAL_STORAGE_DIR"] = str((adronaut_home / "local_storage").resolve())
    # Pre-approve so we can complete approval-gated steps in one shot.
    env["ADRONAUT_APPROVE"] = "1"

    if extra:
        env.update(extra)

    return env


def _load_campaign_config(adronaut_home: Path, project_id: str) -> Tuple[Optional[Dict[str, Any]], Path]:
    cfg_path = adronaut_home / "projects" / project_id / "artifacts" / "configs" / "campaign_config.json"
    if not cfg_path.exists():
        return None, cfg_path
    try:
        return json.loads(cfg_path.read_text()), cfg_path
    except Exception:
        return None, cfg_path


def _load_full_state(adronaut_home: Path, project_id: str) -> Optional[Dict[str, Any]]:
    st_path = adronaut_home / "projects" / project_id / "state" / "state_full.json"
    if not st_path.exists():
        return None
    try:
        data = json.loads(st_path.read_text())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def run_agent_initialize(project_name: str, inputs_path: Path, adronaut_home: Path) -> AgentRunResult:
    env = _base_env(adronaut_home)

    rc, out, err = _run_cli(["run", "--project-id", project_name, "--inputs", str(inputs_path), "--approve"], env)
    created_id = _extract_created_project_id(out)
    effective_project_id = created_id or project_name

    gates: Dict[str, Any] = {
        "cli_rc": rc,
        "cli_ok": rc == 0,
        "effective_project_id": effective_project_id,
    }

    cfg, cfg_path = _load_campaign_config(adronaut_home, effective_project_id)
    v = validate_campaign_config(cfg) if cfg is not None else _fail("CONFIG_MISSING", f"no campaign config artifact written at {cfg_path}")
    gates["config_valid"] = bool(v.get("ok"))
    gates["config_validation"] = v

    st = _load_full_state(adronaut_home, effective_project_id)
    gates["decision"] = (st or {}).get("decision")

    # Even with pre-approve, approval text should appear somewhere.
    gates["approval_gate_seen"] = ("approv" in (out + err).lower())

    ok = bool(gates["cli_ok"] and gates["config_valid"])

    return AgentRunResult(ok=ok, gates=gates, artifacts={"stdout": out[-4000:], "stderr": err[-4000:], "config": cfg, "state": st})


def run_agent_reflect(project_id: str, inputs_path: Path, adronaut_home: Path, *, needs_change: Optional[bool] = None) -> AgentRunResult:
    """Run a reflect/adjust cycle by uploading experiment results to an existing project."""

    extra: Dict[str, str] = {}
    if needs_change is not None:
        extra["ADRONAUT_EVAL_NEEDS_CHANGE"] = "1" if needs_change else "0"

    env = _base_env(adronaut_home, extra=extra if extra else None)

    rc, out, err = _run_cli(["run", "--project-id", project_id, "--inputs", str(inputs_path), "--approve"], env)

    gates: Dict[str, Any] = {
        "cli_rc": rc,
        "cli_ok": rc == 0,
        "effective_project_id": project_id,
    }

    cfg, cfg_path = _load_campaign_config(adronaut_home, project_id)
    v = validate_campaign_config(cfg) if cfg is not None else _fail("CONFIG_MISSING", f"no campaign config artifact written at {cfg_path}")
    gates["config_valid"] = bool(v.get("ok"))
    gates["config_validation"] = v

    st = _load_full_state(adronaut_home, project_id)
    gates["decision"] = (st or {}).get("decision")

    ok = bool(gates["cli_ok"] and gates["config_valid"])

    return AgentRunResult(ok=ok, gates=gates, artifacts={"stdout": out[-4000:], "stderr": err[-4000:], "config": cfg, "state": st})


# ----------------------------
# Scenario runner
# ----------------------------


def _openai_judge_json(*, model: str, prompt: str) -> Dict[str, Any]:
    """Call OpenAI Responses API and force JSON output.

    Uses stdlib only (no extra deps).
    """
    import urllib.request

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    url = "https://api.openai.com/v1/responses"

    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)

    # Responses API returns a list of output items; we want the text.
    # Typical: data["output"][0]["content"][0]["text"]
    out_items = data.get("output") or []
    text = None
    for item in out_items:
        for c in (item.get("content") or []):
            if c.get("type") == "output_text":
                text = c.get("text")
                break
        if text:
            break

    if not text:
        raise ValueError(f"No output_text found in response: keys={list(data.keys())}")

    return json.loads(text)


def llm_judge_eval(*, scenario_id: str, phase: str, config: Dict[str, Any], guardrails: Dict[str, Any]) -> Dict[str, Any]:
    """LLM-as-judge scoring.

    Provider selection:
    - ADRONAUT_JUDGE_PROVIDER=codex -> OpenAI judge (model defaults to gpt-5.2)
    - otherwise: Gemini if GEMINI_API_KEY set, else deterministic fake
    """
    provider = (os.getenv("ADRONAUT_JUDGE_PROVIDER") or "").strip().lower()

    rubric = {
        "plan_quality": "Coherent, testable, minimal fluff",
        "config_quality": "Complete + sensible defaults (budget/placements/bidding)",
        "grounding": "Avoids made-up numbers; aligns to inputs/guardrails",
        "guardrails": "Suggested actions match alert severity",
    }

    prompt = (
        f"You are judging end-to-end quality for an ads agent run.\n"
        f"Scenario: {scenario_id} phase={phase}.\n\n"
        f"Rubric (0-5 each): {json.dumps(rubric, indent=2)}\n\n"
        f"Agent output campaign config JSON:\n{json.dumps(config, indent=2)[:12000]}\n\n"
        f"Guardrails output JSON:\n{json.dumps(guardrails, indent=2)[:6000]}\n\n"
        "Return STRICT JSON ONLY in this format:\n"
        "{\n"
        "  \"scores\": {\"plan_quality\": 0-5, \"config_quality\": 0-5, \"grounding\": 0-5, \"guardrails\": 0-5},\n"
        "  \"overall\": 0-5,\n"
        "  \"notes\": [\"...\"]\n"
        "}"
    )

    # 1) Codex/OpenAI judge
    if provider in ("codex", "openai"):
        model = os.getenv("ADRONAUT_JUDGE_MODEL", "gpt-5.2")
        try:
            out = _openai_judge_json(model=model, prompt=prompt)
        except Exception as e:
            return {"ok": False, "error": str(e), "judge_kind": "codex", "model": model}

        overall_0_5 = float((out or {}).get("overall", 0) or 0)
        overall_0_100 = max(0.0, min(100.0, (overall_0_5 / 5.0) * 100.0))
        return {"ok": True, "judge": out, "overall_0_100": round(overall_0_100, 2), "judge_kind": "codex", "model": model}

    # 2) Gemini judge (if available)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        from src.llm.gemini import GeminiClient

        judge = GeminiClient()
        judge_kind = "gemini"
        try:
            out = judge.generate_json(prompt=prompt, system_instruction=None, temperature=0.0, task_name="E2E Judge")
        except Exception as e:
            return {"ok": False, "error": str(e), "judge_kind": judge_kind}

        overall_0_5 = float((out or {}).get("overall", 0) or 0)
        overall_0_100 = max(0.0, min(100.0, (overall_0_5 / 5.0) * 100.0))
        return {"ok": True, "judge": out, "overall_0_100": round(overall_0_100, 2), "judge_kind": judge_kind}

    # 3) Deterministic fake judge (default)
    from src.llm.fake_gemini import FakeGeminiClient

    judge = FakeGeminiClient()
    try:
        out = judge.generate_json(prompt=prompt, system_instruction=None, temperature=0.0, task_name="E2E Judge")
    except Exception as e:
        return {"ok": False, "error": str(e), "judge_kind": "fake"}

    overall_0_5 = float((out or {}).get("overall", 0) or 0)
    overall_0_100 = max(0.0, min(100.0, (overall_0_5 / 5.0) * 100.0))
    return {"ok": True, "judge": out, "overall_0_100": round(overall_0_100, 2), "judge_kind": "fake"}


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
    historical_path = scenario_dir / "historical_campaigns.csv"
    if not historical_path.exists():
        return {"scenario": sid, "ok": False, "error": "missing historical_campaigns.csv"}

    init_res = run_agent_initialize(project_name, historical_path, adronaut_home)
    project_id = init_res.gates.get("effective_project_id")

    # Optional second phase: reflect/adjust if experiment_results.csv exists.
    reflect_res: Optional[AgentRunResult] = None
    exp_path = scenario_dir / "experiment_results.csv"
    if project_id and exp_path.exists():
        # Compute whether this scenario *should* require an adjustment.
        # This is used to drive deterministic eval mode (fake LLM) so the diff-gate
        # is exercised meaningfully.
        g_payload = {}
        gp = scenario_dir / "meta_guardrails.json"
        if gp.exists():
            try:
                g_payload = json.loads(gp.read_text())
            except Exception:
                g_payload = {}
        target_cpa = float(g_payload.get("target_cpa", 25.0))
        exp_cpa = compute_experiment_cpa(exp_path)
        needs_change = bool(exp_cpa is not None and exp_cpa > 1.2 * target_cpa)

        reflect_res = run_agent_reflect(str(project_id), exp_path, adronaut_home, needs_change=needs_change)

    guard_ok, guard_details = run_guardrail_eval(scenario_dir)

    # Use latest config for scoring (reflect if present).
    cfg_init = (init_res.artifacts.get("config") or {})
    cfg_reflect = (reflect_res.artifacts.get("config") if reflect_res else None)
    cfg_latest = (cfg_reflect or cfg_init) or {}

    # Quality score (heuristic)
    quality = score_quality(cfg_latest, guardrail_ok=guard_ok)

    gates: Dict[str, Any] = {
        "init": init_res.gates,
        "reflect": reflect_res.gates if reflect_res else None,
        "guardrails_ok": guard_ok,
        "guardrails": guard_details,
    }

    # Extra gate: if reflect scenario, ensure decision was "reflect".
    reflect_gate_ok = True
    patch_gate_ok = True
    patch_details: Dict[str, Any] = {"ok": True, "skipped": True}

    if reflect_res is not None:
        reflect_gate_ok = (reflect_res.gates.get("decision") == "reflect")
        gates["reflect_decision_ok"] = reflect_gate_ok

        # High-ROI diff gate: did adjustment change the right config knob?
        patch_gate_ok, patch_details = diff_gate_reflect_adjust(
            scenario_dir=scenario_dir,
            init_cfg=cfg_init,
            reflect_cfg=cfg_reflect or {},
            guardrails_payload=(json.loads((scenario_dir / "meta_guardrails.json").read_text()) if (scenario_dir / "meta_guardrails.json").exists() else {}),
        )
        gates["reflect_patch_ok"] = patch_gate_ok
        gates["reflect_patch"] = patch_details

    # LLM-as-judge (optional)
    judge = llm_judge_eval(
        scenario_id=sid,
        phase=("reflect" if reflect_res is not None else "initialize"),
        config=cfg_latest,
        guardrails=guard_details,
    )

    ok = bool(init_res.ok and (reflect_res.ok if reflect_res else True) and guard_ok and reflect_gate_ok and patch_gate_ok)

    result = {
        "scenario": sid,
        "timestamp": int(time.time()),
        "ok": ok,
        "gates": gates,
        "quality_score": quality,
        "judge": judge,
    }

    (out_dir / "result.json").write_text(json.dumps(result, indent=2))
    (out_dir / "stdout.txt").write_text(init_res.artifacts.get("stdout", ""))
    (out_dir / "stderr.txt").write_text(init_res.artifacts.get("stderr", ""))
    if reflect_res is not None:
        (out_dir / "stdout_reflect.txt").write_text(reflect_res.artifacts.get("stdout", ""))
        (out_dir / "stderr_reflect.txt").write_text(reflect_res.artifacts.get("stderr", ""))

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
