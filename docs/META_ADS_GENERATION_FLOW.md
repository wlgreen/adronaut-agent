# Meta Ads Generation Flow - End-to-End

**Complete workflow from historical data to live Meta campaigns**

Last Updated: October 21, 2025

---

## Overview

The Meta Ads generation flow transforms historical campaign data into optimized, executable Meta (Facebook/Instagram) campaigns through an AI-powered workflow. This document explains the complete end-to-end process.

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    META ADS GENERATION FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

   USER INPUT              AGENT WORKFLOW                   META ADS API
       │                         │                               │
       │  Historical Data        │                               │
       ├────────────────────────▶│                               │
       │  CSV/JSON               │                               │
       │  Campaign performance   │                               │
       │                         │                               │
       │                    ┌─────────┐                         │
       │                    │  STEP 1 │                         │
       │                    │ Analyze │                         │
       │                    │  Data   │                         │
       │                    └────┬────┘                         │
       │                         │                               │
       │                    Identifies:                          │
       │                    • Top performers                     │
       │                    • CPA trends                         │
       │                    • Platform patterns                  │
       │                         │                               │
       │                    ┌─────────┐                         │
       │                    │  STEP 2 │                         │
       │                    │Generate │                         │
       │                    │Strategy │                         │
       │                    └────┬────┘                         │
       │                         │                               │
       │                    Creates:                             │
       │                    • Campaign strategy                  │
       │                    • Test hypotheses                    │
       │                    • Budget allocation                  │
       │                         │                               │
       │                    ┌─────────┐                         │
       │                    │  STEP 3 │                         │
       │                    │Execution│                         │
       │                    │Timeline │                         │
       │                    └────┬────┘                         │
       │                         │                               │
       │                    Generates:                           │
       │                    • 7-30 day plan                      │
       │                    • Test combinations                  │
       │                    • Creative prompts                   │
       │                         │                               │
       │                    ┌─────────┐                         │
       │                    │  STEP 4 │                         │
       │                    │Campaign │                         │
       │                    │ Config  │                         │
       │                    └────┬────┘                         │
       │                         │                               │
       │                    Outputs:                             │
       │                    campaign_proj_v0.json                │
       │                         │                               │
       │                         ├─────────────────────────────┐ │
       │                         │                             │ │
       │                    ┌─────────┐                   ┌─────────┐
       │                    │  STEP 5 │                   │  STEP 6 │
       │                    │ Manual  │                   │   API   │
       │                    │ Setup   │                   │ Deploy  │
       │                    └────┬────┘                   └────┬────┘
       │                         │                             │
       │                    User creates                   Automated
       │                    in Ads Manager                 via API calls
       │                         │                             │
       │                         └──────────┬──────────────────┘
       │                                    │
       │                               Live Campaign
       │                                    │
       │                         ┌──────────▼──────────┐
       │                         │   META ADS MANAGER  │
       │                         │                     │
       │                         │  Campaign (PAUSED)  │
       │                         │  ├─ Ad Set 1        │
       │                         │  │  ├─ Ad 1         │
       │                         │  │  └─ Ad 2         │
       │                         │  └─ Ad Set 2        │
       │                         │     └─ Ad 3         │
       │                         └─────────────────────┘
       │
       │  Experiment Results
       │  (after 5-7 days)
       ├────────────────────────▶│
       │  CSV with performance   │
       │                         │
       │                    ┌─────────┐
       │                    │  STEP 7 │
       │                    │Optimize │
       │                    └────┬────┘
       │                         │
       │                    Generates:
       │                    • Patch strategy
       │                    • campaign_proj_v1.json
       │                         │
       │                    [Repeat cycle]
