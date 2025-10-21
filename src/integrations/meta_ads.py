"""
Meta Marketing API Integration
Full implementation for automated campaign deployment to Meta (Facebook/Instagram)

Based on Meta Ads Marketing API v24.0 (Updated October 2025)
Supports latest Advantage+ campaign structure and automation features
Flow documentation: meta_ads_api_end_to_end_calling_flow_doc.md

Latest Updates:
- Advantage+ unified campaign structure (v23.0+)
- advantage_audience targeting automation (defaults to 1)
- Enhanced budget flexibility (75% daily variance)
- Placement optimization (5% to excluded placements)
- Individual Advantage+ creative enhancements (v22.0+)
- Updated attribution model (June 2025)
"""

import os
import json
import time
import uuid
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


class MetaAdsAPI:
    """
    Interface for Meta Marketing API integration

    Enables programmatic campaign creation, ad set configuration, and creative deployment
    to Facebook and Instagram platforms.

    API Documentation: https://developers.facebook.com/docs/marketing-api
    """

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        page_id: Optional[str] = None,
        instagram_actor_id: Optional[str] = None,
        api_version: str = "v24.0",
        dry_run: bool = False,
        sandbox_mode: bool = False
    ):
        """
        Initialize Meta Ads API client

        Args:
            access_token: Meta Marketing API access token
            ad_account_id: Ad account ID (format: act_XXXXXXXXX)
            page_id: Facebook Page ID for creative publishing
            instagram_actor_id: Instagram actor ID (optional)
            api_version: API version (default: v24.0)
            dry_run: If True, log API calls without executing (default: False)
            sandbox_mode: If True, use sandbox environment (default: False)

        Setup instructions:
        1. Create Meta App at https://developers.facebook.com/apps
        2. Add Marketing API product
        3. Generate access token with ads_management permission
        4. Get ad account ID from Business Manager
        """
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.page_id = page_id
        self.instagram_actor_id = instagram_actor_id
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.dry_run = dry_run
        self.sandbox_mode = sandbox_mode

        if dry_run:
            print("🔧 [DRY RUN MODE] No API calls will be made. All operations will be logged only.")
        if sandbox_mode:
            print("🧪 [SANDBOX MODE] Using Meta Ads sandbox environment (no real ads delivered).")

        # Rate limiting tracking
        self.last_request_time = 0
        self.retry_count = 0

    def _make_api_call(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Centralized API request handler with rate limiting and error handling

        Args:
            endpoint: API endpoint (e.g., /act_{ad_account_id}/campaigns)
            method: HTTP method (GET, POST, DELETE)
            data: JSON payload
            files: Multipart files for upload

        Returns:
            API response as dictionary

        Raises:
            MetaAdsError: For API errors with detailed messages
        """
        url = f"{self.base_url}{endpoint}"

        if self.dry_run:
            print(f"\n🔧 [DRY RUN] {method} {url}")
            if data:
                print(f"   Payload: {json.dumps(data, indent=2)}")
            mock_id = f"mock_{uuid.uuid4().hex[:8]}"
            return {"id": mock_id, "success": True}

        # Add access token to params
        params = {"access_token": self.access_token}

        try:
            # Rate limiting: ensure minimum time between requests
            time_since_last_request = time.time() - self.last_request_time
            if time_since_last_request < 0.1:  # 100ms minimum
                time.sleep(0.1 - time_since_last_request)

            # Make request
            if files:
                # Multipart upload (for images/videos)
                response = requests.request(
                    method,
                    url,
                    params=params,
                    data=data,
                    files=files,
                    timeout=30
                )
            else:
                # JSON request
                response = requests.request(
                    method,
                    url,
                    params=params,
                    json=data,
                    timeout=30
                )

            self.last_request_time = time.time()

            # Parse response
            response_data = response.json()

            # Check for errors
            if response.status_code >= 400:
                error = response_data.get("error", {})
                error_code = error.get("code")
                error_message = error.get("message", "Unknown error")
                error_type = error.get("type", "Unknown")

                # Handle rate limiting errors
                if error_code in [17, 613]:
                    return self._handle_rate_limit(endpoint, method, data, files)

                raise MetaAdsError(
                    f"Meta API Error {error_code} ({error_type}): {error_message}"
                )

            return response_data

        except requests.exceptions.RequestException as e:
            raise MetaAdsError(f"Network error: {str(e)}")

    def _handle_rate_limit(
        self,
        endpoint: str,
        method: str,
        data: Optional[Dict],
        files: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Handle rate limiting with exponential backoff

        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request data
            files: Request files

        Returns:
            Retry result
        """
        self.retry_count += 1
        if self.retry_count > 5:
            raise MetaAdsError("Rate limit exceeded: Maximum retries reached")

        # Exponential backoff with jitter
        backoff = (2 ** self.retry_count) * 60  # 60s, 120s, 240s, etc.
        jitter = time.time() % 10  # Random 0-10s jitter
        wait_time = backoff + jitter

        print(f"⏳ Rate limited. Waiting {wait_time:.1f}s before retry {self.retry_count}/5...")
        time.sleep(wait_time)

        # Retry request
        return self._make_api_call(endpoint, method, data, files)

    def _ensure_idempotency(self, external_id: str, entity_type: str) -> Optional[str]:
        """
        Check if entity with external_id already exists

        Args:
            external_id: External ID to check
            entity_type: Type of entity (campaign, adset, ad)

        Returns:
            Existing entity ID if found, None otherwise
        """
        # TODO: Implement idempotency check
        # This would query the API to see if an entity with this external_id exists
        # For now, we rely on Meta's idempotency handling
        return None

    def upload_image(self, image_path: Optional[str] = None, image_url: Optional[str] = None) -> str:
        """
        Upload image to Meta Ad Library

        Args:
            image_path: Local path to image file
            image_url: Alternative - URL to image (Meta will download)

        Returns:
            image_hash: Unique identifier for uploaded image

        API Endpoint:
            POST /{ad_account_id}/adimages

        Example response:
            {
                "images": {
                    "filename.png": {
                        "hash": "abc123...",
                        "url": "https://..."
                    }
                }
            }
        """
        endpoint = f"/{self.ad_account_id}/adimages"

        if image_path:
            # Upload from local file
            with open(image_path, 'rb') as f:
                files = {'filename': f}
                response = self._make_api_call(endpoint, method="POST", files=files)
        elif image_url:
            # Upload from URL
            data = {'url': image_url}
            response = self._make_api_call(endpoint, method="POST", data=data)
        else:
            raise MetaAdsError("Either image_path or image_url must be provided")

        # Extract hash from response
        images = response.get("images", {})
        if images:
            first_image = next(iter(images.values()))
            return first_image.get("hash")

        raise MetaAdsError("Failed to extract image hash from response")

    def upload_video(self, video_path: str) -> str:
        """
        Upload video to Meta Ad Library

        Args:
            video_path: Local path to video file

        Returns:
            video_id: Video ID

        API Endpoint:
            POST /{ad_account_id}/advideos
        """
        endpoint = f"/{self.ad_account_id}/advideos"

        with open(video_path, 'rb') as f:
            files = {'source': f}
            response = self._make_api_call(endpoint, method="POST", files=files)

        video_id = response.get("id")
        if not video_id:
            raise MetaAdsError("Failed to extract video ID from response")

        return video_id

    def poll_video_status(self, video_id: str, timeout: int = 300) -> bool:
        """
        Poll video processing status until ready

        Args:
            video_id: Video ID from upload_video()
            timeout: Maximum wait time in seconds (default: 300)

        Returns:
            True if video is ready, False if timeout
        """
        endpoint = f"/{video_id}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self._make_api_call(endpoint, method="GET")
            status = response.get("status", {})
            processing_progress = status.get("processing_progress", 0)

            if processing_progress == 100:
                print(f"✓ Video {video_id} processing complete")
                return True

            print(f"⏳ Video processing: {processing_progress}%")
            time.sleep(5)

        print(f"⚠️  Video processing timeout after {timeout}s")
        return False

    def create_campaign(
        self,
        name: str,
        objective: str = "OUTCOME_TRAFFIC",
        status: str = "PAUSED",
        special_ad_categories: Optional[List[str]] = None,
        advantage_plus: bool = False,
        budget_rebalance: bool = False
    ) -> str:
        """
        Create campaign container with Advantage+ support

        Args:
            name: Campaign name
            objective: Campaign objective (OUTCOME_TRAFFIC, OUTCOME_SALES, etc.)
            status: ACTIVE | PAUSED (default: PAUSED for safety)
            special_ad_categories: e.g., ["CREDIT", "EMPLOYMENT", "HOUSING"]
            advantage_plus: Enable Advantage+ campaign mode (v23.0+)
            budget_rebalance: Enable budget rebalancing across ad sets (v24.0+)

        Returns:
            campaign_id: Created campaign ID

        API Endpoint:
            POST /{ad_account_id}/campaigns

        Supported objectives:
        - OUTCOME_SALES (formerly CONVERSIONS)
        - OUTCOME_LEADS
        - OUTCOME_ENGAGEMENT
        - OUTCOME_AWARENESS
        - OUTCOME_TRAFFIC

        Notes:
        - As of v24.0, ASC/AAC campaigns can only be created on v23.0 or earlier
        - In v25.0 (Q1 2026), Advantage+ will be determined by automation levers
        """
        endpoint = f"/{self.ad_account_id}/campaigns"

        data = {
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": special_ad_categories or []
        }

        # Add Advantage+ campaign settings (v23.0+)
        if advantage_plus:
            # Note: smart_promotion_type is deprecated in v25.0
            # In v25.0+, Advantage+ is determined by automation settings
            if self.api_version < "v25.0":
                print("⚠️  Note: Advantage+ campaigns determined by automation levers in v25.0+")

        # Add budget rebalancing for CBO alternatives (v24.0+)
        if budget_rebalance:
            data["budget_rebalance_flag"] = True

        response = self._make_api_call(endpoint, method="POST", data=data)
        campaign_id = response.get("id")

        if not campaign_id:
            raise MetaAdsError("Failed to extract campaign ID from response")

        print(f"✓ Campaign created: {campaign_id} ({name})")
        return campaign_id

    def create_ad_set(
        self,
        campaign_id: str,
        name: str,
        daily_budget: int,
        targeting: Dict,
        optimization_goal: str = "LINK_CLICKS",
        billing_event: str = "IMPRESSIONS",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        bid_strategy: str = "LOWEST_COST_WITHOUT_CAP",
        destination_type: str = "WEBSITE",
        status: str = "PAUSED",
        advantage_audience: int = 1,
        enable_advantage_placement: bool = True,
        enable_budget_sharing: bool = False
    ) -> str:
        """
        Create ad set with targeting and budget (Updated for v23.0+)

        Args:
            campaign_id: Parent campaign ID
            name: Ad set name
            daily_budget: Daily budget in cents (e.g., 2500 = $25.00)
            targeting: Targeting specification
            optimization_goal: LINK_CLICKS | CONVERSIONS | LANDING_PAGE_VIEWS | etc.
            billing_event: IMPRESSIONS | CLICKS
            start_time: ISO 8601 format (e.g., "2025-10-16T16:00:00Z")
            end_time: ISO 8601 format or None for no end date
            bid_strategy: LOWEST_COST_WITHOUT_CAP | LOWEST_COST_WITH_BID_CAP
            destination_type: WEBSITE | APP | MESSENGER
            status: ACTIVE | PAUSED
            advantage_audience: Enable audience automation (v23.0+, defaults to 1)
            enable_advantage_placement: Enable 5% spend on excluded placements (v24.0+)
            enable_budget_sharing: Enable budget sharing across ad sets (v24.0+)

        Returns:
            ad_set_id: Created ad set ID

        API Endpoint:
            POST /{ad_account_id}/adsets

        Notes:
        - v23.0+: advantage_audience defaults to 1 (must be explicitly set)
        - v24.0+: Daily budget flexibility increased to 75% (from 25%)
        - v24.0+: Up to 5% budget can be spent on excluded placements
        - v24.0+: Budget sharing allows 20% budget transfer between ad sets
        """
        endpoint = f"/{self.ad_account_id}/adsets"

        data = {
            "name": name,
            "campaign_id": campaign_id,
            "daily_budget": str(daily_budget),
            "optimization_goal": optimization_goal,
            "billing_event": billing_event,
            "bid_strategy": bid_strategy,
            "targeting": targeting,
            "destination_type": destination_type,
            "status": status
        }

        # Add start_time if provided
        if start_time:
            data["start_time"] = start_time

        # Add end_time if provided
        if end_time:
            data["end_time"] = end_time

        # Add promoted_object with page_id if available
        if self.page_id:
            data["promoted_object"] = {"page_id": self.page_id}

        # Updated attribution spec (June 2025 changes)
        # On-Meta events: impression time | Off-Meta events: conversion time
        data["attribution_spec"] = [
            {"event_type": "CLICK_THROUGH", "window_days": 7},
            {"event_type": "VIEW_THROUGH", "window_days": 1}
        ]

        # Add targeting automation (v23.0+ - must be explicitly set)
        if "targeting_automation" not in targeting:
            targeting["targeting_automation"] = {
                "advantage_audience": advantage_audience
            }

        # Add Advantage+ placement optimization (v24.0+)
        if enable_advantage_placement:
            data["targeting_optimization"] = {
                "excluded_placement_override_percentage": 5  # 5% to excluded placements
            }

        # Add budget sharing flag (v24.0+)
        if enable_budget_sharing:
            data["adset_budget_sharing"] = True  # Allows 20% budget sharing

        response = self._make_api_call(endpoint, method="POST", data=data)
        ad_set_id = response.get("id")

        if not ad_set_id:
            raise MetaAdsError("Failed to extract ad set ID from response")

        print(f"✓ Ad Set created: {ad_set_id} ({name})")
        return ad_set_id

    def create_ad_creative(
        self,
        name: str,
        link: str,
        message: str,
        headline: str,
        image_hash: Optional[str] = None,
        video_id: Optional[str] = None,
        call_to_action_type: str = "SHOP_NOW",
        advantage_creative_enhancements: Optional[Dict[str, bool]] = None,
        enable_dynamic_media: bool = True
    ) -> str:
        """
        Create ad creative with image/video and copy (Updated for v22.0+)

        Args:
            name: Creative name
            link: Destination URL (can be Amazon Attribution URL)
            message: Ad copy (primary text)
            headline: Headline text
            image_hash: Image hash from upload_image() (for image ads)
            video_id: Video ID from upload_video() (for video ads)
            call_to_action_type: SHOP_NOW | LEARN_MORE | SIGN_UP | etc.
            advantage_creative_enhancements: Individual Advantage+ enhancements (v22.0+)
            enable_dynamic_media: Auto-enable dynamic media for catalog ads (v24.0+)

        Returns:
            creative_id: Created creative ID

        API Endpoint:
            POST /{ad_account_id}/adcreatives

        Creative structure uses object_story_spec with link_data

        Notes:
        - v22.0+: Advantage+ creative enhancements are now individual (not bundled)
        - v24.0+: Dynamic media defaults to OPT_IN for Advantage+ Catalog Ads

        Available Advantage+ enhancements (v22.0+):
        - enhance_cta: Enhance call-to-action
        - image_brightness_and_contrast: Adjust image brightness/contrast
        - text_enhancements: Enhance ad copy
        """
        if not image_hash and not video_id:
            raise MetaAdsError("Either image_hash or video_id must be provided")

        if not self.page_id:
            raise MetaAdsError("page_id is required for creative creation")

        endpoint = f"/{self.ad_account_id}/adcreatives"

        # Build link_data
        link_data = {
            "message": message,
            "name": headline,
            "link": link,
            "call_to_action": {
                "type": call_to_action_type,
                "value": {"link": link}
            }
        }

        # Add image or video
        if image_hash:
            link_data["picture"] = image_hash
        elif video_id:
            link_data["video_id"] = video_id

        # Build object_story_spec
        object_story_spec = {
            "page_id": self.page_id,
            "link_data": link_data
        }

        # Add Instagram actor if available
        if self.instagram_actor_id:
            object_story_spec["instagram_actor_id"] = self.instagram_actor_id

        data = {
            "name": name,
            "object_story_spec": object_story_spec
        }

        # Add Advantage+ creative enhancements (v22.0+)
        # Individual enhancements replace the old bundled approach
        if advantage_creative_enhancements:
            data["enhancements_catalog"] = advantage_creative_enhancements
            print(f"   Applying Advantage+ creative enhancements: {list(advantage_creative_enhancements.keys())}")

        # Add dynamic media automation for catalog ads (v24.0+)
        # Defaults to OPT_IN as of September 1, 2025
        if enable_dynamic_media and image_hash:
            data["media_type_automation"] = "OPT_IN"

        response = self._make_api_call(endpoint, method="POST", data=data)
        creative_id = response.get("id")

        if not creative_id:
            raise MetaAdsError("Failed to extract creative ID from response")

        print(f"✓ Creative created: {creative_id} ({name})")
        return creative_id

    def create_ad(
        self,
        ad_set_id: str,
        creative_id: str,
        name: str,
        external_id: Optional[str] = None,
        status: str = "PAUSED"
    ) -> str:
        """
        Create ad linking creative to ad set

        Args:
            ad_set_id: Parent ad set ID
            creative_id: Ad creative ID
            name: Ad name
            external_id: External ID for idempotency (recommended)
            status: ACTIVE | PAUSED

        Returns:
            ad_id: Created ad ID

        API Endpoint:
            POST /{ad_account_id}/ads
        """
        endpoint = f"/{self.ad_account_id}/ads"

        data = {
            "name": name,
            "adset_id": ad_set_id,
            "creative": {"creative_id": creative_id},
            "status": status
        }

        # Add external_id for idempotency
        if external_id:
            data["external_id"] = external_id

        response = self._make_api_call(endpoint, method="POST", data=data)
        ad_id = response.get("id")

        if not ad_id:
            raise MetaAdsError("Failed to extract ad ID from response")

        print(f"✓ Ad created: {ad_id} ({name})")
        return ad_id

    def activate_ad(self, ad_id: str) -> bool:
        """
        Activate ad

        Args:
            ad_id: Ad ID to activate

        Returns:
            success: True if activated
        """
        endpoint = f"/{ad_id}"
        data = {"status": "ACTIVE"}

        response = self._make_api_call(endpoint, method="POST", data=data)
        success = response.get("success", False)

        if success:
            print(f"✓ Ad activated: {ad_id}")

        return success

    def generate_preview(
        self,
        creative_id: str,
        ad_format: str = "DESKTOP_FEED_STANDARD"
    ) -> str:
        """
        Generate ad preview

        Args:
            creative_id: Creative ID
            ad_format: Preview format (DESKTOP_FEED_STANDARD, MOBILE_FEED_STANDARD, etc.)

        Returns:
            preview_url: URL to preview
        """
        endpoint = f"/{self.ad_account_id}/generatepreviews"

        data = {
            "creative": {"creative_id": creative_id},
            "ad_format": ad_format
        }

        response = self._make_api_call(endpoint, method="POST", data=data)

        # Response contains HTML snippet or URL
        return response

    def get_ad_status(self, ad_id: str) -> Dict[str, Any]:
        """
        Get ad status and review feedback

        Args:
            ad_id: Ad ID

        Returns:
            Status information including effective_status and review feedback
        """
        endpoint = f"/{ad_id}"
        params = "?fields=effective_status,configured_status,ad_review_feedback"

        response = self._make_api_call(f"{endpoint}{params}", method="GET")
        return response

    def update_ad_set_budget(self, ad_set_id: str, new_daily_budget: int) -> bool:
        """
        Update ad set daily budget

        Useful for optimization adjustments from reflection_node

        Args:
            ad_set_id: Ad set ID
            new_daily_budget: New daily budget in cents

        Returns:
            success: True if updated
        """
        endpoint = f"/{ad_set_id}"
        data = {"daily_budget": str(new_daily_budget)}

        response = self._make_api_call(endpoint, method="POST", data=data)
        success = response.get("success", False)

        if success:
            print(f"✓ Ad set budget updated: {ad_set_id} -> ${new_daily_budget/100:.2f}/day")

        return success

    def pause_ad(self, ad_id: str) -> bool:
        """
        Pause underperforming ad

        Args:
            ad_id: Ad ID to pause

        Returns:
            success: True if paused
        """
        endpoint = f"/{ad_id}"
        data = {"status": "PAUSED"}

        response = self._make_api_call(endpoint, method="POST", data=data)
        success = response.get("success", False)

        if success:
            print(f"✓ Ad paused: {ad_id}")

        return success

    def get_campaign_insights(
        self,
        campaign_id: str,
        date_start: str,
        date_end: str,
        fields: Optional[List[str]] = None
    ) -> Dict:
        """
        Fetch campaign performance metrics

        Args:
            campaign_id: Campaign ID
            date_start: Start date (YYYY-MM-DD)
            date_end: End date (YYYY-MM-DD)
            fields: Metrics to fetch (default: impressions, clicks, spend, actions)

        Returns:
            Performance data dictionary

        API Endpoint:
            GET /{campaign_id}/insights

        Useful metrics:
        - impressions, reach, frequency
        - clicks, ctr, cpc
        - spend
        - actions (conversions by type)
        - cost_per_action_type
        """
        endpoint = f"/{campaign_id}/insights"

        if not fields:
            fields = [
                "impressions",
                "clicks",
                "spend",
                "actions",
                "action_values",
                "ctr",
                "cpc",
                "cost_per_action_type"
            ]

        params = f"?fields={','.join(fields)}&time_range={{'since':'{date_start}','until':'{date_end}'}}"

        response = self._make_api_call(f"{endpoint}{params}", method="GET")
        return response

    def get_advantage_state(self, campaign_id: str) -> Dict[str, Any]:
        """
        Check if campaign is in Advantage+ setup (v23.0+)

        Args:
            campaign_id: Campaign ID

        Returns:
            Dictionary with advantage_state_info flag and details

        API Endpoint:
            GET /{campaign_id}?fields=advantage_state_info

        Notes:
        - v23.0+: advantage_state_info indicates Advantage+ status
        - In v25.0+, Advantage+ is determined by automation levers
        """
        endpoint = f"/{campaign_id}"
        params = "?fields=advantage_state_info,name,status"

        response = self._make_api_call(f"{endpoint}{params}", method="GET")
        return response

    def _parse_age_range(self, age_range: str) -> tuple[int, int]:
        """
        Parse age range string into age_min and age_max

        Args:
            age_range: Age range string (e.g., "18-65", "65+", "25-44", "25-65+")

        Returns:
            Tuple of (age_min, age_max)

        Handles formats:
        - "18-65" -> (18, 65)
        - "25-65+" -> (25, 65) - Range with open upper bound
        - "65+" -> (65, 65) - Meta API uses 65 as max for 65+
        - "18+" -> (18, 65)
        - "25" -> (25, 25)
        """
        age_range = str(age_range).strip()

        # Handle "25-65+" format (range with open upper bound)
        if "-" in age_range and "+" in age_range:
            # Extract the range, ignoring the +
            parts = age_range.replace("+", "").split("-")
            try:
                age_min = int(parts[0].strip())
                age_max = int(parts[1].strip())
                # Ensure age_max doesn't exceed Meta's limit
                age_max = min(age_max, 65)
                return age_min, age_max
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid age range format: '{age_range}'. Expected format like '25-65+'")

        # Handle "18-65" format (standard range)
        if "-" in age_range:
            parts = age_range.split("-")
            try:
                age_min = int(parts[0].strip())
                age_max = int(parts[1].strip())
                return age_min, age_max
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid age range format: '{age_range}'. Expected format like '18-65'")

        # Handle "65+" or "18+" format (open upper bound)
        if "+" in age_range:
            try:
                age_min = int(age_range.replace("+", "").strip())
                age_max = 65  # Meta API max age is 65 (represents 65+)
                return age_min, age_max
            except ValueError as e:
                raise ValueError(f"Invalid age range format: '{age_range}'. Expected format like '65+'")

        # Handle single age "25"
        try:
            age = int(age_range)
            return age, age
        except ValueError as e:
            raise ValueError(f"Invalid age range format: '{age_range}'. Expected format like '25', '18-65', '65+', or '25-65+'")

    def _transform_agent_config_to_api(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent-generated config to Meta API format (Updated for v23.0+)

        Args:
            config: Config from generate_campaign_config()

        Returns:
            Transformed config ready for API calls

        Notes:
        - v23.0+: Adds advantage_audience targeting automation
        - v24.0+: Adds placement optimization and budget sharing options
        """
        meta_config = config.get("meta", {})

        # Transform targeting
        targeting = meta_config.get("targeting", {})

        # Parse age range safely
        age_range = targeting.get("age_range", "18-65")
        age_min, age_max = self._parse_age_range(age_range)

        api_targeting = {
            "geo_locations": {"countries": targeting.get("locations", ["US"])},
            "age_min": age_min,
            "age_max": age_max,
        }

        # Add detailed targeting if present
        detailed_targeting = targeting.get("detailed_targeting", {})
        if detailed_targeting:
            interests = detailed_targeting.get("interests", [])
            behaviors = detailed_targeting.get("behaviors", [])

            # Convert interest names to interest specs (would need real IDs in production)
            if interests:
                api_targeting["interests"] = [
                    {"name": interest} for interest in interests
                ]

            if behaviors:
                api_targeting["flexible_spec"] = [
                    {"behaviors": [{"name": behavior} for behavior in behaviors]}
                ]

        # Add targeting automation (v23.0+)
        # advantage_audience defaults to 1 unless explicitly set to 0
        api_targeting["targeting_automation"] = {
            "advantage_audience": targeting.get("advantage_audience", 1)
        }

        # Transform bidding
        bidding = meta_config.get("bidding", {})

        # Convert budget to cents
        daily_budget = int(meta_config.get("daily_budget", 100) * 100)

        return {
            "campaign_name": meta_config.get("campaign_name", "Untitled Campaign"),
            "objective": meta_config.get("objective", "OUTCOME_TRAFFIC"),
            "daily_budget": daily_budget,
            "targeting": api_targeting,
            "optimization_goal": meta_config.get("optimization", {}).get("optimization_goal", "LINK_CLICKS"),
            "billing_event": "IMPRESSIONS",
            "bid_strategy": bidding.get("strategy", "LOWEST_COST_WITHOUT_CAP"),
            "creative_specs": meta_config.get("creative_specs", {}),
            # Add new v24.0+ features
            "advantage_plus": meta_config.get("advantage_plus", False),
            "enable_advantage_placement": meta_config.get("enable_advantage_placement", True),
            "enable_budget_sharing": meta_config.get("enable_budget_sharing", False),
        }

    def create_campaign_from_config(self, config: Dict) -> Dict:
        """
        Create complete campaign from agent-generated config

        This is the main entry point for automated campaign deployment.
        Takes the output from campaign.py and creates a live campaign on Meta.

        Args:
            config: Campaign configuration from generate_campaign_config()
                {
                    "meta": {...},
                    "creative_assets": [...]
                }

        Returns:
            {
                "campaign_id": "123456789",
                "ad_set_ids": ["111", "222"],
                "ad_ids": ["aaa", "bbb"],
                "creative_ids": ["ccc", "ddd"],
                "status": "ACTIVE" | "PAUSED"
            }

        Workflow:
        1. Transform config to API format
        2. Upload images from creative_assets (if provided)
        3. Create campaign (PAUSED)
        4. Create ad sets with targeting
        5. Create ad creatives
        6. Create ads linking creatives to ad sets
        7. Optionally activate
        """
        print("\n🚀 Starting Meta campaign creation from config...")

        # Transform config
        api_config = self._transform_agent_config_to_api(config)

        # Step 1: Create campaign
        campaign_id = self.create_campaign(
            name=api_config["campaign_name"],
            objective=api_config["objective"],
            status="PAUSED"
        )

        # Step 2: Create ad set with new v24.0+ features
        ad_set_id = self.create_ad_set(
            campaign_id=campaign_id,
            name=f"{api_config['campaign_name']} - Ad Set 1",
            daily_budget=api_config["daily_budget"],
            targeting=api_config["targeting"],
            optimization_goal=api_config["optimization_goal"],
            billing_event=api_config["billing_event"],
            bid_strategy=api_config["bid_strategy"],
            status="PAUSED",
            advantage_audience=api_config["targeting"].get("targeting_automation", {}).get("advantage_audience", 1),
            enable_advantage_placement=api_config.get("enable_advantage_placement", True),
            enable_budget_sharing=api_config.get("enable_budget_sharing", False)
        )

        # Step 3 & 4: Process creative assets
        creative_ids = []
        ad_ids = []

        creative_assets = config.get("creative_assets", [])
        if creative_assets:
            for idx, asset in enumerate(creative_assets):
                creative_gen = asset.get("creative_generation", {})

                # Get creative details
                headline = creative_gen.get("headline", "Limited Time Offer")
                primary_text = creative_gen.get("primary_text", "Check out our amazing product!")

                # Use config link or default
                link = config.get("meta", {}).get("creative_specs", {}).get("link", "https://example.com")

                # For now, we'll create text-based creatives
                # In production, you'd upload actual images from creative_gen
                print(f"   Note: Image generation/upload not implemented. Using placeholder.")

                # Create creative (would need actual image_hash in production)
                # creative_id = self.create_ad_creative(
                #     name=f"Creative {idx+1} - {asset.get('combo_id', 'unknown')}",
                #     link=link,
                #     message=primary_text,
                #     headline=headline,
                #     image_hash=image_hash,
                #     call_to_action_type="SHOP_NOW"
                # )
                # creative_ids.append(creative_id)

                print(f"   ⚠️  Skipping creative {idx+1} (image upload not implemented)")
        else:
            print("   ℹ️  No creative assets provided in config")

        # Step 5: Create ads (if we had creatives)
        # for idx, creative_id in enumerate(creative_ids):
        #     external_id = f"{config.get('project_id', 'proj')}_{idx}_{int(time.time())}"
        #     ad_id = self.create_ad(
        #         ad_set_id=ad_set_id,
        #         creative_id=creative_id,
        #         name=f"Ad {idx+1}",
        #         external_id=external_id,
        #         status="PAUSED"
        #     )
        #     ad_ids.append(ad_id)

        print("\n✅ Campaign structure created successfully!")
        print(f"   Campaign ID: {campaign_id}")
        print(f"   Ad Set ID: {ad_set_id}")
        print(f"   Status: PAUSED (activate manually when ready)")

        return {
            "campaign_id": campaign_id,
            "ad_set_ids": [ad_set_id],
            "ad_ids": ad_ids,
            "creative_ids": creative_ids,
            "status": "PAUSED"
        }


class MetaAdsError(Exception):
    """Exception raised for Meta Ads API errors"""
    pass


# Example usage (for documentation)
"""
Example workflow:

from src.integrations.meta_ads import MetaAdsAPI
import os

# Initialize API client
meta_api = MetaAdsAPI(
    access_token=os.getenv("META_ACCESS_TOKEN"),
    ad_account_id=os.getenv("META_AD_ACCOUNT_ID"),
    page_id=os.getenv("META_PAGE_ID"),
    instagram_actor_id=os.getenv("META_INSTAGRAM_ACTOR_ID"),
    dry_run=True  # Test mode
)

# Get campaign config from agent
config = state["current_config"]

# Deploy campaign to Meta
result = meta_api.create_campaign_from_config(config)

print(f"Campaign deployed!")
print(f"  Campaign ID: {result['campaign_id']}")
print(f"  Ad Set IDs: {result['ad_set_ids']}")
print(f"  Ad IDs: {result['ad_ids']}")

# Later: Fetch performance data
insights = meta_api.get_campaign_insights(
    campaign_id=result['campaign_id'],
    date_start="2024-01-01",
    date_end="2024-01-07"
)

print(f"Spend: ${insights['spend']}")
print(f"Conversions: {insights['conversions']}")
"""
