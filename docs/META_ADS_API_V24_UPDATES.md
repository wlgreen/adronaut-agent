# Meta Ads API v24.0 Updates - October 2025

This document outlines the major updates made to the Meta Ads API integration to support the latest API changes from v22.0 through v24.0.

## Overview

The integration has been updated to reflect the latest Meta Marketing API changes as of October 2025. The current implementation supports API v24.0 and is prepared for the upcoming v25.0 changes in Q1 2026.

## Major Changes

### 1. Advantage+ Campaign Structure (v23.0+)

**What Changed:**
- Meta introduced a unified campaign structure that eliminates separate workflows for Advantage+ Shopping Campaigns (ASC) and Advantage+ App Campaigns (AAC)
- The new structure uses automation levers (budget, audience, placement) to determine Advantage+ status
- The `smart_promotion_type` flag is deprecated in v25.0 (Q1 2026)

**Implementation:**
```python
# New campaign creation with Advantage+ support
campaign_id = api.create_campaign(
    name="My Campaign",
    objective="OUTCOME_SALES",
    advantage_plus=True,  # Enable Advantage+ mode
    budget_rebalance=True  # Enable budget rebalancing (v24.0+)
)
```

**New Method:**
- `get_advantage_state(campaign_id)` - Check if campaign is in Advantage+ setup using the `advantage_state_info` flag

### 2. Advantage Audience Targeting Automation (v23.0+)

**What Changed:**
- The `advantage_audience` parameter in `targeting_automation` now defaults to 1
- Must be explicitly set to 1 or 0 when creating new ad sets

**Implementation:**
```python
# Ad set creation now includes advantage_audience
ad_set_id = api.create_ad_set(
    campaign_id=campaign_id,
    name="Ad Set 1",
    daily_budget=2500,
    targeting=targeting_spec,
    advantage_audience=1  # Enable audience automation (default)
)
```

### 3. Enhanced Budget Flexibility (v24.0+)

**What Changed:**
- Daily budget flexibility increased from 25% to 75%
- Ad sets can now spend up to 75% more on high-opportunity days while maintaining weekly cap
- Budget sharing allows up to 20% transfer between ad sets without CBO

**Implementation:**
```python
ad_set_id = api.create_ad_set(
    # ... other params ...
    enable_budget_sharing=True  # Allow 20% budget sharing
)
```

### 4. Placement Optimization (v24.0+)

**What Changed:**
- Meta now allocates up to 5% of budget to excluded placements when they're likely to perform well
- Applies to Sales and Leads objectives

**Implementation:**
```python
ad_set_id = api.create_ad_set(
    # ... other params ...
    enable_advantage_placement=True  # Enable 5% to excluded placements
)
```

### 5. Attribution Model Updates (June 2025)

**What Changed:**
- On-Meta events (link clicks, page views, Facebook lead forms) are attributed to impression time
- Off-Meta events (website purchases, external signups) are attributed to conversion time

**Implementation:**
```python
# Attribution spec automatically updated in create_ad_set()
data["attribution_spec"] = [
    {"event_type": "CLICK_THROUGH", "window_days": 7},
    {"event_type": "VIEW_THROUGH", "window_days": 1}
]
```

### 6. Advantage+ Creative Enhancements (v22.0+)

**What Changed:**
- Advantage+ Creative Standard Enhancements bundle deprecated
- Individual enhancements must now be opted into separately
- New support for previewing individual enhancements

**Available Enhancements:**
- `enhance_cta` - Enhance call-to-action
- `image_brightness_and_contrast` - Adjust image brightness/contrast
- `text_enhancements` - Enhance ad copy

**Implementation:**
```python
creative_id = api.create_ad_creative(
    name="My Creative",
    link="https://example.com",
    message="Ad copy",
    headline="Headline",
    image_hash=image_hash,
    advantage_creative_enhancements={
        "enhance_cta": True,
        "image_brightness_and_contrast": True,
        "text_enhancements": True
    }
)
```

### 7. Dynamic Media Default (v24.0+)

**What Changed:**
- Dynamic media now defaults to OPT_IN for Advantage+ Catalog Ads as of September 1, 2025
- Applies to Single Image, Carousel, and Collection formats

**Implementation:**
```python
creative_id = api.create_ad_creative(
    # ... other params ...
    enable_dynamic_media=True  # Default for catalog ads
)
```

## Breaking Changes (v24.0 → v25.0)

### Q1 2026: Marketing API v25.0

**Critical Changes:**
1. **ASC/AAC Campaigns:** Creation or updates will no longer be possible across all API versions
2. **Advantage+ Determination:** Will be solely based on automation levers (no `smart_promotion_type`)
3. **Video Feed Placements:** No longer supported as of v24.0

## Updated Workflow

### Complete Campaign Creation Flow

