# Adronaut E2E Eval Harness (Local)

This repo includes a **local, deterministic end-to-end eval harness** for Adronaut.

The goal is to continuously measure and improve:
- Plan → execute → verify behavior (agent loop quality)
- Campaign config validity/safety
- Meta guardrails/watch logic
- Reflect/adjust behavior (post-results optimization)

> TL;DR
> ```bash
> cd adronaut-agent
> python3 scripts/eval_runner.py --scenarios tests/fixtures/eval --out tmp/eval_runs
> ```

---

## What you get

Running the harness produces:
- A **pass rate**: how many scenarios clear all hard gates
- A **heuristic quality score** (0–100) for each scenario
- An **LLM-as-judge score** (0–100) per scenario (real if `GEMINI_API_KEY` is set; otherwise deterministic fake)
- A `results.jsonl` file containing per-scenario metrics and gate details

Output layout:
- `tmp/eval_runs/<scenario_id>/result.json` (full per-scenario report)
- `tmp/eval_runs/<scenario_id>/stdout*.txt` / `stderr*.txt` (agent logs)
- `tmp/eval_runs/results.jsonl` (one JSON per scenario)

---

## Eval runner

Script: `scripts/eval_runner.py`

### Basic usage

```bash
python3 scripts/eval_runner.py \
  --scenarios tests/fixtures/eval \
  --out tmp/eval_runs
```

Arguments:
- `--scenarios`: directory containing scenario subfolders
- `--out`: output directory (safe to delete)

### Deterministic agent mode

The runner enables offline evaluation via environment variables:

- `ADRONAUT_EVAL_MODE=1`
  - Makes `src/llm/gemini.get_gemini()` return a deterministic fake LLM client.
- `ADRONAUT_APPROVE=1`
  - Auto-approves approval-gated steps during eval.
- `ADRONAUT_DISABLE_DB=1`
  - Avoids Supabase.
- `ADRONAUT_HOME=<out>/adronaut_home`
  - All artifacts/checkpoints go under the scenario output directory.

Why deterministic mode exists:
- You can run E2E evals without API keys.
- Results don’t drift across runs.
- It’s easy to reproduce regressions.

---

## Record / Replay (recommended for real-model eval)

When you start using real models, reproducibility becomes the main pain.
This repo supports a lightweight record/replay mechanism for LLM calls.

### Record

Set `ADRONAUT_LLM_RECORD_PATH` to a JSONL file.
Every LLM call (`generate_json`/`generate_text`) will append a record with:
- `task_name`, `temperature`, `system_instruction`, `prompt`
- `response`
- a stable `key` (hash) used for replay

Example:

```bash
export ADRONAUT_LLM_RECORD_PATH=tmp/llm_traces/sc_001.jsonl
python3 scripts/eval_runner.py --scenarios tests/fixtures/eval --out tmp/eval_runs
```

### Replay

Set `ADRONAUT_LLM_REPLAY_PATH` to a previously recorded JSONL trace.
The model will not be called; responses are returned from the trace.

```bash
export ADRONAUT_LLM_REPLAY_PATH=tmp/llm_traces/sc_001.jsonl
python3 scripts/eval_runner.py --scenarios tests/fixtures/eval --out tmp/eval_runs
```

Notes:
- Replay matches calls by a stable hash of `(kind, task_name, system_instruction, prompt)`.
- You can enable both replay + record at once (record will capture replayed outputs).

## LLM-as-judge

The harness includes an optional **judge step** for scoring qualities that are hard to validate mechanically.

### Judge modes

- **Real judge**: if `GEMINI_API_KEY` is set
  - Uses `GeminiClient()` directly (bypasses eval fake) with temperature 0.
- **Fake judge**: if `GEMINI_API_KEY` is not set
  - Uses `FakeGeminiClient()` and returns deterministic scores.

This means `result.json` / `results.jsonl` always contains a `judge` field.

### Judge rubric (v1)

The prompt asks for 0–5 scores:
- `plan_quality`
- `config_quality`
- `grounding`
- `guardrails`

It then converts `overall` (0–5) → `overall_0_100`.

---

## Scenario format

All scenarios live under: `tests/fixtures/eval/<scenario_id>/`

