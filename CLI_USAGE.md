# CLI Usage Guide

Complete reference for all Adronaut Agent CLI commands.

---

## Command Overview

| Command | Purpose | Meta API Calls |
|---------|---------|----------------|
| `run` | Generate campaign config | ❌ No |
| `deploy-to-meta` | Deploy config to Meta Ads | ✅ Yes (optional) |
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

### Example
```bash
# New project
python cli.py run --project-id eco-bottle-campaign

# Existing project (resume/iterate)
python cli.py run --project-id 8f7a2b1c-4e3d-9a5f-1b2c-3d4e5f6a7b8c

# Force restart
python cli.py run --project-id my-campaign --restart
```

### Output
- `campaign_<project_id>_v0.json` - Campaign configuration
- Console output with strategy breakdown and execution timeline

---

## 2. Deploy to Meta Ads (Automated)

**Deploys config to Meta Ads via API**

```bash
python cli.py deploy-to-meta --config-path <config-file.json> [--dry-run]
```

### Options
- `--config-path` (required): Path to campaign config JSON
- `--dry-run`: Test mode - logs API calls without executing

### Prerequisites
Set environment variables in `.env`:
```bash
META_ACCESS_TOKEN=your_token_here
META_AD_ACCOUNT_ID=act_your_account_id
META_PAGE_ID=your_facebook_page_id
META_INSTAGRAM_ACTOR_ID=your_instagram_id  # Optional
```

Or for sandbox testing:
```bash
META_SANDBOX_MODE=true
META_SANDBOX_TOKEN=your_sandbox_token
META_SANDBOX_ACCOUNT_ID=act_sandbox_id
```

### What it does
1. ✅ Loads campaign config
2. ✅ Validates Meta API credentials
3. ✅ Creates campaign on Meta (PAUSED state)
4. ✅ Creates ad sets with targeting and budget
5. ✅ (Optionally) Creates ad creatives
6. ✅ Saves deployment result JSON

### Example Usage

**Dry-run mode (no API calls)**
```bash
python cli.py deploy-to-meta \
  --config-path campaign_eco-bottle_v0.json \
  --dry-run
```

**Sandbox deployment**
```bash
# Set sandbox mode in .env
export META_SANDBOX_MODE=true

python cli.py deploy-to-meta \
  --config-path campaign_eco-bottle_v0.json
```

**Production deployment**
```bash
python cli.py deploy-to-meta \
  --config-path campaign_eco-bottle_v0.json
```

### Output
- Console output with deployment progress
- `campaign_<project_id>_v0_deployment_result.json` - Deployment details
- Campaign ID, Ad Set IDs, Ad IDs (if created)

### Common Errors

**Missing credentials**
```
Error: META_ACCESS_TOKEN not set in environment
```
→ Add to `.env` file

**Invalid credentials**
```
Meta API Error 190: Invalid OAuth access token
```
→ Regenerate token in Meta Developer Portal

**Rate limiting**
```
Meta API Error 17: User request limit reached
```
→ Wait and retry (automatic exponential backoff included)

---

## 3. Export Manual Setup Guide

**Generates customized checklist for manual Meta Ads Manager setup**

```bash
python cli.py export-manual-guide \
  --config-path <config-file.json> \
  [--output <output-file.md>]
```

### Options
- `--config-path` (required): Path to campaign config JSON
- `--output`: Output markdown file (default: `<config>_manual_setup.md`)

### What it does
1. ✅ Loads campaign config
2. ✅ Generates customized markdown checklist
3. ✅ Includes all settings from config with actual values
4. ✅ Provides step-by-step manual setup instructions

### Example
```bash
python cli.py export-manual-guide \
  --config-path campaign_eco-bottle_v0.json \
  --output my_setup_checklist.md
```

### Output
- Markdown file with checkbox-based setup guide
- Includes campaign name, budget, targeting, creative specs
- Ready to follow in Meta Ads Manager

---

## Complete Workflow Examples

### Workflow 1: Generate Config Only
```bash
# Step 1: Generate config
python cli.py run --project-id my-campaign

# Output: campaign_<id>_v0.json
# No Meta deployment happens
```

### Workflow 2: Generate + Deploy (Automated)
```bash
# Step 1: Generate config
python cli.py run --project-id my-campaign

# Step 2: Test deployment (dry-run)
python cli.py deploy-to-meta \
  --config-path campaign_<id>_v0.json \
  --dry-run

# Step 3: Deploy to sandbox
export META_SANDBOX_MODE=true
python cli.py deploy-to-meta \
  --config-path campaign_<id>_v0.json

# Step 4: Deploy to production
export META_SANDBOX_MODE=false
python cli.py deploy-to-meta \
  --config-path campaign_<id>_v0.json
```

