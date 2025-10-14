#!/usr/bin/env python3
"""
Test script for URL scraping functionality

Usage:
    python test_url_scraper.py <product_url>

Example:
    python test_url_scraper.py https://www.example.com/product
"""

import sys
import json
from src.modules.url_scraper import scrape_product_url


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_url_scraper.py <product_url>")
        print("Example: python test_url_scraper.py https://www.example.com/product")
        return 1

    url = sys.argv[1]

    print("=" * 60)
    print(f"Testing URL Scraper")
    print("=" * 60)
    print(f"\nURL: {url}\n")

    print("Scraping...")
    facts = scrape_product_url(url)

    print("\n" + "=" * 60)
    print("Extracted Facts")
    print("=" * 60)

    if not facts:
        print("No facts extracted")
        return 1

    if 'error' in facts:
        print(f"Error: {facts['error']['value']}")
        return 1

    # Display facts
    for key, fact in facts.items():
        value = fact.get('value')
        confidence = fact.get('confidence', 0)
        source = fact.get('source', 'unknown')

        print(f"\n{key}:")
        print(f"  Value: {value}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Source: {source}")

    # Save to JSON for inspection
    output_file = "test_url_extraction.json"
    with open(output_file, 'w') as f:
        # Convert facts to serializable format
        serializable_facts = {
            k: {
                'value': str(v['value']) if isinstance(v['value'], list) else v['value'],
                'confidence': v['confidence'],
                'source': v['source']
            }
            for k, v in facts.items()
        }
        json.dump(serializable_facts, f, indent=2)

    print(f"\n✓ Results saved to {output_file}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
