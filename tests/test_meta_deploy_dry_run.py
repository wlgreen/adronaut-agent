import os


def test_meta_deploy_creatives_dry_run(tmp_path):
    # No real API calls
    os.environ["META_DRY_RUN"] = "true"

    from src.integrations.meta_ads import MetaAdsAPI

    api = MetaAdsAPI(
        access_token="test",
        ad_account_id="act_test",
        page_id="123",  # required for creatives
        dry_run=True,
    )

    cfg = {
        "project_id": "proj1",
        "meta": {
            "campaign_name": "Test Campaign",
            "daily_budget": 10,
            "objective": "OUTCOME_TRAFFIC",
            "creative_specs": {
                "link": "https://example.com",
                "call_to_action": "LEARN_MORE",
                "image_url": "https://via.placeholder.com/300.png",
            },
        },
        "creative_assets": [
            {
                "combo_id": "c1",
                "headline": "Hello",
                "primary_text": "World",
            }
        ],
    }

    res = api.create_campaign_from_config(cfg)
    assert res["campaign_id"]
    assert len(res["ad_set_ids"]) == 1
    # In dry_run we can create creatives and ads (mock ids)
    assert isinstance(res["creative_ids"], list)
    assert isinstance(res["ad_ids"], list)