```

---

## Step-by-Step Breakdown

### STEP 1: Data Analysis

**Input Required:**
```
Historical campaign data (CSV or JSON)
```

**Required Columns:**
```
campaign_name, platform, spend, conversions, CPA, ROAS
```

**Optional Columns:**
```
impressions, clicks, CTR, audience, creative_type, placement
```

**Example Data:**
```csv
campaign_name,platform,spend,conversions,CPA,ROAS
Summer Sale - TikTok,TikTok,500.00,25,20.00,3.5
Summer Sale - Meta,Meta,600.00,30,20.00,4.2
Fall Promo - TikTok,TikTok,450.00,18,25.00,2.8
```

**What Happens:**
```python
# Agent Node: data_collection_node
DataLoader.get_detailed_analysis(historical_data)
```

**Output:**
```
Performance Summary:
• Total campaigns: 3
• Average CPA: $21.67
• Best platform: Meta (CPA $20, ROAS 4.2)
• Top performer: Summer Sale - Meta
• Bottom performer: Fall Promo - TikTok
```

**Agent Uses This To:**
- Identify what's working (Meta vs TikTok)
- Find CPA trends and patterns
- Understand audience/creative effectiveness

---

### STEP 2: Strategy Generation

**Input:**
- Historical data analysis (from Step 1)
- User inputs (product, budget, goals)

**LLM Task:**
```
Task: "Strategy & Insights Generation"
Temperature: 0.7 (creative but grounded)
Model: Gemini 2.0 Flash
```

**What It Generates:**
```json
{
  "strategic_insights": [
    {
      "insight": "Meta campaigns consistently outperform TikTok by 15% on CPA",
      "data_reference": "Meta avg CPA $20 vs TikTok $25",
      "confidence": 0.9
    },
    {
      "insight": "Lifestyle creative yields 20% better ROAS than product demos",
      "data_reference": "Lifestyle ROAS 4.2 vs Demo 3.5",
      "confidence": 0.85
    }
  ],
  "strategic_recommendations": {
    "platform_allocation": {
      "meta": 0.6,
      "tiktok": 0.4,
      "reasoning": "Meta shows lower CPA and higher ROAS"
    },
    "testing_priorities": [
      "Test new audience segments on Meta",
      "Compare UGC vs lifestyle creative on TikTok"
    ]
  },
  "hypotheses_to_test": [
    {
      "hypothesis": "Expanding Meta audience to 35-44 age group will maintain CPA <$25",
      "test_design": "A/B test current 25-34 vs new 35-44 segment",
      "success_criteria": "CPA < $25, min 15 conversions"
    }
  ]
}
```

**File Output:**
```
None - stored in agent state
```

---

### STEP 3: Execution Timeline

**Input:**
- Strategy (from Step 2)
- User budget constraint
- Campaign complexity

**LLM Task:**
```
Task: "Execution Timeline Planning"
Temperature: 0.6 (structured but adaptive)
Model: Gemini 2.0 Flash
```

**What It Generates:**
```json
{
  "timeline": {
    "total_duration_days": 14,
    "reasoning": "14 days allows for 2 phases with statistically significant results",
    "phases": [
      {
        "name": "Phase 1: Discovery",
        "duration_days": 7,
        "budget_allocation_percent": 50,
        "test_combinations": [
          {
            "combo_id": "meta_f_25-34_lifestyle",
            "platform": "Meta",
            "audience": "Females 25-34, fitness enthusiasts",
            "creative_style": "Lifestyle - aspirational",
            "messaging_angle": "Transformation",
            "daily_budget": 75.00,

            "creative_generation": {
              "visual_prompt": "A 28-year-old woman in athletic wear...",
              "copy_primary_text": "Your morning routine just got better...",
              "copy_headline": "Premium Quality, Zero Compromise",
              "copy_cta": "SHOP_NOW",
              "hooks": [
                "Ever notice how the best mornings start with...",
                "I've tried 12 water bottles. This is the one.",
                "24-hour cold. I fill it once a day.",
                "Your commute could be the best part of...",
                "The difference between good and great? Details."
              ],
              "technical_specs": {
                "aspect_ratio": "1:1",
                "dimensions": "1080x1080",
                "file_format": "PNG"
              }
            }
          },
          {
            "combo_id": "meta_m_25-34_professional",
            "platform": "Meta",
            "audience": "Males 25-34, tech professionals",
            "creative_style": "Professional - minimalist",
            "messaging_angle": "Performance",
            "daily_budget": 75.00,

            "creative_generation": { /* ... */ }
          }
        ]
      },
      {
        "name": "Phase 2: Optimization",
        "duration_days": 7,
        "budget_allocation_percent": 50,
        "test_combinations": [ /* ... */ ]
      }
    ]
  }
}
```

**File Output:**
```
None - stored in agent state as experiment_plan
```

**Creative Generation Detail:**
Each test combination includes:
- `visual_prompt`: 250-600 word image generation prompt
- `copy_primary_text`: Platform-compliant ad copy
- `copy_headline`: Attention-grabbing headline
- `copy_cta`: Call-to-action type
- `hooks`: 5 variations for testing
- `technical_specs`: Platform requirements

---

### STEP 4: Campaign Configuration

**Input:**
- Strategy (from Step 2)
- Execution timeline (from Step 3)
- User inputs (budget, product)

**LLM Task:**
```
Task: "Campaign Configuration"
Temperature: 0.5 (balanced)
Model: Gemini 2.0 Flash
```

**What It Generates:**
```json
{
  "tiktok": {
    "campaign_name": "EcoBottle - Phase 1 Discovery - TikTok",
    "objective": "CONVERSIONS",
    "daily_budget": 150.00,
    "targeting": {
      "age_range": "25-44",
      "gender": "ALL",
      "locations": ["United States"],
      "interests": ["Fitness", "Sustainability", "Wellness"],
      "behaviors": ["Online shoppers", "Engaged shoppers"]
    },
    "placements": ["TikTok In-Feed", "TikTok TopView"],
    "bidding": {
      "strategy": "LOWEST_COST_WITH_BID_CAP",
      "bid_amount": 32.00,
      "target_cpa": 25.00
    },
    "creative_specs": {
      "format": "Video (9:16 for primary, 1:1 for secondary)",
      "duration": "15-30 seconds",
      "messaging": [
        "Problem/Solution: Articulate single-use plastic problem",
        "Authenticity: UGC-style video",
        "Benefit-driven: Highlight '24hrs cold' feature"
      ]
    },
    "optimization": {
      "optimization_goal": "CONVERSIONS",
      "attribution_window": "7_DAY_CLICK"
    }
  },

  "meta": {
    "campaign_name": "EcoBottle - Phase 1 Discovery - Meta",
    "objective": "OUTCOME_SALES",
    "daily_budget": 150.00,
    "targeting": {
      "age_range": "25-44",
      "gender": "ALL",
      "locations": ["United States"],
      "detailed_targeting": {
        "interests": [
          "Environmentalism",
          "Sustainable living",
          "Fitness and wellness",
          "Yoga",
          "Running"
        ],
        "behaviors": [
          "Online shoppers",
          "Engaged shoppers",
          "Frequent travelers"
        ]
      },
      "advantage_audience": 1
    },
    "placements": [
      "Facebook Feed",
      "Instagram Feed",
      "Instagram Stories",
      "Instagram Reels"
    ],
    "bidding": {
      "strategy": "LOWEST_COST_WITH_BID_CAP",
      "bid_amount": 32.00,
      "target_cpa": 25.00
    },
    "creative_specs": {
      "formats": [
        "Video (9:16 for Stories/Reels, 1:1 for Feeds)",
        "Carousel (1:1) - backup format"
      ],
      "messaging": [
        "Problem/Solution: Single-use plastic problem",
        "Authenticity: UGC-style or lifestyle photography",
        "Benefit: 24-hour temperature retention",
        "Urgency: Limited time offer"
      ]
    },
    "optimization": {
      "optimization_goal": "CONVERSIONS",
      "conversion_window": "7_DAY_CLICK",
      "pixel_event": "Purchase"
    },
    "advantage_plus": false,
    "enable_advantage_placement": true,
    "enable_budget_sharing": false
  },

  "summary": {
    "total_daily_budget": 300.00,
    "budget_allocation": {
      "tiktok": 150.00,
      "meta": 150.00
    },
    "experiment": "Testing audience segments and creative styles across platforms"
  },

  "creative_assets": [
    {
      "combo_id": "meta_f_25-34_lifestyle",
      "platform": "Meta",
      "creative_generation": {
        "visual_prompt": "A 28-year-old woman in athletic wear stands...",
        "copy_primary_text": "Your morning routine just got better...",
        "copy_headline": "Premium Quality, Zero Compromise",
        "copy_cta": "SHOP_NOW",
        "hooks": [ /* 5 variations */ ],
        "technical_specs": { /* Meta specs */ }
      }
    },
    {
      "combo_id": "meta_m_25-34_professional",
      "platform": "Meta",
      "creative_generation": { /* ... */ }
    }
    /* ... more creative assets ... */
  ]
}
```

**File Output:**
```
campaign_[project_id]_v0.json
```

**This file is the bridge between agent and Meta Ads API**

---

### STEP 5: Manual Campaign Setup (Current)

**Using:** `docs/MANUAL_META_ADS_SETUP.md`

**Process:**
1. User opens Meta Ads Manager
2. Follows guide to manually create:
   - Campaign with objective
   - Ad Set with targeting
   - Creative with copy
   - Ads linking creative to ad set

**Status:** All campaigns created as PAUSED for review

**Timeline:** 15-30 minutes per campaign

**Pros:**
- Full control over settings
- Visual review before activation
- No API credentials needed

**Cons:**
- Manual work
- Potential for human error
- Time-consuming for multiple campaigns

---

### STEP 6: API Deployment (Future/In Development)

**Using:** `src/integrations/meta_ads.py`

**Automated Flow:**
```python
from src.integrations.meta_ads import MetaAdsAPI
import json

