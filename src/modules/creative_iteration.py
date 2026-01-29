from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.llm import gemini as gemini_mod


@dataclass
class CreativeVariant:
    creative_id: str
    parent_creative_id: Optional[str]
    source: str  # "generated"
    angle: str
    hypothesis: str
    assets: Dict[str, Any]


def _safe_str(x: Any) -> str:
    return x if isinstance(x, str) else "" if x is None else str(x)


ITERATE_META_IMAGE_SYSTEM = """You are an expert direct-response creative strategist for Meta (Facebook/Instagram) image ads.
You generate compliant, high-performing ad creative iterations.
Return ONLY valid JSON; no extra text."""


ITERATE_META_IMAGE_PROMPT = """We are iterating Meta IMAGE ad creatives.

CONTEXT
- Product description: {product_description}
- Brand guidelines: {brand_guidelines}
- Optimization goal: {optimization_goal}

BASE CREATIVE (the current best/starting point)
- Angle: {base_angle}
- Hypothesis: {base_hypothesis}
- Visual prompt (for image generation / art direction): {base_visual_prompt}
- Primary text: {base_primary_text}
- Headline: {base_headline}
- CTA: {base_cta}

TASK
Generate 3 new variants:
A) "refine": same angle, improved hook + clarity
B) "explore": a different angle (new framing)
C) "format tweak": still image ad, but different composition concept (e.g., product hero vs lifestyle vs testimonial card style)

For EACH variant, provide:
- angle (string)
- hypothesis (string)
- visual_prompt (1 paragraph, concrete, photorealistic, describes composition + lighting + product prominence; avoid text-in-image)
- primary_text (1-3 sentences)
- headline (<= 40 chars ideal)
- cta (one of: SHOP_NOW, LEARN_MORE, SIGN_UP, GET_OFFER, BUY_NOW)

EXPERIMENT PLAN
Suggest:
- allocation_percent: [60, 20, 20] for {A,B,C} (can adjust if justified)
- minimum_spend_per_variant_usd: a single number (e.g., 20-50)
- stop_rules: list of 2-4 simple rules (e.g., "Pause if spend>$X and conversions=0")

OUTPUT JSON FORMAT (exact):
{{
  "variants": [
    {{"kind":"refine","angle":"...","hypothesis":"...","visual_prompt":"...","primary_text":"...","headline":"...","cta":"SHOP_NOW"}},
    {{"kind":"explore","angle":"...","hypothesis":"...","visual_prompt":"...","primary_text":"...","headline":"...","cta":"SHOP_NOW"}},
    {{"kind":"format_tweak","angle":"...","hypothesis":"...","visual_prompt":"...","primary_text":"...","headline":"...","cta":"SHOP_NOW"}}
  ],
  "experiment": {{
    "allocation_percent": [60,20,20],
    "minimum_spend_per_variant_usd": 30,
    "stop_rules": ["..."]
  }}
}}
"""


def generate_meta_image_variants(
    *,
    product_description: str,
    brand_guidelines: str,
    optimization_goal: str,
    base: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate 3 Meta image ad creative variants + experiment plan.

    `base` should include: visual_prompt, primary_text, headline, cta, plus optional base_angle/base_hypothesis.
    """

    gemini = gemini_mod.get_gemini()

    prompt = ITERATE_META_IMAGE_PROMPT.format(
        product_description=_safe_str(product_description) or "(not provided)",
        brand_guidelines=_safe_str(brand_guidelines) or "(not provided)",
        optimization_goal=_safe_str(optimization_goal) or "CONVERSIONS",
        base_angle=_safe_str(base.get("angle")) or "(unknown)",
        base_hypothesis=_safe_str(base.get("hypothesis")) or "(unknown)",
        base_visual_prompt=_safe_str(base.get("visual_prompt")) or "(none)",
        base_primary_text=_safe_str(base.get("primary_text")) or "(none)",
        base_headline=_safe_str(base.get("headline")) or "(none)",
        base_cta=_safe_str(base.get("cta")) or "SHOP_NOW",
    )

    out = gemini.generate_json(
        prompt=prompt,
        system_instruction=ITERATE_META_IMAGE_SYSTEM,
        temperature=0.7,
        task_name="Meta Image Creative Iteration",
    )

    # Minimal validation / normalization
    variants = out.get("variants") if isinstance(out, dict) else None
    if not isinstance(variants, list) or len(variants) < 3:
        raise ValueError("LLM output missing variants")

    exp = out.get("experiment") if isinstance(out, dict) else None
    if not isinstance(exp, dict):
        out["experiment"] = {
            "allocation_percent": [60, 20, 20],
            "minimum_spend_per_variant_usd": 30,
            "stop_rules": [
                "Pause any variant if spend>$30 and conversions=0",
                "Pause any variant if CTR is materially below baseline after 1k impressions",
            ],
        }

    return out


def new_creative_id() -> str:
    return str(uuid.uuid4())
