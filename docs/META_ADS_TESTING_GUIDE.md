# Meta Ads API Testing Guide

Complete step-by-step guide for testing the Meta Ads creation flow.

---

## Testing Strategy Overview

We'll test in **3 levels** with increasing realism:

| Level | API Calls | Ads Created | Spend | Use Case |
|-------|-----------|-------------|-------|----------|
| **1. Dry-Run** | ❌ No | ❌ No | $0 | Validate code & config |
| **2. Sandbox** | ✅ Yes | ⚠️ Fake | $0 | Test API integration |
| **3. Production** | ✅ Yes | ✅ Real | $$$ | Live deployment |

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `facebook-business-sdk>=21.0.0` and other dependencies.

### 2. Generate a Campaign Config

You need a config file to test with:

```bash
# Option A: Run agent to generate config
python cli.py run --project-id test-campaign
# Upload: examples/sample_outputs/config_v0.json or your data

# Option B: Use existing sample config
cp examples/sample_outputs/config_v0.json test_config.json
```

---

## Level 1: Dry-Run Testing (No API Calls)

**Purpose**: Validate code works and config is correct **without** hitting Meta's API.

### Setup

No credentials needed for dry-run!

### Run Test

```bash
python cli.py deploy-to-meta \
  --config-path test_config.json \
  --dry-run
```

### Expected Output

```
============================================================
  Meta Ads Deployment
============================================================

Config file: test_config.json
Campaign: Eco Bottle - Phase 1 Discovery - Meta
Daily budget: $300.0

🔧 DRY RUN MODE: No actual API calls will be made

Starting deployment...

🔧 [DRY RUN] POST https://graph.facebook.com/v24.0/act_test/campaigns
   Payload: {
     "name": "Eco Bottle - Phase 1 Discovery - Meta",
     "objective": "OUTCOME_TRAFFIC",
     "status": "PAUSED",
     "special_ad_categories": []
   }
✓ Campaign created: mock_a1b2c3d4 (Eco Bottle - Phase 1 Discovery - Meta)

🔧 [DRY RUN] POST https://graph.facebook.com/v24.0/act_test/adsets
   Payload: {
     "name": "Eco Bottle - Phase 1 Discovery - Meta - Ad Set 1",
     "campaign_id": "mock_a1b2c3d4",
     "daily_budget": "30000",
     ...
   }
✓ Ad Set created: mock_e5f6g7h8 (...)

============================================================
  Deployment Complete
============================================================

✓ Campaign ID: mock_a1b2c3d4
✓ Ad Set IDs: mock_e5f6g7h8

Status: PAUSED

✓ Deployment result saved to: test_config_deployment_result.json
```

### Validation Checklist

- [ ] Command runs without errors
- [ ] All payloads logged with correct structure
- [ ] Budget converted correctly (dollars → cents)
- [ ] Targeting spec formatted properly
- [ ] Mock IDs generated
- [ ] Result JSON saved

### Common Issues

**"Config file not found"**
```bash
# Check file exists
ls -la test_config.json

# Use absolute path
python cli.py deploy-to-meta --config-path $(pwd)/test_config.json --dry-run
```

**"No 'meta' section found"**
- Ensure config has `meta` key with campaign data
- Check JSON is valid: `python -m json.tool test_config.json`

---

## Level 2: Sandbox Testing (Real API, Fake Ads)

**Purpose**: Test against Meta's sandbox environment - real API calls, but no actual ads delivered.

### Setup Sandbox Account

#### Step 1: Create Meta App

1. Go to https://developers.facebook.com/apps
2. Click **Create App**
3. Select **Business** type
4. Enter app name: `Adronaut Testing`
5. Click **Create App**

#### Step 2: Add Marketing API

1. In your app dashboard, click **Add Product**
2. Find **Marketing API**, click **Set Up**
3. Complete the setup flow

#### Step 3: Create Sandbox Ad Account

1. In left sidebar: **Marketing API** → **Tools**
2. Click **Sandbox Ad Account Management**
3. Click **Create Sandbox Ad Account**
4. Note the **Sandbox Ad Account ID** (format: `act_XXXXXXXXX`)

#### Step 4: Generate Sandbox Token

1. In left sidebar: **Tools** → **Access Token Tool**
2. Under your app, select **User Token**
3. Add permissions: `ads_management`, `business_management`
4. Click **Generate Token**
5. Copy the token (starts with `EAA...`)

**Important**: Sandbox tokens expire! Regenerate when needed.

#### Step 5: Get Page ID (Optional for Creative Testing)

1. Go to your Facebook Page
2. Click **About** → **Page Transparency**
3. Copy **Page ID**