# Load config
with open("campaign_proj_v0.json") as f:
    config = json.load(f)

# Initialize API
api = MetaAdsAPI(
    access_token=os.getenv("META_ACCESS_TOKEN"),
    ad_account_id=os.getenv("META_AD_ACCOUNT_ID"),
    page_id=os.getenv("META_PAGE_ID"),
    api_version="v24.0"
)

# Deploy campaign
result = api.create_campaign_from_config(config)

print(f"Campaign ID: {result['campaign_id']}")
print(f"Ad Set IDs: {result['ad_set_ids']}")
print(f"Status: {result['status']}")
```

**What `create_campaign_from_config()` Does:**

```
Step 1: Transform config to API format
        ├─ Parse targeting (age_range → age_min/age_max)
        ├─ Convert budget to cents ($150 → 15000)
        └─ Add v24.0 features (advantage_audience, etc.)

Step 2: Create Campaign
        POST /{ad_account_id}/campaigns
        {
          "name": "EcoBottle - Phase 1 Discovery - Meta",
          "objective": "OUTCOME_SALES",
          "status": "PAUSED",
          "special_ad_categories": []
        }
        → Returns: campaign_id

Step 3: Create Ad Set
        POST /{ad_account_id}/adsets
        {
          "campaign_id": "123456789",
          "name": "EcoBottle - Phase 1 Discovery - Meta - Ad Set 1",
          "daily_budget": "15000",  // In cents
          "optimization_goal": "CONVERSIONS",
          "billing_event": "IMPRESSIONS",
          "targeting": {
            "geo_locations": {"countries": ["US"]},
            "age_min": 25,
            "age_max": 44,
            "interests": [{"name": "Environmentalism"}, ...],
            "targeting_automation": {"advantage_audience": 1}
          },
          "attribution_spec": [
            {"event_type": "CLICK_THROUGH", "window_days": 7},
            {"event_type": "VIEW_THROUGH", "window_days": 1}
          ],
          "status": "PAUSED"
        }
        → Returns: ad_set_id

