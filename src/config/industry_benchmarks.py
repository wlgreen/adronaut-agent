"""
Industry Benchmarks Database

Provides realistic CPA/ROAS targets for cold start campaigns.
Data sourced from industry reports, platform benchmarks, and aggregated research.

Last updated: 2025-01
Sources:
- WordStream Advertising Benchmarks 2024
- Meta Ads Benchmarks Q4 2024
- Google Ads Industry Benchmarks 2024
- TikTok for Business Industry Reports
"""

from typing import Dict, List, Optional

# =============================================================================
# E-COMMERCE BENCHMARKS
# =============================================================================

ECOMMERCE_BENCHMARKS = {
    "apparel_fashion": {
        "category": "E-commerce",
        "subcategory": "Apparel & Fashion",
        "metrics": {
            "cpa": {"min": 8, "median": 15, "max": 25, "currency": "USD"},
            "roas": {"min": 2.5, "median": 3.2, "max": 4.5},
            "ctr": {"min": 0.8, "median": 1.5, "max": 2.5},  # Click-through rate %
            "conversion_rate": {"min": 1.5, "median": 2.8, "max": 4.5},  # %
        },
        "platforms": {
            "tiktok": {"performance_tier": "excellent", "avg_cpa": 12, "market_share": 35},
            "instagram": {"performance_tier": "excellent", "avg_cpa": 14, "market_share": 30},
            "meta": {"performance_tier": "good", "avg_cpa": 16, "market_share": 25},
            "google": {"performance_tier": "moderate", "avg_cpa": 22, "market_share": 10},
        },
        "audience": {
            "age_range": "18-45",
            "top_age_segment": "18-34",
            "gender_split": {"female": 65, "male": 35},
            "interests": ["fashion", "shopping", "style", "clothing"],
        },
        "creative_best_practices": {
            "formats": ["video", "carousel", "static"],
            "top_format": "video",
            "video_length": "15-30 seconds",
            "key_elements": ["lifestyle imagery", "model shots", "product close-ups"],
        },
        "seasonality": {
            "high": ["Q4", "Nov-Dec"],
            "medium": ["Q1", "Q3"],
            "low": ["Q2"],
        },
    },

    "electronics": {
        "category": "E-commerce",
        "subcategory": "Electronics",
        "metrics": {
            "cpa": {"min": 15, "median": 28, "max": 45, "currency": "USD"},
            "roas": {"min": 2.0, "median": 2.8, "max": 4.0},
            "ctr": {"min": 0.6, "median": 1.2, "max": 2.0},
            "conversion_rate": {"min": 1.0, "median": 2.2, "max": 3.5},
        },
        "platforms": {
            "tiktok": {"performance_tier": "excellent", "avg_cpa": 22, "market_share": 30},
            "google": {"performance_tier": "good", "avg_cpa": 26, "market_share": 35},
            "meta": {"performance_tier": "good", "avg_cpa": 28, "market_share": 25},
            "youtube": {"performance_tier": "moderate", "avg_cpa": 35, "market_share": 10},
        },
        "audience": {
            "age_range": "18-55",
            "top_age_segment": "25-44",
            "gender_split": {"male": 60, "female": 40},
            "interests": ["technology", "gadgets", "electronics", "tech reviews"],
        },
        "creative_best_practices": {
            "formats": ["video", "static"],
            "top_format": "video",
            "video_length": "30-60 seconds",
            "key_elements": ["product demos", "feature highlights", "comparison shots"],
        },
        "seasonality": {
            "high": ["Q4", "Nov-Dec", "Black Friday"],
            "medium": ["Q1", "Q3"],
            "low": ["Q2"],
        },
    },

    "beauty_cosmetics": {
        "category": "E-commerce",
        "subcategory": "Beauty & Cosmetics",
        "metrics": {
            "cpa": {"min": 10, "median": 18, "max": 30, "currency": "USD"},
            "roas": {"min": 2.8, "median": 3.5, "max": 5.0},
            "ctr": {"min": 1.0, "median": 2.0, "max": 3.5},
            "conversion_rate": {"min": 2.0, "median": 3.5, "max": 5.5},
        },
        "platforms": {
            "tiktok": {"performance_tier": "excellent", "avg_cpa": 14, "market_share": 40},
            "instagram": {"performance_tier": "excellent", "avg_cpa": 16, "market_share": 35},
            "meta": {"performance_tier": "good", "avg_cpa": 19, "market_share": 20},
            "pinterest": {"performance_tier": "moderate", "avg_cpa": 25, "market_share": 5},
        },
        "audience": {
            "age_range": "18-55",
            "top_age_segment": "18-34",
            "gender_split": {"female": 80, "male": 20},
            "interests": ["beauty", "skincare", "makeup", "cosmetics"],
        },
        "creative_best_practices": {
            "formats": ["video", "ugc"],
            "top_format": "ugc_video",
            "video_length": "15-30 seconds",
            "key_elements": ["before/after", "tutorials", "influencer content"],
        },
        "seasonality": {
            "high": ["Q4", "Valentine's Day", "Mother's Day"],
            "medium": ["Q1", "Q3"],
            "low": ["Q2"],
        },
    },

    "home_garden": {
        "category": "E-commerce",
        "subcategory": "Home & Garden",
        "metrics": {
            "cpa": {"min": 12, "median": 22, "max": 38, "currency": "USD"},
            "roas": {"min": 2.2, "median": 3.0, "max": 4.2},
            "ctr": {"min": 0.7, "median": 1.3, "max": 2.2},
            "conversion_rate": {"min": 1.2, "median": 2.5, "max": 4.0},
        },
        "platforms": {
            "meta": {"performance_tier": "excellent", "avg_cpa": 20, "market_share": 35},
            "google": {"performance_tier": "good", "avg_cpa": 24, "market_share": 30},
            "pinterest": {"performance_tier": "good", "avg_cpa": 22, "market_share": 20},
            "tiktok": {"performance_tier": "moderate", "avg_cpa": 26, "market_share": 15},
        },
        "audience": {
            "age_range": "25-65",
            "top_age_segment": "35-54",
            "gender_split": {"female": 55, "male": 45},
            "interests": ["home decor", "gardening", "DIY", "furniture"],
        },
        "creative_best_practices": {
            "formats": ["static", "carousel", "video"],
            "top_format": "carousel",
            "video_length": "30-45 seconds",
            "key_elements": ["lifestyle shots", "room settings", "product in use"],
        },
        "seasonality": {
            "high": ["Spring", "Q2"],
            "medium": ["Q3", "Q4"],
            "low": ["Q1"],
        },
    },

    "food_beverage": {
        "category": "E-commerce",
        "subcategory": "Food & Beverage",
        "metrics": {
            "cpa": {"min": 10, "median": 20, "max": 35, "currency": "USD"},
            "roas": {"min": 2.5, "median": 3.3, "max": 4.8},
            "ctr": {"min": 0.9, "median": 1.8, "max": 3.0},
            "conversion_rate": {"min": 1.5, "median": 3.0, "max": 5.0},
        },
        "platforms": {
            "instagram": {"performance_tier": "excellent", "avg_cpa": 16, "market_share": 35},
            "meta": {"performance_tier": "excellent", "avg_cpa": 18, "market_share": 30},
            "tiktok": {"performance_tier": "good", "avg_cpa": 22, "market_share": 25},
            "google": {"performance_tier": "moderate", "avg_cpa": 28, "market_share": 10},
        },
        "audience": {
            "age_range": "18-55",
            "top_age_segment": "25-44",
            "gender_split": {"female": 60, "male": 40},
            "interests": ["food", "cooking", "health", "wellness"],
        },
        "creative_best_practices": {
            "formats": ["video", "static"],
            "top_format": "video",
            "video_length": "15-30 seconds",
            "key_elements": ["product shots", "recipe videos", "testimonials"],
        },
        "seasonality": {
            "high": ["Q1", "New Year"],
            "medium": ["Q2", "Q3"],
            "low": ["Q4"],
        },
    },
}

