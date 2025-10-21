"""
Unit tests for Meta Ads API integration

Tests individual API methods with mocked responses
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import json
from src.integrations.meta_ads import MetaAdsAPI, MetaAdsError


class TestMetaAdsAPI(unittest.TestCase):
    """Test suite for MetaAdsAPI class"""

    def setUp(self):
        """Set up test fixtures"""
        self.access_token = "test_token_123"
        self.ad_account_id = "act_123456789"
        self.page_id = "page_123"
        self.instagram_actor_id = "ig_123"

        self.api = MetaAdsAPI(
            access_token=self.access_token,
            ad_account_id=self.ad_account_id,
            page_id=self.page_id,
            instagram_actor_id=self.instagram_actor_id
        )

    def test_init_default_values(self):
        """Test API initialization with default values"""
        self.assertEqual(self.api.access_token, self.access_token)
        self.assertEqual(self.api.ad_account_id, self.ad_account_id)
        self.assertEqual(self.api.api_version, "v24.0")
        self.assertFalse(self.api.dry_run)
        self.assertFalse(self.api.sandbox_mode)

    def test_init_dry_run_mode(self):
        """Test API initialization in dry-run mode"""
        api = MetaAdsAPI(
            access_token="token",
            ad_account_id="act_123",
            dry_run=True
        )
        self.assertTrue(api.dry_run)

    def test_init_sandbox_mode(self):
        """Test API initialization in sandbox mode"""
        api = MetaAdsAPI(
            access_token="token",
            ad_account_id="act_123",
            sandbox_mode=True
        )
        self.assertTrue(api.sandbox_mode)

    @patch('requests.request')
    def test_create_campaign_success(self, mock_request):
        """Test successful campaign creation"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "campaign_123"}
        mock_request.return_value = mock_response

        # Call method
        campaign_id = self.api.create_campaign(
            name="Test Campaign",
            objective="OUTCOME_TRAFFIC"
        )

        # Assertions
        self.assertEqual(campaign_id, "campaign_123")
        mock_request.assert_called_once()

        # Check request parameters
        call_args = mock_request.call_args
        self.assertIn("campaigns", call_args[0][1])  # URL contains 'campaigns'
        self.assertEqual(call_args[1]["json"]["name"], "Test Campaign")
        self.assertEqual(call_args[1]["json"]["objective"], "OUTCOME_TRAFFIC")
        self.assertEqual(call_args[1]["json"]["status"], "PAUSED")

    @patch('requests.request')
    def test_create_campaign_error(self, mock_request):
        """Test campaign creation with API error"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": 100,
                "message": "Invalid parameter",
                "type": "OAuthException"
            }
        }
        mock_request.return_value = mock_response

        # Expect exception
        with self.assertRaises(MetaAdsError) as context:
            self.api.create_campaign(name="Test", objective="INVALID")

        self.assertIn("Invalid parameter", str(context.exception))

    @patch('requests.request')
    def test_create_ad_set_success(self, mock_request):
        """Test successful ad set creation"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "adset_456"}
        mock_request.return_value = mock_response

        # Targeting spec
        targeting = {
            "geo_locations": {"countries": ["US"]},
            "age_min": 25,
            "age_max": 45
        }

        # Call method
        adset_id = self.api.create_ad_set(
            campaign_id="campaign_123",
            name="Test Ad Set",
            daily_budget=2500,
            targeting=targeting,
            optimization_goal="LINK_CLICKS"
        )

        # Assertions
        self.assertEqual(adset_id, "adset_456")
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["json"]["campaign_id"], "campaign_123")
        self.assertEqual(call_args[1]["json"]["daily_budget"], "2500")
        self.assertEqual(call_args[1]["json"]["optimization_goal"], "LINK_CLICKS")
        self.assertEqual(call_args[1]["json"]["billing_event"], "IMPRESSIONS")

    @patch('requests.request')
    def test_create_ad_creative_with_image(self, mock_request):
        """Test creative creation with image"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "creative_789"}
        mock_request.return_value = mock_response

        # Call method
        creative_id = self.api.create_ad_creative(
            name="Test Creative",
            link="https://example.com",
            message="Test message",
            headline="Test Headline",
            image_hash="image_hash_abc",
            call_to_action_type="SHOP_NOW"
        )

        # Assertions
        self.assertEqual(creative_id, "creative_789")
        call_args = mock_request.call_args
        object_story_spec = call_args[1]["json"]["object_story_spec"]
        self.assertEqual(object_story_spec["page_id"], self.page_id)
        self.assertEqual(object_story_spec["instagram_actor_id"], self.instagram_actor_id)
        self.assertEqual(object_story_spec["link_data"]["message"], "Test message")
        self.assertEqual(object_story_spec["link_data"]["picture"], "image_hash_abc")

    @patch('requests.request')
    def test_create_ad_creative_with_video(self, mock_request):
        """Test creative creation with video"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "creative_video_123"}
        mock_request.return_value = mock_response

        # Call method
        creative_id = self.api.create_ad_creative(
            name="Video Creative",
            link="https://example.com",
            message="Video ad message",
            headline="Video Headline",
            video_id="video_xyz",
            call_to_action_type="LEARN_MORE"
        )

        # Assertions
        self.assertEqual(creative_id, "creative_video_123")
        call_args = mock_request.call_args
        link_data = call_args[1]["json"]["object_story_spec"]["link_data"]
        self.assertEqual(link_data["video_id"], "video_xyz")
        self.assertNotIn("picture", link_data)

    def test_create_ad_creative_no_media(self):
        """Test creative creation without image or video raises error"""
        with self.assertRaises(MetaAdsError) as context:
            self.api.create_ad_creative(
                name="Invalid Creative",
                link="https://example.com",
                message="Test",
                headline="Test"
            )
        self.assertIn("Either image_hash or video_id must be provided", str(context.exception))

    @patch('requests.request')
    def test_create_ad_success(self, mock_request):
        """Test successful ad creation"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "ad_999"}
        mock_request.return_value = mock_response

        # Call method
        ad_id = self.api.create_ad(
            ad_set_id="adset_456",
            creative_id="creative_789",
            name="Test Ad",
            external_id="ext_123",
            status="PAUSED"
        )

        # Assertions
        self.assertEqual(ad_id, "ad_999")
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["json"]["adset_id"], "adset_456")
        self.assertEqual(call_args[1]["json"]["creative"]["creative_id"], "creative_789")
        self.assertEqual(call_args[1]["json"]["external_id"], "ext_123")

    @patch('requests.request')
    def test_upload_image_from_path(self, mock_request):
        """Test image upload from local file"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": {
                "test.jpg": {
                    "hash": "abc123hash",
                    "url": "https://example.com/image.jpg"
                }
            }
        }
        mock_request.return_value = mock_response

        # Mock file open
        with patch("builtins.open", mock_open(read_data=b"image_data")):
            image_hash = self.api.upload_image(image_path="/path/to/image.jpg")

        # Assertions
        self.assertEqual(image_hash, "abc123hash")
        self.assertIn("adimages", mock_request.call_args[0][1])

    @patch('requests.request')
    def test_upload_image_from_url(self, mock_request):
        """Test image upload from URL"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "images": {
                "image.jpg": {
                    "hash": "url_hash_xyz",
                    "url": "https://example.com/image.jpg"
                }
            }
        }
        mock_request.return_value = mock_response

        # Call method
        image_hash = self.api.upload_image(image_url="https://source.com/image.jpg")

        # Assertions
        self.assertEqual(image_hash, "url_hash_xyz")
        call_args = mock_request.call_args
        # URL upload uses json parameter in _make_api_call (not data)
        self.assertEqual(call_args[1]["json"]["url"], "https://source.com/image.jpg")

    def test_upload_image_no_params(self):
        """Test image upload without parameters raises error"""
        with self.assertRaises(MetaAdsError) as context:
            self.api.upload_image()
        self.assertIn("Either image_path or image_url must be provided", str(context.exception))

    @patch('requests.request')
    def test_activate_ad(self, mock_request):
        """Test ad activation"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        # Call method
        success = self.api.activate_ad(ad_id="ad_999")

        # Assertions
        self.assertTrue(success)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["json"]["status"], "ACTIVE")

    @patch('requests.request')
    def test_pause_ad(self, mock_request):
        """Test ad pause"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        # Call method
        success = self.api.pause_ad(ad_id="ad_999")

        # Assertions
        self.assertTrue(success)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["json"]["status"], "PAUSED")

    @patch('requests.request')
    def test_update_ad_set_budget(self, mock_request):
        """Test ad set budget update"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        # Call method
        success = self.api.update_ad_set_budget(ad_set_id="adset_456", new_daily_budget=5000)

        # Assertions
        self.assertTrue(success)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["json"]["daily_budget"], "5000")

    @patch('requests.request')
    def test_rate_limit_handling(self, mock_request):
        """Test rate limit error handling with retry"""
        # First call returns rate limit error, second succeeds
        error_response = Mock()
        error_response.status_code = 400
        error_response.json.return_value = {
            "error": {"code": 17, "message": "User request limit reached", "type": "OAuthException"}
        }

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"id": "campaign_retry"}

        mock_request.side_effect = [error_response, success_response]

        # Mock sleep to avoid actual delay
        with patch('time.sleep'):
            campaign_id = self.api.create_campaign(name="Test", objective="OUTCOME_TRAFFIC")

        # Should succeed after retry
        self.assertEqual(campaign_id, "campaign_retry")
        self.assertEqual(mock_request.call_count, 2)

    def test_dry_run_mode(self):
        """Test dry-run mode returns mock IDs without API calls"""
        api_dry = MetaAdsAPI(
            access_token="token",
            ad_account_id="act_123",
            dry_run=True
        )

        # These should not make real API calls
        campaign_id = api_dry.create_campaign(name="Dry Run Campaign", objective="OUTCOME_TRAFFIC")
        self.assertTrue(campaign_id.startswith("mock_"))

    def test_parse_age_range_standard(self):
        """Test parsing standard age range"""
        age_min, age_max = self.api._parse_age_range("25-45")
        self.assertEqual(age_min, 25)
        self.assertEqual(age_max, 45)

    def test_parse_age_range_plus(self):
        """Test parsing age range with plus sign (65+)"""
        age_min, age_max = self.api._parse_age_range("65+")
        self.assertEqual(age_min, 65)
        self.assertEqual(age_max, 65)  # Meta uses 65 as max

    def test_parse_age_range_young_plus(self):
        """Test parsing age range with plus sign (18+)"""
        age_min, age_max = self.api._parse_age_range("18+")
        self.assertEqual(age_min, 18)
        self.assertEqual(age_max, 65)  # Meta max

    def test_parse_age_range_single(self):
        """Test parsing single age value"""
        age_min, age_max = self.api._parse_age_range("30")
        self.assertEqual(age_min, 30)
        self.assertEqual(age_max, 30)

    def test_transform_agent_config_to_api(self):
        """Test config transformation from agent format to API format"""
        agent_config = {
            "meta": {
                "campaign_name": "Test Campaign",
                "objective": "CONVERSIONS",
                "daily_budget": 50.0,
                "targeting": {
                    "age_range": "25-45",
                    "locations": ["US", "CA"],
                    "detailed_targeting": {
                        "interests": ["Fitness", "Running"],
                        "behaviors": ["Online shoppers"]
                    }
                },
                "bidding": {
                    "strategy": "LOWEST_COST_WITH_BID_CAP"
                },
                "optimization": {
                    "optimization_goal": "CONVERSIONS"
                }
            }
        }

        api_config = self.api._transform_agent_config_to_api(agent_config)

        # Assertions
        self.assertEqual(api_config["campaign_name"], "Test Campaign")
        self.assertEqual(api_config["objective"], "CONVERSIONS")
        self.assertEqual(api_config["daily_budget"], 5000)  # $50 -> 5000 cents
        self.assertEqual(api_config["targeting"]["age_min"], 25)
        self.assertEqual(api_config["targeting"]["age_max"], 45)
        self.assertEqual(api_config["targeting"]["geo_locations"]["countries"], ["US", "CA"])
        self.assertEqual(len(api_config["targeting"]["interests"]), 2)

    def test_transform_config_with_age_plus(self):
        """Test config transformation with 65+ age range"""
        agent_config = {
            "meta": {
                "campaign_name": "Senior Campaign",
                "objective": "OUTCOME_TRAFFIC",
                "daily_budget": 100.0,
                "targeting": {
                    "age_range": "65+",
                    "locations": ["US"]
                },
                "optimization": {
                    "optimization_goal": "LINK_CLICKS"
                }
            }
        }

        api_config = self.api._transform_agent_config_to_api(agent_config)

        # Should handle 65+ correctly
        self.assertEqual(api_config["targeting"]["age_min"], 65)
        self.assertEqual(api_config["targeting"]["age_max"], 65)

    @patch('src.integrations.meta_ads.MetaAdsAPI.create_campaign')
    @patch('src.integrations.meta_ads.MetaAdsAPI.create_ad_set')
    def test_create_campaign_from_config(self, mock_create_ad_set, mock_create_campaign):
        """Test end-to-end campaign creation from config"""
        # Mock responses
        mock_create_campaign.return_value = "campaign_e2e"
        mock_create_ad_set.return_value = "adset_e2e"

        # Sample config
        config = {
            "meta": {
                "campaign_name": "E2E Test",
                "objective": "OUTCOME_TRAFFIC",
                "daily_budget": 100.0,
                "targeting": {
                    "age_range": "18-65",
                    "locations": ["US"]
                },
                "optimization": {
                    "optimization_goal": "LINK_CLICKS"
                },
                "bidding": {
                    "strategy": "LOWEST_COST_WITHOUT_CAP"
                }
            }
        }

        # Call method
        result = self.api.create_campaign_from_config(config)

        # Assertions
        self.assertEqual(result["campaign_id"], "campaign_e2e")
        self.assertEqual(result["ad_set_ids"], ["adset_e2e"])
        self.assertEqual(result["status"], "PAUSED")
        mock_create_campaign.assert_called_once()
        mock_create_ad_set.assert_called_once()


if __name__ == "__main__":
    unittest.main()