Step 4: Upload Images (IF PROVIDED)
        POST /{ad_account_id}/adimages
        {
          "bytes": <image_data>
        }
        → Returns: image_hash

Step 5: Create Ad Creative
        POST /{ad_account_id}/adcreatives
        {
          "name": "Creative 1 - meta_f_25-34_lifestyle",
          "object_story_spec": {
            "page_id": "987654321",
            "link_data": {
              "message": "Your morning routine just got better...",
              "name": "Premium Quality, Zero Compromise",
              "link": "https://example.com/product",
              "picture": "<image_hash>",
              "call_to_action": {
                "type": "SHOP_NOW",
                "value": {"link": "https://example.com/product"}
              }
            }
          },
          "advantage_creative_enhancements": {
            "enhance_cta": true,
            "text_enhancements": true
          }
        }
        → Returns: creative_id

Step 6: Create Ad
        POST /{ad_account_id}/ads
        {
          "name": "Ad 1",
          "adset_id": "<ad_set_id>",
          "creative": {"creative_id": "<creative_id>"},
          "status": "PAUSED"
        }
        → Returns: ad_id

Step 7: Return Results
        {
          "campaign_id": "123456789",
          "ad_set_ids": ["111222333"],
          "creative_ids": ["444555666"],
          "ad_ids": ["777888999"],
          "status": "PAUSED"
        }
```

**Timeline:** 30-60 seconds (automated)

**Current Status:**
- ✅ Campaign creation implemented
- ✅ Ad Set creation implemented (with v24.0 features)
- ⚠️  Image upload implemented
- ⚠️  Creative creation partially implemented
- ⚠️  Ad creation stubbed (needs creative IDs)

**Blocker:** Image generation from visual_prompt not yet integrated

---

### STEP 7: Optimization Cycle

**After 5-7 Days:**

User exports performance data from Meta Ads Manager:

```csv
campaign_name,ad_set_name,spend,impressions,clicks,conversions,CPA,ROAS
EcoBottle - Meta - Ad Set 1,Ad Set 1,525.00,12500,450,21,25.00,3.8
```

**Upload to Agent:**
```bash
python cli.py run --project-id ecobottle-001
# Prompted for experiment results file
> experiment_results.csv
```

**Agent Workflow:**
```
STEP 7a: Reflection
         ├─ Compare performance vs targets (CPA < $25 ✓)
         ├─ Identify top performers (Ad Set 1 performing well)
         └─ Find optimization opportunities (expand winning audience)

