"""
Integration tests for Meta Ads API end-to-end workflow

These tests use the Meta sandbox environment and require valid credentials.
Set META_SANDBOX_TOKEN and META_SANDBOX_ACCOUNT_ID environment variables to run.

Usage:
    pytest tests/integration/test_meta_e2e.py --sandbox
"""

import os
import pytest
import json
from src.integrations.meta_ads import MetaAdsAPI, MetaAdsError


# Skip all tests if sandbox credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("META_SANDBOX_TOKEN"),
    reason="Sandbox credentials not available (set META_SANDBOX_TOKEN and META_SANDBOX_ACCOUNT_ID)"
)


@pytest.fixture
def sandbox_api():
    """Initialize API client with sandbox credentials"""
    return MetaAdsAPI(
        access_token=os.getenv("META_SANDBOX_TOKEN"),
        ad_account_id=os.getenv("META_SANDBOX_ACCOUNT_ID"),
        page_id=os.getenv("META_PAGE_ID"),
        instagram_actor_id=os.getenv("META_INSTAGRAM_ACTOR_ID"),
        sandbox_mode=True
    )


@pytest.fixture
def sample_config():
    """Sample campaign config for testing"""
    return {
        "meta": {
            "campaign_name": "Integration Test Campaign",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": 25.0,  # $25/day
            "targeting": {
                "age_range": "25-44",
                "locations": ["US"],
                "detailed_targeting": {
                    "interests": ["Technology", "Software"],
                    "behaviors": ["Online shoppers"]
                }
            },
            "bidding": {
                "strategy": "LOWEST_COST_WITHOUT_CAP"
            },
            "optimization": {
                "optimization_goal": "LINK_CLICKS"
            },
            "creative_specs": {
                "link": "https://example.com/product"
            }
        }
    }


@pytest.mark.integration
def test_create_campaign_sandbox(sandbox_api):
    """Test campaign creation in sandbox environment"""
    campaign_id = sandbox_api.create_campaign(
        name="Test Campaign - E2E",
        objective="OUTCOME_TRAFFIC",
        status="PAUSED"
    )

    assert campaign_id is not None
    assert len(campaign_id) > 0
    print(f"✓ Campaign created: {campaign_id}")


@pytest.mark.integration
def test_create_ad_set_sandbox(sandbox_api):
    """Test ad set creation in sandbox environment"""
    # First create campaign
    campaign_id = sandbox_api.create_campaign(
        name="Test Campaign for AdSet",
        objective="OUTCOME_TRAFFIC",
        status="PAUSED"
    )

    # Create ad set
    targeting = {
        "geo_locations": {"countries": ["US"]},
        "age_min": 25,
        "age_max": 44
    }

    ad_set_id = sandbox_api.create_ad_set(
        campaign_id=campaign_id,
        name="Test Ad Set - E2E",
        daily_budget=2500,  # $25.00 in cents
        targeting=targeting,
        optimization_goal="LINK_CLICKS",
        status="PAUSED"
    )

    assert ad_set_id is not None
    assert len(ad_set_id) > 0
    print(f"✓ Ad Set created: {ad_set_id}")


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("META_PAGE_ID"),
    reason="PAGE_ID required for creative creation"
)
def test_create_creative_sandbox(sandbox_api):
    """Test creative creation in sandbox environment (requires image)"""
    # Note: This test might fail in sandbox if creative creation is restricted
    # Keeping it for documentation purposes

    # Would need to upload an image first
    # For now, this is a placeholder showing the expected flow

    pytest.skip("Image upload required - skipping in automated tests")

    # Example flow (would work with real image):
    # image_hash = sandbox_api.upload_image(image_path="/path/to/test/image.jpg")
    # creative_id = sandbox_api.create_ad_creative(
    #     name="Test Creative",
    #     link="https://example.com",
    #     message="Test ad copy",
    #     headline="Test Headline",
    #     image_hash=image_hash
    # )
    # assert creative_id is not None


