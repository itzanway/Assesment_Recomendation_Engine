"""
Crawler for SHL Product Catalogue

This script crawls SHL's public product catalogue page and builds a JSON
file of "Individual Test Solutions" (excluding "Pre-packaged Job Solutions").

NOTE:
- This script is intended to be run locally by you; it will make HTTP
  requests to shl.com and parse the HTML structure as it exists today.
- The HTML structure of the site may change. If it does, you may need to
  adjust CSS selectors below.
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import List, Optional

import requests
from bs4 import BeautifulSoup


CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_PATH = "product_catalogue.json"
REQUEST_TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 0.5  # polite crawling


@dataclass
class Assessment:
    id: str
    name: str
    url: str
    category: str = "individual_test_solution"
    type: Optional[str] = None
    description: Optional[str] = None


def _fetch(url: str) -> Optional[str]:
    """Fetch a URL and return its text, or None on error."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.text
        print(f"[WARN] Got status {resp.status_code} for {url}")
    except Exception as exc:
        print(f"[ERROR] Failed to fetch {url}: {exc}")
    return None


def _extract_product_links(html: str) -> List[str]:
    """
    Extract links to individual test solution pages from the catalogue HTML.

    This relies on the current site structure. You may need to tweak the CSS
    selectors if SHL updates the catalogue page layout.
    """
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []

    # Example strategy:
    # - Find product cards in the main catalogue grid/list
    # - Filter out anything that is clearly "Pre-packaged Job Solutions"
    for a in soup.select("a"):
        href = a.get("href") or ""
        text = (a.get_text() or "").strip()
        href_lower = href.lower()
        text_lower = text.lower()

        # Basic heuristics to capture product pages and avoid non-product links.
        if not href_lower.startswith("http"):
            continue
        if "product-catalog" in href_lower:
            # main index page itself
            continue
        # Skip obvious non-product areas if they appear in the URL.
        if "pre-packaged-job-solutions" in href_lower or "pre-packaged" in text_lower:
            continue

        # Very rough filter: SHL product pages tend to live under /solutions/products/
        if "/solutions/products/" in href_lower:
            links.append(href)

    # De-duplicate while preserving order
    seen = set()
    unique_links: List[str] = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return unique_links


def _slug_from_url(url: str) -> str:
    """Create a stable-ish ID from the product URL."""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = slug or "product"
    return slug.replace("-", "_").replace(" ", "_")


def _parse_product_page(url: str, html: str) -> Assessment:
    """
    Parse a single product page to extract core fields.
    This is intentionally conservative: we mainly want name, url, description.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Name: usually in <h1>
    h1 = soup.find("h1")
    name = (h1.get_text() if h1 else "").strip() or "SHL Assessment"

    # Description: take main content text (may need adjustment per layout).
    # Fallback to full page text if we can't find a clear main content element.
    main = soup.find("main")
    if main:
        desc_text = main.get_text(" ", strip=True)
    else:
        desc_text = soup.get_text(" ", strip=True)

    # Heuristic "type" from text snippets if any labels exist.
    type_value: Optional[str] = None
    possible_types = ["cognitive", "personality", "situational", "motivation", "development", "feedback"]
    lower_desc = desc_text.lower()
    for t in possible_types:
        if t in lower_desc:
            type_value = t
            break

    return Assessment(
        id=_slug_from_url(url),
        name=name,
        url=url,
        type=type_value,
        description=desc_text,
    )


def crawl_catalog() -> List[Assessment]:
    """Crawl the SHL catalog and return a list of assessments."""
    print(f"[INFO] Fetching catalogue index: {CATALOG_URL}")
    index_html = _fetch(CATALOG_URL)
    if not index_html:
        raise RuntimeError("Failed to fetch catalogue index page.")

    product_links = _extract_product_links(index_html)
    print(f"[INFO] Found {len(product_links)} candidate product links to crawl.")

    assessments: List[Assessment] = []

    for i, link in enumerate(product_links, start=1):
        print(f"[INFO] ({i}/{len(product_links)}) Fetching product page: {link}")
        html = _fetch(link)
        if not html:
            continue
        assessment = _parse_product_page(link, html)
        assessments.append(assessment)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"[INFO] Crawled {len(assessments)} assessments.")
    if len(assessments) < 377:
        print(
            f"[WARN] Only {len(assessments)} assessments found. "
            "The assignment expects at least 377 Individual Test Solutions. "
            "You may need to refine the selectors in _extract_product_links()."
        )

    return assessments


def save_catalog(assessments: List[Assessment], path: str = OUTPUT_PATH) -> None:
    """Save assessments to JSON in the same structure used by the app."""
    data = {
        "assessments": [asdict(a) for a in assessments],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Saved {len(assessments)} assessments to {path}")


if __name__ == "__main__":
    asses = crawl_catalog()
    save_catalog(asses, OUTPUT_PATH)


