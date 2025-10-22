"""
Product Classification Module

Uses LLM to classify products into benchmark categories.
Enables cold start campaigns to use industry-specific benchmarks.
"""

from typing import Dict, Optional
from src.llm.gemini import GeminiClient
from src.config.industry_benchmarks import (
    ECOMMERCE_BENCHMARKS,
    SAAS_BENCHMARKS,
    SERVICES_BENCHMARKS,
    DEFAULT_BENCHMARK,
)


CLASSIFICATION_PROMPT_TEMPLATE = """You are a product classification expert for advertising campaigns.

Analyze this product and classify it into the most appropriate category.

PRODUCT INFORMATION:
Product Name: {product_name}
Product Description: {product_description}
Price (if known): {price}
Target Audience (if known): {audience}
Landing Page URL (if known): {landing_page}

AVAILABLE CATEGORIES:

E-COMMERCE:
- apparel_fashion: Clothing, shoes, accessories, fashion items
- electronics: Tech products, gadgets, computers, phones, headphones
- beauty_cosmetics: Makeup, skincare, beauty products, cosmetics
- home_garden: Furniture, home decor, gardening, home improvement
- food_beverage: Food products, beverages, supplements, meal kits

SAAS:
- productivity_tools: Project management, collaboration, note-taking, calendars
- marketing_tools: Email marketing, social media, analytics, SEO tools

SERVICES:
- local_services.home_services: Plumbing, HVAC, cleaning, home repair
- local_services.professional_services: Legal, accounting, consulting
- local_services.health_wellness: Dental, fitness, therapy, medical

INSTRUCTIONS:
1. Analyze the product description carefully
2. Determine the main category (E-commerce, SaaS, or Services)
3. Select the most specific subcategory that matches
4. For SaaS, also determine price tier (low: <$50/mo, mid: $50-200/mo, high: >$200/mo)
5. For Services, determine service_type
6. Provide confidence score (0.0-1.0)

Return ONLY valid JSON in this exact format:
{{
    "category_type": "ecommerce|saas|services",
    "category_key": "exact_key_from_list_above",
    "subcategory_name": "Human readable name",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this classification fits",
    "price_tier": "low|mid|high",
    "service_type": "home_services|professional_services|health_wellness",
    "characteristics": ["key", "characteristics", "identified"]
}}

Example for headphones:
{{
    "category_type": "ecommerce",
    "category_key": "electronics",
    "subcategory_name": "Electronics",
    "confidence": 0.95,
    "reasoning": "Wireless headphones are consumer electronics",
    "price_tier": null,
    "service_type": null,
    "characteristics": ["tech product", "consumer electronics", "audio device"]
}}

Example for CRM software at $99/month:
{{
    "category_type": "saas",
    "category_key": "productivity_tools",
    "subcategory_name": "Productivity Tools",
    "confidence": 0.90,
    "reasoning": "CRM is a productivity and business management tool",
    "price_tier": "mid",
    "service_type": null,
    "characteristics": ["business software", "subscription", "cloud-based"]
}}
"""