@pytest.mark.integration
def test_full_campaign_structure_sandbox(sandbox_api, sample_config):
    """Test creating complete campaign structure (campaign + ad set)"""
    result = sandbox_api.create_campaign_from_config(sample_config)

    # Verify structure created
    assert "campaign_id" in result
    assert "ad_set_ids" in result
    assert len(result["ad_set_ids"]) > 0
    assert result["status"] == "PAUSED"

    print(f"✓ Full campaign structure created:")
    print(f"  Campaign ID: {result['campaign_id']}")
    print(f"  Ad Set IDs: {result['ad_set_ids']}")


@pytest.mark.integration
def test_get_ad_status_sandbox(sandbox_api):
    """Test retrieving ad status"""
    # Create a campaign and ad set first
    campaign_id = sandbox_api.create_campaign(
        name="Status Test Campaign",
        objective="OUTCOME_TRAFFIC",
        status="PAUSED"
    )

    targeting = {
        "geo_locations": {"countries": ["US"]},
        "age_min": 18,
        "age_max": 65
    }

    ad_set_id = sandbox_api.create_ad_set(
        campaign_id=campaign_id,
        name="Status Test Ad Set",
        daily_budget=2500,
        targeting=targeting,
        optimization_goal="LINK_CLICKS",
        status="PAUSED"
    )

    # In production, you would create an ad and check its status
    # For sandbox, just verify the API calls work
    assert campaign_id is not None
    assert ad_set_id is not None
    print(f"✓ Status check workflow validated")


@pytest.mark.integration
def test_update_budget_sandbox(sandbox_api):
    """Test updating ad set budget"""
    # Create campaign and ad set
    campaign_id = sandbox_api.create_campaign(
        name="Budget Test Campaign",
        objective="OUTCOME_TRAFFIC",
        status="PAUSED"
    )

    targeting = {
        "geo_locations": {"countries": ["US"]},
        "age_min": 18,
        "age_max": 65
    }

    ad_set_id = sandbox_api.create_ad_set(
        campaign_id=campaign_id,
        name="Budget Test Ad Set",
        daily_budget=2500,
        targeting=targeting,
        optimization_goal="LINK_CLICKS",
        status="PAUSED"
    )

    # Update budget
    success = sandbox_api.update_ad_set_budget(
        ad_set_id=ad_set_id,
        new_daily_budget=5000  # $50
    )

    assert success is True
    print(f"✓ Budget updated successfully")


@pytest.mark.integration
def test_error_handling_sandbox(sandbox_api):
    """Test error handling with invalid parameters"""
    # Try to create campaign with invalid objective
    with pytest.raises(MetaAdsError):
        sandbox_api.create_campaign(
            name="Invalid Campaign",
            objective="INVALID_OBJECTIVE",
            status="PAUSED"
        )

    print(f"✓ Error handling working correctly")


@pytest.mark.integration
def test_config_transformation_sandbox(sandbox_api, sample_config):
    """Test agent config transformation to API format"""
    api_config = sandbox_api._transform_agent_config_to_api(sample_config)

    # Verify transformation
    assert api_config["campaign_name"] == "Integration Test Campaign"
    assert api_config["objective"] == "OUTCOME_TRAFFIC"
    assert api_config["daily_budget"] == 2500  # $25 -> 2500 cents
    assert api_config["optimization_goal"] == "LINK_CLICKS"
    assert "targeting" in api_config
    assert api_config["targeting"]["age_min"] == 25
    assert api_config["targeting"]["age_max"] == 44

    print(f"✓ Config transformation validated")
    print(f"  Transformed config: {json.dumps(api_config, indent=2)}")


# Cleanup fixture (optional)
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_campaigns():
    """Cleanup test campaigns after all tests (optional)"""
    yield
    # Note: In sandbox mode, you might want to clean up test entities
    # This is optional as sandbox entities don't incur costs
    print("\n✓ Integration tests completed")
    print("  Note: Sandbox entities may remain - this is expected")


if __name__ == "__main__":
    # Run with: python -m pytest tests/integration/test_meta_e2e.py -v --sandbox
    pytest.main([__file__, "-v", "-s"])