STEP 7b: Generate Patch Strategy
         {
           "reasoning": "Ad Set 1 exceeded target with CPA $25 and ROAS 3.8.
                        Recommend expanding budget and testing broader age range.",
           "changes": {
             "meta": {
               "daily_budget": 200.00,  // +$50
               "targeting": {
                 "age_range": "25-50"   // Expanded from 25-44
               }
             }
           }
         }

STEP 7c: Generate New Config
         campaign_ecobottle-001_v1.json
```

**User repeats STEP 5 or 6 with new config**

**Iteration continues until:**
- Performance goals achieved
- Budget exhausted
- Test complete

---

## Data Flow Summary

```
Historical CSV → Agent State → Strategy JSON → Timeline JSON →
Campaign Config JSON → Meta API Calls → Live Campaign →
Performance CSV → Agent State → Patch JSON → Updated Campaign Config
```

---

## Config-to-API Mapping Reference

### Campaign Level

| Config Field | API Parameter | Transformation |
|--------------|---------------|----------------|
| `meta.campaign_name` | `name` | Direct |
| `meta.objective` | `objective` | Direct (OUTCOME_SALES) |
| `meta.advantage_plus` | Campaign-level flag | v23.0+ feature |

### Ad Set Level

| Config Field | API Parameter | Transformation |
|--------------|---------------|----------------|
| `meta.daily_budget` | `daily_budget` | $150 → "15000" (cents) |
| `meta.targeting.age_range` | `age_min`, `age_max` | "25-44" → 25, 44 |
| `meta.targeting.locations` | `geo_locations.countries` | ["United States"] |
| `meta.targeting.detailed_targeting.interests` | `interests` | Array of `{name: "..."}` |
| `meta.targeting.advantage_audience` | `targeting_automation.advantage_audience` | 0 or 1 (default: 1) |
| `meta.optimization.optimization_goal` | `optimization_goal` | Direct |
| `meta.optimization.conversion_window` | `attribution_spec` | "7_DAY_CLICK" → array |
| `meta.bidding.strategy` | `bid_strategy` | Direct |
| `meta.bidding.bid_amount` | Cost control | $32 |
| `meta.enable_advantage_placement` | `targeting_optimization.excluded_placement_override_percentage` | true → 5 |
| `meta.enable_budget_sharing` | `adset_budget_sharing` | true/false |

### Creative Level

| Config Field | API Parameter | Transformation |
|--------------|---------------|----------------|
| `creative_assets[].creative_generation.copy_primary_text` | `object_story_spec.link_data.message` | Direct |
| `creative_assets[].creative_generation.copy_headline` | `object_story_spec.link_data.name` | Direct |
| `creative_assets[].creative_generation.copy_cta` | `object_story_spec.link_data.call_to_action.type` | Direct |
| `creative_specs.link` | `object_story_spec.link_data.link` | Direct |
| `<image_file>` | `picture` | Upload → image_hash |

---

## Testing the Flow

### Dry Run Mode (No API Calls)

```python
api = MetaAdsAPI(
    access_token="test_token",
    ad_account_id="act_123",
    dry_run=True  # Logs calls, doesn't execute
)

result = api.create_campaign_from_config(config)
# Prints all API calls that WOULD be made
```

### Sandbox Mode (Test Environment)

```python
api = MetaAdsAPI(
    access_token=os.getenv("META_SANDBOX_TOKEN"),
    ad_account_id=os.getenv("META_SANDBOX_ACCOUNT"),
    sandbox_mode=True  # Uses Meta's sandbox
)

result = api.create_campaign_from_config(config)
# Creates campaign in sandbox (no real ads delivered)
```

### Production Mode

```python
api = MetaAdsAPI(
    access_token=os.getenv("META_ACCESS_TOKEN"),
    ad_account_id=os.getenv("META_AD_ACCOUNT_ID"),
    page_id=os.getenv("META_PAGE_ID"),
    api_version="v24.0"
)

