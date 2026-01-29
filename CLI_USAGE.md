# CLI Usage Guide

Complete reference for all Adronaut Agent CLI commands.

---

## Command Overview

| Command | Purpose | Meta API Calls |
|---------|---------|----------------|
| `run` | Generate campaign config | ❌ No |
| `deploy-to-meta` | Deploy config to Meta Ads | ✅ Yes (optional) |
| `monitor-meta` | Fetch Meta campaign status + insights | ✅ Yes |
| `watch-meta` | Guardrail monitoring (today vs trailing 7d), saves snapshots | ✅ Yes |
| `iterate-creatives` | Generate 3 Meta IMAGE creative variants + experiment plan (saves lineage artifacts) | ❌ No (LLM only) |
| `setup-cron` | Print crontab entry for hourly 9am-9pm watch-meta | ❌ No |
| `export-manual-guide` | Generate manual setup checklist | ❌ No |

---

## 1. Generate Campaign Config (Main Workflow)

**Creates strategy and config JSON - NO Meta API deployment**

```bash
python cli.py run --project-id <project-name-or-uuid>
```

### Options
- `--project-id` (required): Project identifier
  - **New project**: Use any name (e.g., `my-campaign-001`)
  - **Existing project**: Use UUID from previous run
- `--restart`: Force fresh start (ignore previous state)

### What it does
1. ✅ Loads project or creates new one
2. ✅ Prompts for file uploads (CSV, JSON) or product URLs
3. ✅ Analyzes data and generates insights
4. ✅ Creates campaign strategy
5. ✅ Generates campaign configuration
6. ✅ Saves to `campaign_<project_id>_v<iteration>.json`
7. ❌ **Does NOT deploy to Meta** (deployment is separate)

---

## 2. Deploy to Meta Ads (Automated)

**Deploys config to Meta Ads via API**

```bash
python cli.py deploy-to-meta --config-path <config-file.json> [--dry-run]
```

⚠️ Approval gate: you must type **YES** before any writes occur.

### Options
- `--config-path` (required): Path to campaign config JSON
- `--dry-run`: Test mode - log API calls without executing

### Prerequisites
Set environment variables in `.env`:
```bash
META_ACCESS_TOKEN=your_token_here
META_AD_ACCOUNT_ID=act_your_account_id
META_PAGE_ID=your_facebook_page_id
META_INSTAGRAM_ACTOR_ID=your_instagram_id  # Optional
```

### Creating real Ads (Creatives + Ads)
To create actual ads (not just campaign + ad set), you must provide:
- `META_PAGE_ID` (required by Meta to create creatives)
- an image asset via either:
  - `meta.creative_specs.image_url` (quickest for demo), or
  - `meta.creative_specs.image_path`, or
  - per-asset `creative_assets[].image_url/image_path`

By default, everything is created in **PAUSED** state for safety.

If you don’t provide `creative_assets`, deploy will synthesize **3 creatives** using `meta.creative_specs.headline/primary_text` and the shared image.

Deployment writes a `*_deployment_result.json` that includes guardrails used by `watch-meta`.

---

## 3. Monitor Meta (Status + Insights)

Fetch performance and status for a deployed campaign.

```bash
python cli.py monitor-meta --campaign-id <campaign_id> --since YYYY-MM-DD --until YYYY-MM-DD
```

Or if you have a deployment result file:
```bash
python cli.py monitor-meta --deployment-result campaign_<...>_deployment_result.json --since YYYY-MM-DD --until YYYY-MM-DD
```

### Output
Writes a JSON file:
- `campaign_<campaign_id>_<since>_to_<until>_insights.json`

---

## 4. Watch Meta (Guardrails, Cron-Friendly)

Checks today vs trailing 7 days and evaluates demo guardrails:
- Spend > daily cap
- CTR drop > 20% vs 7d avg
- CPA up > 20% vs target

```bash
python cli.py watch-meta --deployment-result campaign_<...>_deployment_result.json
```

Optional overrides (useful for older deployment files):
```bash
python cli.py watch-meta --deployment-result dep.json --daily-cap 75 --target-cpa 18
```

### Output
- Saves a snapshot to `snapshots/<timestamp>.json`
- Prints a Telegram-ready alert block

---

## 5. Iterate Creatives (Meta Image Ads)

Generates **3 new Meta IMAGE creative variants** (refine / explore / format tweak) plus an **experiment plan**, and saves a **creative lineage** artifact.

```bash
python cli.py iterate-creatives --deployment-result campaign_<...>_deployment_result.json
```

Optionally link a watch-meta snapshot (for traceability):
```bash
python cli.py iterate-creatives --deployment-result dep.json --snapshot $ADRONAUT_HOME/projects/<project_id>/artifacts/snapshots/<timestamp>.json
```

### Output
- `artifacts/creative_lineage/<timestamp>.json`
- `artifacts/experiments/exp_<timestamp>.json`

---

## 6. Setup Cron

Print a crontab entry for hourly monitoring (9am-9pm):

```bash
python cli.py setup-cron --deployment-result campaign_<...>_deployment_result.json
```

---

## 7. Export Manual Guide

```bash
python cli.py export-manual-guide --config-path <config-file.json>
```
