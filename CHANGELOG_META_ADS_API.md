# Meta Ads API Integration - Changelog

## [2.0.0] - 2025-10-21

### Added
- **Advantage+ Campaign Support (v23.0+)**
  - Added `advantage_plus` parameter to `create_campaign()`
  - Added `budget_rebalance` parameter for campaign budget optimization
  - Added `get_advantage_state()` method to check Advantage+ status

- **Advantage Audience Automation (v23.0+)**
  - Added `advantage_audience` parameter to `create_ad_set()` (defaults to 1)
  - Automatic inclusion of `targeting_automation` in targeting specs
  - Updated `_transform_agent_config_to_api()` to include advantage_audience

- **Enhanced Budget Features (v24.0+)**
  - Added `enable_budget_sharing` parameter for 20% budget sharing between ad sets
  - Daily budget flexibility increased from 25% to 75%

- **Placement Optimization (v24.0+)**
  - Added `enable_advantage_placement` parameter to allocate 5% to excluded placements
  - Applies to Sales and Leads objectives

- **Advantage+ Creative Enhancements (v22.0+)**
  - Added `advantage_creative_enhancements` parameter to `create_ad_creative()`
  - Support for individual enhancements: `enhance_cta`, `image_brightness_and_contrast`, `text_enhancements`
  - Added `enable_dynamic_media` parameter for catalog ads (defaults to OPT_IN)

- **Updated Attribution Model (June 2025)**
  - Updated attribution spec with both CLICK_THROUGH and VIEW_THROUGH
  - Aligned with new attribution timing model (impression time vs conversion time)

- **Documentation**
  - Created `docs/META_ADS_API_V24_UPDATES.md` with comprehensive migration guide
  - Created this changelog

### Changed
- **API Version**: Updated from v21.0/v22.0 to v24.0
- **Module Docstring**: Updated to reflect October 2025 changes and new features
- **create_campaign()**: Added new optional parameters for Advantage+ support
- **create_ad_set()**: Added 3 new parameters for automation features
- **create_ad_creative()**: Added 2 new parameters for creative enhancements
- **_transform_agent_config_to_api()**: Updated to include new v23.0+ and v24.0+ features

### Fixed
- Test `test_upload_image_from_url`: Fixed assertion to check `json` parameter instead of `data`
- Attribution spec now properly reflects June 2025 changes

### Deprecated
- **smart_promotion_type** flag will be deprecated in v25.0 (Q1 2026)
- **Advantage+ Creative bundles** replaced with individual enhancements (v22.0)
- **Video feed ad placements** no longer supported (v24.0)

### Upcoming (v25.0 - Q1 2026)
- ASC/AAC campaigns will no longer be supported across all API versions
- Advantage+ status will be solely determined by automation levers
- Prepare for migration to unified Advantage+ campaign structure

## [1.0.0] - Previous Version

### Features
- Basic campaign creation
- Ad set management
- Creative upload and management
- Image and video upload
- Performance tracking via Insights API
- Rate limiting and error handling
- Dry-run mode for testing

---

## Version Compatibility

| Integration Version | Meta API Version | Supported |
|---------------------|------------------|-----------|
| 2.0.0               | v24.0            | ✅ Current |
| 2.0.0               | v23.0            | ✅ Yes     |
| 2.0.0               | v22.0            | ✅ Yes     |
| 1.0.0               | v21.0            | ⚠️ Legacy  |

## Migration Path

To migrate from v1.0.0 to v2.0.0, see [META_ADS_API_V24_UPDATES.md](docs/META_ADS_API_V24_UPDATES.md).