### Required file

- `historical_campaigns.csv`

### Optional files

- `meta_guardrails.json`
  - Used to evaluate watch/guardrails logic via `src.integrations.meta_watch.evaluate_guardrails()`.

- `experiment_results.csv`
  - If present, the runner executes **two phases**:
    1) initialize with `historical_campaigns.csv`
    2) reflect/adjust with `experiment_results.csv` (same project)

### meta_guardrails.json schema

Example:

```json
{
  "campaign_id": "cmp_008",
  "daily_cap": 30.0,
  "target_cpa": 20.0,
  "today_insights": {"data": [{"spend": "55.00", "impressions": "8000", "clicks": "200",
    "actions": [{"action_type": "purchase", "value": "1"}]}]},
  "trailing_7d_insights": {"data": [{"spend": "200.00", "impressions": "60000", "clicks": "1500",
    "actions": [{"action_type": "purchase", "value": "12"}]}]},
  "expected_codes": ["SPEND_CAP", "CPA_HIGH"]
}
```

Notes:
- `today_insights` / `trailing_7d_insights` are Meta-like responses (`{"data": [...]}`)
- `expected_codes` is the set of alerts you expect to show up.
  - The harness currently checks `expected_codes ⊆ got_codes`.

---

## Gates (hard pass/fail)

Per scenario, we currently gate on:
- CLI exit code == 0
- A config artifact exists and is schema-valid (light schema in eval runner)
- Guardrails expectations match (if fixture present)
- If `experiment_results.csv` exists:
  - reflect phase decision must equal `"reflect"`
  - **reflect diff-gate**: config changes should match the performance signal

### Reflect diff-gate (high ROI)

When `experiment_results.csv` exists, the harness computes a blended CPA:

- If `exp_cpa > 1.2 * target_cpa` → **require** the config to change a key knob (v1: bidding `target_cpa`).
- If `exp_cpa <= target_cpa` → **require** no churn (v1: bidding `target_cpa` should not change).

This catches the common failure mode where the agent "sounds right" but doesn’t actually change the config appropriately.

---

## Interpreting results

`results.jsonl` contains one JSON object per scenario:

Key fields:
- `ok`: overall pass/fail
- `gates.init`: init-phase gates
- `gates.reflect`: reflect-phase gates (or null)
- `gates.guardrails`: computed guardrail alerts and aggregates
- `quality_score`: heuristic 0–100
- `judge.overall_0_100`: judge score 0–100
- `judge.judge_kind`: `real` or `fake`

---

## Adding new scenarios

1) Create a folder:

```bash
mkdir -p tests/fixtures/eval/sc_010_my_case
```

2) Add `historical_campaigns.csv`.

3) (Optional) Add `experiment_results.csv` to force a reflect/adjust phase.

4) (Optional) Add `meta_guardrails.json` to validate watch behavior.

5) Run:

```bash
python3 scripts/eval_runner.py --scenarios tests/fixtures/eval --out tmp/eval_runs
```

---

## Troubleshooting

### 1) Graph recursion limit errors

If you see:

> `Recursion limit ... reached without hitting a stop condition`

It typically means the plan/verify loop is repeatedly replanning without advancing.

In eval mode, we mitigate this by:
- Auto-approving gated steps (`ADRONAUT_APPROVE=1`)
- Ensuring reflect planning does not get stuck in reflection→replan cycles

If it happens in real runs:
- Inspect `logs/node_io.jsonl` and `state/state_full.json` for the last step.
- Verify which step fails verification and causes replanning.

### 2) “unknown” failures / missing config

Common causes:
- Artifact paths not found due to relative `ADRONAUT_HOME`.
  - The runner uses absolute paths.
- Approval gate not passed.
  - Ensure `ADRONAUT_APPROVE=1` (runner sets this).

---

## Roadmap / making this less “toy”

This is intentionally a v1 harness.
High-leverage next improvements:
- Add **diff-based checks** for reflect/adjust (config should change in expected ways)
- Add **grounding validators** (numbers claimed in summaries must exist in inputs)
- Run agent with **real LLM** while keeping judge fixed (to measure true drift)
- Add a small human labeling loop for judge calibration