# =============================================================================
# SAAS BENCHMARKS
# =============================================================================

SAAS_BENCHMARKS = {
    "productivity_tools": {
        "category": "SaaS",
        "subcategory": "Productivity Tools",
        "price_tiers": {
            "low": {  # <$50/month
                "cpa": {"min": 20, "median": 45, "max": 80, "currency": "USD"},
                "roas": {"min": 3.0, "median": 4.0, "max": 6.0},
                "ltv_cac_ratio": {"min": 3.0, "median": 4.5, "max": 7.0},
                "trial_to_paid_rate": {"min": 10, "median": 15, "max": 25},  # %
            },
            "mid": {  # $50-200/month
                "cpa": {"min": 80, "median": 150, "max": 250, "currency": "USD"},
                "roas": {"min": 2.5, "median": 3.5, "max": 5.0},
                "ltv_cac_ratio": {"min": 2.5, "median": 4.0, "max": 6.0},
                "trial_to_paid_rate": {"min": 12, "median": 18, "max": 28},
            },
            "high": {  # >$200/month
                "cpa": {"min": 200, "median": 400, "max": 800, "currency": "USD"},
                "roas": {"min": 2.0, "median": 3.0, "max": 4.5},
                "ltv_cac_ratio": {"min": 2.0, "median": 3.5, "max": 5.5},
                "trial_to_paid_rate": {"min": 8, "median": 12, "max": 20},
            },
        },
        "platforms": {
            "google": {"performance_tier": "excellent", "avg_cpa": 120, "market_share": 40},
            "meta": {"performance_tier": "good", "avg_cpa": 150, "market_share": 30},
            "linkedin": {"performance_tier": "good", "avg_cpa": 180, "market_share": 20},
            "youtube": {"performance_tier": "moderate", "avg_cpa": 200, "market_share": 10},
        },
        "audience": {
            "age_range": "25-55",
            "top_age_segment": "30-45",
            "job_titles": ["manager", "director", "founder", "executive"],
            "interests": ["productivity", "business tools", "software"],
        },
        "creative_best_practices": {
            "formats": ["video", "static"],
            "top_format": "video",
            "video_length": "30-60 seconds",
            "key_elements": ["product demo", "use cases", "testimonials", "ROI claims"],
        },
        "sales_cycle": {
            "avg_days": 14,
            "touchpoints": 5,
        },
    },

    "marketing_tools": {
        "category": "SaaS",
        "subcategory": "Marketing Tools",
        "price_tiers": {
            "low": {
                "cpa": {"min": 25, "median": 55, "max": 100, "currency": "USD"},
                "roas": {"min": 2.8, "median": 3.8, "max": 5.5},
                "ltv_cac_ratio": {"min": 2.8, "median": 4.2, "max": 6.5},
                "trial_to_paid_rate": {"min": 12, "median": 18, "max": 30},
            },
            "mid": {
                "cpa": {"min": 100, "median": 180, "max": 300, "currency": "USD"},
                "roas": {"min": 2.3, "median": 3.3, "max": 4.8},
                "ltv_cac_ratio": {"min": 2.3, "median": 3.8, "max": 5.5},
                "trial_to_paid_rate": {"min": 10, "median": 15, "max": 25},
            },
            "high": {
                "cpa": {"min": 250, "median": 500, "max": 1000, "currency": "USD"},
                "roas": {"min": 1.8, "median": 2.8, "max": 4.0},
                "ltv_cac_ratio": {"min": 2.0, "median": 3.2, "max": 5.0},
                "trial_to_paid_rate": {"min": 6, "median": 10, "max": 18},
            },
        },
        "platforms": {
            "google": {"performance_tier": "excellent", "avg_cpa": 140, "market_share": 45},
            "linkedin": {"performance_tier": "good", "avg_cpa": 200, "market_share": 25},
            "meta": {"performance_tier": "good", "avg_cpa": 180, "market_share": 20},
            "twitter": {"performance_tier": "moderate", "avg_cpa": 220, "market_share": 10},
        },
        "audience": {
            "age_range": "25-55",
            "top_age_segment": "28-42",
            "job_titles": ["marketing manager", "CMO", "growth lead", "digital marketer"],
            "interests": ["marketing", "digital advertising", "analytics"],
        },
        "creative_best_practices": {
            "formats": ["video", "static", "carousel"],
            "top_format": "video",
            "video_length": "30-90 seconds",
            "key_elements": ["results-focused", "case studies", "platform demos"],
        },
        "sales_cycle": {
            "avg_days": 21,
            "touchpoints": 6,
        },
    },
}