Or use Meta's test pages if you don't have one.

### Configure Environment

Create or update `.env`:

```bash
# Sandbox Configuration
META_SANDBOX_MODE=true
META_SANDBOX_TOKEN=EAAx...your_sandbox_token_here
META_SANDBOX_ACCOUNT_ID=act_1234567890123456  # Your sandbox account ID

# Optional: For creative testing
META_PAGE_ID=123456789
META_INSTAGRAM_ACTOR_ID=123456789

# Keep production creds separate
META_ACCESS_TOKEN=  # Leave empty for now
META_AD_ACCOUNT_ID=  # Leave empty for now
```

### Run Sandbox Test

```bash
python cli.py deploy-to-meta \
  --config-path test_config.json
```

(No `--dry-run` flag = real API calls)

### Expected Output

```
============================================================
  Meta Ads Deployment
============================================================

Config file: test_config.json
Campaign: Eco Bottle - Phase 1 Discovery - Meta
Daily budget: $300.0

🧪 SANDBOX MODE: Using Meta sandbox environment

Starting deployment...

✓ Campaign created: 120213241234567 (Eco Bottle - Phase 1 Discovery - Meta)
✓ Ad Set created: 120213241234568 (Eco Bottle - Phase 1 Discovery - Meta - Ad Set 1)
   Note: Image generation/upload not implemented. Using placeholder.
   ⚠️  Skipping creative 1 (image upload not implemented)
   ℹ️  No creative assets provided in config

============================================================
  Deployment Complete
============================================================

✓ Campaign ID: 120213241234567
✓ Ad Set IDs: 120213241234568

Status: PAUSED

⚠️  Campaign created in PAUSED state
   Review in Meta Ads Manager, then activate when ready
   https://business.facebook.com/adsmanager

✓ Deployment result saved to: test_config_deployment_result.json
```

### Verify in Meta Ads Manager

**Important**: Sandbox campaigns are **NOT visible in Ads Manager UI**. You can only verify via API.

#### Verify Campaign via API

```bash
# Install curl or use Python
curl -X GET \
  "https://graph.facebook.com/v24.0/120213241234567?access_token=YOUR_SANDBOX_TOKEN&fields=name,status,objective"
```

Expected response:
```json
{
  "name": "Eco Bottle - Phase 1 Discovery - Meta",
  "status": "PAUSED",
  "objective": "OUTCOME_TRAFFIC",
  "id": "120213241234567"
}
```

#### Verify Ad Set via API

```bash
curl -X GET \
  "https://graph.facebook.com/v24.0/120213241234568?access_token=YOUR_SANDBOX_TOKEN&fields=name,status,daily_budget,targeting"
```

### Run Unit Tests Against Sandbox

```bash
# Set sandbox credentials
export META_SANDBOX_TOKEN=your_token
export META_SANDBOX_ACCOUNT_ID=act_your_id

# Run integration tests
pytest tests/integration/test_meta_e2e.py -v
```

Expected output:
```
tests/integration/test_meta_e2e.py::test_create_campaign_sandbox PASSED
tests/integration/test_meta_e2e.py::test_create_ad_set_sandbox PASSED
tests/integration/test_meta_e2e.py::test_full_campaign_structure_sandbox PASSED
tests/integration/test_meta_e2e.py::test_update_budget_sandbox PASSED
tests/integration/test_meta_e2e.py::test_config_transformation_sandbox PASSED

✓ Integration tests completed
```

### Validation Checklist

- [ ] Campaign created with real ID
- [ ] Ad set created with real ID
- [ ] IDs returned are numeric (not `mock_xxx`)
- [ ] Campaign visible via API GET request
- [ ] Status is PAUSED
- [ ] Budget set correctly (check via API)
- [ ] Targeting parameters correct (check via API)
- [ ] No errors in API responses

### Common Sandbox Issues

**"Invalid OAuth access token"**
```
Meta API Error 190 (OAuthException): Invalid OAuth access token
```
→ Token expired. Regenerate in Access Token Tool.

**"Ad account does not exist"**
```
Meta API Error 100: Invalid parameter
```
→ Double-check `META_SANDBOX_ACCOUNT_ID` format: `act_XXXXXXXXX`

**"Permissions error"**
```
Meta API Error 200: Permissions error
```
→ Regenerate token with `ads_management` permission.

**Sandbox limitations**
- Campaigns not visible in Ads Manager UI (this is expected!)
- Creative creation may have restrictions
- Insights data is simulated

---

## Level 3: Production Testing (Real Ads, Real Spend)