### Workflow 3: Generate + Manual Setup
```bash
# Step 1: Generate config
python cli.py run --project-id my-campaign

# Step 2: Export manual checklist
python cli.py export-manual-guide \
  --config-path campaign_<id>_v0.json

# Step 3: Follow checklist in Meta Ads Manager
open campaign_<id>_v0_manual_setup.md
```

### Workflow 4: Optimization Iteration
```bash
# After running initial campaign for 5-7 days...

# Step 1: Upload experiment results
python cli.py run --project-id <existing-uuid>
# (Upload results CSV when prompted)

# Step 2: Agent generates optimized config v1
# Output: campaign_<id>_v1.json

# Step 3: Deploy optimization
python cli.py deploy-to-meta \
  --config-path campaign_<id>_v1.json
```

---

## Environment Variables Reference

### Required for Production Deployment
```bash
META_ACCESS_TOKEN=EAAx...        # Meta Marketing API token
META_AD_ACCOUNT_ID=act_123456789 # Ad account ID
META_PAGE_ID=123456789           # Facebook Page ID
META_INSTAGRAM_ACTOR_ID=123456   # Instagram account (optional)
```

### Optional - Testing Modes
```bash
META_DRY_RUN=true               # Logs API calls without executing
META_SANDBOX_MODE=true          # Use Meta sandbox environment
META_SANDBOX_TOKEN=EAAx...      # Sandbox access token
META_SANDBOX_ACCOUNT_ID=act_... # Sandbox ad account ID
```

### Getting Meta Credentials

1. **Access Token**:
   - Go to https://developers.facebook.com/apps
   - Create app or select existing
   - Add "Marketing API" product
   - Tools → Access Token Tool → Generate Token
   - Needs `ads_management` permission

2. **Ad Account ID**:
   - Go to https://business.facebook.com/adsmanager
   - Select account → Settings
   - Copy "Ad Account ID" (format: `act_XXXXXXXXX`)

3. **Page ID**:
   - Go to your Facebook Page
   - About → Page Transparency → Page ID

4. **Sandbox Account**:
   - Developer Portal → Marketing API → Tools → Sandbox
   - Create sandbox ad account
   - Get sandbox token and ID

---

## Testing Strategy

### Level 1: Dry-Run (No API Calls)
```bash
python cli.py deploy-to-meta \
  --config-path campaign_v0.json \
  --dry-run
```
✅ Validates config structure
✅ Logs what would be called
❌ No network requests

### Level 2: Sandbox (Fake Ads)
```bash
export META_SANDBOX_MODE=true
python cli.py deploy-to-meta \
  --config-path campaign_v0.json
```
✅ Real API calls
✅ Returns real IDs
❌ No ads delivered
❌ No spend

### Level 3: Production ($$$)
```bash
export META_SANDBOX_MODE=false
python cli.py deploy-to-meta \
  --config-path campaign_v0.json
```
✅ Real campaigns created
✅ Real ads (in PAUSED state)
⚠️ Real money spent when activated

---

## Troubleshooting

### "Config file not found"
```bash
# List files in current directory
ls campaign_*.json

# Use correct path
python cli.py deploy-to-meta --config-path ./campaign_xxx_v0.json
```

### "No 'meta' section found"
Your config doesn't have Meta configuration. Check the config file has this structure:
```json
{
  "meta": {
    "campaign_name": "...",
    "objective": "...",
    ...
  }
}
```

### "Invalid OAuth access token"
Token expired or invalid:
1. Go to Meta Developer Portal
2. Regenerate access token
3. Update `.env` file
4. Restart command

### Rate limiting
Meta API limits requests. The CLI automatically retries with exponential backoff, but if you see persistent errors:
- Wait 5-10 minutes
- Reduce request frequency
- Use sandbox for testing

---

## Help Commands

```bash
# General help
python cli.py --help

# Command-specific help
python cli.py run --help
python cli.py deploy-to-meta --help
python cli.py export-manual-guide --help
```

---

## Quick Reference Card

```bash
# Generate config (no deployment)
python cli.py run --project-id <name>

# Test deployment (dry-run)
python cli.py deploy-to-meta --config-path <file> --dry-run

# Deploy to sandbox
META_SANDBOX_MODE=true python cli.py deploy-to-meta --config-path <file>

# Deploy to production
python cli.py deploy-to-meta --config-path <file>

# Export manual checklist
python cli.py export-manual-guide --config-path <file>

# View all commands
python cli.py --help
```

---

**Need more help?**
- Full manual setup guide: `/docs/MANUAL_META_ADS_SETUP.md`
- Architecture docs: `/ARCHITECTURE.md`, `/CLAUDE.md`
- Meta API docs: https://developers.facebook.com/docs/marketing-api