def classify_product(
    product_name: str = "",
    product_description: str = "",
    price: str = "",
    audience: str = "",
    landing_page: str = "",
) -> Dict:
    """
    Classify product into benchmark category using LLM

    Args:
        product_name: Name of the product
        product_description: Detailed product description
        price: Product price (if known)
        audience: Target audience (if known)
        landing_page: Product landing page URL (if known)

    Returns:
        Dictionary with classification results:
        {
            "category_type": "ecommerce|saas|services",
            "category_key": "electronics",
            "subcategory_name": "Electronics",
            "confidence": 0.85,
            "reasoning": "...",
            "price_tier": "mid" (for SaaS),
            "service_type": "home_services" (for Services),
            "benchmark_data": {...}  # Full benchmark dict
        }
    """

    # If no product info provided, return default
    if not product_description and not product_name:
        return {
            "category_type": "general",
            "category_key": "default",
            "subcategory_name": "Unknown",
            "confidence": 0.3,
            "reasoning": "No product information provided",
            "price_tier": None,
            "service_type": None,
            "benchmark_data": DEFAULT_BENCHMARK,
        }

    # Build prompt
    prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
        product_name=product_name or "Unknown",
        product_description=product_description or "Not provided",
        price=price or "Unknown",
        audience=audience or "Not specified",
        landing_page=landing_page or "Not provided",
    )

    try:
        # Call LLM
        gemini = GeminiClient()
        response = gemini.generate_json(
            prompt=prompt,
            system_instruction="You are a product classification expert. Return only valid JSON.",
            temperature=0.3,  # Low temperature for consistent classification
            task_name="Product Classification",
        )

        # Validate and enrich response
        category_type = response.get("category_type", "general")
        category_key = response.get("category_key")
        confidence = response.get("confidence", 0.5)

        # Get full benchmark data
        benchmark_data = DEFAULT_BENCHMARK
        if category_key:
            if category_type == "ecommerce":
                benchmark_data = ECOMMERCE_BENCHMARKS.get(category_key, DEFAULT_BENCHMARK)
            elif category_type == "saas":
                benchmark_data = SAAS_BENCHMARKS.get(category_key, DEFAULT_BENCHMARK)
            elif category_type == "services":
                benchmark_data = SERVICES_BENCHMARKS.get(category_key, DEFAULT_BENCHMARK)

        # Add benchmark data to response
        response["benchmark_data"] = benchmark_data

        return response

    except Exception as e:
        # Fallback on error
        print(f"Product classification failed: {e}")
        return {
            "category_type": "general",
            "category_key": "default",
            "subcategory_name": "Unknown",
            "confidence": 0.3,
            "reasoning": f"Classification failed: {str(e)}",
            "price_tier": None,
            "service_type": None,
            "benchmark_data": DEFAULT_BENCHMARK,
        }


def get_classification_summary(classification: Dict) -> str:
    """
    Generate human-readable summary of classification

    Args:
        classification: Result from classify_product()

    Returns:
        Formatted string summary
    """
    category = classification.get("subcategory_name", "Unknown")
    confidence = classification.get("confidence", 0)
    reasoning = classification.get("reasoning", "")

    summary = f"""
PRODUCT CLASSIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Category: {category}
Confidence: {confidence:.0%}
Reasoning: {reasoning}
"""

    # Add price tier for SaaS
    if classification.get("price_tier"):
        tier_labels = {"low": "<$50/mo", "mid": "$50-200/mo", "high": ">$200/mo"}
        tier = classification["price_tier"]
        summary += f"\nPrice Tier: {tier.upper()} ({tier_labels.get(tier, '')})"

    # Add service type for Services
    if classification.get("service_type"):
        summary += f"\nService Type: {classification['service_type'].replace('_', ' ').title()}"

    summary += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    return summary


def get_benchmark_summary(classification: Dict) -> str:
    """
    Generate human-readable benchmark summary

    Args:
        classification: Result from classify_product()

    Returns:
        Formatted string with benchmark data
    """
    benchmark = classification.get("benchmark_data", {})
    metrics = benchmark.get("metrics", {})

    # Handle SaaS price tiers
    if classification.get("price_tier") and "price_tiers" in benchmark:
        price_tier = classification["price_tier"]
        metrics = benchmark["price_tiers"].get(price_tier, {})

    # Handle Services service types
    if classification.get("service_type") and "service_types" in benchmark:
        service_type = classification["service_type"]
        metrics = benchmark["service_types"].get(service_type, {})

    if not metrics:
        return "No benchmark data available"

    cpa = metrics.get("cpa", {})
    roas = metrics.get("roas", {})

    summary = f"""
INDUSTRY BENCHMARKS ({classification.get('subcategory_name', 'Unknown')})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TARGET CPA:
  Range: ${cpa.get('min', 0)}-${cpa.get('max', 0)}
  Median: ${cpa.get('median', 0)}

TARGET ROAS:
  Range: {roas.get('min', 0):.1f}x-{roas.get('max', 0):.1f}x
  Median: {roas.get('median', 0):.1f}x
"""

    # Add platform recommendations
    platforms = benchmark.get("platforms", {})
    if platforms:
        summary += "\nBEST PLATFORMS:\n"
        sorted_platforms = sorted(
            platforms.items(),
            key=lambda x: x[1].get("market_share", 0),
            reverse=True
        )
        for platform_name, platform_data in sorted_platforms[:3]:
            tier = platform_data.get("performance_tier", "moderate")
            cpa_avg = platform_data.get("avg_cpa", 0)
            summary += f"  • {platform_name.title()}: {tier} (avg CPA: ${cpa_avg})\n"

    summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    return summary
