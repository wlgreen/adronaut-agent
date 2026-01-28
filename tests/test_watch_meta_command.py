import json
from types import SimpleNamespace
from datetime import date, timedelta


def test_watch_meta_emits_alerts_and_saves_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("ADRONAUT_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    # Create deployment result with guardrails
    dep = {
        "project_id": "p1",
        "campaign_id": "cmp_123",
        "guardrails": {"daily_cap": 50.0, "target_cpa": 10.0},
    }
    dep_path = tmp_path / "dep.json"
    dep_path.write_text(json.dumps(dep))

    # Patch MetaAdsAPI methods to avoid network and return deterministic insights
    from src.integrations import meta_ads as meta_ads_mod

    today = date.today().isoformat()
    trailing_start = (date.today() - timedelta(days=7)).isoformat()
    trailing_end = (date.today() - timedelta(days=1)).isoformat()

    def fake_get_campaign_insights(self, campaign_id, date_start, date_end, fields=None):
        assert campaign_id == "cmp_123"
        if date_start == today and date_end == today:
            # Today is bad: high spend, low CTR, high CPA
            return {
                "data": [
                    {
                        "spend": "60.0",
                        "impressions": "1000",
                        "clicks": "10",
                        # ctr provided as percent string by Meta
                        "ctr": "1.0",
                        "actions": [{"action_type": "purchase", "value": "3"}],
                    }
                ]
            }
        if date_start == trailing_start and date_end == trailing_end:
            return {
                "data": [
                    {
                        "spend": "300.0",
                        "impressions": "10000",
                        "clicks": "300",
                        "ctr": "3.0",
                        "actions": [{"action_type": "purchase", "value": "60"}],
                    }
                ]
            }
        raise AssertionError("Unexpected date range")

    monkeypatch.setattr(meta_ads_mod.MetaAdsAPI, "get_campaign_insights", fake_get_campaign_insights, raising=True)
    monkeypatch.setattr(meta_ads_mod.MetaAdsAPI, "get_advantage_state", lambda self, campaign_id: {}, raising=True)

    # Env vars required when not in dry-run
    monkeypatch.setenv("META_ACCESS_TOKEN", "test")
    monkeypatch.setenv("META_AD_ACCOUNT_ID", "act_test")

    import cli

    args = SimpleNamespace(
        deployment_result=str(dep_path),
        daily_cap=None,
        target_cpa=None,
        dry_run=False,
    )

    code = cli.watch_meta_command(args)
    assert code == 0

    snaps = sorted((tmp_path / "projects" / "p1" / "artifacts" / "snapshots").glob("*.json"))
    assert snaps, "expected a snapshot json to be created"

    snap = json.loads(snaps[-1].read_text())
    codes = [a["code"] for a in snap["alerts"]]

    assert "SPEND_CAP" in codes
    assert "CTR_DROP" in codes
    assert "CPA_HIGH" in codes
