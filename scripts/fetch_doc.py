#!/usr/bin/env python3
"""Fetch HTML document with proper encoding handling."""

import sys
import requests
from bs4 import BeautifulSoup


def fetch_document(url: str, output_path: str) -> None:
    """Fetch HTML document and save with normalized formatting.

    Args:
        url: URL to fetch
        output_path: Path to save the HTML file
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse and prettify HTML for better diff readability
        soup = BeautifulSoup(response.content, 'html5lib')

        # Remove dynamic content that changes frequently (scripts, style timestamps, etc.)
        for tag in soup.find_all(['script', 'noscript']):
            tag.decompose()

        # Remove common timestamp/session metadata
        for meta in soup.find_all('meta'):
            if meta.get('name') in ['generator', 'date', 'timestamp']:
                meta.decompose()

        # Prettify for human-readable diffs
        html_content = soup.prettify()

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Successfully fetched and saved to {output_path}")
        print(f"📄 File size: {len(html_content)} bytes")

    except requests.RequestException as e:
        print(f"❌ Failed to fetch document: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error processing document: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: fetch_doc.py <url> <output_path>")
        sys.exit(1)

    fetch_document(sys.argv[1], sys.argv[2])
