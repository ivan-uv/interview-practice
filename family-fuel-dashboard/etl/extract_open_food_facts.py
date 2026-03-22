"""
Extract food product data from the Open Food Facts API.

Rate limits (as of 2026):
  - 10 req/min for search queries
  - 100 req/min for product lookups by barcode

Strategy:
  - Use the openfoodfacts Python SDK (v5.0.1+).
  - Search by category to get packaged foods relevant to family meal planning.
  - Sleep 6 seconds between search calls to respect the 10/min limit.
  - Fetch at most 20 products per category per run.
"""
import os
import time
import logging

import openfoodfacts

log = logging.getLogger(__name__)

USER_AGENT = os.getenv("OFF_USER_AGENT", "FamilyFuelDashboard/1.0 (portfolio-project)")


def fetch_off_products(
    categories: list[str] | None = None,
    max_per_category: int = 20,
) -> list[dict]:
    """
    Fetch food products from Open Food Facts by category.

    Args:
        categories: List of category strings to search (e.g. "breakfast cereals").
        max_per_category: Maximum products to fetch per category.

    Returns:
        List of Open Food Facts product dicts.
    """
    categories = categories or ["breakfast cereals", "snacks", "dairy"]
    api = openfoodfacts.API(user_agent=USER_AGENT)
    all_products: list[dict] = []

    for category in categories:
        log.debug(f"Open Food Facts: searching category '{category}'")
        try:
            result = api.product.text_search(
                category,
                page_size=max_per_category,
                fields=["code", "product_name", "nutriments", "nutriscore_grade",
                        "nova_group", "allergens_tags", "categories_tags",
                        "ingredients_text", "image_url"],
            )
            products = result.get("products", [])
            log.debug(f"Open Food Facts: got {len(products)} products for '{category}'")
            all_products.extend(products)

            # 10 req/min limit → sleep 6s between calls
            time.sleep(6)

        except Exception as exc:
            log.error(f"Open Food Facts search failed for '{category}': {exc}")

    # Deduplicate by barcode
    seen: set[str] = set()
    unique: list[dict] = []
    for p in all_products:
        code = p.get("code", "")
        if code and code not in seen:
            seen.add(code)
            unique.append(p)

    log.info(f"Open Food Facts: fetched {len(unique)} unique products across {len(categories)} categories")
    return unique


def fetch_product_by_barcode(barcode: str) -> dict | None:
    """
    Fetch a single product by barcode (e.g., from scanning a grocery item).

    Args:
        barcode: The product barcode string.

    Returns:
        Product dict or None if not found.
    """
    api = openfoodfacts.API(user_agent=USER_AGENT)
    try:
        result = api.product.get(barcode)
        if result and result.get("status") == 1:
            return result.get("product")
    except Exception as exc:
        log.error(f"Open Food Facts barcode lookup failed for '{barcode}': {exc}")
    return None
