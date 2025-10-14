"""
URL scraping and product information extraction
"""

import json
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch HTML content from a URL with error handling

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content as string, or None if fetch fails
    """
    try:
        # Add user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        return response.text

    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {str(e)}")
        return None


def extract_structured_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract structured data from HTML (JSON-LD, Open Graph, meta tags)

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        Dictionary of extracted structured data
    """
    data = {}

    # Extract JSON-LD structured data (schema.org)
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            ld_data = json.loads(script.string)

            # Look for Product schema
            if isinstance(ld_data, dict):
                if ld_data.get('@type') == 'Product':
                    data['json_ld'] = ld_data
                    break
            elif isinstance(ld_data, list):
                for item in ld_data:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        data['json_ld'] = item
                        break
        except (json.JSONDecodeError, AttributeError):
            continue

    # Extract Open Graph tags
    og_tags = {}
    for tag in soup.find_all('meta', property=re.compile(r'^og:')):
        prop = tag.get('property', '')
        content = tag.get('content', '')
        if prop and content:
            og_tags[prop] = content

    if og_tags:
        data['open_graph'] = og_tags

    # Extract meta tags
    meta_tags = {}
    for tag in soup.find_all('meta'):
        name = tag.get('name', '') or tag.get('property', '')
        content = tag.get('content', '')
        if name and content:
            meta_tags[name] = content

    if meta_tags:
        data['meta'] = meta_tags

    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        data['title'] = title_tag.get_text().strip()

    return data


def extract_main_content(soup: BeautifulSoup, max_length: int = 2000) -> str:
    """
    Extract main text content from page, avoiding navigation/footer

    Args:
        soup: BeautifulSoup parsed HTML
        max_length: Maximum length of extracted text

    Returns:
        Cleaned main content text
    """
    # Remove script, style, nav, footer tags
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    # Try to find main content area
    main_content = None

    # Look for common main content containers
    for selector in ['main', 'article', '[role="main"]', '.product-description',
                     '#product-description', '.content', '#content']:
        main_content = soup.select_one(selector)
        if main_content:
            break

    # Fallback to body
    if not main_content:
        main_content = soup.find('body')

    if main_content:
        # Extract text with some structure
        text = main_content.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + '...'

        return text

    return ""


def extract_with_llm(structured_data: Dict[str, Any],
                     main_content: str,
                     url: str) -> Dict[str, Dict[str, Any]]:
    """
    Use LLM to extract product information from scraped data

    Args:
        structured_data: Extracted structured data (JSON-LD, OG tags, etc.)
        main_content: Main text content from page
        url: Original URL for context

    Returns:
        Dictionary of facts with confidence scores
    """
    from ..llm.gemini import get_gemini

    facts = {}

    # Build context for LLM
    context_parts = []

    if structured_data.get('json_ld'):
        context_parts.append(f"JSON-LD Product Data:\n{json.dumps(structured_data['json_ld'], indent=2)}")

    if structured_data.get('open_graph'):
        context_parts.append(f"\nOpen Graph Tags:\n{json.dumps(structured_data['open_graph'], indent=2)}")

    if structured_data.get('meta'):
        meta = structured_data['meta']
        relevant_meta = {k: v for k, v in meta.items()
                        if any(keyword in k.lower() for keyword in ['description', 'title', 'keywords'])}
        if relevant_meta:
            context_parts.append(f"\nMeta Tags:\n{json.dumps(relevant_meta, indent=2)}")

    if structured_data.get('title'):
        context_parts.append(f"\nPage Title: {structured_data['title']}")

    if main_content:
        context_parts.append(f"\nMain Content (excerpt):\n{main_content[:1000]}")

    context = "\n".join(context_parts)

    if not context.strip():
        return facts

    try:
        gemini = get_gemini()

        extraction_prompt = f"""
Analyze this product page data and extract key information for advertising campaign setup.

URL: {url}

{context}

Extract the following information (return "null" for any field you cannot determine with confidence):

1. Product name and description (1-2 sentences)
2. Pricing information (if available)
3. Target audience hints based on product features and language
4. Key product features/benefits (top 3-5)
5. Product category/industry

Respond with JSON:
{{
  "product_name": "name or null",
  "product_description": "clear 1-2 sentence description or null",
  "price": "price with currency or null",
  "target_audience": "inferred audience description or null",
  "key_features": ["feature1", "feature2"] or [],
  "product_category": "category or null",
  "confidence_notes": "explain what data was available and what was inferred"
}}
"""

        result = gemini.generate_json(
            prompt=extraction_prompt,
            temperature=0.3,
            task_name="Product URL Extraction"
        )

        # Build facts from LLM response with confidence scores

        # Product description - highest priority
        if result.get('product_description') and result['product_description'] != "null":
            description = result['product_description']

            # Add product name if available
            if result.get('product_name') and result['product_name'] != "null":
                description = f"{result['product_name']} - {description}"

            # Determine confidence based on source
            confidence = 0.9  # High confidence from structured data
            if 'json_ld' in structured_data or 'description' in structured_data.get('meta', {}):
                confidence = 0.95  # Very high if from structured data
            elif main_content and len(main_content) < 200:
                confidence = 0.7  # Lower if limited content

            facts['product_description'] = {
                'value': description,
                'confidence': confidence,
                'source': 'url_scrape'
            }

        # Target audience (inferred, medium confidence)
        if result.get('target_audience') and result['target_audience'] != "null":
            facts['target_audience'] = {
                'value': result['target_audience'],
                'confidence': 0.7,  # Inferred data
                'source': 'url_scrape'
            }

        # Product category (for context)
        if result.get('product_category') and result['product_category'] != "null":
            facts['product_category'] = {
                'value': result['product_category'],
                'confidence': 0.8,
                'source': 'url_scrape'
            }

        # Price information (can help determine budget/CPA targets)
        if result.get('price') and result['price'] != "null":
            facts['product_price'] = {
                'value': result['price'],
                'confidence': 0.9,
                'source': 'url_scrape'
            }

        # Key features (for creative strategy)
        if result.get('key_features') and len(result.get('key_features', [])) > 0:
            facts['product_features'] = {
                'value': result['key_features'],
                'confidence': 0.85,
                'source': 'url_scrape'
            }

    except Exception as e:
        print(f"LLM extraction error: {str(e)}")

    return facts


def scrape_product_url(url: str) -> Dict[str, Dict[str, Any]]:
    """
    Main entry point: scrape URL and extract product information

    Args:
        url: Product page URL

    Returns:
        Dictionary of facts with confidence scores
    """
    facts = {}

    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {
                'error': {
                    'value': f"Invalid URL format: {url}",
                    'confidence': 1.0,
                    'source': 'url_scrape'
                }
            }
    except Exception:
        return {
            'error': {
                'value': f"Could not parse URL: {url}",
                'confidence': 1.0,
                'source': 'url_scrape'
            }
        }

    # Fetch HTML
    html = fetch_url(url)
    if not html:
        return {
            'error': {
                'value': f"Could not fetch URL: {url}",
                'confidence': 1.0,
                'source': 'url_scrape'
            }
        }

    # Parse HTML
    soup = BeautifulSoup(html, 'lxml')

    # Extract structured data
    structured_data = extract_structured_data(soup)

    # Extract main content
    main_content = extract_main_content(soup)

    # Use LLM to extract product information
    facts = extract_with_llm(structured_data, main_content, url)

    # Store URL for reference
    facts['source_url'] = {
        'value': url,
        'confidence': 1.0,
        'source': 'url_scrape'
    }

    return facts
