#!/usr/bin/env python3
"""Fetch HTML document with CSS and resources inlined for complete archival."""

import sys
import re
import base64
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


def fetch_resource(url: str, headers: dict, timeout: int = 30) -> bytes:
    """Fetch a resource and return its content as bytes.

    Args:
        url: URL to fetch
        headers: HTTP headers
        timeout: Request timeout

    Returns:
        Resource content as bytes
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"⚠️  Failed to fetch {url}: {e}", file=sys.stderr)
        return b""


def inline_css(soup: BeautifulSoup, base_url: str, headers: dict) -> None:
    """Inline external CSS stylesheets.

    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs
        headers: HTTP headers
    """
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if not href:
            continue

        css_url = urljoin(base_url, href)
        print(f"📥 Fetching CSS: {css_url}")

        css_content = fetch_resource(css_url, headers)
        if css_content:
            # Create inline style tag
            style_tag = soup.new_tag('style')
            style_tag.string = css_content.decode('utf-8', errors='ignore')
            link.replace_with(style_tag)


def inline_images(soup: BeautifulSoup, base_url: str, headers: dict) -> None:
    """Convert external images to base64 data URIs.

    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs
        headers: HTTP headers
    """
    for img in soup.find_all('img'):
        src = img.get('src')
        if not src or src.startswith('data:'):
            continue

        img_url = urljoin(base_url, src)
        print(f"🖼️  Fetching image: {img_url}")

        img_content = fetch_resource(img_url, headers)
        if img_content:
            # Determine MIME type from extension
            ext = urlparse(img_url).path.split('.')[-1].lower()
            mime_types = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'svg': 'image/svg+xml',
                'webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/png')

            # Convert to base64 data URI
            b64_data = base64.b64encode(img_content).decode('utf-8')
            img['src'] = f"data:{mime_type};base64,{b64_data}"


def fetch_document(url: str, output_path: str) -> None:
    """Fetch HTML document with all resources inlined.

    Args:
        url: URL to fetch
        output_path: Path to save the HTML file
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        print(f"🌐 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html5lib')

        # Inline external CSS
        inline_css(soup, url, headers)

        # Inline images (optional, can make file very large)
        # inline_images(soup, url, headers)

        # Remove dynamic content that changes frequently
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