result = api.create_campaign_from_config(config)
# Creates real campaign (PAUSED by default)
```

---

## Required Credentials

### For Manual Setup (Step 5):
```
✓ Meta Ads Manager access
✓ Ad account with payment method
✓ Facebook Page
✓ (Optional) Meta Pixel for conversion tracking
```

### For API Deployment (Step 6):
```
✓ Meta App created at developers.facebook.com/apps
✓ Marketing API product added
✓ Access token with ads_management permission
✓ Ad Account ID (format: act_XXXXXXXXX)
✓ Facebook Page ID
✓ (Optional) Instagram Actor ID
```

**Setup Guide:** `docs/META_ADS_TESTING_GUIDE.md`

---

## Current Limitations & Roadmap

### Current Limitations:
1. ⚠️  **Image generation not integrated**
   - Visual prompts generated but not converted to images
   - Manual upload required

2. ⚠️  **Single ad set per campaign**
   - API creates 1 ad set per campaign
   - Multiple test combinations need separate campaigns

3. ⚠️  **No automatic activation**
   - All campaigns created as PAUSED
   - Manual review and activation required

### Roadmap:

**Q1 2026:**
- [ ] Integrate image generation API (Nano Banana / Gemini Image)
- [ ] Multi-ad set support per campaign
- [ ] Batch creative upload
- [ ] Automatic campaign activation option

**Q2 2026:**
- [ ] Real-time performance monitoring
- [ ] Automatic budget adjustment
- [ ] A/B test automation
- [ ] Cross-platform budget optimization

---

## File Reference

| File | Purpose |
|------|---------|
| `src/modules/campaign.py` | Generates campaign config from strategy |
| `src/integrations/meta_ads.py` | Meta Marketing API integration |
| `src/modules/creative_generator.py` | Generates creative prompts |
| `docs/MANUAL_META_ADS_SETUP.md` | Manual setup guide |
| `docs/META_ADS_API_V24_UPDATES.md` | API v24.0 changes |
| `docs/META_ADS_TESTING_GUIDE.md` | Testing & credentials setup |

---

## Example: Complete Flow

```bash
# 1. Upload historical data
python cli.py run --project-id ecobottle-001
> historical_campaigns.csv

# Agent generates:
# - Strategy
# - Execution timeline with creative prompts
# - campaign_ecobottle-001_v0.json

# 2. Review generated config
cat campaign_ecobottle-001_v0.json

# 3a. OPTION A: Manual setup
# Follow docs/MANUAL_META_ADS_SETUP.md

# 3b. OPTION B: API deployment (future)
python -c "
from src.integrations.meta_ads import MetaAdsAPI
import json, os

with open('campaign_ecobottle-001_v0.json') as f:
    config = json.load(f)

api = MetaAdsAPI(
    access_token=os.getenv('META_ACCESS_TOKEN'),
    ad_account_id=os.getenv('META_AD_ACCOUNT_ID'),
    page_id=os.getenv('META_PAGE_ID')
)

result = api.create_campaign_from_config(config)
print(f'Campaign created: {result[\"campaign_id\"]}')
"

# 4. Run campaign for 5-7 days

# 5. Export performance data from Meta Ads Manager
# Save as experiment_results.csv

# 6. Upload results for optimization
python cli.py run --project-id ecobottle-001
> experiment_results.csv

# Agent generates:
# - campaign_ecobottle-001_v1.json (optimized)

# 7. Repeat steps 3-6 until goals achieved
```

---

## Troubleshooting

### "Config not generating creative_assets"
**Cause:** No execution timeline in state
**Fix:** Ensure STEP 3 completes successfully

### "API returns 400 Bad Request"
**Cause:** Invalid targeting or config format
**Fix:** Review API error message, check config transformation

### "Campaign created but no ads"
**Cause:** Image upload not implemented
**Fix:** Use manual setup (Step 5) for now

### "Advantage+ features not applying"
**Cause:** Using API version < v23.0
**Fix:** Update `api_version="v24.0"` in MetaAdsAPI init

---

## Support

- **Manual Setup Issues:** See `docs/MANUAL_META_ADS_SETUP.md`
- **API Integration:** See `docs/META_ADS_API_V24_UPDATES.md`
- **Testing:** See `docs/META_ADS_TESTING_GUIDE.md`
- **Creative Generation:** See `docs/AD_GENERATION_WORKFLOW.md`

---

**Last Updated:** October 21, 2025
**API Version:** v24.0
**Status:** Manual setup (Step 5) fully functional, API deployment (Step 6) in development
