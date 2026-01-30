"""Deterministic fake LLM for local eval runs.

This is intentionally *very* small and rule-based. It exists so we can run
end-to-end flows (planning → nodes → artifacts) without an API key.

Enable by setting `ADRONAUT_EVAL_MODE=1` or `ADRONAUT_FAKE_LLM=1`.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional


def _stable_id(prefix: str, payload: str) -> str:
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{h}"


class FakeGeminiClient:
    """Drop-in replacement for GeminiClient with deterministic outputs."""

    model_name = "fake-gemini-deterministic"

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        task_name: str = "JSON Generation",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        tn = (task_name or "").lower()

        # --- Agent orchestration ---
        if "planning" in tn:
            # Heuristic: if the planner prompt indicates experiment results exist, run reflect/adjust flow.
            p = (prompt or "")
            if "Previous experiments:" in p:
                try:
                    num = int(p.split("Previous experiments:", 1)[1].split("\n", 1)[0].strip())
                except Exception:
                    num = 0
            else:
                num = 0

            if num and num > 0 or "experiment_results" in p.lower() or "experiment results" in p.lower() or "week" in p.lower() and "results" in p.lower():
                # ReflectionSkill forces a replan after it runs. If a latest reflection summary
                # already exists in the prompt, skip reflection and proceed to adjustment.
                has_latest_reflection = "LATEST REFLECTION (JSON, if available):\nnull" not in p

                # Decide whether we actually need an adjustment based on latest_reflection.
                # ReflectionSkill writes a compact summary with threshold_status.
                cpa_ok = False
                if has_latest_reflection:
                    # Heuristic: detect cpa ok in latest_reflection JSON.
                    import re
                    cpa_ok = re.search(r"\"cpa\"\s*:\s*\"ok\"", p) is not None

                import os
                env_needs_change = os.environ.get("ADRONAUT_EVAL_NEEDS_CHANGE")

                # If CPA seems ok (or scenario says no change), do not churn config: just save.
                if has_latest_reflection and (cpa_ok or env_needs_change == "0"):
                    steps = [
                        {"id": "s_save", "action": "save", "rationale": "Persist state; no changes needed", "success": "state saved", "requires_approval": False},
                    ]
                else:
                    steps = [
                        {"id": "s_adjust", "action": "adjustment", "rationale": "Generate safe patch config", "success": "current_config updated", "requires_approval": True},
                        {"id": "s_save", "action": "save", "rationale": "Persist state", "success": "state saved", "requires_approval": False},
                    ]
                    if not has_latest_reflection:
                        steps = [
                            {"id": "s_reflect", "action": "reflection", "rationale": "Analyze experiment performance", "success": "latest_reflection summarized", "requires_approval": False},
                        ] + steps

                return {
                    "decision": "reflect",
                    "reasoning": "[eval] Deterministic reflect plan (experiment results present)",
                    "steps": steps,
                }

            return {
                "decision": "initialize",
                "reasoning": "[eval] Deterministic plan for offline evaluation",
                "steps": [
                    {"id": "s_discovery", "action": "discovery", "rationale": "Fill missing product/goals", "success": "knowledge_facts populated", "requires_approval": False},
                    {"id": "s_collect", "action": "data_collection", "rationale": "Load uploaded CSVs", "success": "historical_data.metadata exists", "requires_approval": False},
                    {"id": "s_insight", "action": "insight", "rationale": "Derive insights from data", "success": "current_strategy.insights exists", "requires_approval": False},
                    {"id": "s_creatives", "action": "creative_generation", "rationale": "Create creative prompts", "success": "artifacts.creatives exists", "requires_approval": False},
                    {"id": "s_campaign", "action": "campaign_setup", "rationale": "Produce platform configs (no live deploy)", "success": "current_config exists", "requires_approval": True},
                    {"id": "s_save", "action": "save", "rationale": "Persist state", "success": "state saved", "requires_approval": False},
                ],
            }

        if "router decision" in tn:
            return {
                "decision": "initialize",
                "reasoning": "[eval] Default initialize",
                "next_action": "Run discovery and build a config",
                "confidence": 0.9,
            }

        # --- Core modules ---
        if "data inference" in tn:
            # Used in agent.nodes to infer user_inputs.
            return {
                "product_description": "[eval] demo product",
                "target_budget": 100.0,
                "target_cpa": 25.0,
                "target_roas": 3.0,
            }

        if "strategy & insights generation" in tn:
            return {
                "insights": {
                    "patterns": ["[eval] Higher CTR on simple messaging"],
                    "risks": ["[eval] CPA sensitive to broad targeting"],
                },
                "strategy": {
                    "primary_goal": "conversions",
                    "positioning": "clear value prop, fast benefits",
                    "audience_hypotheses": ["prospecting lookalikes", "interest-based"],
                },
            }

        if "execution timeline planning" in tn:
            return {
                "timeline": {
                    "phases": [
                        {
                            "name": "Week 1",
                            "goal": "Baseline",
                            "test_combinations": [
                                {
                                    "id": "combo_1",
                                    "platform": "Meta",
                                    "audience": "Broad",
                                    "creative": "UGC",
                                    "budget_percent": 50,
                                    "creative_generation": {"headline": "[eval] Try it today", "primary_text": "[eval] Simple value prop", "image_prompt": "[eval] clean product shot"},
                                }
                            ],
                        }
                    ]
                }
            }

        if "creative prompt generation" in tn or "creative batch generation" in tn:
            # Enough structure to be attached as creative_assets.
            return {
                "headline": "[eval] Headline",
                "primary_text": "[eval] Primary text",
                "description": "[eval] Description",
                "image_prompt": "[eval] Minimalist product on white background",
                "cta": "SHOP_NOW",
            }

        if "creative prompt rating" in tn or "generated image rating" in tn:
            return {
                "overall_score": 70,
                "category_scores": {"clarity": 70, "brand_fit": 70},
                "strengths": ["[eval] clear"],
                "weaknesses": [],
                "suggestions": ["[eval] add one specific benefit"],
                "error": None,
            }

        if "campaign configuration" in tn:
            # This is the core artifact we validate in eval.
            # Keep it simple, schema-complete, and deterministic.
            # Budget split: 60/40.
            is_adjusted = "adjusted" in tn
            target_cpa = 24.0 if is_adjusted else 25.0

            return {
                "tiktok": {
                    "campaign_name": "[eval][DTC][PURCHASE] TikTok Prospecting",
                    "objective": "CONVERSIONS",
                    "daily_budget": 60.0,
                    "targeting": {
                        "age_range": "18-54",
                        "gender": "all",
                        "locations": ["US"],
                        "interests": [],
                        "behaviors": ["engaged shoppers"],
                    },
                    "placements": ["TikTok"],
                    "creative_specs": {
                        "format": "video",
                        "duration": "9-15s",
                        "messaging": [
                            "Problem→Solution: what it fixes + how",
                            "Proof: reviews/results before/after",
                            "Offer: incentive + guarantee + shipping clarity",
                        ],
                    },
                    "optimization": {
                        "optimization_goal": "CONVERSIONS",
                        "attribution_window": "7_DAY_CLICK",
                        "conversion_event": "Purchase",
                    },
                    "bidding": {
                        "strategy": "LOWEST_COST_WITH_BID_CAP",
                        "bid_amount": 0.0,
                        "target_cpa": target_cpa,
                    },
                    "funnel": {
                        "prospecting": {
                            "budget_share": 0.85,
                            "ad_groups": [
                                {
                                    "name": "P1_Broad_18-54",
                                    "daily_budget": 30.0,
                                    "targeting": {"age_range": "18-54", "gender": "all", "locations": ["US"], "interests": [], "behaviors": ["engaged shoppers"]},
                                    "placements": ["TikTok"],
                                },
                                {
                                    "name": "P2_Interest_Stack",
                                    "daily_budget": 15.0,
                                    "targeting": {"age_range": "25-44", "gender": "all", "locations": ["US"], "interests": ["online shopping", "wellness", "fitness"], "behaviors": ["engaged shoppers"]},
                                    "placements": ["TikTok"],
                                },
                                {
                                    "name": "P3_Test_Hook_Variants",
                                    "daily_budget": 6.0,
                                    "targeting": {"age_range": "25-44", "gender": "all", "locations": ["US"], "interests": [], "behaviors": ["engaged shoppers"]},
                                    "placements": ["TikTok"],
                                }
                            ],
                        },
                        "retargeting": {
                            "budget_share": 0.15,
                            "ad_groups": [
                                {
                                    "name": "R1_7D_ViewContent_ATC",
                                    "daily_budget": 9.0,
                                    "audiences": ["7D ViewContent", "7D AddToCart"],
                                    "exclusions": ["180D Purchasers"],
                                    "placements": ["TikTok"],
                                }
                            ],
                        },
                    },
                    "creative_plan": {
                        "formats": ["UGC_video_9-15s", "UGC_video_20-30s"],
                        "required_angles": [
                            "Problem→Solution",
                            "Before/After",
                            "Social Proof/Testimonial",
                            "Offer + Urgency",
                            "Objection handler (shipping/price/quality)",
                        ],
                        "hooks": [
                            "Stop doing X…",
                            "If you struggle with X, try this…",
                            "I tried this for 7 days—here’s what happened",
                        ],
                        "cta": "SHOP_NOW",
                    },
                    "tracking": {
                        "utm_template": "utm_source=tiktok&utm_medium=paid_social&utm_campaign={{campaign_name}}&utm_content={{ad_name}}",
                        "naming": {
                            "campaign": "[DTC][PURCHASE][TT] {{funnel}} | {{angle}}",
                            "ad_group": "{{audience}} | {{placement}}",
                            "ad": "{{hook}} | {{creator}} | v{{version}}",
                        },
                    },
                },
                "meta": {
                    "campaign_name": "[eval][DTC][PURCHASE] Meta Prospecting",
                    "objective": "CONVERSIONS",
                    "daily_budget": 40.0,
                    "targeting": {
                        "age_range": "18-54",
                        "gender": "all",
                        "locations": ["US"],
                        "detailed_targeting": {"interests": [], "behaviors": ["engaged_shoppers"]},
                    },
                    "placements": ["advantage_plus"],
                    "creative_specs": {
                        "formats": ["reels_9x16", "feed_1x1", "carousel"],
                        "messaging": [
                            "Hook → benefit → proof → offer → CTA",
                            "UGC testimonial + social proof",
                            "Offer + guarantee + shipping clarity",
                        ],
                    },
                    "optimization": {
                        "optimization_goal": "CONVERSIONS",
                        "conversion_window": "7_DAY_CLICK",
                        "conversion_event": "Purchase",
                        "attribution": {"click": "7d", "view": "1d"},
                    },
                    "bidding": {
                        "strategy": "LOWEST_COST_WITH_BID_CAP",
                        "bid_amount": 0.0,
                        "target_cpa": target_cpa,
                    },
                    "funnel": {
                        "prospecting": {
                            "budget_share": 0.8,
                            "ad_sets": [
                                {
                                    "name": "P1_Broad_Advantage+",
                                    "daily_budget": 20.0,
                                    "targeting": {
                                        "age_range": "18-54",
                                        "gender": "all",
                                        "locations": ["US"],
                                        "detailed_targeting": {"interests": [], "behaviors": ["engaged_shoppers"]},
                                    },
                                },
                                {
                                    "name": "P2_Interest_Stack",
                                    "daily_budget": 8.0,
                                    "targeting": {
                                        "age_range": "25-44",
                                        "gender": "all",
                                        "locations": ["US"],
                                        "detailed_targeting": {"interests": ["fitness", "wellness"], "behaviors": ["engaged_shoppers"]},
                                    },
                                },
                                {
                                    "name": "P3_Creative_Test_Cell",
                                    "daily_budget": 4.0,
                                    "targeting": {
                                        "age_range": "18-54",
                                        "gender": "all",
                                        "locations": ["US"],
                                        "detailed_targeting": {"interests": [], "behaviors": ["engaged_shoppers"]},
                                    },
                                }
                            ],
                        },
                        "retargeting": {
                            "budget_share": 0.2,
                            "ad_sets": [
                                {
                                    "name": "R1_7D_ATC",
                                    "daily_budget": 5.0,
                                    "custom_audiences": ["7D AddToCart"],
                                    "exclude_audiences": ["180D Purchasers"],
                                },
                                {
                                    "name": "R2_14D_ViewContent_IG_Engagers",
                                    "daily_budget": 3.0,
                                    "custom_audiences": ["14D ViewContent", "14D IG Engagers"],
                                    "exclude_audiences": ["180D Purchasers"],
                                }
                            ],
                        },
                    },
                    "creative_plan": {
                        "formats": ["reels_9x16", "feed_1x1", "carousel"],
                        "required_angles": [
                            "Problem→Solution",
                            "Proof (UGC + results)",
                            "Offer + guarantee",
                            "Competitor comparison",
                            "Objection handler",
                        ],
                        "primary_text_templates": [
                            "Hook → benefit → proof → CTA",
                            "Question hook → empathy → solution → CTA",
                        ],
                        "cta": "SHOP_NOW",
                    },
                    "tracking": {
                        "utm_template": "utm_source=meta&utm_medium=paid_social&utm_campaign={{campaign_name}}&utm_content={{ad_name}}",
                        "events_required": ["ViewContent", "AddToCart", "InitiateCheckout", "Purchase"],
                        "notes": "Ensure Pixel + CAPI are enabled before scaling.",
                    },
                },
                "summary": {
                    "total_daily_budget": 100.0,
                    "budget_allocation": {"tiktok": 60.0, "meta": 40.0},
                    "experiment": "[DTC] 2-week creative angle test (5 angles) with prospecting+retargeting split",
                    "success_metrics": {
                        "primary": "CPA (Purchase)",
                        "secondary": ["CTR", "CVR", "AOV", "MER"],
                        "stop_rules": ["If CPA > 1.5x target for 2 days → pause worst ad", "If CTR drops >20% vs 7d avg → refresh creatives"],
                    },
                },
            }

        if "performance analysis" in tn:
            # Try to infer whether CPA is above target from the prompt.
            # This is intentionally heuristic; it exists to drive reflect/adjust eval gates.
            import re

            p = prompt or ""

            # Extract target_cpa from the prompt (defaults in reflection.py: 25.0)
            m = re.search(r"target_cpa\s*=\s*([0-9]+(?:\.[0-9]+)?)", p)
            target_cpa = float(m.group(1)) if m else 25.0

            # Prefer explicit cpa fields if present
            cpas = [float(x) for x in re.findall(r"\"cpa\"\s*:\s*([0-9]+(?:\.[0-9]+)?)", p)]
            blended_cpa = None
            if cpas:
                blended_cpa = sum(cpas) / len(cpas)
            else:
                spends = [float(x) for x in re.findall(r"\"spend\"\s*:\s*([0-9]+(?:\.[0-9]+)?)", p)]
                convs = [float(x) for x in re.findall(r"\"conversions\"\s*:\s*([0-9]+(?:\.[0-9]+)?)", p)]
                if spends and convs and len(spends) == len(convs):
                    s = sum(spends)
                    c = sum(convs)
                    if c > 0:
                        blended_cpa = s / c

            status = {"cpa": "unknown", "roas": "ok"}
            if blended_cpa is None:
                status["cpa"] = "unknown"
            elif blended_cpa > 1.2 * target_cpa:
                status["cpa"] = "high"
            else:
                status["cpa"] = "ok"

            return {
                "summary": "[eval] Deterministic performance analysis",
                "threshold_status": status,
                "diagnosis": ["[eval] heuristic"],
                "recommendations": ["[eval] adjust if CPA high"],
            }

        if "optimization patch generation" in tn:
            return {
                "reasoning": "[eval] Small safe tweak",
                "changes": {
                    "meta": {"bidding": {"target_cpa": 24.0}},
                    "tiktok": {"bidding": {"target_cpa": 24.0}},
                },
                "risk_level": "low",
            }

        if "e2e judge" in tn:
            return {
                "scores": {"plan_quality": 4, "config_quality": 5, "grounding": 4, "guardrails": 4},
                "overall": 4,
                "notes": ["[eval] deterministic judge"],
            }

        if "product url extraction" in tn:
            return {"urls": []}

        # Default deterministic response for unknown tasks.
        return {"_eval": True, "task_name": task_name, "id": _stable_id("resp", (task_name or "") + "|" + (prompt or "")[:200])}

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        task_name: str = "Text Generation",
        **kwargs: Any,
    ) -> str:
        # Deterministic text: stable hash preview.
        return f"[eval:{_stable_id('txt', (task_name or '') + '|' + (prompt or '')[:200])}]"

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", task_name: str = "Image Generation", product_image_path: Optional[str] = None) -> Dict[str, Any]:
        # We don't generate real images in eval mode.
        ts = int(time.time())
        return {"success": True, "image_path": f"output/eval_images/{ts}.png", "model": self.model_name, "error": None}