**⚠️ WARNING**: This creates real campaigns that can spend real money when activated!

### Setup Production Credentials

#### Step 1: Get Production Access Token

1. Use the same Meta App from sandbox setup
2. Or create a production-ready app with full review
3. Generate token with `ads_management` permission
4. Store securely (consider using a secrets manager)

#### Step 2: Get Ad Account ID

1. Go to https://business.facebook.com/adsmanager
2. Select your ad account
3. Click **Settings** (gear icon)
4. Copy **Ad Account ID** (format: `act_XXXXXXXXX`)

#### Step 3: Verify Payment Method

1. In Ads Manager → **Billing & Payment Methods**
2. Ensure valid payment method is added
3. Set spending limits if desired

### Configure Environment

Update `.env`:

```bash
# Production Configuration
META_SANDBOX_MODE=false  # Important!

# Production credentials
META_ACCESS_TOKEN=EAAx...your_production_token
META_AD_ACCOUNT_ID=act_your_real_account_id
META_PAGE_ID=your_facebook_page_id
META_INSTAGRAM_ACTOR_ID=your_instagram_id

# Optional: API version
META_API_VERSION=v24.0
```

### Test with Minimal Budget First

**Best Practice**: Create a test campaign with $5/day budget first.

Modify your config:
```json
{
  "meta": {
    "campaign_name": "TEST - Delete After Review",
    "objective": "OUTCOME_TRAFFIC",
    "daily_budget": 5.0,  // $5/day
    ...
  }
}
```

### Run Production Test

```bash
# Double-check you're ready
echo "About to create REAL ads. Press Ctrl+C to cancel, Enter to continue."
read

python cli.py deploy-to-meta \
  --config-path test_config.json
```

### Expected Output

```
============================================================
  Meta Ads Deployment
============================================================

Config file: test_config.json
Campaign: TEST - Delete After Review
Daily budget: $5.0

Starting deployment...

✓ Campaign created: 120213999888777 (TEST - Delete After Review)
✓ Ad Set created: 120213999888778 (TEST - Delete After Review - Ad Set 1)

============================================================
  Deployment Complete
============================================================

✓ Campaign ID: 120213999888777
✓ Ad Set IDs: 120213999888778

Status: PAUSED

⚠️  Campaign created in PAUSED state
   Review in Meta Ads Manager, then activate when ready
   https://business.facebook.com/adsmanager

✓ Deployment result saved to: test_config_deployment_result.json
```

### Verify in Meta Ads Manager

1. Go to https://business.facebook.com/adsmanager
2. You should see your campaign: **TEST - Delete After Review**
3. Status: **Paused**
4. Click on campaign → Ad Set to review all settings

### Verification Checklist

**Campaign Level**
- [ ] Campaign name matches config
- [ ] Objective correct (Traffic, Sales, etc.)
- [ ] Status is PAUSED

**Ad Set Level**
- [ ] Daily budget: $5.00
- [ ] Targeting: Locations correct
- [ ] Targeting: Age range correct
- [ ] Targeting: Interests added
- [ ] Targeting: Behaviors added
- [ ] Placements: Only selected platforms checked
- [ ] Optimization goal: LINK_CLICKS or CONVERSIONS
- [ ] Billing: Impressions
- [ ] Attribution: 7-day click

**Ad Level** (if created)
- [ ] Creative attached
- [ ] Destination URL correct
- [ ] Status: PAUSED

### Test Activation (1 Hour Test)

If everything looks good:

1. In Ads Manager, select the ad set
2. Click **Edit**
3. Change status to **Active**
4. Monitor for 1 hour
5. Check for:
   - Ad delivery started (impressions > 0)
   - No errors in delivery column
   - Spend tracking works
6. **Pause immediately** after 1 hour
7. Delete test campaign

### Validation Checklist

- [ ] Campaign delivered impressions
- [ ] No errors in ad review
- [ ] Spend tracked correctly
- [ ] Link clicks recorded (if any)
- [ ] Can pause/unpause successfully
- [ ] Can update budget via API

### Clean Up Test Campaign

```python
# delete_test_campaign.py
import os
from src.integrations.meta_ads import MetaAdsAPI

api = MetaAdsAPI(
    access_token=os.getenv('META_ACCESS_TOKEN'),
    ad_account_id=os.getenv('META_AD_ACCOUNT_ID')
)

# First pause
api.pause_ad(ad_id="your_ad_id")

# Then delete via API (or manually in Ads Manager)
```

Or delete manually in Ads Manager.

---

## Automated Test Suite

Run the full test suite:

```bash
# Unit tests (no API calls)
pytest tests/test_meta_ads_api.py -v

# Integration tests (requires sandbox)
export META_SANDBOX_TOKEN=your_token
export META_SANDBOX_ACCOUNT_ID=act_your_id
pytest tests/integration/test_meta_e2e.py -v

# Specific test
pytest tests/test_meta_ads_api.py::TestMetaAdsAPI::test_create_campaign_success -v
```

---

## Testing Checklist (Complete Flow)

### Phase 1: Code Validation
- [ ] Dry-run test passes
- [ ] Config transformation works
- [ ] All payloads logged correctly
- [ ] Unit tests pass

### Phase 2: API Integration
- [ ] Sandbox account created
- [ ] Sandbox token generated
- [ ] Campaign created in sandbox
- [ ] Ad set created in sandbox
- [ ] IDs returned and verified via API
- [ ] Integration tests pass

### Phase 3: Production Readiness
- [ ] Production credentials configured
- [ ] Test campaign ($5/day) created
- [ ] Campaign visible in Ads Manager
- [ ] All settings correct
- [ ] 1-hour activation test successful
- [ ] Test campaign deleted

### Phase 4: Full Deployment
- [ ] Real campaign config generated by agent
- [ ] Deployed to production
- [ ] Reviewed in Ads Manager
- [ ] Activated for live traffic
- [ ] Monitoring and optimization in place

---

## Troubleshooting Guide

### Issue: "Config file not found"
```bash
# Check current directory
pwd

# List config files
ls -la campaign_*.json

# Use absolute path
python cli.py deploy-to-meta --config-path /full/path/to/config.json
```

### Issue: "No 'meta' section found"
Your config needs this structure:
```json
{
  "meta": {
    "campaign_name": "...",
    "objective": "...",
    "daily_budget": 100.0,
    ...
  }
}
```

Run agent to generate proper config:
```bash
python cli.py run --project-id test
```

### Issue: Token expired
```
Meta API Error 190: Invalid OAuth access token
```

**Sandbox**: Regenerate in Access Token Tool
**Production**: Use long-lived token or refresh token flow

### Issue: Rate limiting
```
Meta API Error 17: User request limit reached
```

The CLI has built-in retry with exponential backoff. If persistent:
- Wait 10-15 minutes
- Reduce request frequency
- Check account-level rate limits in Meta Business Suite

### Issue: Permissions error
```
Meta API Error 200: Permissions error
```

Token needs `ads_management` permission:
1. Access Token Tool → Generate New Token
2. Check `ads_management` permission
3. Generate and copy new token

### Issue: Sandbox campaigns not visible in UI
This is **expected behavior**. Sandbox campaigns only visible via API:
```bash
curl "https://graph.facebook.com/v24.0/CAMPAIGN_ID?access_token=TOKEN"
```

### Issue: Budget too low
```
Meta API Error: Budget too low for selected placements
```

Increase daily_budget in config (minimum ~$20/day for most campaigns).

---

## Best Practices

### Development
1. **Always start with dry-run** to validate config
2. **Use sandbox extensively** before production
3. **Run unit tests** before deploying
4. **Version control** deployment results

### Testing
1. **Test with minimal budget** first ($5-10/day)
2. **Review in Ads Manager** before activating
3. **Monitor for 1 hour** on first activation
4. **Keep test campaigns separate** (prefix with "TEST -")

### Production
1. **Create in PAUSED state** (default behavior)
2. **Review settings thoroughly** before activation
3. **Set spending limits** in ad account
4. **Monitor daily** for first week
5. **Keep deployment result JSONs** for audit trail

---

## Quick Reference

```bash
# Dry-run test
python cli.py deploy-to-meta --config-path config.json --dry-run

# Sandbox test
META_SANDBOX_MODE=true python cli.py deploy-to-meta --config-path config.json

# Production test
python cli.py deploy-to-meta --config-path config.json

# Unit tests
pytest tests/test_meta_ads_api.py -v

# Integration tests
pytest tests/integration/test_meta_e2e.py -v

# Verify via API
curl "https://graph.facebook.com/v24.0/CAMPAIGN_ID?access_token=TOKEN&fields=name,status"
```

---

## Additional Resources

- **Meta Marketing API Docs**: https://developers.facebook.com/docs/marketing-api
- **Sandbox Setup**: https://developers.facebook.com/docs/marketing-api/sandbox
- **Error Codes**: https://developers.facebook.com/docs/graph-api/using-graph-api/error-handling
- **Rate Limits**: https://developers.facebook.com/docs/graph-api/overview/rate-limiting

---

**Ready to test?** Start with Level 1 (dry-run) and work your way up!