# =============================================================================
# SERVICES BENCHMARKS
# =============================================================================

SERVICES_BENCHMARKS = {
    "local_services": {
        "category": "Services",
        "subcategory": "Local Services",
        "service_types": {
            "home_services": {  # Plumbing, HVAC, etc.
                "cpa": {"min": 15, "median": 35, "max": 60, "currency": "USD"},
                "roas": {"min": 3.5, "median": 5.0, "max": 8.0},
                "lead_to_customer_rate": {"min": 20, "median": 35, "max": 50},  # %
                "avg_job_value": {"min": 200, "median": 500, "max": 1500},
            },
            "professional_services": {  # Legal, accounting, etc.
                "cpa": {"min": 50, "median": 120, "max": 250, "currency": "USD"},
                "roas": {"min": 3.0, "median": 4.5, "max": 7.0},
                "lead_to_customer_rate": {"min": 15, "median": 25, "max": 40},
                "avg_job_value": {"min": 1000, "median": 3000, "max": 10000},
            },
            "health_wellness": {  # Dental, fitness, etc.
                "cpa": {"min": 25, "median": 60, "max": 120, "currency": "USD"},
                "roas": {"min": 2.8, "median": 4.0, "max": 6.5},
                "lead_to_customer_rate": {"min": 18, "median": 30, "max": 45},
                "avg_job_value": {"min": 300, "median": 800, "max": 2500},
            },
        },
        "platforms": {
            "google": {"performance_tier": "excellent", "avg_cpa": 40, "market_share": 60},
            "meta": {"performance_tier": "good", "avg_cpa": 55, "market_share": 30},
            "nextdoor": {"performance_tier": "moderate", "avg_cpa": 70, "market_share": 10},
        },
        "audience": {
            "age_range": "25-65",
            "top_age_segment": "35-55",
            "location_targeting": "local_radius",
            "radius_miles": {"min": 10, "median": 25, "max": 50},
        },
        "creative_best_practices": {
            "formats": ["static", "video"],
            "top_format": "static",
            "video_length": "15-30 seconds",
            "key_elements": ["local presence", "reviews", "before/after", "urgency"],
        },
    },
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_all_categories() -> List[str]:
    """Returns list of all available categories"""
    categories = []
    for benchmarks in [ECOMMERCE_BENCHMARKS, SAAS_BENCHMARKS, SERVICES_BENCHMARKS]:
        for key in benchmarks.keys():
            categories.append(benchmarks[key]["category"])
    return list(set(categories))


def get_subcategories_by_category(category: str) -> List[str]:
    """Returns list of subcategories for a given category"""
    subcategories = []

    if category.lower() == "e-commerce":
        for key, data in ECOMMERCE_BENCHMARKS.items():
            subcategories.append(data["subcategory"])
    elif category.lower() == "saas":
        for key, data in SAAS_BENCHMARKS.items():
            subcategories.append(data["subcategory"])
    elif category.lower() == "services":
        for key, data in SERVICES_BENCHMARKS.items():
            subcategories.append(data["subcategory"])

    return subcategories


def get_benchmark(category_key: str, category_type: str = "ecommerce") -> Optional[Dict]:
    """
    Get benchmark data for a specific category

    Args:
        category_key: The key for the benchmark (e.g., "apparel_fashion")
        category_type: Type of benchmark ("ecommerce", "saas", "services")

    Returns:
        Dictionary with benchmark data or None if not found
    """
    if category_type == "ecommerce":
        return ECOMMERCE_BENCHMARKS.get(category_key)
    elif category_type == "saas":
        return SAAS_BENCHMARKS.get(category_key)
    elif category_type == "services":
        return SERVICES_BENCHMARKS.get(category_key)
    return None


def get_platform_recommendations(category_key: str, category_type: str = "ecommerce") -> Dict:
    """Get platform performance data for a category"""
    benchmark = get_benchmark(category_key, category_type)
    if benchmark and "platforms" in benchmark:
        return benchmark["platforms"]
    return {}


def get_target_metrics(category_key: str, category_type: str = "ecommerce", price_tier: str = None) -> Dict:
    """
    Get target CPA/ROAS metrics for a category

    For SaaS, requires price_tier ("low", "mid", "high")
    For Services, requires service_type
    """
    benchmark = get_benchmark(category_key, category_type)

    if not benchmark:
        return {}

    # E-commerce and simple cases
    if "metrics" in benchmark:
        return benchmark["metrics"]

    # SaaS with price tiers
    if "price_tiers" in benchmark and price_tier:
        return benchmark["price_tiers"].get(price_tier, {})

    # Services with service types
    if "service_types" in benchmark:
        return benchmark["service_types"]

    return {}


# =============================================================================
# DEFAULT FALLBACK
# =============================================================================

DEFAULT_BENCHMARK = {
    "category": "General",
    "subcategory": "Unknown",
    "metrics": {
        "cpa": {"min": 15, "median": 30, "max": 60, "currency": "USD"},
        "roas": {"min": 2.0, "median": 3.0, "max": 4.5},
        "ctr": {"min": 0.5, "median": 1.0, "max": 2.0},
        "conversion_rate": {"min": 1.0, "median": 2.0, "max": 4.0},
    },
    "platforms": {
        "meta": {"performance_tier": "moderate", "avg_cpa": 30, "market_share": 40},
        "google": {"performance_tier": "moderate", "avg_cpa": 35, "market_share": 35},
        "tiktok": {"performance_tier": "moderate", "avg_cpa": 28, "market_share": 25},
    },
    "note": "Generic benchmark - product classification recommended for better accuracy"
}