```python
from src.integrations.meta_ads import MetaAdsAPI

# Initialize API
api = MetaAdsAPI(
    access_token=access_token,
    ad_account_id=ad_account_id,
    page_id=page_id,
    api_version="v24.0"  # Latest stable version
)

# Step 1: Create Campaign with Advantage+
campaign_id = api.create_campaign(
    name="My Campaign",
    objective="OUTCOME_SALES",
    advantage_plus=True,
    budget_rebalance=True
)

# Step 2: Create Ad Set with new features
targeting = {
    "geo_locations": {"countries": ["US"]},
    "age_min": 25,
    "age_max": 45,
    "targeting_automation": {
        "advantage_audience": 1  # Enable audience automation
    }
}

ad_set_id = api.create_ad_set(
    campaign_id=campaign_id,
    name="Ad Set 1",
    daily_budget=5000,  # $50/day
    targeting=targeting,
    optimization_goal="CONVERSIONS",
    advantage_audience=1,
    enable_advantage_placement=True,
    enable_budget_sharing=True
)

# Step 3: Upload Image
image_hash = api.upload_image(image_path="path/to/image.jpg")

# Step 4: Create Creative with Advantage+ enhancements
creative_id = api.create_ad_creative(
    name="My Creative",
    link="https://example.com/product",
    message="Check out our amazing product!",
    headline="Limited Time Offer",
    image_hash=image_hash,
    advantage_creative_enhancements={
        "enhance_cta": True,
        "text_enhancements": True
    },
    enable_dynamic_media=True
)

# Step 5: Create Ad
ad_id = api.create_ad(
    ad_set_id=ad_set_id,
    creative_id=creative_id,
    name="Ad 1",
    status="PAUSED"
)

# Step 6: Check Advantage+ status
advantage_status = api.get_advantage_state(campaign_id)
print(f"Advantage+ Status: {advantage_status}")
```

## Migration Guide

### Updating from Previous Versions

If you're using an older version of the integration, follow these steps:

1. **Update API Version:**
   ```python
   api = MetaAdsAPI(
       access_token=token,
       ad_account_id=account_id,
       api_version="v24.0"  # Update from v21.0, v22.0, v23.0
   )
   ```

2. **Add advantage_audience to Targeting:**
   ```python
   # Old way
   targeting = {
       "geo_locations": {"countries": ["US"]},
       "age_min": 25,
       "age_max": 45
   }

   # New way (v23.0+)
   targeting = {
       "geo_locations": {"countries": ["US"]},
       "age_min": 25,
       "age_max": 45,
       "targeting_automation": {
           "advantage_audience": 1  # Must be explicitly set
       }
   }
   ```

3. **Enable New v24.0 Features:**
   ```python
   ad_set_id = api.create_ad_set(
       # ... existing params ...
       enable_advantage_placement=True,  # NEW: 5% to excluded placements
       enable_budget_sharing=True  # NEW: Budget sharing
   )
   ```

4. **Update Creative Enhancements:**
   ```python
   # Old way (deprecated)
   # advantage_plus_creative = True

   # New way (v22.0+)
   advantage_creative_enhancements = {
       "enhance_cta": True,
       "image_brightness_and_contrast": True
   }
   ```

## Testing

All unit tests have been updated to reflect the new API changes:

```bash
# Run unit tests
python -m unittest tests.test_meta_ads_api -v

# Run integration tests (requires sandbox credentials)
python -m pytest tests/integration/test_meta_e2e.py --sandbox
```

## Backward Compatibility

The integration maintains backward compatibility by:

1. **Default Values:** All new parameters have sensible defaults
2. **Optional Features:** New v24.0 features can be opted into via flags
3. **Graceful Degradation:** Old configs will work but won't use new features

## Important Notes

1. **API Version Support:** Meta supports each API version for 2 years
2. **v24.0 Deprecation:** Will be deprecated around October 2027
3. **v25.0 Breaking Changes:** Prepare for ASC/AAC deprecation in Q1 2026
4. **Testing:** Always test in sandbox mode before production deployment

## Resources

- [Meta Marketing API Documentation](https://developers.facebook.com/docs/marketing-api)
- [API Versioning](https://developers.facebook.com/docs/marketing-api/versions)
- [Advantage+ Campaigns Guide](https://www.facebook.com/business/help/advantage-plus-campaigns)
- [Creative Enhancements](https://developers.facebook.com/docs/marketing-api/creative-enhancements)

## Support

For issues or questions:
1. Check the [META_ADS_TESTING_GUIDE.md](./META_ADS_TESTING_GUIDE.md)
2. Review the [MANUAL_META_ADS_SETUP.md](./MANUAL_META_ADS_SETUP.md)
3. Open an issue in the repository

---

**Last Updated:** October 21, 2025
**API Version:** v24.0
**Next Review:** Q1 2026 (for v25.0 changes)
